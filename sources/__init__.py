"""
Grant source scrapers and API integrations.
"""

from .base_source import BaseGrantSource, Grant, GrantType, FundingType
from .grants_gov import GrantsGovSource
from .minority_women import (
    AmberGrantSource,
    IFundWomenSource,
    MBDASource,
    HelloAliceSource,
    get_minority_women_sources,
)

__all__ = [
    "BaseGrantSource",
    "Grant",
    "GrantType",
    "FundingType",
    "GrantsGovSource",
    "AmberGrantSource",
    "IFundWomenSource",
    "MBDASource",
    "HelloAliceSource",
    "get_minority_women_sources",
]


def get_all_sources():
    """Return all available grant sources."""
    return [
        GrantsGovSource(),
        *get_minority_women_sources(),
    ]
