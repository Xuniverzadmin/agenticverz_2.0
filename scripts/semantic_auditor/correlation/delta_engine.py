# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Semantic Delta Engine
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Delta Engine

Computes semantic deltas by comparing declared semantics with observed behavior.
Produces the core risk assessment that feeds into reporting.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .declared_semantics import DeclaredSemantics
from .observed_behavior import ObservedBehavior, FileSignals


@dataclass
class SemanticDelta:
    """A delta between declared and observed semantics."""

    file_path: Path
    delta_type: str
    severity: str  # INFO, WARNING, HIGH_RISK, CRITICAL
    message: str
    declared: Optional[str] = None
    observed: Optional[str] = None
    line_number: int = 1
    signal_data: Optional[Dict[str, Any]] = None


@dataclass
class DeltaReport:
    """Complete delta report for a scan."""

    scan_timestamp: datetime
    root_path: Path
    files_scanned: int
    files_with_signals: int
    total_deltas: int
    deltas: List[SemanticDelta] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for d in self.deltas if d.severity == "CRITICAL")

    @property
    def high_risk_count(self) -> int:
        return sum(1 for d in self.deltas if d.severity == "HIGH_RISK")

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.deltas if d.severity == "WARNING")

    @property
    def info_count(self) -> int:
        return sum(1 for d in self.deltas if d.severity == "INFO")


class DeltaEngine:
    """Computes semantic deltas between declared and observed."""

    # Severity mapping for signal types
    SIGNAL_SEVERITY: Dict[str, str] = {
        "MISSING_SEMANTIC_HEADER": "WARNING",
        "INCOMPLETE_SEMANTIC_HEADER": "INFO",
        "ASYNC_BLOCKING_CALL": "HIGH_RISK",
        "WRITE_OUTSIDE_WRITE_SERVICE": "HIGH_RISK",
        "LAYER_IMPORT_VIOLATION": "WARNING",
    }

    def __init__(self):
        """Initialize the delta engine."""
        self.declared_semantics = DeclaredSemantics()
        self.observed_behavior: Optional[ObservedBehavior] = None

    def compute(
        self,
        root_path: Path,
        file_signals: Dict[Path, FileSignals],
    ) -> DeltaReport:
        """
        Compute semantic deltas from observed signals.

        Args:
            root_path: Root path of the scanned codebase
            file_signals: Dict of file paths to their signals

        Returns:
            DeltaReport with all computed deltas
        """
        deltas: List[SemanticDelta] = []

        for file_path, signals in file_signals.items():
            file_deltas = self._compute_file_deltas(file_path, signals)
            deltas.extend(file_deltas)

        # Build summary
        summary = {}
        for delta in deltas:
            if delta.delta_type not in summary:
                summary[delta.delta_type] = 0
            summary[delta.delta_type] += 1

        return DeltaReport(
            scan_timestamp=datetime.now(),
            root_path=root_path,
            files_scanned=len(file_signals),
            files_with_signals=sum(1 for s in file_signals.values() if s.has_signals),
            total_deltas=len(deltas),
            deltas=deltas,
            summary=summary,
        )

    def _compute_file_deltas(
        self, file_path: Path, signals: FileSignals
    ) -> List[SemanticDelta]:
        """Compute deltas for a single file."""
        deltas = []

        # Convert affordance signals to deltas
        for signal in signals.affordance_signals:
            deltas.append(
                SemanticDelta(
                    file_path=file_path,
                    delta_type=signal.signal_type,
                    severity=self.SIGNAL_SEVERITY.get(signal.signal_type, "INFO"),
                    message=signal.message,
                    declared=signal.expected,
                    observed=signal.actual,
                    line_number=signal.line_number,
                )
            )

        # Convert execution signals to deltas
        for signal in signals.execution_signals:
            deltas.append(
                SemanticDelta(
                    file_path=file_path,
                    delta_type=signal.signal_type,
                    severity=self.SIGNAL_SEVERITY.get(signal.signal_type, "WARNING"),
                    message=signal.message,
                    declared="Async function should use async I/O",
                    observed=f"Uses blocking call: {signal.blocking_call}",
                    line_number=signal.line_number,
                    signal_data={
                        "function": signal.function_name,
                        "blocking_call": signal.blocking_call,
                    },
                )
            )

        # Convert authority signals to deltas
        for signal in signals.authority_signals:
            deltas.append(
                SemanticDelta(
                    file_path=file_path,
                    delta_type=signal.signal_type,
                    severity=self.SIGNAL_SEVERITY.get(signal.signal_type, "HIGH_RISK"),
                    message=signal.message,
                    declared="DB writes should be in *_write_service.py",
                    observed=f"Write operation in: {signal.function_name}",
                    line_number=signal.line_number,
                    signal_data={
                        "function": signal.function_name,
                        "write_operation": signal.write_operation,
                    },
                )
            )

        # Convert layering signals to deltas
        for signal in signals.layering_signals:
            deltas.append(
                SemanticDelta(
                    file_path=file_path,
                    delta_type=signal.signal_type,
                    severity=self.SIGNAL_SEVERITY.get(signal.signal_type, "WARNING"),
                    message=signal.message,
                    declared=f"Layer {signal.source_layer} should not import {signal.target_layer}",
                    observed=f"Import: {signal.import_path}",
                    line_number=signal.line_number,
                    signal_data={
                        "source_layer": signal.source_layer,
                        "target_layer": signal.target_layer,
                        "import_path": signal.import_path,
                    },
                )
            )

        return deltas

    def get_deltas_by_severity(
        self, report: DeltaReport, severity: str
    ) -> List[SemanticDelta]:
        """Get all deltas of a specific severity."""
        return [d for d in report.deltas if d.severity == severity]

    def get_deltas_by_type(
        self, report: DeltaReport, delta_type: str
    ) -> List[SemanticDelta]:
        """Get all deltas of a specific type."""
        return [d for d in report.deltas if d.delta_type == delta_type]

    def get_deltas_for_file(
        self, report: DeltaReport, file_path: Path
    ) -> List[SemanticDelta]:
        """Get all deltas for a specific file."""
        return [d for d in report.deltas if d.file_path == file_path]

    def get_deltas_for_domain(
        self, report: DeltaReport, domain: str
    ) -> List[SemanticDelta]:
        """Get all deltas for a specific domain."""
        return [d for d in report.deltas if domain in str(d.file_path)]
