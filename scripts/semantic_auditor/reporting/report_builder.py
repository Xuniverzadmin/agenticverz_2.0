# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Report Builder
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Report Builder

Builds structured reports from delta reports.
Groups risks by domain, layer, and file for easy navigation.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..correlation.delta_engine import DeltaReport, SemanticDelta
from .risk_model import RiskModel, RiskLevel
from .renderers.markdown import MarkdownRenderer
from .renderers.json import JSONRenderer


@dataclass
class DomainReport:
    """Report section for a single domain."""

    domain: str
    delta_count: int
    high_risk_count: int
    deltas: List[SemanticDelta]


@dataclass
class LayerReport:
    """Report section for a single layer."""

    layer: str
    delta_count: int
    high_risk_count: int
    deltas: List[SemanticDelta]


@dataclass
class StructuredReport:
    """Structured report with multiple views of the data."""

    delta_report: DeltaReport
    risk_scores: Dict[str, int]
    by_domain: Dict[str, DomainReport] = field(default_factory=dict)
    by_layer: Dict[str, LayerReport] = field(default_factory=dict)
    by_severity: Dict[str, List[SemanticDelta]] = field(default_factory=dict)
    by_type: Dict[str, List[SemanticDelta]] = field(default_factory=dict)


class ReportBuilder:
    """Builds structured reports from delta reports."""

    def __init__(self, root_path: Optional[Path] = None):
        """
        Initialize the report builder.

        Args:
            root_path: Root path for relative path display
        """
        self.root_path = root_path
        self.risk_model = RiskModel()
        self.markdown_renderer = MarkdownRenderer(root_path=root_path)
        self.json_renderer = JSONRenderer(root_path=root_path)

    def build(self, delta_report: DeltaReport) -> StructuredReport:
        """
        Build a structured report from a delta report.

        Args:
            delta_report: The delta report to structure

        Returns:
            StructuredReport with multiple views
        """
        # Compute risk scores
        risk_scores = self.risk_model.assess_report(delta_report)

        # Initialize structured report
        report = StructuredReport(
            delta_report=delta_report,
            risk_scores=risk_scores,
        )

        # Group by severity
        for level in RiskLevel:
            report.by_severity[level.value] = [
                d for d in delta_report.deltas if d.severity == level.value
            ]

        # Group by delta type
        for delta in delta_report.deltas:
            if delta.delta_type not in report.by_type:
                report.by_type[delta.delta_type] = []
            report.by_type[delta.delta_type].append(delta)

        # Group by domain (extracted from file path)
        domain_deltas: Dict[str, List[SemanticDelta]] = {}
        for delta in delta_report.deltas:
            domain = self._extract_domain(delta.file_path)
            if domain not in domain_deltas:
                domain_deltas[domain] = []
            domain_deltas[domain].append(delta)

        for domain, deltas in domain_deltas.items():
            high_risk_count = sum(
                1 for d in deltas if d.severity in ["HIGH_RISK", "CRITICAL"]
            )
            report.by_domain[domain] = DomainReport(
                domain=domain,
                delta_count=len(deltas),
                high_risk_count=high_risk_count,
                deltas=deltas,
            )

        # Group by layer
        layer_deltas: Dict[str, List[SemanticDelta]] = {}
        for delta in delta_report.deltas:
            layer = self._extract_layer(delta)
            if layer not in layer_deltas:
                layer_deltas[layer] = []
            layer_deltas[layer].append(delta)

        for layer, deltas in layer_deltas.items():
            high_risk_count = sum(
                1 for d in deltas if d.severity in ["HIGH_RISK", "CRITICAL"]
            )
            report.by_layer[layer] = LayerReport(
                layer=layer,
                delta_count=len(deltas),
                high_risk_count=high_risk_count,
                deltas=deltas,
            )

        return report

    def _extract_domain(self, file_path: Path) -> str:
        """Extract domain from file path."""
        parts = file_path.parts

        # Skip common prefixes
        skip = {"app", "src", "backend", "frontend"}

        for i, part in enumerate(parts):
            if part.lower() in skip:
                continue
            if (
                part.lower() not in skip
                and not part.startswith("_")
                and not part.startswith(".")
                and part != file_path.name
            ):
                return part

        return "unknown"

    def _extract_layer(self, delta: SemanticDelta) -> str:
        """Extract layer from delta or file path."""
        if delta.signal_data and "source_layer" in delta.signal_data:
            return delta.signal_data["source_layer"]

        # Infer from path
        path_str = str(delta.file_path).lower()
        layer_indicators = {
            "api": "L5",
            "routers": "L5",
            "services": "L4",
            "domain": "L3",
            "models": "L3",
            "repositories": "L2",
            "workers": "L7",
            "scripts": "L8",
        }

        for indicator, layer in layer_indicators.items():
            if indicator in path_str:
                return layer

        return "UNKNOWN"

    def render_markdown(self, report: StructuredReport) -> str:
        """Render the report as markdown."""
        return self.markdown_renderer.render(report)

    def render_json(self, report: StructuredReport) -> str:
        """Render the report as JSON."""
        return self.json_renderer.render(report)

    def save_markdown(self, report: StructuredReport, output_path: Path) -> None:
        """Save the report as a markdown file."""
        content = self.render_markdown(report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    def save_json(self, report: StructuredReport, output_path: Path) -> None:
        """Save the report as a JSON file."""
        content = self.render_json(report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
