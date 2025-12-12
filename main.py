#!/usr/bin/env python3
"""
MARV Media Grant Finder CLI
Discover grants, draft applications, and track submissions.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import json
import logging

from config import validate_config, LOG_LEVEL
from company_profile import get_profile, get_eligibility_attributes, to_json as profile_to_json

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """MARV Media Grant Finder - Discover and apply for grants automatically."""
    pass


@cli.command()
def scan():
    """Scan all sources for new grant opportunities."""
    console.print(Panel("Scanning for grants...", style="blue"))

    # Import sources here to avoid circular imports
    from sources import BaseGrantSource

    sources_to_scan = []

    # TODO: Add configured sources
    # from sources.grants_gov import GrantsGovSource
    # from sources.minority_women import AmberGrantSource
    # sources_to_scan = [GrantsGovSource(), AmberGrantSource()]

    if not sources_to_scan:
        console.print("[yellow]No grant sources configured yet.[/yellow]")
        console.print("Run [bold]python main.py sources[/bold] to see available sources.")
        return

    all_grants = []
    for source in sources_to_scan:
        console.print(f"  Scanning {source.name}...")
        try:
            grants = source.fetch_grants()
            all_grants.extend(grants)
            console.print(f"    Found {len(grants)} grants")
        except Exception as e:
            console.print(f"    [red]Error: {e}[/red]")

    console.print(f"\n[green]Total grants found: {len(all_grants)}[/green]")


@cli.command()
@click.option("--source", "-s", help="Filter by source name")
@click.option("--limit", "-l", default=20, help="Maximum results to show")
def match(source, limit):
    """Show grants matching MARV Media's eligibility criteria."""
    console.print(Panel("Finding matching grants...", style="blue"))

    # Get eligibility attributes
    attrs = get_eligibility_attributes()

    console.print(f"[dim]Matching criteria:[/dim]")
    console.print(f"  Location: {attrs['city']}, {attrs['state']}")
    console.print(f"  Revenue: ${attrs['annual_revenue']:,.0f}")
    console.print(f"  Employees: {attrs['employee_count']}")
    console.print(f"  Woman-owned: {attrs['woman_owned']}")
    console.print(f"  Minority-owned: {attrs['minority_owned']}")
    console.print()

    # TODO: Implement actual matching with stored grants
    console.print("[yellow]No grants scanned yet. Run 'python main.py scan' first.[/yellow]")


@cli.command()
@click.argument("grant_id")
def draft(grant_id):
    """Generate an application draft for a specific grant."""
    console.print(Panel(f"Drafting application for grant: {grant_id}", style="blue"))

    # TODO: Implement Gemini-based drafting
    console.print("[yellow]Gemini integration not yet implemented.[/yellow]")
    console.print("This will generate narrative responses based on:")
    console.print("  - Company profile (company_profile.py)")
    console.print("  - Grant requirements")
    console.print("  - Templates (templates/)")


