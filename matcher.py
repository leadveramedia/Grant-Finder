"""
Grant eligibility matcher for MARV Media.
Scores grants based on how well they match the company profile.
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import date

from sources.base_source import Grant
from company_profile import get_eligibility_attributes, MARV_PROFILE
from config import MIN_ELIGIBILITY_SCORE

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of matching a grant against company profile."""
    grant: Grant
    score: float  # 0.0 to 1.0
    reasons: List[str]  # Why it matched
    warnings: List[str]  # Potential issues
    disqualified: bool  # Definitely not eligible
    disqualification_reason: str = ""


class GrantMatcher:
    """Match grants against MARV Media's eligibility criteria."""

    def __init__(self):
        self.attrs = get_eligibility_attributes()
        self.profile = MARV_PROFILE

    def match_grant(self, grant: Grant) -> MatchResult:
        """
        Score a single grant for eligibility.

        Returns a MatchResult with:
        - score: 0.0 to 1.0 (higher = better match)
        - reasons: List of positive matching factors
        - warnings: List of potential concerns
        - disqualified: True if definitely not eligible
        """
        score = 0.0
        max_score = 0.0
        reasons = []
        warnings = []

        # Check for disqualifying factors first
        disqualified, disq_reason = self._check_disqualifiers(grant)
        if disqualified:
            return MatchResult(
                grant=grant,
                score=0.0,
                reasons=[],
                warnings=[],
                disqualified=True,
                disqualification_reason=disq_reason,
            )

        # Location matching (weight: 20%)
        max_score += 0.20
        loc_score, loc_reasons = self._score_location(grant)
        score += loc_score * 0.20
        reasons.extend(loc_reasons)

        # Revenue/size matching (weight: 20%)
        max_score += 0.20
        size_score, size_reasons, size_warnings = self._score_size(grant)
        score += size_score * 0.20
        reasons.extend(size_reasons)
        warnings.extend(size_warnings)

        # Ownership requirements (weight: 25%)
        max_score += 0.25
        own_score, own_reasons = self._score_ownership(grant)
        score += own_score * 0.25
        reasons.extend(own_reasons)

        # Industry alignment (weight: 15%)
        max_score += 0.15
        ind_score, ind_reasons = self._score_industry(grant)
        score += ind_score * 0.15
        reasons.extend(ind_reasons)

        # Certification requirements (weight: 10%)
        max_score += 0.10
        cert_score, cert_reasons, cert_warnings = self._score_certifications(grant)
        score += cert_score * 0.10
        reasons.extend(cert_reasons)
        warnings.extend(cert_warnings)

        # Deadline proximity bonus (weight: 10%)
        max_score += 0.10
        deadline_score = self._score_deadline(grant)
        score += deadline_score * 0.10
        if deadline_score > 0.5:
            reasons.append(f"Deadline in {grant.days_until_deadline} days")

        # Normalize score
        final_score = score / max_score if max_score > 0 else 0.0

        return MatchResult(
            grant=grant,
            score=final_score,
            reasons=reasons,
            warnings=warnings,
            disqualified=False,
        )

    def _check_disqualifiers(self, grant: Grant) -> Tuple[bool, str]:
        """Check for immediate disqualifying factors."""

        # Past deadline
        if grant.deadline and grant.days_until_deadline is not None:
            if grant.days_until_deadline < 0:
                return True, "Deadline has passed"

        # Requires certifications we don't have
        if grant.required_certifications:
            missing = [
                cert for cert in grant.required_certifications
                if cert not in self.attrs["certifications"]
            ]
            # Some certifications are hard requirements
            hard_requirements = ["8(a)", "HUBZone", "SDVOSB"]
            if any(req in missing for req in hard_requirements):
                return True, f"Requires certification: {', '.join(missing)}"

        # Revenue too high
        if grant.max_revenue and self.attrs["annual_revenue"] > grant.max_revenue:
            return True, f"Revenue exceeds limit (${grant.max_revenue:,.0f})"

        # Employees too many
        if grant.max_employees and self.attrs["employee_count"] > grant.max_employees:
            return True, f"Employee count exceeds limit ({grant.max_employees})"

        # Wrong location (if strict location requirement)
        if grant.eligible_locations:
            locations_lower = [loc.lower() for loc in grant.eligible_locations]
            our_locations = [
                self.attrs["state"].lower(),
                self.attrs["city"].lower(),
                self.attrs["country"].lower(),
                "california",
                "ca",
                "us",
                "usa",
                "united states",
            ]
            if not any(loc in locations_lower or any(our in loc for our in our_locations)
                      for loc in locations_lower):
                # Check if it's a strict exclusion
                if "nationwide" not in " ".join(locations_lower):
                    return True, f"Location restricted to: {', '.join(grant.eligible_locations)}"

        return False, ""

    def _score_location(self, grant: Grant) -> Tuple[float, List[str]]:
        """Score based on location eligibility."""
        reasons = []

        if not grant.eligible_locations:
            # No location restriction = full score
            return 1.0, ["No location restrictions"]

        locations_lower = [loc.lower() for loc in grant.eligible_locations]

        # Check for specific California/Sacramento preference
        if any("sacramento" in loc or "sacramento" == loc for loc in locations_lower):
            reasons.append("Sacramento specifically eligible")
            return 1.0, reasons

        if any("california" in loc or "ca" == loc for loc in locations_lower):
            reasons.append("California specifically eligible")
            return 1.0, reasons

        # Check for nationwide eligibility
        if any(loc in ["nationwide", "us", "usa", "united states", "all states"]
               for loc in locations_lower):
            reasons.append("Nationwide eligibility")
            return 0.9, reasons

        # Partial match
        return 0.5, ["Location may be eligible - verify"]

    def _score_size(self, grant: Grant) -> Tuple[float, List[str], List[str]]:
        """Score based on company size requirements."""
        reasons = []
        warnings = []
        score = 1.0

        # Revenue check
        if grant.max_revenue:
            if self.attrs["annual_revenue"] <= grant.max_revenue:
                reasons.append(f"Revenue under ${grant.max_revenue:,.0f} limit")
            else:
                score *= 0.0
                warnings.append(f"Revenue may exceed limit")

        # Employee check
        if grant.max_employees:
            if self.attrs["employee_count"] <= grant.max_employees:
                reasons.append(f"Under {grant.max_employees} employee limit")
            else:
                score *= 0.0
                warnings.append("Employee count may exceed limit")

        # Small business bonus (we're very small)
        if self.attrs["annual_revenue"] < 100000:
            score *= 1.1  # Bonus for being micro-business
            reasons.append("Micro-business status (under $100k revenue)")

        # Years in business
        if grant.min_years_in_business:
            if self.attrs["years_in_business"] >= grant.min_years_in_business:
                reasons.append(f"Meets {grant.min_years_in_business}+ years requirement")
            else:
                score *= 0.5
                warnings.append(f"May not meet {grant.min_years_in_business} year requirement")

        return min(score, 1.0), reasons, warnings

    def _score_ownership(self, grant: Grant) -> Tuple[float, List[str]]:
        """Score based on ownership requirements."""
        reasons = []
        score = 0.5  # Base score if no specific requirements

        # Woman-owned requirement
        if grant.requires_woman_owned:
            if self.attrs["woman_owned"]:
                score = 1.0
                reasons.append(f"Woman-owned ({self.attrs['woman_owned_percentage']:.0f}%)")
            else:
                return 0.0, ["Requires woman-owned status"]

        # Minority-owned requirement
        if grant.requires_minority_owned:
            if self.attrs["minority_owned"]:
                score = 1.0
                reasons.append(f"Minority-owned ({self.attrs['minority_owned_percentage']:.0f}%)")
            else:
                return 0.0, ["Requires minority-owned status"]

        # Veteran requirement
        if grant.requires_veteran_owned:
            if not self.attrs["veteran_owned"]:
                return 0.0, ["Requires veteran-owned status"]
            reasons.append("Veteran-owned")

        # Bonus if we match diversity criteria even when not required
        if not grant.requires_woman_owned and self.attrs["woman_owned"]:
            score += 0.1
            reasons.append("Woman-owned (bonus eligibility)")

        if not grant.requires_minority_owned and self.attrs["minority_owned"]:
            score += 0.1
            reasons.append("Minority-owned (bonus eligibility)")

        return min(score, 1.0), reasons

    def _score_industry(self, grant: Grant) -> Tuple[float, List[str]]:
        """Score based on industry/NAICS code alignment."""
        reasons = []

        if not grant.eligible_industries:
            return 0.8, ["No industry restrictions"]

        # Check NAICS codes
        our_naics = set(self.attrs["naics_codes"])
        grant_industries_lower = [ind.lower() for ind in grant.eligible_industries]

        # Direct NAICS match
        for our_code in our_naics:
            for their_code in grant.eligible_industries:
                if our_code.startswith(their_code) or their_code.startswith(our_code):
                    reasons.append(f"NAICS code match: {our_code}")
                    return 1.0, reasons

        # Keyword matching
        keywords = ["advertising", "marketing", "media", "consulting", "business services",
                   "professional services", "small business", "technology"]

        for keyword in keywords:
            if any(keyword in ind for ind in grant_industries_lower):
                reasons.append(f"Industry keyword match: {keyword}")
                return 0.9, reasons

        # General/open industry
        if any(word in " ".join(grant_industries_lower)
               for word in ["all", "any", "open", "general"]):
            reasons.append("Open to all industries")
            return 0.8, reasons

        return 0.3, ["Industry alignment uncertain"]

    def _score_certifications(self, grant: Grant) -> Tuple[float, List[str], List[str]]:
        """Score based on certification requirements."""
        reasons = []
        warnings = []

        if not grant.required_certifications:
            return 1.0, ["No certifications required"], []

        our_certs = set(self.attrs["certifications"])
        required = set(grant.required_certifications)

        if required.issubset(our_certs):
            reasons.append(f"Have required certifications: {', '.join(required)}")
            return 1.0, reasons, []

        missing = required - our_certs
        warnings.append(f"Missing certifications: {', '.join(missing)}")

        # Some grants prefer but don't require certifications
        # Check eligibility summary for "preferred" language
        if grant.eligibility_summary and "prefer" in grant.eligibility_summary.lower():
            return 0.5, [], warnings

        return 0.0, [], warnings

    def _score_deadline(self, grant: Grant) -> float:
        """Score based on deadline proximity (prefer sooner deadlines for prioritization)."""
        if not grant.deadline or grant.days_until_deadline is None:
            return 0.5  # Unknown deadline

        days = grant.days_until_deadline

        if days < 0:
            return 0.0  # Past
        elif days <= 7:
            return 1.0  # Urgent
        elif days <= 14:
            return 0.9
        elif days <= 30:
            return 0.8
        elif days <= 60:
            return 0.6
        else:
            return 0.4  # Far out

    def match_all(self, grants: List[Grant]) -> List[MatchResult]:
        """Match all grants and return sorted by score."""
        results = []

        for grant in grants:
            result = self.match_grant(grant)
            if not result.disqualified and result.score >= MIN_ELIGIBILITY_SCORE:
                results.append(result)

        # Sort by deadline first (soonest first), then by score
        results.sort(key=lambda r: (
            r.grant.deadline if r.grant.deadline else date.max,
            -r.score
        ))

        return results

    def filter_eligible(self, grants: List[Grant]) -> List[Grant]:
        """Return only eligible grants, sorted by deadline."""
        results = self.match_all(grants)
        return [r.grant for r in results]


def match_grants(grants: List[Grant]) -> List[MatchResult]:
    """Convenience function to match grants."""
    matcher = GrantMatcher()
    return matcher.match_all(grants)
