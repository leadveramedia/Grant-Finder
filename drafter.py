"""
Gemini-powered grant application drafter.
Generates narrative responses for grant applications using company profile and templates.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

import google.generativeai as genai

from config import GEMINI_API_KEY, TEMPLATES_DIR
from company_profile import get_profile, to_json as profile_to_json
from sources.base_source import Grant

logger = logging.getLogger(__name__)


class ApplicationDrafter:
    """Generate grant application content using Gemini AI."""

    def __init__(self):
        self.profile = get_profile()
        self.profile_json = profile_to_json()
        self._model = None

    @property
    def model(self):
        """Lazy-load the Gemini model."""
        if self._model is None:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            genai.configure(api_key=GEMINI_API_KEY)
            self._model = genai.GenerativeModel("gemini-pro")
        return self._model

    def draft_application(self, grant: Grant) -> Dict[str, str]:
        """
        Generate a complete application draft for a grant.

        Returns a dictionary with common application sections:
        - company_overview
        - business_description
        - use_of_funds
        - impact_statement
        - owner_bios
        - why_we_deserve_this
        """
        sections = {}

        # Generate each section
        sections["company_overview"] = self._generate_company_overview(grant)
        sections["business_description"] = self._generate_business_description(grant)
        sections["use_of_funds"] = self._generate_use_of_funds(grant)
        sections["impact_statement"] = self._generate_impact_statement(grant)
        sections["owner_bios"] = self._generate_owner_bios(grant)
        sections["why_we_deserve_this"] = self._generate_why_us(grant)

        return sections

    def _generate_company_overview(self, grant: Grant, max_words: int = 250) -> str:
        """Generate a company overview tailored to the grant."""
        prompt = f"""You are writing a grant application for MARV Media LLC.
Generate a company overview (max {max_words} words) for this grant:

Grant: {grant.title}
Funder: {grant.funder}
Grant Focus: {grant.description[:500] if grant.description else 'General business grant'}

Company Information:
{json.dumps(self.profile_json['descriptions'], indent=2)}

Location: {self.profile_json['location']['city']}, {self.profile_json['location']['state']}
Founded: Recently established
Employees: {self.profile_json['financials']['employee_count']}
Revenue: ${self.profile_json['financials']['annual_revenue']:,.0f}

Ownership:
- Woman-owned: {self.profile_json['ownership']['woman_owned_percentage']:.0f}%
- Minority-owned (POC): {self.profile.minority_owned_percentage:.0f}%

Write a professional, compelling company overview that:
1. Clearly states what MARV Media does
2. Highlights relevant ownership characteristics if the grant targets diverse businesses
3. Shows alignment with the grant's focus area
4. Uses specific, concrete language (avoid generic statements)
5. Is written in third person

Output only the overview text, no headers or metadata."""

        return self._generate(prompt)

    def _generate_business_description(self, grant: Grant, max_words: int = 500) -> str:
        """Generate detailed business description."""
        prompt = f"""You are writing a grant application for MARV Media LLC.
Generate a detailed business description (max {max_words} words) for this grant:

Grant: {grant.title}
Funder: {grant.funder}

Company Details:
{self.profile.company_description}

Products/Services:
{self.profile.products_services}

Target Market:
{self.profile.target_market}

Competitive Advantage:
{self.profile.competitive_advantage}

Write a detailed business description that:
1. Explains the business model clearly
2. Describes the target market and opportunity
3. Highlights competitive advantages
4. Shows business viability and growth potential
5. Aligns with grant focus areas where relevant

Output only the description text, no headers or metadata."""

        return self._generate(prompt)

    def _generate_use_of_funds(self, grant: Grant, max_words: int = 300) -> str:
        """Generate use of funds statement."""
        amount = grant.amount_max or grant.amount_min or 10000

        prompt = f"""You are writing a grant application for MARV Media LLC.
Generate a "Use of Funds" statement (max {max_words} words) for this grant:

Grant: {grant.title}
Amount: ${amount:,.0f}
Funder: {grant.funder}

MARV Media's planned use of funds:
{json.dumps(self.profile.use_of_funds, indent=2)}

Growth Goals:
{self.profile.growth_goals}

Write a specific, detailed use of funds statement that:
1. Breaks down how the ${amount:,.0f} would be allocated
2. Ties spending to specific business outcomes
3. Shows clear ROI potential
4. Aligns with the grant's intended purpose
5. Includes specific dollar amounts where appropriate

Example format:
- Marketing campaigns: $X,XXX (acquire Y new clients)
- Technology tools: $X,XXX (improve efficiency by Z%)
- Working capital: $X,XXX (fund operations during growth phase)

Output only the use of funds text, no headers or metadata."""

        return self._generate(prompt)

    def _generate_impact_statement(self, grant: Grant, max_words: int = 300) -> str:
        """Generate impact/diversity statement."""
        prompt = f"""You are writing a grant application for MARV Media LLC.
Generate an impact statement (max {max_words} words) for this grant:

Grant: {grant.title}
Funder: {grant.funder}
Focus: {grant.description[:300] if grant.description else 'Small business support'}

