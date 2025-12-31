# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: File Role Classifier
# Authority: None (observational only)
# Callers: semantic_auditor.runner, semantic_auditor.signals
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
File Classifier

Classifies Python files by their structural role based on naming conventions
and directory structure. Identifies APIs, workers, services, models, etc.
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import re


class FileRole(Enum):
    """Structural roles for Python files."""

    API_ROUTER = "api_router"
    API_ENDPOINT = "api_endpoint"
    SERVICE = "service"
    WRITE_SERVICE = "write_service"
    READ_SERVICE = "read_service"
    WORKER = "worker"
    MODEL = "model"
    SCHEMA = "schema"
    REPOSITORY = "repository"
    MIGRATION = "migration"
    CONFIG = "config"
    UTIL = "util"
    TEST = "test"
    INIT = "init"
    UNKNOWN = "unknown"


class LayerLevel(Enum):
    """Architecture layers (L1-L8)."""

    L1_STORAGE = "L1"      # Storage/Persistence
    L2_DATA = "L2"         # Data Access Layer
    L3_DOMAIN = "L3"       # Domain/Business Logic
    L4_SERVICE = "L4"      # Service Layer
    L5_API = "L5"          # API Layer
    L6_INTEGRATION = "L6"  # External Integrations
    L7_WORKERS = "L7"      # Background Workers
    L8_META = "L8"         # Meta/Tooling
    UNKNOWN = "UNKNOWN"


@dataclass
class FileClassification:
    """Classification result for a file."""

    file_path: Path
    role: FileRole
    layer: LayerLevel
    domain: Optional[str]
    is_boundary_file: bool
    is_test_file: bool

    def __repr__(self) -> str:
        return (
            f"FileClassification({self.file_path.name}, "
            f"role={self.role.value}, layer={self.layer.value})"
        )


