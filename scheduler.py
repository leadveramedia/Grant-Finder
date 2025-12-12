"""
Scheduler for automated grant scanning and deadline notifications.
"""

import logging
import schedule
import time
from datetime import datetime, date, timedelta
from typing import List, Callable
from pathlib import Path

from config import DEADLINE_REMINDER_DAYS, NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)


class GrantScheduler:
    """Schedule automated grant tasks."""

    def __init__(self):
        self.jobs = []
        self._running = False

    def schedule_daily_scan(self, scan_func: Callable, time_str: str = "09:00"):
        """Schedule daily grant scanning."""
        job = schedule.every().day.at(time_str).do(self._run_with_logging, scan_func, "Daily scan")
        self.jobs.append(job)
        logger.info(f"Scheduled daily scan at {time_str}")

    def schedule_deadline_check(self, check_func: Callable, time_str: str = "08:00"):
        """Schedule daily deadline checking."""
        job = schedule.every().day.at(time_str).do(self._run_with_logging, check_func, "Deadline check")
        self.jobs.append(job)
        logger.info(f"Scheduled deadline check at {time_str}")

    def schedule_weekly_summary(self, summary_func: Callable, day: str = "monday", time_str: str = "09:00"):
        """Schedule weekly summary report."""
        job = getattr(schedule.every(), day).at(time_str).do(
            self._run_with_logging, summary_func, "Weekly summary"
        )
        self.jobs.append(job)
        logger.info(f"Scheduled weekly summary on {day} at {time_str}")

    def _run_with_logging(self, func: Callable, task_name: str):
        """Run a function with logging."""
        logger.info(f"Starting: {task_name}")
        try:
            func()
            logger.info(f"Completed: {task_name}")
        except Exception as e:
            logger.error(f"Failed: {task_name} - {e}")

    def run(self):
        """Run the scheduler loop."""
        self._running = True
        logger.info("Scheduler started")

        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        logger.info("Scheduler stopped")

    def run_once(self):
        """Run all pending jobs once (useful for testing)."""
        schedule.run_all()


