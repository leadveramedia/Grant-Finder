"""
Google Sheets integration for tracking grant applications.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_SHEETS_ID,
    GOOGLE_SHEETS_SCOPES,
)
from sources.base_source import Grant

logger = logging.getLogger(__name__)


class SheetsTracker:
    """Track grants and applications in Google Sheets."""

    # Sheet names
    PIPELINE_SHEET = "Grant Pipeline"
    SUBMITTED_SHEET = "Submitted Applications"
    CERTIFICATIONS_SHEET = "Certifications"
    ACTIVITY_LOG_SHEET = "Activity Log"

    # Column headers for each sheet
    PIPELINE_HEADERS = [
        "Grant ID", "Grant Name", "Source", "Funder", "Amount",
        "Deadline", "Days Left", "Eligibility Score", "Status",
        "Draft Link", "Notes", "Added Date"
    ]

    SUBMITTED_HEADERS = [
        "Grant ID", "Grant Name", "Funder", "Amount Requested",
        "Submitted Date", "Confirmation #", "Expected Response",
        "Result", "Amount Awarded", "Notes"
    ]

    CERTIFICATIONS_HEADERS = [
        "Certification", "Type", "Status", "Application Date",
        "Approval Date", "Expiration", "Benefits", "Next Steps", "Notes"
    ]

    ACTIVITY_LOG_HEADERS = [
        "Timestamp", "Action", "Grant/Certification", "Details"
    ]

    def __init__(self):
        self.service = None
        self.sheet_id = GOOGLE_SHEETS_ID
        self._connected = False

    def connect(self) -> bool:
        """Initialize connection to Google Sheets."""
        if not GOOGLE_APPLICATION_CREDENTIALS:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS not set")
            return False

        if not self.sheet_id:
            logger.error("GOOGLE_SHEETS_ID not set")
            return False

        try:
            creds = Credentials.from_service_account_file(
                GOOGLE_APPLICATION_CREDENTIALS,
                scopes=GOOGLE_SHEETS_SCOPES
            )
            self.service = build("sheets", "v4", credentials=creds)
            self._connected = True
            logger.info("Connected to Google Sheets")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False

    def setup_sheets(self) -> bool:
        """Create sheet structure if it doesn't exist."""
        if not self._connected:
            if not self.connect():
                return False

        try:
            # Get existing sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            existing_sheets = {
                sheet["properties"]["title"]
                for sheet in spreadsheet.get("sheets", [])
            }

            # Create missing sheets
            sheets_to_create = [
                self.PIPELINE_SHEET,
                self.SUBMITTED_SHEET,
                self.CERTIFICATIONS_SHEET,
                self.ACTIVITY_LOG_SHEET,
            ]

            requests = []
            for sheet_name in sheets_to_create:
                if sheet_name not in existing_sheets:
                    requests.append({
                        "addSheet": {
                            "properties": {"title": sheet_name}
                        }
                    })

            if requests:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={"requests": requests}
                ).execute()
                logger.info(f"Created {len(requests)} new sheets")

            # Add headers to each sheet
            self._ensure_headers(self.PIPELINE_SHEET, self.PIPELINE_HEADERS)
            self._ensure_headers(self.SUBMITTED_SHEET, self.SUBMITTED_HEADERS)
            self._ensure_headers(self.CERTIFICATIONS_SHEET, self.CERTIFICATIONS_HEADERS)
            self._ensure_headers(self.ACTIVITY_LOG_SHEET, self.ACTIVITY_LOG_HEADERS)

            return True

        except HttpError as e:
            logger.error(f"Failed to setup sheets: {e}")
            return False

    def _ensure_headers(self, sheet_name: str, headers: List[str]):
        """Ensure a sheet has the correct headers."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"'{sheet_name}'!A1:Z1"
            ).execute()

            existing = result.get("values", [[]])[0]
            if existing != headers:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"'{sheet_name}'!A1",
                    valueInputOption="RAW",
                    body={"values": [headers]}
                ).execute()
        except HttpError:
            # Sheet might be new, just add headers
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f"'{sheet_name}'!A1",
                valueInputOption="RAW",
                body={"values": [headers]}
            ).execute()

    def add_grant_to_pipeline(
        self,
        grant: Grant,
        eligibility_score: float = 0.0,
        status: str = "New",
        notes: str = ""
    ) -> bool:
        """Add a discovered grant to the pipeline."""
        if not self._connected:
            if not self.connect():
                return False

        row = [
            grant.id,
            grant.title,
            grant.source,
            grant.funder,
            grant.amount_display,
            grant.deadline.isoformat() if grant.deadline else "",
            str(grant.days_until_deadline) if grant.days_until_deadline else "",
            f"{eligibility_score:.0%}",
            status,
            "",  # Draft link
            notes,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ]

        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"'{self.PIPELINE_SHEET}'!A:L",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]}
            ).execute()

            self._log_activity("Added to pipeline", grant.title, f"Score: {eligibility_score:.0%}")
            return True

        except HttpError as e:
            logger.error(f"Failed to add grant to pipeline: {e}")
            return False

    def update_grant_status(
        self,
        grant_id: str,
        status: str,
        draft_link: str = None,
        notes: str = None
    ) -> bool:
        """Update the status of a grant in the pipeline."""
        if not self._connected:
            if not self.connect():
                return False

        try:
            # Find the row with this grant ID
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"'{self.PIPELINE_SHEET}'!A:L"
            ).execute()

            rows = result.get("values", [])
            for i, row in enumerate(rows):
                if row and row[0] == grant_id:
                    # Update status (column I = index 8)
                    updates = [(f"'{self.PIPELINE_SHEET}'!I{i+1}", status)]

                    if draft_link:
                        updates.append((f"'{self.PIPELINE_SHEET}'!J{i+1}", draft_link))
                    if notes:
                        updates.append((f"'{self.PIPELINE_SHEET}'!K{i+1}", notes))

                    for range_name, value in updates:
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.sheet_id,
                            range=range_name,
                            valueInputOption="RAW",
                            body={"values": [[value]]}
                        ).execute()

                    self._log_activity("Status updated", row[1] if len(row) > 1 else grant_id, status)
                    return True

            logger.warning(f"Grant {grant_id} not found in pipeline")
            return False

        except HttpError as e:
            logger.error(f"Failed to update grant status: {e}")
            return False

    def mark_as_submitted(
        self,
        grant_id: str,
        confirmation_number: str = "",
        amount_requested: float = None,
        expected_response: str = ""
    ) -> bool:
        """Move a grant from pipeline to submitted."""
        if not self._connected:
            if not self.connect():
                return False

        try:
            # Find grant in pipeline
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"'{self.PIPELINE_SHEET}'!A:L"
            ).execute()

            rows = result.get("values", [])
            grant_row = None
            grant_index = None

            for i, row in enumerate(rows):
                if row and row[0] == grant_id:
                    grant_row = row
                    grant_index = i
                    break

            if not grant_row:
                logger.warning(f"Grant {grant_id} not found in pipeline")
                return False

            # Add to submitted sheet
            submitted_row = [
                grant_row[0],  # Grant ID
                grant_row[1],  # Grant Name
                grant_row[3],  # Funder
                f"${amount_requested:,.0f}" if amount_requested else grant_row[4],
                datetime.now().strftime("%Y-%m-%d"),  # Submitted Date
                confirmation_number,
                expected_response,
                "Pending",  # Result
                "",  # Amount Awarded
                grant_row[10] if len(grant_row) > 10 else "",  # Notes
            ]

            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"'{self.SUBMITTED_SHEET}'!A:J",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [submitted_row]}
            ).execute()

            # Update status in pipeline
            self.update_grant_status(grant_id, "Submitted")

            self._log_activity("Submitted", grant_row[1], f"Confirmation: {confirmation_number}")
            return True

        except HttpError as e:
            logger.error(f"Failed to mark grant as submitted: {e}")
            return False

    def add_certification(
        self,
        name: str,
        cert_type: str,
        status: str = "Not Started",
        benefits: str = "",
        next_steps: str = "",
        notes: str = ""
    ) -> bool:
        """Add a certification opportunity to track."""
        if not self._connected:
            if not self.connect():
                return False

        row = [
            name,
            cert_type,
            status,
            "",  # Application Date
            "",  # Approval Date
            "",  # Expiration
            benefits,
            next_steps,
            notes,
        ]

        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"'{self.CERTIFICATIONS_SHEET}'!A:I",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]}
            ).execute()

            self._log_activity("Certification tracked", name, status)
            return True

        except HttpError as e:
            logger.error(f"Failed to add certification: {e}")
            return False

    def _log_activity(self, action: str, item: str, details: str = ""):
        """Add entry to activity log."""
        try:
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                action,
                item,
                details,
            ]

            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"'{self.ACTIVITY_LOG_SHEET}'!A:D",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]}
            ).execute()
        except HttpError:
            pass  # Don't fail on logging errors

    def get_pipeline(self) -> List[Dict[str, Any]]:
        """Get all grants in the pipeline."""
        if not self._connected:
            if not self.connect():
                return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"'{self.PIPELINE_SHEET}'!A:L"
            ).execute()

            rows = result.get("values", [])
            if len(rows) <= 1:  # Only headers or empty
                return []

            headers = rows[0]
            return [
                dict(zip(headers, row + [""] * (len(headers) - len(row))))
                for row in rows[1:]
            ]

        except HttpError as e:
            logger.error(f"Failed to get pipeline: {e}")
            return []

    def get_submitted(self) -> List[Dict[str, Any]]:
        """Get all submitted applications."""
        if not self._connected:
            if not self.connect():
                return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"'{self.SUBMITTED_SHEET}'!A:J"
            ).execute()

            rows = result.get("values", [])
            if len(rows) <= 1:
                return []

            headers = rows[0]
            return [
                dict(zip(headers, row + [""] * (len(headers) - len(row))))
                for row in rows[1:]
            ]

        except HttpError as e:
            logger.error(f"Failed to get submitted applications: {e}")
            return []

    def grant_exists(self, grant_id: str) -> bool:
        """Check if a grant is already in the pipeline or submitted."""
        pipeline = self.get_pipeline()
        submitted = self.get_submitted()

        all_ids = {g.get("Grant ID") for g in pipeline + submitted}
        return grant_id in all_ids
