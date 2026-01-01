# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Layering Signal Detector
# Authority: None (observational only)
# Callers: semantic_auditor.correlation.observed_behavior
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Layering Signal Detector

Detects layering-related signals:
- Import graph violations (e.g., L3 importing L5)
- Cross-layer dependencies that violate architecture
- Circular dependencies between layers

Phase 1 MVP focuses on LAYER_IMPORT_VIOLATION.
"""

from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

from ..scanner.ast_loader import ASTAnalysis, ImportInfo
from ..scanner.file_classifier import FileClassification, LayerLevel


@dataclass
class LayeringSignal:
    """A detected layering signal."""

    signal_type: str
    file_path: Path
    line_number: int
    message: str
    source_layer: str
    target_layer: str
    import_path: str

    def __repr__(self) -> str:
        return f"LayeringSignal({self.signal_type}, {self.source_layer}->{self.target_layer})"


class LayeringSignalDetector:
    """Detects layering-related signals in files."""

    # Layer hierarchy (lower numbers are lower layers)
    # Higher layers should not import from lower layers in certain cases
    # But more importantly, lower layers should NOT import from higher layers
    LAYER_ORDER: Dict[LayerLevel, int] = {
        LayerLevel.L1_STORAGE: 1,
        LayerLevel.L2_DATA: 2,
        LayerLevel.L3_DOMAIN: 3,
        LayerLevel.L4_SERVICE: 4,
        LayerLevel.L5_API: 5,
        LayerLevel.L6_INTEGRATION: 6,
        LayerLevel.L7_WORKERS: 7,
        LayerLevel.L8_META: 8,
        LayerLevel.UNKNOWN: 0,
    }

    # Allowed import directions
    # Key: source layer, Value: set of allowed target layers
    # Lower layers should not import from higher layers
    ALLOWED_IMPORTS: Dict[LayerLevel, Set[LayerLevel]] = {
        LayerLevel.L1_STORAGE: {LayerLevel.L1_STORAGE},
        LayerLevel.L2_DATA: {
            LayerLevel.L1_STORAGE,
            LayerLevel.L2_DATA,
            LayerLevel.L3_DOMAIN,
        },
        LayerLevel.L3_DOMAIN: {LayerLevel.L3_DOMAIN},
        LayerLevel.L4_SERVICE: {
            LayerLevel.L2_DATA,
            LayerLevel.L3_DOMAIN,
            LayerLevel.L4_SERVICE,
            LayerLevel.L6_INTEGRATION,
        },
        LayerLevel.L5_API: {
            LayerLevel.L3_DOMAIN,
            LayerLevel.L4_SERVICE,
            LayerLevel.L5_API,
        },
        LayerLevel.L6_INTEGRATION: {
            LayerLevel.L3_DOMAIN,
            LayerLevel.L6_INTEGRATION,
        },
        LayerLevel.L7_WORKERS: {
            LayerLevel.L3_DOMAIN,
            LayerLevel.L4_SERVICE,
            LayerLevel.L6_INTEGRATION,
            LayerLevel.L7_WORKERS,
        },
        LayerLevel.L8_META: {
            # Meta layer can import from anywhere
            LayerLevel.L1_STORAGE,
            LayerLevel.L2_DATA,
            LayerLevel.L3_DOMAIN,
            LayerLevel.L4_SERVICE,
            LayerLevel.L5_API,
            LayerLevel.L6_INTEGRATION,
            LayerLevel.L7_WORKERS,
            LayerLevel.L8_META,
        },
    }

    # Directory patterns that indicate layer
    LAYER_INDICATORS: Dict[str, LayerLevel] = {
        "api": LayerLevel.L5_API,
        "routers": LayerLevel.L5_API,
        "endpoints": LayerLevel.L5_API,
        "services": LayerLevel.L4_SERVICE,
        "service": LayerLevel.L4_SERVICE,
        "domain": LayerLevel.L3_DOMAIN,
        "core": LayerLevel.L3_DOMAIN,
        "models": LayerLevel.L3_DOMAIN,
        "repositories": LayerLevel.L2_DATA,
        "repos": LayerLevel.L2_DATA,
        "db": LayerLevel.L1_STORAGE,
        "database": LayerLevel.L1_STORAGE,
        "workers": LayerLevel.L7_WORKERS,
        "tasks": LayerLevel.L7_WORKERS,
        "integrations": LayerLevel.L6_INTEGRATION,
        "external": LayerLevel.L6_INTEGRATION,
        "clients": LayerLevel.L6_INTEGRATION,
        "scripts": LayerLevel.L8_META,
        "tools": LayerLevel.L8_META,
    }

    def __init__(self, app_root: Optional[Path] = None):
        """Initialize the detector."""
        self.app_root = app_root
        self._module_layer_cache: Dict[str, LayerLevel] = {}

    def detect(
        self, analysis: ASTAnalysis, classification: FileClassification
    ) -> List[LayeringSignal]:
        """
        Detect layering signals in a file.

        Args:
            analysis: AST analysis of the file
            classification: File classification info

        Returns:
            List of detected layering signals
        """
        signals = []

        # Skip test files
        if classification.is_test_file:
            return signals

        source_layer = classification.layer

        # Skip unknown layers
        if source_layer == LayerLevel.UNKNOWN:
            return signals

        # Check each import
        for imp in analysis.imports:
            target_layer = self._infer_layer_from_import(imp)

            if target_layer == LayerLevel.UNKNOWN:
                continue

            if self._is_layer_violation(source_layer, target_layer):
                signals.append(
                    LayeringSignal(
                        signal_type="LAYER_IMPORT_VIOLATION",
                        file_path=analysis.file_path,
                        line_number=imp.line_number,
                        message=f"{source_layer.value} imports from {target_layer.value}",
                        source_layer=source_layer.value,
                        target_layer=target_layer.value,
                        import_path=imp.module,
                    )
                )

        return signals

    def _infer_layer_from_import(self, imp: ImportInfo) -> LayerLevel:
        """Infer the layer of an imported module."""
        module = imp.module

        # Check cache
        if module in self._module_layer_cache:
            return self._module_layer_cache[module]

        # Skip standard library and external packages
        if self._is_external_module(module):
            return LayerLevel.UNKNOWN

        # Parse module path for layer indicators
        parts = module.split(".")

        for part in parts:
            part_lower = part.lower()
            if part_lower in self.LAYER_INDICATORS:
                layer = self.LAYER_INDICATORS[part_lower]
                self._module_layer_cache[module] = layer
                return layer

        # No layer detected
        return LayerLevel.UNKNOWN

    def _is_external_module(self, module: str) -> bool:
        """Check if a module is external (not part of the app)."""
        # Standard library and common packages
        external_prefixes = {
            "os",
            "sys",
            "re",
            "json",
            "ast",
            "typing",
            "pathlib",
            "collections",
            "dataclasses",
            "enum",
            "functools",
            "itertools",
            "datetime",
            "time",
            "logging",
            "copy",
            "io",
            "abc",
            "fastapi",
            "pydantic",
            "sqlalchemy",
            "starlette",
            "celery",
            "redis",
            "httpx",
            "aiohttp",
            "requests",
            "pytest",
            "unittest",
            "mock",
        }

        first_part = module.split(".")[0]
        return first_part in external_prefixes

    def _is_layer_violation(
        self, source_layer: LayerLevel, target_layer: LayerLevel
    ) -> bool:
        """Check if importing target_layer from source_layer is a violation."""
        # Unknown layers don't trigger violations
        if source_layer == LayerLevel.UNKNOWN or target_layer == LayerLevel.UNKNOWN:
            return False

        # Get allowed imports for source layer
        allowed = self.ALLOWED_IMPORTS.get(source_layer, set())

        # If target is not in allowed list, it's a violation
        # But we focus on the most egregious violations:
        # Lower layers importing from higher layers
        source_order = self.LAYER_ORDER.get(source_layer, 0)
        target_order = self.LAYER_ORDER.get(target_layer, 0)

        # Violation if lower layer imports from significantly higher layer
        # L3 importing from L5 is a clear violation
        if source_order < target_order and (target_order - source_order) >= 2:
            return True

        # Also check against allowed imports map for stricter violations
        if target_layer not in allowed and source_order < 5:  # Only for lower layers
            # Be more lenient - only flag clear violations
            if target_order > source_order + 1:
                return True

        return False

    def get_layer_for_module(self, module: str) -> LayerLevel:
        """Get the layer for a module path."""
        return self._infer_layer_from_import(
            ImportInfo(module=module, names=[], is_from_import=False, line_number=0)
        )
