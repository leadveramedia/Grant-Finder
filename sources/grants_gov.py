"""
Grants.gov API integration for federal grant opportunities.

API Documentation: https://www.grants.gov/api/api-guide
New 2025 API - no authentication required.
"""

import logging
from datetime import datetime, date
from typing import List, Optional

from .base_source import BaseGrantSource, Grant, GrantType, FundingType

logger = logging.getLogger(__name__)


class GrantsGovSource(BaseGrantSource):
    """
    Fetch grants from Grants.gov federal database.

    Uses the new 2025 REST API (search2) which requires no authentication.
    """

    name = "grants.gov"
    base_url = "https://api.grants.gov"
    grant_type = GrantType.FEDERAL

    # Keywords to search for (relevant to MARV Media)
    RELEVANT_KEYWORDS = [
        "small business",
        "minority business",
        "women owned business",
        "marketing",
        "advertising",
        "economic development",
        "business development",
        "entrepreneur",
    ]

    def fetch_grants(self) -> List[Grant]:
        """Fetch all relevant grants from Grants.gov."""
        grants = []

        # Search by multiple keywords to cast wide net
        for keyword in self.RELEVANT_KEYWORDS:
            try:
                keyword_grants = self._search_grants(keyword)
                grants.extend(keyword_grants)
            except Exception as e:
                logger.warning(f"Error searching for '{keyword}': {e}")

        # Deduplicate by grant ID
        seen_ids = set()
        unique_grants = []
        for grant in grants:
            if grant.id not in seen_ids:
                seen_ids.add(grant.id)
                unique_grants.append(grant)

        logger.info(f"Found {len(unique_grants)} unique grants from Grants.gov")
        return unique_grants

    def _search_grants(self, keyword: str, rows: int = 25) -> List[Grant]:
        """Search for grants by keyword using the new search2 API."""
        url = f"{self.base_url}/v1/api/search2"

        # POST request with JSON body
        # Note: Don't use oppStatuses filter as it returns 0 results
        payload = {
            "keyword": keyword,
            "rows": rows,
        }

        try:
            response = self._post(url, json=payload)
            data = response.json()
            return self._parse_search_results(data)
        except Exception as e:
            logger.error(f"Grants.gov search failed for '{keyword}': {e}")
            return []

    def _parse_search_results(self, data: dict) -> List[Grant]:
        """Parse JSON search results from REST API."""
        grants = []

        # The new API returns: data['data']['oppHits']
        inner_data = data.get("data", {})
        if isinstance(inner_data, dict):
            opportunities = inner_data.get("oppHits", [])
        else:
            opportunities = data.get("oppHits", [])

        if not isinstance(opportunities, list):
            logger.warning(f"Unexpected response format: {type(opportunities)}")
            return []

        for opp in opportunities:
            try:
                grant = self._parse_opportunity(opp)
                if grant:
                    grants.append(grant)
            except Exception as e:
                logger.warning(f"Error parsing opportunity: {e}")

        return grants

    def _parse_opportunity(self, opp: dict) -> Optional[Grant]:
        """Parse a single opportunity into a Grant object."""
        # Handle different field names from API
        opp_id = (
            opp.get("opportunityId") or
            opp.get("id") or
            opp.get("oppNumber") or
            opp.get("opportunity_id")
        )
        if not opp_id:
            return None

        # Parse dates - try multiple field names
        close_date = self._parse_date(
            opp.get("closeDate") or
            opp.get("close_date") or
            opp.get("applicationDeadline")
        )

        posted_date = self._parse_date(
            opp.get("openDate") or
            opp.get("open_date") or
            opp.get("postedDate") or
            opp.get("posted_date")
        )

        # Parse award amounts
        amount_min = self._parse_amount(opp.get("awardFloor") or opp.get("award_floor"))
        amount_max = self._parse_amount(opp.get("awardCeiling") or opp.get("award_ceiling"))

        # Get title and description
        title = (
            opp.get("title") or
            opp.get("opportunityTitle") or
            opp.get("opportunity_title") or
            "Untitled"
        )

        description = (
            opp.get("synopsis") or
            opp.get("description") or
            opp.get("opportunitySynopsis") or
            ""
        )

        # Get agency name
        funder = (
            opp.get("agencyName") or
            opp.get("agency") or
            opp.get("agency_name") or
            "Federal Agency"
        )

        # Build grant object
        return Grant(
            id=f"grants_gov_{opp_id}",
            source=self.name,
            source_url=f"https://www.grants.gov/search-results-detail/{opp_id}",
            title=title,
            description=description,
            funder=funder,
            amount_min=amount_min,
            amount_max=amount_max,
            deadline=close_date,
            posted_date=posted_date,
            grant_type=GrantType.FEDERAL,
            funding_type=FundingType.GRANT,
            eligibility_summary=opp.get("eligibleApplicants", opp.get("eligible_applicants", "")),
            application_url=f"https://www.grants.gov/search-results-detail/{opp_id}",
            raw_data=opp,
        )

    def _parse_date(self, date_str) -> Optional[date]:
        """Parse date from various formats."""
        if not date_str:
            return None

        # Try multiple date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:19], fmt).date()
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount) -> Optional[float]:
        """Parse amount from various formats."""
        if not amount:
            return None

        try:
            # Handle string with commas or dollar signs
            if isinstance(amount, str):
                amount = amount.replace("$", "").replace(",", "")
            return float(amount)
        except (ValueError, TypeError):
            return None

    def get_grant_details(self, grant_id: str) -> Optional[Grant]:
        """Get detailed information about a specific grant."""
        # Extract the Grants.gov ID from our prefixed ID
        if grant_id.startswith("grants_gov_"):
            opp_id = grant_id[11:]
        else:
            opp_id = grant_id

        url = f"{self.base_url}/v1/api/fetchOpportunity"

        try:
            response = self._post(url, json={"opportunityId": opp_id})
            data = response.json()
            return self._parse_opportunity(data.get("data", data))
        except Exception as e:
            logger.error(f"Failed to get grant details: {e}")
            return None