class DeadlineNotifier:
    """Check for upcoming deadlines and send notifications."""

    def __init__(self):
        self.reminder_days = DEADLINE_REMINDER_DAYS

    def check_deadlines(self, grants: List[dict]) -> List[dict]:
        """
        Check for grants with upcoming deadlines.

        Returns list of grants needing attention with reminder info.
        """
        today = date.today()
        alerts = []

        for grant in grants:
            deadline_str = grant.get("Deadline") or grant.get("deadline")
            if not deadline_str:
                continue

            try:
                if isinstance(deadline_str, str):
                    deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                else:
                    deadline = deadline_str

                days_left = (deadline - today).days

                # Check if this matches any reminder threshold
                for reminder_day in self.reminder_days:
                    if days_left == reminder_day:
                        alerts.append({
                            "grant": grant,
                            "days_left": days_left,
                            "deadline": deadline,
                            "urgency": self._get_urgency(days_left),
                        })
                        break

                # Also alert for anything past due or due today
                if days_left <= 0:
                    alerts.append({
                        "grant": grant,
                        "days_left": days_left,
                        "deadline": deadline,
                        "urgency": "CRITICAL" if days_left == 0 else "PAST_DUE",
                    })

            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse deadline: {deadline_str}")

        return alerts

    def _get_urgency(self, days_left: int) -> str:
        """Determine urgency level."""
        if days_left <= 1:
            return "CRITICAL"
        elif days_left <= 3:
            return "HIGH"
        elif days_left <= 7:
            return "MEDIUM"
        else:
            return "LOW"

    def format_alerts(self, alerts: List[dict]) -> str:
        """Format alerts for display or notification."""
        if not alerts:
            return "No upcoming deadlines."

        lines = ["📅 DEADLINE ALERTS\n"]

        # Sort by urgency
        urgency_order = {"PAST_DUE": 0, "CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
        alerts.sort(key=lambda x: urgency_order.get(x["urgency"], 5))

        for alert in alerts:
            grant = alert["grant"]
            name = grant.get("Grant Name") or grant.get("title", "Unknown")
            days = alert["days_left"]
            urgency = alert["urgency"]

            if urgency == "PAST_DUE":
                emoji = "🚨"
                status = "PAST DUE"
            elif urgency == "CRITICAL":
                emoji = "⚠️"
                status = "DUE TODAY" if days == 0 else f"DUE IN {days} DAY"
            elif urgency == "HIGH":
                emoji = "🔴"
                status = f"{days} days left"
            elif urgency == "MEDIUM":
                emoji = "🟡"
                status = f"{days} days left"
            else:
                emoji = "🟢"
                status = f"{days} days left"

            lines.append(f"{emoji} [{urgency}] {name}")
            lines.append(f"   Deadline: {alert['deadline']} ({status})")
            lines.append("")

        return "\n".join(lines)


def run_daily_scan():
    """Run daily grant scan (called by scheduler)."""
    from sources.grants_gov import GrantsGovSource
    from sources.minority_women import get_minority_women_sources
    from matcher import match_grants
    from sheets_tracker import SheetsTracker

    logger.info("Running daily grant scan...")

    all_grants = []

    # Scan federal grants
    try:
        federal_source = GrantsGovSource()
        federal_grants = federal_source.fetch_grants()
        all_grants.extend(federal_grants)
        logger.info(f"Found {len(federal_grants)} federal grants")
    except Exception as e:
        logger.error(f"Federal scan failed: {e}")

    # Scan minority/women grants
    for source in get_minority_women_sources():
        try:
            grants = source.fetch_grants()
            all_grants.extend(grants)
            logger.info(f"Found {len(grants)} grants from {source.name}")
        except Exception as e:
            logger.error(f"{source.name} scan failed: {e}")

    # Match and filter
    matched = match_grants(all_grants)
    logger.info(f"Matched {len(matched)} eligible grants")

    # Add new grants to tracker
    try:
        tracker = SheetsTracker()
        if tracker.connect():
            new_count = 0
            for result in matched:
                if not tracker.grant_exists(result.grant.id):
                    tracker.add_grant_to_pipeline(
                        result.grant,
                        eligibility_score=result.score,
                        status="New",
                        notes="; ".join(result.reasons[:3])
                    )
                    new_count += 1
            logger.info(f"Added {new_count} new grants to pipeline")
    except Exception as e:
        logger.error(f"Failed to update tracker: {e}")


def run_deadline_check():
    """Check for upcoming deadlines (called by scheduler)."""
    from sheets_tracker import SheetsTracker

    logger.info("Checking deadlines...")

    try:
        tracker = SheetsTracker()
        if not tracker.connect():
            logger.error("Could not connect to sheets")
            return

        pipeline = tracker.get_pipeline()
        notifier = DeadlineNotifier()
        alerts = notifier.check_deadlines(pipeline)

        if alerts:
            message = notifier.format_alerts(alerts)
            logger.warning(f"Deadline alerts:\n{message}")
            # TODO: Send email notification if configured
        else:
            logger.info("No deadline alerts")

    except Exception as e:
        logger.error(f"Deadline check failed: {e}")


def run_weekly_summary():
    """Generate weekly summary (called by scheduler)."""
    from sheets_tracker import SheetsTracker

    logger.info("Generating weekly summary...")

    try:
        tracker = SheetsTracker()
        if not tracker.connect():
            logger.error("Could not connect to sheets")
            return

        pipeline = tracker.get_pipeline()
        submitted = tracker.get_submitted()

        # Count by status
        status_counts = {}
        for grant in pipeline:
            status = grant.get("Status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        summary = [
            "📊 WEEKLY GRANT SUMMARY",
            f"Date: {date.today()}",
            "",
            f"Pipeline: {len(pipeline)} grants",
        ]

        for status, count in sorted(status_counts.items()):
            summary.append(f"  - {status}: {count}")

        summary.extend([
            "",
            f"Submitted: {len(submitted)} applications",
            f"  - Pending: {sum(1 for s in submitted if s.get('Result') == 'Pending')}",
        ])

        logger.info("\n".join(summary))
        # TODO: Send email summary if configured

    except Exception as e:
        logger.error(f"Weekly summary failed: {e}")
