# MARV Media Grant Finder

Automated grant discovery and application drafting for MARV Media LLC.

## Features

- **Automated Grant Discovery**: Scans federal (grants.gov), state, and private grant sources daily
- **Eligibility Matching**: Scores grants based on MARV Media's profile (woman-owned, minority-owned, Sacramento CA)
- **Application Drafting**: Uses Gemini AI to generate application narratives
- **Google Sheets Tracking**: Logs all grants to a spreadsheet for human review
- **Certification Tracking**: Recommends and tracks business certifications (WOSB, MBE, etc.)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/Grant-Finder.git
cd Grant-Finder
pip install -r requirements.txt
```

### 2. Configure GitHub Secrets

Go to **Settings > Secrets and variables > Actions** and add:

| Secret | Description |
|--------|-------------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GOOGLE_SHEETS_ID` | ID from your Google Sheet URL |
| `GOOGLE_CREDENTIALS_JSON` | Full contents of service account JSON |
| `GRANTS_GOV_API_KEY` | (Optional) Grants.gov API key |

### 3. Create Google Sheet

1. Create a new Google Sheet
2. Copy the ID from the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
3. Share the sheet with your service account email (found in credentials JSON)

### 4. Enable GitHub Actions

The workflow runs automatically:
- **Daily at 9 AM Pacific**: Scans for new grants
- **Manual trigger**: Go to Actions tab > Grant Scanner > Run workflow

## CLI Commands

```bash
python main.py scan            # Scan all sources for grants
python main.py match           # Show eligible grants
python main.py status          # View pipeline status
python main.py draft <id>      # Generate application draft
python main.py certifications  # View certification opportunities
python main.py profile         # View company profile
python main.py sources         # List available grant sources
python main.py setup           # Initialize Google Sheets
```

## Project Structure

```
├── main.py              # CLI entry point
├── company_profile.py   # MARV Media company data
├── matcher.py           # Eligibility scoring
├── drafter.py           # Gemini AI application drafting
├── scheduler.py         # Automated tasks
├── sheets_tracker.py    # Google Sheets integration
├── certifications.py    # Certification tracking
├── sources/             # Grant source scrapers
│   ├── grants_gov.py    # Federal grants
│   └── minority_women.py # Amber Grant, MBDA, etc.
└── templates/           # Application narrative templates
```

## Grant Sources

| Source | Type | Status |
|--------|------|--------|
| grants.gov | Federal | Active |
| Amber Grant | Private (Women) | Active |
| MBDA | Federal (Minority) | Active |
| iFundWomen | Private (Women) | Active |
| Hello Alice | Corporate | Active |

## Recommended Certifications

1. **WOSB** - Women-Owned Small Business (Federal) - Anna Rea qualifies
2. **SBE-CA** - Small Business Enterprise (California) - Free, quick approval
3. **MBE** - Minority Business Enterprise - Roger Shao qualifies

## Company Profile

- **Company**: MARV Media LLC
- **Location**: Sacramento, CA
- **Industry**: Legal marketing, advertising, lead generation
- **Ownership**: 33% woman-owned, 33% minority-owned (POC)
- **Size**: 3 employees, <$100k revenue

## License

Private - MARV Media LLC
