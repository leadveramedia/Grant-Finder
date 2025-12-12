"""
Grant sources specifically for minority and women-owned businesses.
"""

import logging
import re
from datetime import datetime, date, timedelta
import calendar
from typing import List, Optional
from bs4 import BeautifulSoup

from .base_source import BaseGrantSource, Grant, GrantType, FundingType

logger = logging.getLogger(__name__)


class AmberGrantSource(BaseGrantSource):
    """
    Amber Grant for Women - $10,000 monthly grant.
    https://ambergrantsforwomen.com

    One of the most accessible grants for women-owned businesses.
    - $10,000 monthly grant
    - $25,000 annual grant (from monthly winners)
    - No business plan required
    - Simple application
    """

    name = "amber_grant"
    base_url = "https://ambergrantsforwomen.com"
    grant_type = GrantType.PRIVATE

    def fetch_grants(self) -> List[Grant]:
        """Fetch current Amber Grant opportunities."""
        grants = []

        try:
            # Scrape the main page for current grant info
            response = self._get(self.base_url)
            soup = BeautifulSoup(response.text, "lxml")

            # The Amber Grant has consistent monthly deadlines
            # Deadline is last day of each month
            today = date.today()
            if today.month == 12:
                next_deadline = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = calendar.monthrange(today.year, today.month)[1]
                next_deadline = date(today.year, today.month, last_day)

            # Monthly grant
            grants.append(Grant(
                id=f"amber_grant_monthly_{today.strftime('%Y%m')}",
                source=self.name,
                source_url="https://ambergrantsforwomen.com/get-an-amber-grant/",
                title=f"Amber Grant for Women - {today.strftime('%B %Y')}",
                description="""The Amber Grant awards $10,000 each month to a woman-owned business.
At the end of the year, one of the monthly winners receives an additional $25,000.

The Amber Grant was started in 1998 in honor of Amber Wigdahl, who died at 19 before
fulfilling her entrepreneurial dreams. Since then, WomensNet has awarded over $1 million
to women business owners.

To apply, you must:
- Be a woman business owner (51%+ ownership)
- Describe your business and what you would do with the grant
- Pay a $15 application fee (helps fund the grants)""",
                funder="WomensNet",
                amount_min=10000,
                amount_max=10000,
                deadline=next_deadline,
                grant_type=GrantType.PRIVATE,
                funding_type=FundingType.GRANT,
                eligibility_summary="Women-owned businesses (51%+ ownership), any industry, any stage",
                requires_woman_owned=True,
                application_url="https://ambergrantsforwomen.com/get-an-amber-grant/",
                application_requirements=[
                    "Business description (500 words or less)",
                    "Explanation of how you'd use the $10,000",
                    "$15 application fee",
                    "51%+ woman ownership",
                ],
            ))

            # Bonus grant for specific categories (if available)
            # Amber Grant also offers category-specific grants
            category_grants = self._get_category_grants(soup)
            grants.extend(category_grants)

        except Exception as e:
            logger.error(f"Error fetching Amber Grant: {e}")

        return grants

    def _get_category_grants(self, soup: BeautifulSoup) -> List[Grant]:
        """Extract any category-specific grants from the page."""
        grants = []

        # Amber Grant sometimes has category bonuses (e.g., "Encore Entrepreneur" for 50+)
        # This would need to be updated based on current offerings

        return grants


class IFundWomenSource(BaseGrantSource):
    """
    iFundWomen Universal Grant Database.
    Aggregates grants for women entrepreneurs.
    """

    name = "ifundwomen"
    base_url = "https://ifundwomen.com"
    grant_type = GrantType.PRIVATE

    def fetch_grants(self) -> List[Grant]:
        """Fetch grants from iFundWomen database."""
        grants = []

        try:
            # iFundWomen has a grant database
            url = f"{self.base_url}/grants"
            response = self._get(url)
            soup = BeautifulSoup(response.text, "lxml")

            # Parse grant listings
            # Note: Actual selectors depend on site structure
            grant_cards = soup.select(".grant-card, .grant-listing, [data-grant]")

            for card in grant_cards:
                grant = self._parse_grant_card(card)
                if grant:
                    grants.append(grant)

        except Exception as e:
            logger.error(f"Error fetching iFundWomen grants: {e}")

        return grants

    def _parse_grant_card(self, card) -> Optional[Grant]:
        """Parse a grant card element."""
        try:
            title = card.select_one("h2, h3, .grant-title")
            if not title:
                return None

            title_text = title.get_text(strip=True)

            # Extract other details
            amount_el = card.select_one(".amount, .grant-amount")
            deadline_el = card.select_one(".deadline, .grant-deadline")
            link_el = card.select_one("a[href]")

            amount_max = None
            if amount_el:
                amount_text = amount_el.get_text()
                amount_match = re.search(r'\$?([\d,]+)', amount_text)
                if amount_match:
                    amount_max = float(amount_match.group(1).replace(",", ""))

            deadline = None
            if deadline_el:
                # Parse various date formats
                deadline_text = deadline_el.get_text(strip=True)
                # Add date parsing logic

            source_url = self.base_url
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if href.startswith("http"):
                    source_url = href
                else:
                    source_url = f"{self.base_url}{href}"

            return Grant(
                id=f"ifundwomen_{hash(title_text) % 100000}",
                source=self.name,
                source_url=source_url,
                title=title_text,
                description=card.get_text(strip=True)[:500],
                funder="Various (via iFundWomen)",
                amount_max=amount_max,
                deadline=deadline,
                grant_type=GrantType.PRIVATE,
                funding_type=FundingType.GRANT,
                requires_woman_owned=True,
                application_url=source_url,
            )

        except Exception as e:
            logger.warning(f"Error parsing grant card: {e}")
            return None


