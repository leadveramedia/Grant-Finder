"""
Grants.gov API integration for federal grant opportunities.

API Documentation: https://www.grants.gov/web/grants/s2s/grantor/schemas.html
"""

import logging
from datetime import datetime, date
from typing import List, Optional
import xml.etree.ElementTree as ET

from .base_source import BaseGrantSource, Grant, GrantType, FundingType
from config import GRANTS_GOV_API_KEY, GRANTS_GOV_BASE_URL

logger = logging.getLogger(__name__)


class GrantsGovSource(BaseGrantSource):
    """
    Fetch grants from Grants.gov federal database.

    Note: Grants.gov has both REST API and XML endpoints.
    The REST API requires registration at grants.gov.
    """

    name = "grants.gov"
    base_url = "https://www.grants.gov/grantsws/rest"
    grant_type = GrantType.FEDERAL

    # CFDA (Catalog of Federal Domestic Assistance) codes relevant to MARV Media
    RELEVANT_CFDA_PREFIXES = [
        "11.",  # Department of Commerce (MBDA grants)
        "59.",  # Small Business Administration
        "19.",  # State Department (international trade)
    ]

    # Keywords to search for
    RELEVANT_KEYWORDS = [
        "small business",
        "minority business",
        "women owned",
        "marketing",
        "advertising",
        "economic development",
        "business development",
        "entrepreneur",
    ]

    def __init__(self):
        super().__init__()
        self.api_key = GRANTS_GOV_API_KEY

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

    def _search_grants(self, keyword: str, rows: int = 100) -> List[Grant]:
        """Search for grants by keyword."""
        # Use the search endpoint
        url = f"{self.base_url}/opportunities/search"

        params = {
            "keyword": keyword,
            "oppStatuses": "forecasted|posted",  # Active opportunities
            "rows": rows,
            "sortBy": "openDate|desc",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self._get(url, params=params)
            data = response.json()
            return self._parse_search_results(data)
        except Exception as e:
            logger.error(f"Grants.gov search failed: {e}")
            # Fall back to XML endpoint if REST fails
            return self._fetch_xml_opportunities(keyword)

    def _parse_search_results(self, data: dict) -> List[Grant]:
        """Parse JSON search results from REST API."""
        grants = []

        opportunities = data.get("oppHits", [])

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
        opp_id = opp.get("id") or opp.get("opportunityId")
        if not opp_id:
            return None

        # Parse dates
        close_date = None
        if opp.get("closeDate"):
            try:
                close_date = datetime.strptime(
                    opp["closeDate"][:10], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        posted_date = None
        if opp.get("openDate"):
            try:
                posted_date = datetime.strptime(
                    opp["openDate"][:10], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        # Parse award amounts
        amount_min = None
        amount_max = None
        if opp.get("awardCeiling"):
            try:
                amount_max = float(opp["awardCeiling"])
            except (ValueError, TypeError):
                pass
        if opp.get("awardFloor"):
            try:
                amount_min = float(opp["awardFloor"])
            except (ValueError, TypeError):
                pass

        # Build grant object
        return Grant(
            id=f"grants_gov_{opp_id}",
            source=self.name,
            source_url=f"https://www.grants.gov/search-results-detail/{opp_id}",
            title=opp.get("title", "Untitled"),
            description=opp.get("synopsis", opp.get("description", "")),
            funder=opp.get("agencyName", opp.get("agency", "Federal Agency")),
            amount_min=amount_min,
            amount_max=amount_max,
            deadline=close_date,
            posted_date=posted_date,
            grant_type=GrantType.FEDERAL,
            funding_type=FundingType.GRANT,
            eligibility_summary=opp.get("eligibleApplicants", ""),
            application_url=f"https://www.grants.gov/search-results-detail/{opp_id}",
            raw_data=opp,
        )

    def _fetch_xml_opportunities(self, keyword: str = None) -> List[Grant]:
        """
        Fallback: Fetch from XML extract (doesn't require API key).
        Note: This is a larger download and should be cached.
        """
        # Grants.gov provides daily XML extracts
        # For now, return empty - implement caching later
        logger.info("XML fallback not yet implemented")
        return []

    def get_grant_details(self, grant_id: str) -> Optional[Grant]:
        """Get detailed information about a specific grant."""
        # Extract the Grants.gov ID from our prefixed ID
        if grant_id.startswith("grants_gov_"):
            opp_id = grant_id[11:]
        else:
            opp_id = grant_id

        url = f"{self.base_url}/opportunities/v1/{opp_id}"

        if self.api_key:
            url += f"?api_key={self.api_key}"

        try:
            response = self._get(url)
            data = response.json()
            return self._parse_opportunity(data)
        except Exception as e:
            logger.error(f"Failed to get grant details: {e}")
            return None

    def search_by_cfda(self, cfda_number: str) -> List[Grant]:
        """Search for grants by CFDA number."""
        url = f"{self.base_url}/opportunities/search"

        params = {
            "cfdaNumber": cfda_number,
            "oppStatuses": "forecasted|posted",
            "rows": 100,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self._get(url, params=params)
            data = response.json()
            return self._parse_search_results(data)
        except Exception as e:
            logger.error(f"CFDA search failed: {e}")
            return []
