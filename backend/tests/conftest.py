"""Shared pytest fixtures."""
import pytest
from memory.models import CareerGoals, JobOpportunity, RemotePolicy, WorkStyle


@pytest.fixture
def goals_remote_senior_pm() -> CareerGoals:
    """Senior PM targeting Bangalore/remote fintech, min ₹80L/year ($96k USD approx)."""
    return CareerGoals(
        target_roles=["Senior Product Manager", "Product Lead", "VP Product"],
        min_comp_usd=96_000,  # ≈ ₹80L at 83x
        preferred_locations=["Bangalore", "Hyderabad"],
        open_to_relocation=False,
        work_style=WorkStyle.REMOTE,
        must_have_criteria=["fintech", "payments", "SaaS"],
        dealbreakers=["crypto", "trading"],
        company_stages=["Series A", "Series B", "Series C"],
    )


@pytest.fixture
def opp_high_match() -> JobOpportunity:
    """Luminary Pay — senior PM, remote, ₹90L, fintech. Should score high."""
    return JobOpportunity(
        contact_id="contact_001",
        company="Luminary Pay",
        role="Senior Product Manager – Payments",
        comp_range_min=80_00_000,   # ₹80L
        comp_range_max=1_00_00_000,  # ₹1Cr
        location="Bangalore",
        remote_policy=RemotePolicy.REMOTE,
        jd_summary="Fintech SaaS payments product role at Series B startup.",
    )


@pytest.fixture
def opp_crypto_dealbreaker() -> JobOpportunity:
    """CryptoEdge — crypto trading PM. Should score 0 due to dealbreaker."""
    return JobOpportunity(
        contact_id="contact_002",
        company="CryptoEdge",
        role="Product Lead – Trading Platform",
        comp_range_min=45_00_000,   # ₹45L
        comp_range_max=60_00_000,   # ₹60L
        location="Mumbai",
        remote_policy=RemotePolicy.ONSITE,
        jd_summary="Crypto exchange trading platform PM role.",
    )


@pytest.fixture
def opp_vp_remote() -> JobOpportunity:
    """Orbit Analytics — VP Product, fully remote, ₹1.2-1.5Cr. Strong match."""
    return JobOpportunity(
        contact_id="contact_003",
        company="Orbit Analytics",
        role="VP of Product",
        comp_range_min=1_20_00_000,  # ₹1.2Cr
        comp_range_max=1_50_00_000,  # ₹1.5Cr
        location="Remote",
        remote_policy=RemotePolicy.REMOTE,
        jd_summary="Enterprise SaaS analytics product. AI-powered. Series A. Remote-first.",
    )


@pytest.fixture
def opp_no_comp() -> JobOpportunity:
    """Unknown company — comp not disclosed. Should score mid."""
    return JobOpportunity(
        contact_id="contact_004",
        company="Stealth Fintech",
        role="Senior PM",
        comp_range_min=None,
        comp_range_max=None,
        location="Bangalore",
        remote_policy=RemotePolicy.HYBRID,
        jd_summary="Stealth fintech startup senior PM role in payments.",
    )