class MBDASource(BaseGrantSource):
    """
    Minority Business Development Agency (MBDA) grants.
    Federal agency focused on minority business growth.
    """

    name = "mbda"
    base_url = "https://www.mbda.gov"
    grant_type = GrantType.FEDERAL

    def fetch_grants(self) -> List[Grant]:
        """Fetch MBDA grant opportunities."""
        grants = []

        try:
            # MBDA grants page
            url = f"{self.base_url}/grants"
            response = self._get(url)
            soup = BeautifulSoup(response.text, "lxml")

            # Look for grant/funding opportunity listings
            # MBDA often links to grants.gov for actual applications
            articles = soup.select("article, .grant-item, .funding-opportunity")

            for article in articles:
                grant = self._parse_mbda_listing(article)
                if grant:
                    grants.append(grant)

        except Exception as e:
            logger.error(f"Error fetching MBDA grants: {e}")

        # Also add standing MBDA Business Center resources
        grants.append(Grant(
            id="mbda_business_center",
            source=self.name,
            source_url="https://www.mbda.gov/mbda-programs/business-centers",
            title="MBDA Business Center Services",
            description="""MBDA Business Centers provide consulting and technical assistance
to minority-owned businesses, including:
- Strategic business consulting
- Access to capital assistance
- Contract procurement help
- Exporting assistance
- Bonding assistance

Services are often free or low-cost for qualifying minority businesses.
Sacramento area is served by the Northern California MBDA Business Center.""",
            funder="U.S. Department of Commerce / MBDA",
            grant_type=GrantType.FEDERAL,
            funding_type=FundingType.GRANT,
            eligibility_summary="Minority-owned businesses",
            requires_minority_owned=True,
            application_url="https://www.mbda.gov/mbda-programs/business-centers",
        ))

        return grants

    def _parse_mbda_listing(self, article) -> Optional[Grant]:
        """Parse an MBDA grant listing."""
        try:
            title_el = article.select_one("h2, h3, .title")
            if not title_el:
                return None

            title = title_el.get_text(strip=True)

            link_el = article.select_one("a[href]")
            source_url = self.base_url
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("http"):
                    source_url = href
                elif href:
                    source_url = f"{self.base_url}{href}"

            description = article.get_text(strip=True)[:1000]

            return Grant(
                id=f"mbda_{hash(title) % 100000}",
                source=self.name,
                source_url=source_url,
                title=title,
                description=description,
                funder="MBDA",
                grant_type=GrantType.FEDERAL,
                funding_type=FundingType.GRANT,
                requires_minority_owned=True,
                application_url=source_url,
            )

        except Exception as e:
            logger.warning(f"Error parsing MBDA listing: {e}")
            return None


class HelloAliceSource(BaseGrantSource):
    """
    Hello Alice - Small business grants and resources.
    Partners with major corporations to distribute grants.
    """

    name = "hello_alice"
    base_url = "https://helloalice.com"
    grant_type = GrantType.CORPORATE

    def fetch_grants(self) -> List[Grant]:
        """Fetch grants from Hello Alice."""
        grants = []

        try:
            # Hello Alice funding page
            url = f"{self.base_url}/funding"
            response = self._get(url)
            soup = BeautifulSoup(response.text, "lxml")

            # Parse grant listings
            grant_sections = soup.select(".grant-card, .funding-card, [data-funding]")

            for section in grant_sections:
                grant = self._parse_hello_alice_grant(section)
                if grant:
                    grants.append(grant)

        except Exception as e:
            logger.error(f"Error fetching Hello Alice grants: {e}")

        return grants

    def _parse_hello_alice_grant(self, section) -> Optional[Grant]:
        """Parse a Hello Alice grant listing."""
        try:
            title_el = section.select_one("h2, h3, .title, .grant-title")
            if not title_el:
                return None

            title = title_el.get_text(strip=True)

            # Get other details
            funder_el = section.select_one(".partner, .sponsor, .funder")
            funder = funder_el.get_text(strip=True) if funder_el else "Hello Alice Partner"

            amount_el = section.select_one(".amount, .grant-amount")
            amount_max = None
            if amount_el:
                amount_text = amount_el.get_text()
                match = re.search(r'\$?([\d,]+)', amount_text)
                if match:
                    amount_max = float(match.group(1).replace(",", ""))

            link_el = section.select_one("a[href]")
            source_url = self.base_url
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("http"):
                    source_url = href
                elif href:
                    source_url = f"{self.base_url}{href}"

            return Grant(
                id=f"hello_alice_{hash(title) % 100000}",
                source=self.name,
                source_url=source_url,
                title=title,
                description=section.get_text(strip=True)[:500],
                funder=funder,
                amount_max=amount_max,
                grant_type=GrantType.CORPORATE,
                funding_type=FundingType.GRANT,
                application_url=source_url,
            )

        except Exception as e:
            logger.warning(f"Error parsing Hello Alice grant: {e}")
            return None


# Convenience function to get all minority/women sources
def get_minority_women_sources() -> List[BaseGrantSource]:
    """Return all minority and women-focused grant sources."""
    return [
        AmberGrantSource(),
        IFundWomenSource(),
        MBDASource(),
        HelloAliceSource(),
    ]