class FileClassifier:
    """Classifies files by structural role and layer."""

    # Patterns for role detection
    ROLE_PATTERNS = {
        FileRole.API_ROUTER: [
            r"router\.py$",
            r"routes\.py$",
            r"api\.py$",
        ],
        FileRole.API_ENDPOINT: [
            r"endpoints?\.py$",
            r"views?\.py$",
        ],
        FileRole.WRITE_SERVICE: [
            r"_write_service\.py$",
            r"write_service\.py$",
        ],
        FileRole.READ_SERVICE: [
            r"_read_service\.py$",
            r"read_service\.py$",
        ],
        FileRole.SERVICE: [
            r"_service\.py$",
            r"service\.py$",
            r"services\.py$",
        ],
        FileRole.WORKER: [
            r"_worker\.py$",
            r"worker\.py$",
            r"workers\.py$",
            r"tasks?\.py$",
            r"celery.*\.py$",
        ],
        FileRole.MODEL: [
            r"models?\.py$",
            r"entities?\.py$",
        ],
        FileRole.SCHEMA: [
            r"schemas?\.py$",
            r"dto\.py$",
            r"dtos?\.py$",
        ],
        FileRole.REPOSITORY: [
            r"repositor(y|ies)\.py$",
            r"repo\.py$",
            r"repos\.py$",
            r"dal\.py$",
        ],
        FileRole.MIGRATION: [
            r"migration.*\.py$",
            r"alembic.*\.py$",
        ],
        FileRole.CONFIG: [
            r"config\.py$",
            r"settings\.py$",
            r"conf\.py$",
        ],
        FileRole.UTIL: [
            r"utils?\.py$",
            r"helpers?\.py$",
            r"common\.py$",
        ],
        FileRole.TEST: [
            r"test_.*\.py$",
            r".*_test\.py$",
        ],
        FileRole.INIT: [
            r"__init__\.py$",
        ],
    }

    # Directory patterns for layer detection
    LAYER_DIR_PATTERNS = {
        LayerLevel.L1_STORAGE: ["db", "database", "storage", "persistence"],
        LayerLevel.L2_DATA: ["repositories", "repos", "dal", "data"],
        LayerLevel.L3_DOMAIN: ["domain", "core", "business", "entities"],
        LayerLevel.L4_SERVICE: ["services", "service", "application"],
        LayerLevel.L5_API: ["api", "rest", "graphql", "endpoints", "routers"],
        LayerLevel.L6_INTEGRATION: ["integrations", "external", "clients", "adapters"],
        LayerLevel.L7_WORKERS: ["workers", "tasks", "jobs", "celery", "background"],
        LayerLevel.L8_META: ["scripts", "tools", "cli", "meta", "tooling"],
    }

    # Boundary file indicators - files at architectural boundaries
    BOUNDARY_INDICATORS = [
        FileRole.API_ROUTER,
        FileRole.API_ENDPOINT,
        FileRole.SERVICE,
        FileRole.WRITE_SERVICE,
        FileRole.READ_SERVICE,
        FileRole.WORKER,
    ]

    def __init__(self):
        """Initialize the classifier with compiled patterns."""
        self._compiled_patterns = {}
        for role, patterns in self.ROLE_PATTERNS.items():
            self._compiled_patterns[role] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify(self, file_path: Path) -> FileClassification:
        """
        Classify a file by its role and layer.

        Args:
            file_path: Path to the Python file

        Returns:
            FileClassification with role, layer, and domain info
        """
        file_name = file_path.name

        # Detect role from filename
        role = self._detect_role(file_name)

        # Detect layer from directory structure
        layer = self._detect_layer(file_path)

        # Extract domain from path
        domain = self._extract_domain(file_path)

        # Determine if boundary file
        is_boundary = role in self.BOUNDARY_INDICATORS

        # Check if test file
        is_test = role == FileRole.TEST or "test" in str(file_path).lower()

        return FileClassification(
            file_path=file_path,
            role=role,
            layer=layer,
            domain=domain,
            is_boundary_file=is_boundary,
            is_test_file=is_test,
        )

    def _detect_role(self, file_name: str) -> FileRole:
        """Detect the role from the filename."""
        # Check write_service first (more specific than service)
        for role in [FileRole.WRITE_SERVICE, FileRole.READ_SERVICE]:
            for pattern in self._compiled_patterns[role]:
                if pattern.search(file_name):
                    return role

        # Check other roles
        for role, patterns in self._compiled_patterns.items():
            if role in [FileRole.WRITE_SERVICE, FileRole.READ_SERVICE]:
                continue
            for pattern in patterns:
                if pattern.search(file_name):
                    return role

        return FileRole.UNKNOWN

    def _detect_layer(self, file_path: Path) -> LayerLevel:
        """Detect the layer from directory structure."""
        path_parts = [p.lower() for p in file_path.parts]

        for layer, indicators in self.LAYER_DIR_PATTERNS.items():
            for indicator in indicators:
                if indicator in path_parts:
                    return layer

        # Fallback: use role-based layer inference
        role = self._detect_role(file_path.name)
        return self._infer_layer_from_role(role)

    def _infer_layer_from_role(self, role: FileRole) -> LayerLevel:
        """Infer layer from role when directory doesn't indicate it."""
        role_to_layer = {
            FileRole.MODEL: LayerLevel.L3_DOMAIN,
            FileRole.REPOSITORY: LayerLevel.L2_DATA,
            FileRole.SERVICE: LayerLevel.L4_SERVICE,
            FileRole.WRITE_SERVICE: LayerLevel.L4_SERVICE,
            FileRole.READ_SERVICE: LayerLevel.L4_SERVICE,
            FileRole.API_ROUTER: LayerLevel.L5_API,
            FileRole.API_ENDPOINT: LayerLevel.L5_API,
            FileRole.WORKER: LayerLevel.L7_WORKERS,
            FileRole.SCHEMA: LayerLevel.L5_API,
            FileRole.CONFIG: LayerLevel.L8_META,
            FileRole.UTIL: LayerLevel.L4_SERVICE,
        }
        return role_to_layer.get(role, LayerLevel.UNKNOWN)

    def _extract_domain(self, file_path: Path) -> Optional[str]:
        """Extract domain name from file path."""
        # Look for common domain directory patterns
        path_parts = list(file_path.parts)

        # Skip common prefixes
        skip_dirs = {
            "app", "src", "backend", "frontend", "api", "services",
            "routers", "models", "schemas", "core", "common", "utils",
        }

        for i, part in enumerate(path_parts):
            part_lower = part.lower()
            if part_lower in skip_dirs:
                continue
            # Check if this looks like a domain directory
            if (
                i > 0
                and part_lower not in skip_dirs
                and not part.startswith("_")
                and not part.startswith(".")
                and part != file_path.name
            ):
                # Validate it looks like a domain name
                if re.match(r"^[a-z][a-z0-9_]*$", part_lower):
                    return part_lower

        return None

    def is_write_service_file(self, file_path: Path) -> bool:
        """Check if a file is a write service file."""
        return self.classify(file_path).role == FileRole.WRITE_SERVICE

    def get_boundary_files(self, files: list[Path]) -> list[Path]:
        """Filter to only boundary files."""
        return [f for f in files if self.classify(f).is_boundary_file]
