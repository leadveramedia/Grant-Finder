"""
Configuration settings for MARV Media Grant Finder.
Load API keys from environment variables or .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

# Google Cloud / Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Google Sheets
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Grants.gov API (free, requires registration)
GRANTS_GOV_API_KEY = os.getenv("GRANTS_GOV_API_KEY", "")
GRANTS_GOV_BASE_URL = "https://www.grants.gov/grantsws/rest/opportunities/search"

# SAM.gov API
SAM_GOV_API_KEY = os.getenv("SAM_GOV_API_KEY", "")
SAM_GOV_BASE_URL = "https://api.sam.gov/opportunities/v2/search"

# Scraping settings
REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY = 2  # seconds between requests to same domain
MAX_RETRIES = 3
USER_AGENT = "MARV-Grant-Finder/1.0 (grant-research-tool)"

# Grant matching settings
MIN_ELIGIBILITY_SCORE = 0.6  # Minimum score to consider a grant (0-1)
DEADLINE_BUFFER_DAYS = 3  # Minimum days before deadline to flag for review

# Notification settings
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")
DEADLINE_REMINDER_DAYS = [7, 3, 1]  # Days before deadline to send reminders

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "grant_finder.log"


def validate_config():
    """Check that required configuration is present."""
    missing = []

    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not GOOGLE_SHEETS_ID:
        missing.append("GOOGLE_SHEETS_ID")

    if missing:
        print(f"Warning: Missing configuration: {', '.join(missing)}")
        print("Create a .env file with these values or set environment variables.")
        return False
    return True


# Example .env file content
ENV_TEMPLATE = """
# MARV Media Grant Finder Configuration
# Copy this to .env and fill in your values

# Gemini API Key (from Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key_here

# Google Sheets ID (from the sheet URL)
# Example: https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
GOOGLE_SHEETS_ID=your_sheet_id_here

# Path to Google Cloud service account JSON (for Sheets API)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Grants.gov API Key (register at grants.gov)
GRANTS_GOV_API_KEY=your_grants_gov_key_here

# SAM.gov API Key (register at api.sam.gov)
SAM_GOV_API_KEY=your_sam_gov_key_here

# Email for notifications
NOTIFICATION_EMAIL=your_email@example.com

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
""".strip()