@cli.command()
def status():
    """Show current pipeline status."""
    console.print(Panel("Grant Pipeline Status", style="blue"))

    try:
        from sheets_tracker import SheetsTracker
        tracker = SheetsTracker()

        if not tracker.connect():
            console.print("[yellow]Could not connect to Google Sheets.[/yellow]")
            console.print("Check GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_SHEETS_ID in .env")
            return

        pipeline = tracker.get_pipeline()
        submitted = tracker.get_submitted()

        # Pipeline table
        if pipeline:
            table = Table(title="Grant Pipeline")
            table.add_column("Grant", style="cyan")
            table.add_column("Source")
            table.add_column("Amount")
            table.add_column("Deadline", style="yellow")
            table.add_column("Score")
            table.add_column("Status")

            for grant in pipeline[:10]:
                table.add_row(
                    grant.get("Grant Name", "")[:40],
                    grant.get("Source", ""),
                    grant.get("Amount", ""),
                    grant.get("Deadline", ""),
                    grant.get("Eligibility Score", ""),
                    grant.get("Status", ""),
                )

            console.print(table)
            if len(pipeline) > 10:
                console.print(f"[dim]...and {len(pipeline) - 10} more[/dim]")
        else:
            console.print("[dim]No grants in pipeline[/dim]")

        console.print()

        # Submitted summary
        console.print(f"[green]Submitted applications: {len(submitted)}[/green]")
        pending = sum(1 for s in submitted if s.get("Result") == "Pending")
        if pending:
            console.print(f"[yellow]  Awaiting response: {pending}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def certifications():
    """Show certification opportunities."""
    console.print(Panel("Certification Opportunities for MARV Media", style="blue"))

    certs = [
        {
            "name": "WOSB",
            "full_name": "Women-Owned Small Business",
            "type": "Federal",
            "benefits": "Access to federal contracts set aside for WOSBs, credibility with corporate partners",
            "requirements": "51%+ woman-owned and controlled, small business by SBA standards",
            "url": "https://www.sba.gov/federal-contracting/contracting-assistance-programs/women-owned-small-business-federal-contracting-program",
        },
        {
            "name": "EDWOSB",
            "full_name": "Economically Disadvantaged Women-Owned Small Business",
            "type": "Federal",
            "benefits": "Sole-source contracts up to $4M, additional set-asides",
            "requirements": "WOSB + personal net worth < $750K, adjusted gross income < $350K",
            "url": "https://www.sba.gov/federal-contracting/contracting-assistance-programs/women-owned-small-business-federal-contracting-program",
        },
        {
            "name": "MBE",
            "full_name": "Minority Business Enterprise",
            "type": "State/Local",
            "benefits": "State contracts, supplier diversity programs, corporate partnerships",
            "requirements": "51%+ minority-owned, CA certification through various agencies",
            "url": "https://caleprocure.ca.gov/pages/sbdvbe-702702.aspx",
        },
        {
            "name": "SBE",
            "full_name": "Small Business Enterprise (California)",
            "type": "State",
            "benefits": "5% bid preference on state contracts, networking opportunities",
            "requirements": "CA-based, independently owned, meet size standards",
            "url": "https://caleprocure.ca.gov/pages/sbdvbe-702702.aspx",
        },
        {
            "name": "8(a)",
            "full_name": "8(a) Business Development Program",
            "type": "Federal",
            "benefits": "Sole-source contracts up to $4M, mentoring, training",
            "requirements": "Socially/economically disadvantaged owner, small business, 2+ years in business",
            "url": "https://www.sba.gov/federal-contracting/contracting-assistance-programs/8a-business-development-program",
        },
    ]

    profile = get_profile()

    for cert in certs:
        panel_content = f"""[bold]{cert['full_name']}[/bold]
Type: {cert['type']}

[green]Benefits:[/green]
{cert['benefits']}

[yellow]Requirements:[/yellow]
{cert['requirements']}

[blue]More info:[/blue] {cert['url']}"""

        console.print(Panel(panel_content, title=cert["name"], border_style="cyan"))
        console.print()

    # Recommendation
    console.print(Panel(
        """[bold green]Recommended Priority:[/bold green]
1. [bold]WOSB[/bold] - Anna Rea's 33% ownership qualifies MARV Media
2. [bold]SBE (California)[/bold] - Simple state certification, immediate benefits
3. [bold]MBE[/bold] - Roger Shao's ownership may qualify for minority programs

[dim]Note: Certifications significantly increase eligible grant pools.[/dim]""",
        title="Recommendations",
        border_style="green"
    ))


@cli.command()
def profile():
    """Show current company profile."""
    console.print(Panel("MARV Media Company Profile", style="blue"))

    p = get_profile()

    console.print(f"[bold]{p.legal_name}[/bold]")
    console.print(f"Location: {p.address_city}, {p.address_state}")
    console.print(f"Entity: {p.entity_type}")
    console.print()

    console.print("[bold]Ownership:[/bold]")
    for owner in p.owners:
        tags = []
        if owner.is_woman:
            tags.append("Woman")
        if owner.is_poc:
            tags.append("POC")
        tag_str = f" ({', '.join(tags)})" if tags else ""
        console.print(f"  - {owner.name}: {owner.ownership_percentage:.1f}%{tag_str}")

    console.print()
    console.print(f"[bold]Financials:[/bold]")
    console.print(f"  Revenue: ${p.annual_revenue:,.0f}")
    console.print(f"  Employees: {p.employee_count}")

    console.print()
    console.print(f"[bold]Industry (NAICS):[/bold]")
    for code in p.naics_codes:
        console.print(f"  - {code}")

    console.print()
    console.print(f"[bold]Current Certifications:[/bold]")
    if p.certifications:
        for cert in p.certifications:
            console.print(f"  - {cert}")
    else:
        console.print("  [dim]None yet[/dim]")


@cli.command()
def sources():
    """List available grant sources."""
    console.print(Panel("Available Grant Sources", style="blue"))

    sources_info = [
        ("Federal", [
            ("grants.gov", "Federal grants database", "API", "Implemented"),
            ("sam.gov", "Federal contracts & opportunities", "API", "Planned"),
            ("sba.gov", "SBA programs (SBIR/STTR)", "Scraper", "Planned"),
        ]),
        ("California State", [
            ("calosba.ca.gov", "CA Office of Small Business", "Scraper", "Planned"),
            ("ibank.ca.gov", "CA Infrastructure Bank", "Scraper", "Planned"),
        ]),
        ("Women/Minority-Owned", [
            ("ambergrantsforwomen.com", "Amber Grant ($10k monthly)", "Scraper", "Implemented"),
            ("mbda.gov", "Minority Business Development", "Scraper", "Planned"),
            ("wbenc.org", "Women's Business Enterprise", "Scraper", "Planned"),
        ]),
        ("Corporate", [
            ("fedex.com", "FedEx Small Business Grant", "Scraper", "Planned"),
            ("nav.com", "Nav Grant Program", "Scraper", "Planned"),
        ]),
        ("Aggregators", [
            ("grantwatch.com", "Grant aggregator", "Scraper", "Planned"),
            ("instrumentl.com", "Grant database (paid)", "API", "Planned"),
        ]),
    ]

    for category, sources in sources_info:
        table = Table(title=category)
        table.add_column("Source", style="cyan")
        table.add_column("Description")
        table.add_column("Method")
        table.add_column("Status")

        for source, desc, method, status in sources:
            status_style = "green" if status == "Implemented" else "yellow"
            table.add_row(source, desc, method, f"[{status_style}]{status}[/{status_style}]")

        console.print(table)
        console.print()


@cli.command()
def setup():
    """Set up Google Sheets and verify configuration."""
    console.print(Panel("Setting up Grant Finder", style="blue"))

    # Check configuration
    console.print("[bold]Checking configuration...[/bold]")
    if validate_config():
        console.print("  [green]Configuration valid[/green]")
    else:
        console.print("  [red]Configuration incomplete[/red]")
        console.print()
        console.print("Create a .env file with:")
        console.print("  GEMINI_API_KEY=your_key")
        console.print("  GOOGLE_SHEETS_ID=your_sheet_id")
        console.print("  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
        return

    # Set up sheets
    console.print()
    console.print("[bold]Setting up Google Sheets...[/bold]")
    try:
        from sheets_tracker import SheetsTracker
        tracker = SheetsTracker()

        if tracker.connect():
            console.print("  [green]Connected to Google Sheets[/green]")

            if tracker.setup_sheets():
                console.print("  [green]Sheet structure created[/green]")
            else:
                console.print("  [red]Failed to create sheet structure[/red]")
        else:
            console.print("  [red]Failed to connect to Google Sheets[/red]")

    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")

    console.print()
    console.print("[bold green]Setup complete![/bold green]")
    console.print()
    console.print("Next steps:")
    console.print("  1. Run [bold]python main.py scan[/bold] to find grants")
    console.print("  2. Run [bold]python main.py match[/bold] to see eligible grants")
    console.print("  3. Run [bold]python main.py draft <grant_id>[/bold] to create applications")


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def export_profile(output):
    """Export company profile as JSON."""
    data = profile_to_json()

    if output:
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Profile exported to {output}[/green]")
    else:
        console.print(json.dumps(data, indent=2))


if __name__ == "__main__":
    cli()
