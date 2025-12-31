# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: CLI Entry Point
# Authority: None (observational only)
# Callers: CLI, scheduled jobs
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Semantic Auditor Runner

CLI entry point for running semantic audits.

Usage:
    python -m scripts.semantic_auditor.runner scan
    python -m scripts.semantic_auditor.runner scan --domain auth
    python -m scripts.semantic_auditor.runner scan --changed-since HEAD~5
    python -m scripts.semantic_auditor.runner scan --output json
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List

from .scanner.repo_walker import RepoWalker
from .correlation.observed_behavior import ObservedBehavior
from .correlation.delta_engine import DeltaEngine
from .reporting.report_builder import ReportBuilder


class SemanticAuditor:
    """Main auditor class that orchestrates the scan."""

    # Default paths
    DEFAULT_APP_ROOT = Path("/root/agenticverz2.0/backend/app")
    DEFAULT_DOCS_ROOT = Path("/root/agenticverz2.0/docs")
    DEFAULT_REPORT_PATH = Path("/root/agenticverz2.0/docs/reports/SEMANTIC_AUDIT_REPORT.md")
    DEFAULT_JSON_REPORT_PATH = Path("/root/agenticverz2.0/docs/reports/semantic_audit_report.json")

    def __init__(
        self,
        app_root: Optional[Path] = None,
        docs_root: Optional[Path] = None,
    ):
        """
        Initialize the auditor.

        Args:
            app_root: Root of the application to scan
            docs_root: Root of documentation directory
        """
        self.app_root = app_root or self.DEFAULT_APP_ROOT
        self.docs_root = docs_root or self.DEFAULT_DOCS_ROOT

        self.repo_walker = RepoWalker(str(self.app_root))
        self.observed_behavior = ObservedBehavior(app_root=self.app_root)
        self.delta_engine = DeltaEngine()
        self.report_builder = ReportBuilder(root_path=self.app_root)

    def scan(
        self,
        domain: Optional[str] = None,
        changed_since: Optional[str] = None,
        changed_files: Optional[List[str]] = None,
    ) -> "ScanResult":
        """
        Run a scan of the codebase.

        Args:
            domain: Optional domain to filter by
            changed_since: Optional reference point for changed files
            changed_files: Optional list of changed file paths

        Returns:
            ScanResult with the report
        """
        # Get files to scan
        if domain:
            files = list(self.repo_walker.walk_domain(domain))
        elif changed_since:
            files = list(self.repo_walker.walk_changed_since(changed_since, changed_files))
        else:
            files = list(self.repo_walker.walk())

        print(f"Scanning {len(files)} files...")

        # Analyze files
        file_signals = self.observed_behavior.analyze_files(files)

        # Compute deltas
        delta_report = self.delta_engine.compute(self.app_root, file_signals)

        # Build structured report
        structured_report = self.report_builder.build(delta_report)

        return ScanResult(
            auditor=self,
            structured_report=structured_report,
            files_scanned=len(files),
        )


class ScanResult:
    """Result of a scan operation."""

    def __init__(self, auditor: SemanticAuditor, structured_report, files_scanned: int):
        self.auditor = auditor
        self.structured_report = structured_report
        self.files_scanned = files_scanned

    def print_summary(self) -> None:
        """Print a summary to stdout."""
        report = self.structured_report
        delta_report = report.delta_report

        print("\n" + "=" * 60)
        print("SEMANTIC AUDIT SUMMARY")
        print("=" * 60)
        print(f"Files Scanned:       {delta_report.files_scanned}")
        print(f"Files with Signals:  {delta_report.files_with_signals}")
        print(f"Total Findings:      {delta_report.total_deltas}")
        print(f"Risk Score:          {report.risk_scores.get('total_score', 0)}")
        print()
        print("Risk Distribution:")
        print(f"  CRITICAL:  {report.risk_scores.get('CRITICAL', 0)}")
        print(f"  HIGH_RISK: {report.risk_scores.get('HIGH_RISK', 0)}")
        print(f"  WARNING:   {report.risk_scores.get('WARNING', 0)}")
        print(f"  INFO:      {report.risk_scores.get('INFO', 0)}")
        print()

        if report.by_type:
            print("Findings by Type:")
            for delta_type, deltas in report.by_type.items():
                print(f"  {delta_type}: {len(deltas)}")
        print("=" * 60)

    def save_markdown(self, output_path: Optional[Path] = None) -> Path:
        """Save the markdown report."""
        path = output_path or self.auditor.DEFAULT_REPORT_PATH
        self.auditor.report_builder.save_markdown(self.structured_report, path)
        print(f"Markdown report saved to: {path}")
        return path

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """Save the JSON report."""
        path = output_path or self.auditor.DEFAULT_JSON_REPORT_PATH
        self.auditor.report_builder.save_json(self.structured_report, path)
        print(f"JSON report saved to: {path}")
        return path


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="semantic_auditor",
        description="Semantic Auditor - Observational codebase analysis tool",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan the codebase")
    scan_parser.add_argument(
        "--domain",
        type=str,
        help="Only scan a specific domain",
    )
    scan_parser.add_argument(
        "--changed-since",
        type=str,
        help="Only scan files changed since reference (e.g., HEAD~5)",
    )
    scan_parser.add_argument(
        "--output",
        type=str,
        choices=["markdown", "json", "both"],
        default="both",
        help="Output format (default: both)",
    )
    scan_parser.add_argument(
        "--app-root",
        type=str,
        help="Root of the application to scan",
    )
    scan_parser.add_argument(
        "--report-path",
        type=str,
        help="Path for the output report",
    )
    scan_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "scan":
        return run_scan(args)

    return 0


def run_scan(args: argparse.Namespace) -> int:
    """Run the scan command."""
    # Determine app root
    app_root = None
    if args.app_root:
        app_root = Path(args.app_root)

    # Create auditor
    auditor = SemanticAuditor(app_root=app_root)

    # Run scan
    result = auditor.scan(
        domain=args.domain,
        changed_since=args.changed_since,
    )

    # Print summary unless quiet
    if not args.quiet:
        result.print_summary()

    # Save reports
    report_path = Path(args.report_path) if args.report_path else None

    if args.output in ["markdown", "both"]:
        md_path = report_path.with_suffix(".md") if report_path else None
        result.save_markdown(md_path)

    if args.output in ["json", "both"]:
        json_path = report_path.with_suffix(".json") if report_path else None
        result.save_json(json_path)

    # Return non-zero if critical findings (but don't fail CI)
    # This is observational - we just indicate status
    return 0


if __name__ == "__main__":
    sys.exit(main())
