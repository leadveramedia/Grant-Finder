"""
MARV Media LLC Company Profile
Used for grant eligibility matching and application auto-fill.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class Owner:
    """Individual owner information."""
    name: str
    title: str
    bio: str
    is_woman: bool = False
    is_poc: bool = False
    ownership_percentage: float = 0.0


@dataclass
class CompanyProfile:
    """Complete company profile for grant applications."""

    # Basic Information
    legal_name: str
    dba_name: Optional[str]
    entity_type: str  # LLC, Corporation, etc.
    ein: str  # Federal Tax ID
    duns: str  # DUNS Number
    cage_code: str  # CAGE Code (for federal contracts)

    # Location
    address_street: str
    address_city: str
    address_state: str
    address_zip: str
    address_country: str

    # Business Details
    founding_date: date
    naics_codes: List[str]  # Industry codes
    sic_codes: List[str]  # Standard Industrial Classification
    website: str
    phone: str
    email: str

    # Size & Financials
    employee_count: int
    annual_revenue: float
    fiscal_year_end: str  # Month

    # Ownership
    owners: List[Owner]
    woman_owned_percentage: float
    minority_owned_percentage: float
    veteran_owned: bool = False
    disabled_veteran_owned: bool = False

    # Certifications (current)
    certifications: List[str] = field(default_factory=list)

    # Business Description
    mission_statement: str = ""
    company_description: str = ""
    products_services: str = ""
    target_market: str = ""
    competitive_advantage: str = ""

    # Grant-specific
    use_of_funds: List[str] = field(default_factory=list)
    growth_goals: str = ""
    impact_statement: str = ""


# MARV Media LLC Profile
MARV_PROFILE = CompanyProfile(
    # Basic Information
    legal_name="MARV Media LLC",
    dba_name="MARV Media",
    entity_type="Limited Liability Company (LLC)",
    ein="",  # TODO: Fill in EIN
    duns="",  # TODO: Fill in DUNS if registered
    cage_code="",  # TODO: Fill in CAGE code if registered

    # Location
    address_street="",  # TODO: Fill in address
    address_city="Sacramento",
    address_state="CA",
    address_zip="",  # TODO: Fill in ZIP
    address_country="United States",

    # Business Details
    founding_date=date(2024, 1, 1),  # TODO: Confirm founding date
    naics_codes=[
        "541810",  # Advertising Agencies
        "541613",  # Marketing Consulting Services
        "541820",  # Public Relations Agencies
        "561422",  # Telemarketing Bureaus and Other Contact Centers
    ],
    sic_codes=[
        "7311",  # Advertising Agencies
        "8742",  # Management Consulting Services
    ],
    website="",  # TODO: Fill in website
    phone="",  # TODO: Fill in phone
    email="",  # TODO: Fill in email

    # Size & Financials
    employee_count=3,
    annual_revenue=100000.0,  # Under $100k
    fiscal_year_end="December",

    # Ownership - 3 founders
    owners=[
        Owner(
            name="Max Goldberg",
            title="Co-Founder",
            bio="""Accomplished marketing leader with expertise in multi-channel strategy,
digital advertising, and brand growth. Data-driven, results-focused, and skilled at
optimizing case acquisition and lowering CPA and increasing ROAS. Proven track record
managing cross-functional teams and complex legal marketing projects. Strong in vendor
relations, compliance, and aligning marketing with business goals for sustained growth.""",
            is_woman=False,
            is_poc=False,
            ownership_percentage=33.33
        ),
        Owner(
            name="Anna Rea",
            title="Co-Founder",
            bio="""Over a decade of leadership experience in legal operations and performance
marketing, with end-to-end expertise in the entire case acquisition pipeline for plaintiff
law firms. Implemented data-driven strategies at Wilshire Law Firm that aligned marketing
and legal operations to boost conversion rates and ROI. Deep proficiency with legal CRM
platforms like Litify and Lead Docket with a proven track record of scaling operational
infrastructure to support firm growth.""",
            is_woman=True,
            is_poc=False,
            ownership_percentage=33.33
        ),
        Owner(
            name="Roger Shao",
            title="Co-Founder",
            bio="""Co-founder with expertise in technology and business operations.""",
            is_woman=False,
            is_poc=True,
            ownership_percentage=33.34
        ),
    ],
    woman_owned_percentage=33.33,  # Anna Rea's ownership
    minority_owned_percentage=33.34,  # Roger Shao's ownership (POC)
    veteran_owned=False,
    disabled_veteran_owned=False,

    # Current certifications (none yet)
    certifications=[],

    # Business Description
    mission_statement="""MARV Media maximizes the return on marketing investment for plaintiff
law firms by combining performance-based digital acquisition with contingency fee economics,
delivering qualified cases while offloading overhead risk.""",

    company_description="""MARV Media is a Sacramento, CA-based legal marketing company that
provides advertising and lead generation services to the legal sector, specifically plaintiff
law firms. We operate a hybrid business model combining lead generation with case referrals,
targeting the $160 billion U.S. plaintiff contingency-fee market.

Our approach leverages AI-driven operations that allow our 3-person team to scale efforts
nationally. We specialize in performance-based digital acquisition, utilizing SEO, paid search,
paid social, traditional media, digital streaming, and programmatic advertising to generate
qualified leads for personal injury, mass tort, and consumer class action cases.

