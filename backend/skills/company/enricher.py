"""
Company Enricher — enriches job opportunities with external company data.
Tier 1: Parse JD text for signals (always available)
Tier 2: Wikipedia API for company description (free)
Tier 3: Apollo API for detailed enrichment (optional, requires API key)
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CompanyEnrichment:
    employee_count: int | None = None
    funding_stage: str = ""           # e.g. "Series B", "Public"
    funding_total_usd: int | None = None
    industry: str = ""
    description: str = ""
    glassdoor_rating: float | None = None
    news_snippets: list[str] = field(default_factory=list)
    source: str = "jd_parsing"        # jd_parsing, wikipedia, apollo


# ─── Tier 1: JD Text Parsing ────────────────────────────────────────────────

_EMPLOYEE_PATTERNS = [
    re.compile(r"[~≈]?\s*(\d[\d,]*)\s*(?:\+\s*)?(?:employees?|people|team members?|staff)", re.IGNORECASE),
    re.compile(r"(?:team of|company of|over|about)\s+(\d[\d,]*)\s*(?:\+\s*)?(?:employees?|people)?", re.IGNORECASE),
]

_FUNDING_STAGE_PATTERNS = [
    re.compile(r"\b(Series\s+[A-F])\b", re.IGNORECASE),
    re.compile(r"\b(Seed(?:\s+stage)?)\b", re.IGNORECASE),
    re.compile(r"\b(Pre-?Seed)\b", re.IGNORECASE),
    re.compile(r"\b(IPO|publicly?\s+traded|public\s+company|NYSE|NASDAQ)\b", re.IGNORECASE),
]

_FUNDING_AMOUNT_PATTERN = re.compile(
    r"\$\s*(\d[\d,.]*)\s*(M|MM|B|million|billion)\s*(?:raised|funding|round|in\s+funding)?",
    re.IGNORECASE,
)

_INDUSTRY_KEYWORDS = [
    "fintech", "healthtech", "edtech", "biotech", "medtech", "cleantech",
    "saas", "e-commerce", "ecommerce", "ai", "machine learning", "cybersecurity",
    "blockchain", "crypto", "devtools", "developer tools", "cloud", "infrastructure",
    "enterprise", "consumer", "marketplace", "logistics", "supply chain",
    "real estate", "proptech", "insurtech", "agritech", "legaltech",
    "gaming", "media", "entertainment", "social", "advertising", "adtech",
    "robotics", "autonomous", "iot", "hardware", "semiconductor",
    "telecom", "telecommunications", "energy", "sustainability",
    "aerospace", "defense", "government", "automotive",
]


def _parse_jd(jd_text: str) -> CompanyEnrichment:
    """Extract company signals from job description text."""
    enrichment = CompanyEnrichment(source="jd_parsing")

    if not jd_text:
        return enrichment

    # Employee count
    for pattern in _EMPLOYEE_PATTERNS:
        match = pattern.search(jd_text)
        if match:
            count_str = match.group(1).replace(",", "")
            try:
                enrichment.employee_count = int(count_str)
            except ValueError:
                pass
            break

    # Funding stage
    for pattern in _FUNDING_STAGE_PATTERNS:
        match = pattern.search(jd_text)
        if match:
            raw = match.group(1).strip()
            if re.match(r"(?i)IPO|NYSE|NASDAQ|publicly?\s+traded|public\s+company", raw):
                enrichment.funding_stage = "Public"
            else:
                enrichment.funding_stage = raw.title()
            break

    # Funding amount
    amount_match = _FUNDING_AMOUNT_PATTERN.search(jd_text)
    if amount_match:
        raw_num = float(amount_match.group(1).replace(",", ""))
        multiplier_str = amount_match.group(2).lower()
        if multiplier_str in ("m", "mm", "million"):
            enrichment.funding_total_usd = int(raw_num * 1_000_000)
        elif multiplier_str in ("b", "billion"):
            enrichment.funding_total_usd = int(raw_num * 1_000_000_000)

    # Industry keywords
    jd_lower = jd_text.lower()
    found_industries = [kw for kw in _INDUSTRY_KEYWORDS if kw in jd_lower]
    if found_industries:
        enrichment.industry = found_industries[0]

    return enrichment


# ─── Tier 2: Wikipedia ───────────────────────────────────────────────────────

async def _enrich_from_wikipedia(company_name: str, enrichment: CompanyEnrichment) -> CompanyEnrichment:
    """Fetch a short company description from Wikipedia REST API."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(company_name)}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"User-Agent": "CadburyAssistant/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                enrichment.description = data.get("extract", "")
                enrichment.source = "wikipedia"
                logger.debug("Wikipedia enrichment succeeded for %s", company_name)
            else:
                logger.debug("Wikipedia returned %d for %s", resp.status_code, company_name)
    except (httpx.HTTPError, httpx.TimeoutException, Exception) as exc:
        logger.warning("Wikipedia enrichment failed for %s: %s", company_name, exc)

    return enrichment


# ─── Tier 3: Apollo ──────────────────────────────────────────────────────────

async def _enrich_from_apollo(
    company_name: str,
    enrichment: CompanyEnrichment,
    apollo_api_key: str,
) -> CompanyEnrichment:
    """Fetch detailed company data from Apollo.io API."""
    # Derive a plausible domain from the company name
    domain = f"{company_name.lower().replace(' ', '')}.com"
    url = "https://api.apollo.io/api/v1/organizations/enrich"
    params = {"domain": domain}
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": apollo_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                org = data.get("organization", {})
                if org:
                    enrichment.employee_count = (
                        org.get("estimated_num_employees") or enrichment.employee_count
                    )
                    enrichment.industry = org.get("industry") or enrichment.industry
                    enrichment.description = org.get("short_description") or enrichment.description
                    enrichment.funding_total_usd = (
                        org.get("total_funding") or enrichment.funding_total_usd
                    )
                    enrichment.funding_stage = (
                        org.get("latest_funding_stage") or enrichment.funding_stage
                    )
                    enrichment.source = "apollo"
                    logger.info("Apollo enrichment succeeded for %s", company_name)
            else:
                logger.debug("Apollo returned %d for %s", resp.status_code, company_name)
    except (httpx.HTTPError, httpx.TimeoutException, Exception) as exc:
        logger.warning("Apollo enrichment failed for %s: %s", company_name, exc)

    return enrichment


# ─── Public API ──────────────────────────────────────────────────────────────

async def enrich_company(
    company_name: str,
    jd_text: str = "",
    apollo_api_key: str = "",
) -> CompanyEnrichment:
    """
    Enrich company data using available sources.

    Applies enrichment tiers in order, with each tier overriding empty fields
    from the previous tier:
      1. JD text parsing (always available, no network)
      2. Wikipedia REST API (free, best-effort)
      3. Apollo.io API (requires API key, most detailed)
    """
    # Tier 1: Parse JD text (always runs)
    enrichment = _parse_jd(jd_text)
    logger.debug(
        "Tier 1 (JD parsing) for %s: employees=%s, stage=%s, funding=%s",
        company_name, enrichment.employee_count, enrichment.funding_stage,
        enrichment.funding_total_usd,
    )

    # Tier 2: Wikipedia (best-effort, no key needed)
    enrichment = await _enrich_from_wikipedia(company_name, enrichment)

    # Tier 3: Apollo (only if API key provided)
    if apollo_api_key:
        enrichment = await _enrich_from_apollo(company_name, enrichment, apollo_api_key)
    else:
        logger.debug("Skipping Apollo enrichment for %s (no API key)", company_name)

    return enrichment
