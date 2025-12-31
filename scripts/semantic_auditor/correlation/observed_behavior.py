# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Observed Behavior Aggregator
# Authority: None (observational only)
# Callers: semantic_auditor.correlation.delta_engine
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Observed Behavior

Aggregates signals from all detectors per file, providing the "actual"
side of the semantic delta comparison.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..scanner.ast_loader import ASTLoader, ASTAnalysis
from ..scanner.file_classifier import FileClassifier, FileClassification
from ..signals.affordance import AffordanceSignalDetector, AffordanceSignal
from ..signals.execution import ExecutionSignalDetector, ExecutionSignal
from ..signals.authority import AuthoritySignalDetector, AuthoritySignal
from ..signals.layering import LayeringSignalDetector, LayeringSignal


@dataclass
class FileSignals:
    """All signals detected for a single file."""

    file_path: Path
    classification: FileClassification
    affordance_signals: List[AffordanceSignal] = field(default_factory=list)
    execution_signals: List[ExecutionSignal] = field(default_factory=list)
    authority_signals: List[AuthoritySignal] = field(default_factory=list)
    layering_signals: List[LayeringSignal] = field(default_factory=list)
    parse_error: Optional[str] = None

    @property
    def total_signal_count(self) -> int:
        """Get total number of signals."""
        return (
            len(self.affordance_signals)
            + len(self.execution_signals)
            + len(self.authority_signals)
            + len(self.layering_signals)
        )

    @property
    def has_signals(self) -> bool:
        """Check if any signals were detected."""
        return self.total_signal_count > 0

    def get_all_signals(self) -> List[Any]:
        """Get all signals as a flat list."""
        return (
            self.affordance_signals
            + self.execution_signals
            + self.authority_signals
            + self.layering_signals
        )


class ObservedBehavior:
    """Aggregates observed signals from the codebase."""

    def __init__(self, app_root: Optional[Path] = None):
        """
        Initialize the observed behavior aggregator.

        Args:
            app_root: Root of the application being analyzed
        """
        self.app_root = app_root
        self.ast_loader = ASTLoader()
        self.file_classifier = FileClassifier()
        self.affordance_detector = AffordanceSignalDetector()
        self.execution_detector = ExecutionSignalDetector()
        self.authority_detector = AuthoritySignalDetector()
        self.layering_detector = LayeringSignalDetector(app_root=app_root)

        self._file_signals: Dict[Path, FileSignals] = {}

    def analyze_file(self, file_path: Path) -> FileSignals:
        """
        Analyze a single file and aggregate all signals.

        Args:
            file_path: Path to the Python file

        Returns:
            FileSignals with all detected signals
        """
        # Classify the file
        classification = self.file_classifier.classify(file_path)

        # Parse the AST
        analysis = self.ast_loader.load(file_path)

        # Create the signals container
        file_signals = FileSignals(
            file_path=file_path,
            classification=classification,
        )

        if not analysis.parse_success:
            file_signals.parse_error = analysis.parse_error
            self._file_signals[file_path] = file_signals
            return file_signals

        # Run all detectors
        file_signals.affordance_signals = self.affordance_detector.detect(
            analysis, classification
        )
        file_signals.execution_signals = self.execution_detector.detect(analysis)
        file_signals.authority_signals = self.authority_detector.detect(
            analysis, classification
        )
        file_signals.layering_signals = self.layering_detector.detect(
            analysis, classification
        )

        self._file_signals[file_path] = file_signals
        return file_signals

    def analyze_files(self, file_paths: List[Path]) -> Dict[Path, FileSignals]:
        """
        Analyze multiple files.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Dict mapping file paths to their signals
        """
        for file_path in file_paths:
            self.analyze_file(file_path)

        return self._file_signals

    def get_file_signals(self, file_path: Path) -> Optional[FileSignals]:
        """Get cached signals for a file."""
        return self._file_signals.get(file_path)

    def get_files_with_signals(self) -> List[Path]:
        """Get list of files that have any signals."""
        return [
            path
            for path, signals in self._file_signals.items()
            if signals.has_signals
        ]

    def get_signal_summary(self) -> Dict[str, int]:
        """Get a summary count of signals by type."""
        summary = {
            "MISSING_SEMANTIC_HEADER": 0,
            "INCOMPLETE_SEMANTIC_HEADER": 0,
            "ASYNC_BLOCKING_CALL": 0,
            "WRITE_OUTSIDE_WRITE_SERVICE": 0,
            "LAYER_IMPORT_VIOLATION": 0,
        }

        for file_signals in self._file_signals.values():
            for signal in file_signals.affordance_signals:
                if signal.signal_type in summary:
                    summary[signal.signal_type] += 1
            for signal in file_signals.execution_signals:
                if signal.signal_type in summary:
                    summary[signal.signal_type] += 1
            for signal in file_signals.authority_signals:
                if signal.signal_type in summary:
                    summary[signal.signal_type] += 1
            for signal in file_signals.layering_signals:
                if signal.signal_type in summary:
                    summary[signal.signal_type] += 1

        return summary

    def clear(self) -> None:
        """Clear all cached signals."""
        self._file_signals.clear()
