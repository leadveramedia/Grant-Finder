"""
Certification tracking and recommendations for MARV Media.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date
from enum import Enum


class CertificationType(Enum):
    """Types of business certifications."""
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    PRIVATE = "private"


class CertificationStatus(Enum):
    """Status of certification application."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


@dataclass
class Certification:
    """Represents a business certification."""
    name: str
    full_name: str
    cert_type: CertificationType
    description: str
    benefits: List[str]
    requirements: List[str]
    application_url: str
    estimated_time: str  # e.g., "2-4 weeks"
    cost: str  # e.g., "Free" or "$500"
    renewal_period: Optional[str] = None  # e.g., "3 years"

    # MARV Media specific
    eligibility_notes: str = ""
    priority: int = 1  # 1 = highest priority
    status: CertificationStatus = CertificationStatus.NOT_STARTED
    application_date: Optional[date] = None
    approval_date: Optional[date] = None
    expiration_date: Optional[date] = None


# Certifications relevant to MARV Media
RECOMMENDED_CERTIFICATIONS = [
    Certification(
        name="WOSB",
        full_name="Women-Owned Small Business",
        cert_type=CertificationType.FEDERAL,
        description="""Federal certification for businesses that are at least 51% owned
and controlled by one or more women who are U.S. citizens.""",
        benefits=[
            "Access to federal contracts set aside for WOSBs",
            "Sole-source contracts up to $4 million (services)",
            "Credibility with corporate supplier diversity programs",
            "Networking opportunities through WOSB community",
        ],
        requirements=[
            "51%+ unconditionally owned by women who are U.S. citizens",
            "Women must control management and daily operations",
            "Small business by SBA size standards (NAICS-based)",
            "Annual recertification required",
        ],
        application_url="https://www.sba.gov/federal-contracting/contracting-assistance-programs/women-owned-small-business-federal-contracting-program",
        estimated_time="30-90 days",
        cost="Free (self-certification) or $99-$500 (third-party)",
        renewal_period="Annual recertification",
        eligibility_notes="Anna Rea's 33% ownership qualifies MARV Media. Need to verify control requirements.",
        priority=1,
    ),
    Certification(
        name="SBE-CA",
        full_name="Small Business Enterprise (California)",
        cert_type=CertificationType.STATE,
        description="""California state certification for small businesses headquartered
in California.""",
        benefits=[
            "5% bid preference on state contracts",
            "Access to state procurement opportunities",
            "Listed in California small business database",
            "Networking and training opportunities",
        ],
        requirements=[
            "Principal office in California",
            "Independently owned and operated",
            "Not dominant in field of operation",
            "Meet size standards (varies by industry)",
        ],
        application_url="https://caleprocure.ca.gov/pages/sbdvbe-702702.aspx",
        estimated_time="2-4 weeks",
        cost="Free",
        renewal_period="2 years",
        eligibility_notes="MARV Media qualifies - Sacramento HQ, under $100k revenue, independently owned.",
        priority=2,
    ),
    Certification(
        name="MBE",
        full_name="Minority Business Enterprise",
        cert_type=CertificationType.STATE,
        description="""Certification for businesses at least 51% owned, operated, and
controlled by minority group members.""",
        benefits=[
            "Access to corporate supplier diversity programs",
            "State and local contract opportunities",
            "Inclusion in MBE directories",
            "Networking and mentorship programs",
        ],
        requirements=[
            "51%+ minority ownership",
            "U.S. citizen or lawful permanent resident",
            "Active management by minority owner(s)",
            "For-profit business operating for at least one year",
        ],
        application_url="https://www.nmsdc.org/mbes/mbe-certification/",
        estimated_time="60-90 days",
        cost="$350-$500 depending on certifying organization",
        renewal_period="Annual",
        eligibility_notes="Roger Shao's 33% POC ownership may qualify. Check if 51% threshold requires multiple minority owners.",
        priority=3,
    ),
    Certification(
        name="EDWOSB",
        full_name="Economically Disadvantaged Women-Owned Small Business",
        cert_type=CertificationType.FEDERAL,
        description="""Enhanced WOSB certification for women owners who meet economic
disadvantage thresholds.""",
        benefits=[
            "All WOSB benefits plus additional set-asides",
            "Sole-source contracts in more industries",
            "Higher priority in federal contracting",
        ],
        requirements=[
            "All WOSB requirements, plus:",
            "Personal net worth less than $750,000",
            "Adjusted gross income averaging $350,000 or less over 3 years",
            "Fair market value of assets $6 million or less",
        ],
        application_url="https://www.sba.gov/federal-contracting/contracting-assistance-programs/women-owned-small-business-federal-contracting-program",
        estimated_time="30-90 days (after WOSB)",
        cost="Free",
        renewal_period="Annual",
        eligibility_notes="Depends on Anna Rea's personal financial situation. Consider after WOSB.",
        priority=4,
    ),
    Certification(
        name="8(a)",
        full_name="8(a) Business Development Program",
        cert_type=CertificationType.FEDERAL,
        description="""SBA program for small disadvantaged businesses, providing
contracting opportunities and business development support.""",
        benefits=[
            "Sole-source federal contracts up to $4 million",
            "Business development assistance",
            "Mentoring from established businesses",
            "Access to surplus government property",
        ],
        requirements=[
            "Small business by SBA standards",
            "51%+ owned by socially/economically disadvantaged individuals",
            "Owner must demonstrate social disadvantage",
            "Business must have been operating for at least 2 years",
            "Personal net worth under $750,000",
        ],
        application_url="https://www.sba.gov/federal-contracting/contracting-assistance-programs/8a-business-development-program",
        estimated_time="90-180 days",
        cost="Free",
        renewal_period="9-year program",
        eligibility_notes="May qualify based on minority ownership. Requires 2+ years in business.",
        priority=5,
    ),
]


