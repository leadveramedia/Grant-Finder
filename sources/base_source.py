"""
Base class for grant source scrapers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
import time
import requests
import logging

from config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, USER_AGENT


logger = logging.getLogger(__name__)


class GrantType(Enum):
    """Types of grants."""
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    PRIVATE = "private"
    CORPORATE = "corporate"
    INTERNATIONAL = "international"


class FundingType(Enum):
    """Types of funding mechanisms."""
    GRANT = "grant"
    LOAN = "loan"
    EQUITY = "equity"
    AWARD = "award"
    COMPETITION = "competition"


@dataclass
class Grant:
    """Represents a single grant opportunity."""

    # Identification
    id: str
    source: str  # Where we found it (e.g., "grants.gov", "amber_grant")
    source_url: str  # Direct link to the grant

    # Basic Info
    title: str
    description: str
    funder: str  # Organization providing the grant

    # Funding
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    amount_description: str = ""

    # Dates
    deadline: Optional[date] = None
    posted_date: Optional[date] = None
    award_date: Optional[date] = None

    # Classification
    grant_type: GrantType = GrantType.PRIVATE
    funding_type: FundingType = FundingType.GRANT

    # Eligibility
    eligibility_summary: str = ""
    eligible_locations: List[str] = field(default_factory=list)  # States/countries
    eligible_industries: List[str] = field(default_factory=list)  # NAICS codes or descriptions
    requires_woman_owned: bool = False
    requires_minority_owned: bool = False
    requires_veteran_owned: bool = False
    max_revenue: Optional[float] = None
    max_employees: Optional[int] = None
    min_years_in_business: Optional[int] = None
    required_certifications: List[str] = field(default_factory=list)

    # Application
    application_url: str = ""
    application_requirements: List[str] = field(default_factory=list)
    contact_email: str = ""
    contact_phone: str = ""

    # Metadata
    scraped_at: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure lists are initialized."""
        if self.eligible_locations is None:
            self.eligible_locations = []
        if self.eligible_industries is None:
            self.eligible_industries = []
        if self.application_requirements is None:
            self.application_requirements = []
        if self.required_certifications is None:
            self.required_certifications = []

    @property
    def amount_display(self) -> str:
        """Human-readable amount string."""
        if self.amount_min and self.amount_max:
            if self.amount_min == self.amount_max:
                return f"${self.amount_min:,.0f}"
            return f"${self.amount_min:,.0f} - ${self.amount_max:,.0f}"
        elif self.amount_max:
            return f"Up to ${self.amount_max:,.0f}"
        elif self.amount_min:
            return f"From ${self.amount_min:,.0f}"
        elif self.amount_description:
            return self.amount_description
        return "Amount varies"

    @property
    def days_until_deadline(self) -> Optional[int]:
        """Days remaining until deadline."""
        if not self.deadline:
            return None
        delta = self.deadline - date.today()
        return delta.days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "source_url": self.source_url,
            "title": self.title,
            "description": self.description,
            "funder": self.funder,
            "amount_min": self.amount_min,
            "amount_max": self.amount_max,
            "amount_display": self.amount_display,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "days_until_deadline": self.days_until_deadline,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "grant_type": self.grant_type.value,
            "funding_type": self.funding_type.value,
            "eligibility_summary": self.eligibility_summary,
            "eligible_locations": self.eligible_locations,
            "requires_woman_owned": self.requires_woman_owned,
            "requires_minority_owned": self.requires_minority_owned,
            "application_url": self.application_url,
            "scraped_at": self.scraped_at.isoformat(),
        }


class BaseGrantSource(ABC):
    """Abstract base class for grant sources."""

    name: str = "base"
    base_url: str = ""
    grant_type: GrantType = GrantType.PRIVATE

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str, params: dict = None, **kwargs) -> requests.Response:
        """Make a GET request with retry logic."""
        self._rate_limit()

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def _post(self, url: str, data: dict = None, json: dict = None, **kwargs) -> requests.Response:
        """Make a POST request with retry logic."""
        self._rate_limit()

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.post(
                    url,
                    data=data,
                    json=json,
                    timeout=REQUEST_TIMEOUT,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)

    @abstractmethod
    def fetch_grants(self) -> List[Grant]:
        """
        Fetch all available grants from this source.
        Must be implemented by subclasses.
        """
        pass

    def search_grants(self, keywords: List[str] = None) -> List[Grant]:
        """
        Search for grants matching keywords.
        Override in subclasses if the source supports search.
        """
        grants = self.fetch_grants()
        if not keywords:
            return grants

        keywords_lower = [k.lower() for k in keywords]
        return [
            g for g in grants
            if any(
                kw in g.title.lower() or kw in g.description.lower()
                for kw in keywords_lower
            )
        ]

    def get_grant_details(self, grant_id: str) -> Optional[Grant]:
        """
        Get detailed information about a specific grant.
        Override in subclasses for sources with detail endpoints.
        """
        grants = self.fetch_grants()
        for grant in grants:
            if grant.id == grant_id:
                return grant
        return None
