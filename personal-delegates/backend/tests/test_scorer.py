"""Unit tests for the recruiter opportunity scorer."""
import pytest
from memory.models import CareerGoals, JobOpportunity, RemotePolicy, WorkStyle
from delegates.recruiter.scorer import (
    score,
    score_comp,
    score_role,
    score_location,
    score_criteria,
)


class TestScoreComp:
    def test_at_minimum_comp_returns_one(self, goals_remote_senior_pm, opp_high_match):
        # opp midpoint = ₹90L, goals min = ₹80L → ratio ~1.12 → should be 1.0
        result = score_comp(opp_high_match, goals_remote_senior_pm)
        assert result == 1.0

    def test_well_below_min_comp_returns_low(self, goals_remote_senior_pm):
        opp = JobOpportunity(
            contact_id="x",
            company="X",
            role="PM",
            comp_range_min=20_00_000,  # ₹20L — far below ₹80L
            comp_range_max=25_00_000,
            location="Bangalore",
            remote_policy=RemotePolicy.REMOTE,
        )
        result = score_comp(opp, goals_remote_senior_pm)
        assert result < 0.2

    def test_no_comp_disclosed_returns_penalty(self, goals_remote_senior_pm, opp_no_comp):
        result = score_comp(opp_no_comp, goals_remote_senior_pm)
        assert result == 0.3

    def test_no_goal_set_returns_neutral(self, opp_high_match):
        goals = CareerGoals(min_comp_usd=0)
        result = score_comp(opp_high_match, goals)
        assert result == 0.5


class TestScoreRole:
    def test_exact_title_match(self, goals_remote_senior_pm, opp_high_match):
        result = score_role(opp_high_match, goals_remote_senior_pm)
        assert result == 1.0

    def test_dealbreaker_title_returns_zero(self, goals_remote_senior_pm, opp_crypto_dealbreaker):
        # "trading" is a dealbreaker and appears in the role title
        result = score_role(opp_crypto_dealbreaker, goals_remote_senior_pm)
        assert result == 0.0

    def test_vp_product_matches_target(self, goals_remote_senior_pm, opp_vp_remote):
        result = score_role(opp_vp_remote, goals_remote_senior_pm)
        assert result > 0.5  # "VP Product" is a target role

    def test_unrelated_role_scores_low(self, goals_remote_senior_pm):
        opp = JobOpportunity(
            contact_id="x", company="X", role="Backend Engineer",
            location="Bangalore", remote_policy=RemotePolicy.REMOTE,
        )
        result = score_role(opp, goals_remote_senior_pm)
        assert result == 0.0


class TestScoreLocation:
    def test_remote_candidate_remote_role(self, goals_remote_senior_pm, opp_high_match):
        # candidate wants remote, role is remote
        result = score_location(opp_high_match, goals_remote_senior_pm)
        assert result == 1.0

    def test_remote_candidate_onsite_role_preferred_city(
        self, goals_remote_senior_pm, opp_crypto_dealbreaker
    ):
        # candidate wants remote, Mumbai onsite, Mumbai not in preferred locations
        result = score_location(opp_crypto_dealbreaker, goals_remote_senior_pm)
        assert result < 0.5

    def test_remote_candidate_hybrid_role(self, goals_remote_senior_pm, opp_no_comp):
        # candidate wants remote, hybrid role
        result = score_location(opp_no_comp, goals_remote_senior_pm)
        assert result == 0.5


class TestScoreCriteria:
    def test_criteria_fully_met(self, goals_remote_senior_pm, opp_high_match):
        # opp_high_match has "fintech" and "payments" in summary, "SaaS" also present
        result = score_criteria(opp_high_match, goals_remote_senior_pm)
        assert result > 0.5

    def test_no_criteria_returns_neutral(self, opp_high_match):
        goals = CareerGoals(must_have_criteria=[])
        result = score_criteria(opp_high_match, goals)
        assert result == 0.5

    def test_crypto_no_criteria_overlap(self, goals_remote_senior_pm, opp_crypto_dealbreaker):
        # "fintech", "payments", "SaaS" not in crypto JD
        result = score_criteria(opp_crypto_dealbreaker, goals_remote_senior_pm)
        assert result == 0.0


class TestOverallScore:
    def test_high_match_scores_above_threshold(self, goals_remote_senior_pm, opp_high_match):
        overall, breakdown = score(opp_high_match, goals_remote_senior_pm)
        assert overall >= 0.65, f"Expected high match, got {overall}"
        assert breakdown.role == 1.0
        assert breakdown.comp == 1.0
        assert breakdown.location == 1.0

    def test_dealbreaker_scores_zero(self, goals_remote_senior_pm, opp_crypto_dealbreaker):
        overall, breakdown = score(opp_crypto_dealbreaker, goals_remote_senior_pm)
        assert overall == 0.0
        assert breakdown.role == 0.0

    def test_vp_remote_scores_high(self, goals_remote_senior_pm, opp_vp_remote):
        overall, breakdown = score(opp_vp_remote, goals_remote_senior_pm)
        assert overall >= 0.60, f"Expected good match for VP remote, got {overall}"

    def test_no_comp_reduces_score(self, goals_remote_senior_pm, opp_no_comp):
        overall, _ = score(opp_no_comp, goals_remote_senior_pm)
        # Good role+location but comp unknown → should be mid range
        assert 0.30 <= overall <= 0.80

    def test_score_is_normalized(self, goals_remote_senior_pm, opp_high_match):
        overall, _ = score(opp_high_match, goals_remote_senior_pm)
        assert 0.0 <= overall <= 1.0

    def test_breakdown_sums_are_valid(self, goals_remote_senior_pm, opp_high_match):
        _, breakdown = score(opp_high_match, goals_remote_senior_pm)
        for val in [breakdown.role, breakdown.comp, breakdown.location, breakdown.criteria]:
            assert 0.0 <= val <= 1.0