def get_recommended_certifications() -> List[Certification]:
    """Return certifications recommended for MARV Media, sorted by priority."""
    return sorted(RECOMMENDED_CERTIFICATIONS, key=lambda c: c.priority)


def get_certification_by_name(name: str) -> Optional[Certification]:
    """Get a specific certification by name."""
    for cert in RECOMMENDED_CERTIFICATIONS:
        if cert.name.lower() == name.lower():
            return cert
    return None


def get_certification_benefits_summary() -> str:
    """Generate a summary of certification benefits."""
    lines = ["## Certification Benefits for MARV Media\n"]

    for cert in get_recommended_certifications():
        lines.append(f"### {cert.name} ({cert.full_name})")
        lines.append(f"Priority: {cert.priority} | Type: {cert.cert_type.value}")
        lines.append(f"Time: {cert.estimated_time} | Cost: {cert.cost}\n")

        lines.append("**Benefits:**")
        for benefit in cert.benefits:
            lines.append(f"- {benefit}")

        lines.append(f"\n**MARV Media Notes:** {cert.eligibility_notes}\n")
        lines.append("---\n")

    return "\n".join(lines)


def calculate_certification_roi() -> dict:
    """Estimate ROI of pursuing certifications."""
    # Rough estimates based on typical outcomes
    return {
        "WOSB": {
            "cost": 0,  # Free self-certification
            "time_hours": 10,
            "potential_annual_value": 50000,  # Federal contract access
            "probability": 0.9,  # High if requirements met
        },
        "SBE-CA": {
            "cost": 0,
            "time_hours": 5,
            "potential_annual_value": 25000,  # State contract preference
            "probability": 0.95,
        },
        "MBE": {
            "cost": 400,
            "time_hours": 15,
            "potential_annual_value": 40000,  # Corporate diversity programs
            "probability": 0.7,  # Depends on ownership structure
        },
        "8(a)": {
            "cost": 0,
            "time_hours": 40,
            "potential_annual_value": 100000,  # Sole-source contracts
            "probability": 0.5,  # Competitive, requires 2+ years
        },
    }


class CertificationTracker:
    """Track certification progress."""

    def __init__(self, sheets_tracker=None):
        self.sheets_tracker = sheets_tracker
        self.certifications = {c.name: c for c in RECOMMENDED_CERTIFICATIONS}

    def update_status(
        self,
        cert_name: str,
        status: CertificationStatus,
        notes: str = ""
    ):
        """Update certification status."""
        if cert_name in self.certifications:
            cert = self.certifications[cert_name]
            cert.status = status

            if status == CertificationStatus.SUBMITTED:
                cert.application_date = date.today()
            elif status == CertificationStatus.APPROVED:
                cert.approval_date = date.today()

            # Update in Google Sheets if connected
            if self.sheets_tracker:
                self.sheets_tracker.add_certification(
                    name=cert.name,
                    cert_type=cert.cert_type.value,
                    status=status.value,
                    benefits="; ".join(cert.benefits[:2]),
                    next_steps=notes,
                )

    def get_next_steps(self) -> List[dict]:
        """Get recommended next steps for certifications."""
        steps = []

        for cert in get_recommended_certifications():
            if cert.status == CertificationStatus.NOT_STARTED:
                steps.append({
                    "certification": cert.name,
                    "action": "Start application",
                    "url": cert.application_url,
                    "priority": cert.priority,
                    "notes": cert.eligibility_notes,
                })
            elif cert.status == CertificationStatus.IN_PROGRESS:
                steps.append({
                    "certification": cert.name,
                    "action": "Complete and submit",
                    "priority": cert.priority,
                })
            elif cert.status == CertificationStatus.APPROVED and cert.expiration_date:
                days_until_expiry = (cert.expiration_date - date.today()).days
                if days_until_expiry <= 60:
                    steps.append({
                        "certification": cert.name,
                        "action": f"Renew (expires in {days_until_expiry} days)",
                        "priority": 1,
                    })

        return sorted(steps, key=lambda x: x["priority"])
