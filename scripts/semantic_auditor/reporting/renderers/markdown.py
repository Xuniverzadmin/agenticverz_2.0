# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Markdown Report Renderer
# Authority: None (observational only)
# Callers: semantic_auditor.reporting.report_builder
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Markdown Renderer

Renders structured reports as human-readable markdown documents.
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..report_builder import StructuredReport


class MarkdownRenderer:
    """Renders reports as markdown."""

    def __init__(self, root_path: Optional[Path] = None):
        """
        Initialize the markdown renderer.

        Args:
            root_path: Root path for relative path display
        """
        self.root_path = root_path

    def render(self, report: "StructuredReport") -> str:
        """
        Render a structured report as markdown.

        Args:
            report: The structured report to render

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append("# Semantic Audit Report")
        lines.append("")
        lines.append(f"**Generated:** {report.delta_report.scan_timestamp.isoformat()}")
        lines.append(f"**Scanned Path:** `{report.delta_report.root_path}`")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Files Scanned | {report.delta_report.files_scanned} |")
        lines.append(f"| Files with Signals | {report.delta_report.files_with_signals} |")
        lines.append(f"| Total Findings | {report.delta_report.total_deltas} |")
        lines.append(f"| Risk Score | {report.risk_scores.get('total_score', 0)} |")
        lines.append("")

        # Risk Distribution
        lines.append("### Risk Distribution")
        lines.append("")
        lines.append("| Level | Count |")
        lines.append("|-------|-------|")
        lines.append(f"| CRITICAL | {report.risk_scores.get('CRITICAL', 0)} |")
        lines.append(f"| HIGH_RISK | {report.risk_scores.get('HIGH_RISK', 0)} |")
        lines.append(f"| WARNING | {report.risk_scores.get('WARNING', 0)} |")
        lines.append(f"| INFO | {report.risk_scores.get('INFO', 0)} |")
        lines.append("")

        # Findings by Type
        lines.append("## Findings by Type")
        lines.append("")

        for delta_type, deltas in report.by_type.items():
            lines.append(f"### {delta_type}")
            lines.append("")
            lines.append(f"**Count:** {len(deltas)}")
            lines.append("")

            if deltas:
                lines.append("| File | Line | Message |")
                lines.append("|------|------|---------|")
                for delta in deltas[:20]:  # Limit to first 20
                    rel_path = self._relative_path(delta.file_path)
                    lines.append(
                        f"| `{rel_path}` | {delta.line_number} | {delta.message} |"
                    )
                if len(deltas) > 20:
                    lines.append(f"| ... | | *{len(deltas) - 20} more* |")
                lines.append("")

        # High Risk Findings (detailed)
        high_risk = report.by_severity.get("HIGH_RISK", []) + report.by_severity.get("CRITICAL", [])
        if high_risk:
            lines.append("## High Risk Findings (Detailed)")
            lines.append("")
            lines.append("These findings require attention and should be reviewed.")
            lines.append("")

            for delta in high_risk:
                rel_path = self._relative_path(delta.file_path)
                lines.append(f"### `{rel_path}:{delta.line_number}`")
                lines.append("")
                lines.append(f"**Type:** {delta.delta_type}")
                lines.append(f"**Severity:** {delta.severity}")
                lines.append("")
                lines.append(f"**Message:** {delta.message}")
                lines.append("")
                if delta.declared:
                    lines.append(f"**Expected:** {delta.declared}")
                if delta.observed:
                    lines.append(f"**Observed:** {delta.observed}")
                lines.append("")

        # Findings by Domain
        if report.by_domain:
            lines.append("## Findings by Domain")
            lines.append("")
            lines.append("| Domain | Total | High Risk |")
            lines.append("|--------|-------|-----------|")
            for domain, domain_report in sorted(
                report.by_domain.items(),
                key=lambda x: x[1].high_risk_count,
                reverse=True,
            ):
                lines.append(
                    f"| {domain} | {domain_report.delta_count} | "
                    f"{domain_report.high_risk_count} |"
                )
            lines.append("")

        # Findings by Layer
        if report.by_layer:
            lines.append("## Findings by Layer")
            lines.append("")
            lines.append("| Layer | Total | High Risk |")
            lines.append("|-------|-------|-----------|")
            for layer, layer_report in sorted(report.by_layer.items()):
                lines.append(
                    f"| {layer} | {layer_report.delta_count} | "
                    f"{layer_report.high_risk_count} |"
                )
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*This report is observational only. It does not block CI or fail builds.*")
        lines.append("*Review findings and address as appropriate for your context.*")
        lines.append("")
        lines.append("Generated by Semantic Auditor v0.1.0")

        return "\n".join(lines)

    def _relative_path(self, file_path: Path) -> str:
        """Get relative path for display."""
        if self.root_path:
            try:
                return str(file_path.relative_to(self.root_path))
            except ValueError:
                pass
        return str(file_path)