Company Impact Statement:
{self.profile.impact_statement}

Ownership:
- Woman-owned: {self.profile.woman_owned_percentage:.0f}% (Anna Rea, Co-Founder)
- Minority-owned (POC): {self.profile.minority_owned_percentage:.0f}% (Roger Shao, Co-Founder)

Location: Sacramento, California

Write an impact statement that:
1. Highlights the significance of supporting a diverse-owned business
2. Describes local economic impact (Sacramento area)
3. Shows industry impact (democratizing access to legal marketing)
4. Includes specific, measurable outcomes where possible
5. Aligns emotional appeal with concrete benefits

Output only the impact statement text, no headers or metadata."""

        return self._generate(prompt)

    def _generate_owner_bios(self, grant: Grant, max_words: int = 400) -> str:
        """Generate owner biographies."""
        owners_info = []
        for owner in self.profile.owners:
            owners_info.append({
                "name": owner.name,
                "title": owner.title,
                "bio": owner.bio,
                "ownership": owner.ownership_percentage,
                "woman": owner.is_woman,
                "poc": owner.is_poc,
            })

        prompt = f"""You are writing a grant application for MARV Media LLC.
Generate professional owner biographies (max {max_words} words total) for this grant:

Grant: {grant.title}
Funder: {grant.funder}

Owners:
{json.dumps(owners_info, indent=2)}

Write professional bios that:
1. Highlight relevant experience for each owner
2. Emphasize qualifications that align with the grant's focus
3. Note diversity characteristics (woman-owned, minority-owned) naturally
4. Show the team's combined expertise
5. Keep each bio concise but impactful

Format as:
[Owner Name], [Title]
[Bio paragraph]

Output only the bios, no additional headers or metadata."""

        return self._generate(prompt)

    def _generate_why_us(self, grant: Grant, max_words: int = 400) -> str:
        """Generate 'why we deserve this grant' narrative."""
        prompt = f"""You are writing a grant application for MARV Media LLC.
Generate a compelling "Why We Deserve This Grant" statement (max {max_words} words):

Grant: {grant.title}
Funder: {grant.funder}
Amount: {grant.amount_display}
Focus: {grant.description[:400] if grant.description else 'Supporting small businesses'}
Eligibility: {grant.eligibility_summary[:200] if grant.eligibility_summary else 'Small businesses'}

About MARV Media:
{self.profile.company_description[:500]}

Competitive Advantage:
{self.profile.competitive_advantage}

Ownership:
- Woman-owned: {self.profile.woman_owned_percentage:.0f}%
- Minority-owned: {self.profile.minority_owned_percentage:.0f}%
- Location: Sacramento, California

Write a persuasive statement that:
1. Directly addresses why MARV Media is an ideal recipient
2. Shows alignment between our mission and the grant's purpose
3. Demonstrates need (early-stage, under $100k revenue)
4. Highlights potential for success and growth
5. Includes a clear call to action
6. Balances confidence with humility

Output only the statement text, no headers or metadata."""

        return self._generate(prompt)

    def _generate(self, prompt: str) -> str:
        """Generate content using Gemini."""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"[Generation failed: {e}]"

    def generate_custom_response(
        self,
        question: str,
        max_words: int = 500,
        context: str = ""
    ) -> str:
        """Generate a custom response to a specific application question."""
        prompt = f"""You are writing a grant application for MARV Media LLC.
Answer the following application question (max {max_words} words):

Question: {question}

Additional Context: {context if context else 'None provided'}

Company Profile:
{json.dumps(self.profile_json, indent=2)}

Write a professional, compelling response that:
1. Directly answers the question
2. Uses specific details from the company profile
3. Is appropriately concise
4. Maintains professional tone

Output only the response text, no headers or metadata."""

        return self._generate(prompt)

    def save_draft(self, grant: Grant, sections: Dict[str, str], output_path: Path) -> Path:
        """Save a complete draft to a file."""
        output = f"""# Grant Application Draft

## Grant Information
- **Title**: {grant.title}
- **Funder**: {grant.funder}
- **Amount**: {grant.amount_display}
- **Deadline**: {grant.deadline if grant.deadline else 'Not specified'}
- **Source**: {grant.source_url}

---

## Company Overview

{sections.get('company_overview', '[Not generated]')}

---

## Business Description

{sections.get('business_description', '[Not generated]')}

---

## Use of Funds

{sections.get('use_of_funds', '[Not generated]')}

---

## Impact Statement

{sections.get('impact_statement', '[Not generated]')}

---

## Owner Biographies

{sections.get('owner_bios', '[Not generated]')}

---

## Why MARV Media Deserves This Grant

{sections.get('why_we_deserve_this', '[Not generated]')}

---

*Draft generated automatically. Please review and customize before submission.*
"""

        output_path.write_text(output)
        logger.info(f"Draft saved to {output_path}")
        return output_path


def draft_application(grant: Grant) -> Dict[str, str]:
    """Convenience function to draft an application."""
    drafter = ApplicationDrafter()
    return drafter.draft_application(grant)
