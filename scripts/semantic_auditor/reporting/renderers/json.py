# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: JSON Report Renderer
# Authority: None (observational only)
# Callers: semantic_auditor.reporting.report_builder
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
JSON Renderer

Renders structured reports as machine-readable JSON documents.
"""

import json
from pathlib import Path
from typing import Optional, Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..report_builder import StructuredReport


class JSONRenderer:
    """Renders reports as JSON."""

    def __init__(self, root_path: Optional[Path] = None):
        """
        Initialize the JSON renderer.

        Args:
            root_path: Root path for relative path display
        """
        self.root_path = root_path

    def render(self, report: "StructuredReport") -> str:
        """
        Render a structured report as JSON.

        Args:
            report: The structured report to render

        Returns:
            JSON string
        """
        data = self._build_json_structure(report)
        return json.dumps(data, indent=2, default=str)

    def _build_json_structure(self, report: "StructuredReport") -> Dict[str, Any]:
        """Build the JSON structure from the report."""
        delta_report = report.delta_report

        return {
            "metadata": {
                "generated": delta_report.scan_timestamp.isoformat(),
                "scanned_path": str(delta_report.root_path),
                "version": "0.1.0",
            },
            "summary": {
                "files_scanned": delta_report.files_scanned,
                "files_with_signals": delta_report.files_with_signals,
                "total_findings": delta_report.total_deltas,
                "risk_scores": report.risk_scores,
            },
            "findings_by_type": {
                delta_type: [
                    self._delta_to_dict(delta)
                    for delta in deltas
                ]
                for delta_type, deltas in report.by_type.items()
            },
            "findings_by_severity": {
                severity: [
                    self._delta_to_dict(delta)
                    for delta in deltas
                ]
                for severity, deltas in report.by_severity.items()
                if deltas  # Only include non-empty severity levels
            },
            "findings_by_domain": {
                domain: {
                    "count": domain_report.delta_count,
                    "high_risk_count": domain_report.high_risk_count,
                    "findings": [
                        self._delta_to_dict(delta)
                        for delta in domain_report.deltas
                    ],
                }
                for domain, domain_report in report.by_domain.items()
            },
            "findings_by_layer": {
                layer: {
                    "count": layer_report.delta_count,
                    "high_risk_count": layer_report.high_risk_count,
                    "findings": [
                        self._delta_to_dict(delta)
                        for delta in layer_report.deltas
                    ],
                }
                for layer, layer_report in report.by_layer.items()
            },
        }

    def _delta_to_dict(self, delta: Any) -> Dict[str, Any]:
        """Convert a SemanticDelta to a dictionary."""
        return {
            "file": self._relative_path(delta.file_path),
            "line": delta.line_number,
            "type": delta.delta_type,
            "severity": delta.severity,
            "message": delta.message,
            "declared": delta.declared,
            "observed": delta.observed,
            "signal_data": delta.signal_data,
        }

    def _relative_path(self, file_path: Path) -> str:
        """Get relative path for display."""
        if self.root_path:
            try:
                return str(file_path.relative_to(self.root_path))
            except ValueError:
                pass
        return str(file_path)