As a woman and minority-owned business, we bring diverse perspectives to an industry
traditionally dominated by large, established players. Our lean structure and technology-first
approach allows us to deliver results at lower costs than traditional marketing agencies.""",

    products_services="""- Performance-based digital lead acquisition for law firms
- Case referral services with contingency fee sharing
- AI-powered intake and case qualification
- Multi-channel marketing campaigns (SEO, PPC, Social, Traditional Media)
- Call center optimization and warm transfer services
- AI-driven case value assessment
- Competitive intelligence and market analysis""",

    target_market="""Plaintiff law firms nationwide, with initial focus on:
- Personal Injury firms
- Mass Tort practices
- Consumer Class Action specialists
- Alternative Business Structures (ABS) in Arizona
- Firms seeking to scale case acquisition without increasing overhead""",

    competitive_advantage="""1. Hybrid Model: Unlike pure lead-gen vendors or traditional law firms,
we combine performance marketing expertise with contingency fee economics.

2. AI-Accelerated Operations: Our technology stack enables a 3-person team to compete with
much larger organizations.

3. Diverse Ownership: Woman and minority-owned, qualifying for specialized grant programs
and supplier diversity initiatives.

4. Industry Expertise: Deep experience in legal marketing, CRM platforms (Litify, Lead Docket),
and the complete case acquisition pipeline.

5. Lean Cost Structure: Lower overhead than competitors, allowing better ROI for clients.""",

    # Grant-specific information
    use_of_funds=[
        "Working capital for business operations",
        "Marketing and advertising campaigns",
        "Technology infrastructure and AI tools",
        "Team expansion and hiring",
    ],

    growth_goals="""Year 1-2: Establish lead generation operations, build client base
Year 3: Achieve profitability, scale to $28M+ revenue
Year 5: Capture 1% of reachable market ($0.5-1B in fees)

Near-term objectives:
- Build out PPC campaigns for client acquisition
- Develop call center infrastructure
- Acquire AZ law firm for ABS structure
- Establish referral network with plaintiff firms""",

    impact_statement="""As a woman and minority-owned business in the legal marketing space,
MARV Media is working to democratize access to justice by helping plaintiff law firms
acquire cases more efficiently. Our success creates:

- Economic impact through job creation in Sacramento, CA
- Increased access to legal services for consumers
- Competition that drives down marketing costs industry-wide
- A model for diverse ownership in legal services

Grant funding will accelerate our growth, enabling us to hire local talent, invest in
technology, and expand our positive impact on the legal services ecosystem."""
)


def get_profile() -> CompanyProfile:
    """Return the MARV Media company profile."""
    return MARV_PROFILE


def get_eligibility_attributes() -> dict:
    """Return key attributes used for grant eligibility matching."""
    profile = MARV_PROFILE
    return {
        "state": profile.address_state,
        "city": profile.address_city,
        "country": profile.address_country,
        "employee_count": profile.employee_count,
        "annual_revenue": profile.annual_revenue,
        "woman_owned": profile.woman_owned_percentage > 0,
        "woman_owned_percentage": profile.woman_owned_percentage,
        "minority_owned": profile.minority_owned_percentage > 0,
        "minority_owned_percentage": profile.minority_owned_percentage,
        "veteran_owned": profile.veteran_owned,
        "disabled_veteran_owned": profile.disabled_veteran_owned,
        "naics_codes": profile.naics_codes,
        "entity_type": profile.entity_type,
        "certifications": profile.certifications,
        "years_in_business": (date.today() - profile.founding_date).days // 365,
    }


def to_json() -> dict:
    """Export profile as JSON-serializable dictionary."""
    profile = MARV_PROFILE
    return {
        "legal_name": profile.legal_name,
        "dba_name": profile.dba_name,
        "entity_type": profile.entity_type,
        "ein": profile.ein,
        "location": {
            "street": profile.address_street,
            "city": profile.address_city,
            "state": profile.address_state,
            "zip": profile.address_zip,
            "country": profile.address_country,
        },
        "contact": {
            "website": profile.website,
            "phone": profile.phone,
            "email": profile.email,
        },
        "financials": {
            "employee_count": profile.employee_count,
            "annual_revenue": profile.annual_revenue,
            "fiscal_year_end": profile.fiscal_year_end,
        },
        "ownership": {
            "owners": [
                {
                    "name": o.name,
                    "title": o.title,
                    "is_woman": o.is_woman,
                    "is_poc": o.is_poc,
                    "ownership_percentage": o.ownership_percentage,
                }
                for o in profile.owners
            ],
            "woman_owned_percentage": profile.woman_owned_percentage,
            "minority_owned_percentage": profile.minority_owned_percentage,
            "veteran_owned": profile.veteran_owned,
        },
        "industry": {
            "naics_codes": profile.naics_codes,
            "sic_codes": profile.sic_codes,
        },
        "certifications": profile.certifications,
        "descriptions": {
            "mission": profile.mission_statement,
            "company": profile.company_description,
            "products_services": profile.products_services,
            "target_market": profile.target_market,
            "competitive_advantage": profile.competitive_advantage,
        },
        "grant_info": {
            "use_of_funds": profile.use_of_funds,
            "growth_goals": profile.growth_goals,
            "impact_statement": profile.impact_statement,
        },
    }
