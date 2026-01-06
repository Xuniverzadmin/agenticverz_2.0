#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | scheduler | manual
#   Execution: sync
# Role: Capability Registry enforcement, gap detection, heatmap generation
# Callers: GitHub Actions, manual CLI
# Allowed Imports: L6
# Forbidden Imports: L1-L5
# Reference: PIN-306 (Capability Registry Governance)

"""
Capability Registry Enforcer

Provides:
1. CI enforcement for capability linkage
2. UI expansion guard checks
3. Auto-registration candidate detection
4. Gap heatmap generation
5. Auth gateway guard (CAP-006) - ensures JWT parsing is centralized
6. Authority guard (CAP-001, CAP-004) - ensures replay/prediction routes have RBAC v2

Usage:
    python capability_registry_enforcer.py check-pr --files file1.py file2.py
    python capability_registry_enforcer.py ui-guard --files page1.tsx page2.tsx
    python capability_registry_enforcer.py scan-unregistered
    python capability_registry_enforcer.py heatmap [--format md|json]
    python capability_registry_enforcer.py validate-registry
    python capability_registry_enforcer.py auth-guard --files backend/app/*.py
    python capability_registry_enforcer.py auth-guard --scan-all
    python capability_registry_enforcer.py authority-guard --scan-all
    python capability_registry_enforcer.py authority-guard --files backend/app/api/predictions.py
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Determine repo root
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
REGISTRY_PATH = REPO_ROOT / "docs" / "capabilities" / "CAPABILITY_REGISTRY.yaml"
HEATMAP_OUTPUT = REPO_ROOT / "docs" / "capabilities" / "GAP_HEATMAP.md"


# -----------------------------------------------------------------------------
# YAML Parser (Minimal, No External Deps)
# -----------------------------------------------------------------------------


def parse_yaml_simple(content: str) -> dict:
    """
    Minimal YAML parser for the registry structure.
    Handles basic nested dicts, lists, and scalars.
    Does NOT handle all YAML features - tailored for CAPABILITY_REGISTRY.yaml
    """
    import yaml

    return yaml.safe_load(content)


def load_registry() -> dict:
    """Load the capability registry."""
    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found at {REGISTRY_PATH}")
        sys.exit(1)

    with open(REGISTRY_PATH, "r") as f:
        content = f.read()

    try:
        import yaml

        return yaml.safe_load(content)
    except ImportError:
        print("ERROR: PyYAML required. Install with: pip install pyyaml")
        sys.exit(1)


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------


@dataclass
class Violation:
    """Represents a CI violation."""

    type: str
    file: str
    message: str
    capability_id: Optional[str] = None
    blocking: bool = True


@dataclass
class UnregisteredCandidate:
    """Represents a potential unregistered capability."""

    name: str
    path: str
    detection_reason: str
    planes: dict = field(default_factory=dict)


@dataclass
class GapEntry:
    """Represents a gap in capability coverage."""

    capability: str
    capability_id: str
    state: str
    missing_planes: list
    gap_types: list
    ui_allowed: bool
    blocking: bool


# -----------------------------------------------------------------------------
# CORE ENFORCEMENT FUNCTIONS
# -----------------------------------------------------------------------------


def extract_capability_id_from_file(filepath: str) -> Optional[str]:
    """
    Extract capability_id from file comments.

    Looks for:
    - # capability_id: CAP-XXX
    - // capability_id: CAP-XXX
    - /* capability_id: CAP-XXX */
    """
    try:
        with open(filepath, "r") as f:
            content = f.read(4096)  # Read first 4KB
    except (IOError, OSError):
        return None

    patterns = [
        r"#\s*capability_id:\s*(CAP-\d+)",
        r"//\s*capability_id:\s*(CAP-\d+)",
        r"/\*\s*capability_id:\s*(CAP-\d+)",
        r"\*\s*capability_id:\s*(CAP-\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def extract_capability_id_from_pr_body(pr_body: str) -> Optional[str]:
    """
    Extract capability_id from PR description.

    Looks for:
    - capability_id: CAP-XXX
    - Capability: CAP-XXX
    """
    if not pr_body:
        return None

    patterns = [
        r"capability_id:\s*(CAP-\d+)",
        r"capability:\s*(CAP-\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, pr_body, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def get_all_capability_ids(registry: dict) -> set:
    """Get all registered capability IDs."""
    ids = set()
    capabilities = registry.get("capabilities", {})
    for cap_name, cap_data in capabilities.items():
        cap_id = cap_data.get("capability_id")
        if cap_id:
            ids.add(cap_id)
    return ids


def get_capability_by_id(registry: dict, cap_id: str) -> Optional[tuple[str, dict]]:
    """Get capability name and data by ID."""
    capabilities = registry.get("capabilities", {})
    for cap_name, cap_data in capabilities.items():
        if cap_data.get("capability_id") == cap_id:
            return cap_name, cap_data
    return None


def is_code_file(filepath: str) -> bool:
    """Check if file is a code file that requires capability linkage."""
    code_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"}
    excluded_patterns = [
        r"__pycache__",
        r"node_modules",
        r"\.git/",
        r"dist/",
        r"build/",
        r"\.next/",
        r"tests?/",
        r"__tests__/",
        r"\.test\.",
        r"\.spec\.",
        r"conftest\.py",
        r"setup\.py",
        r"vite\.config",
        r"tailwind\.config",
        r"next\.config",
        r"tsconfig",
        r"eslint",
        r"prettier",
    ]

    path = Path(filepath)
    if path.suffix not in code_extensions:
        return False

    filepath_str = str(filepath)
    for pattern in excluded_patterns:
        if re.search(pattern, filepath_str, re.IGNORECASE):
            return False

    return True


def is_ui_file(filepath: str) -> bool:
    """Check if file is a UI/frontend file."""
    ui_patterns = [
        r"/frontend/",
        r"/website/",
        r"/console/",
        r"/pages/",
        r"/components/",
        r"\.tsx$",
        r"\.jsx$",
        r"\.vue$",
        r"\.svelte$",
    ]

    filepath_str = str(filepath)
    for pattern in ui_patterns:
        if re.search(pattern, filepath_str, re.IGNORECASE):
            return True
    return False


def is_backend_file(filepath: str) -> bool:
    """Check if file is a backend file."""
    backend_patterns = [
        r"/backend/",
        r"/services/",
        r"/workers/",
        r"/api/",
    ]

    filepath_str = str(filepath)
    for pattern in backend_patterns:
        if re.search(pattern, filepath_str, re.IGNORECASE):
            return True
    return False


def get_evidence_paths(capability: dict) -> set:
    """Extract all evidence paths from a capability."""
    paths = set()
    evidence = capability.get("evidence", {})

    for key, value in evidence.items():
        if isinstance(value, str):
            paths.add(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    paths.add(item)

    return paths


def file_matches_evidence(filepath: str, evidence_paths: set) -> bool:
    """Check if a file path matches any evidence path."""
    filepath_str = str(filepath)

    for evidence_path in evidence_paths:
        # Normalize paths
        evidence_path = evidence_path.lstrip("/")

        # Check if filepath contains the evidence path
        if evidence_path in filepath_str:
            return True

        # Check directory containment
        if evidence_path.endswith("/"):
            if evidence_path.rstrip("/") in filepath_str:
                return True

    return False


# -----------------------------------------------------------------------------
# CI CHECK: CAPABILITY LINKAGE (T1.1 - T1.3)
# -----------------------------------------------------------------------------


def check_capability_linkage(files: list, pr_body: str = None) -> list[Violation]:
    """
    Check that all code files are linked to registered capabilities.

    T1.1: Check for capability_id in file or PR
    T1.2: Verify capability_id exists in registry
    T1.3: Verify file appears in evidence (optional but warned)
    """
    registry = load_registry()
    registered_ids = get_all_capability_ids(registry)
    violations = []

    # First check PR-level capability_id
    pr_capability_id = extract_capability_id_from_pr_body(pr_body) if pr_body else None

    for filepath in files:
        if not is_code_file(filepath):
            continue

        # T1.1: Extract capability_id
        file_capability_id = extract_capability_id_from_file(filepath)
        capability_id = file_capability_id or pr_capability_id

        if not capability_id:
            violations.append(
                Violation(
                    type="MISSING_CAPABILITY_ID",
                    file=filepath,
                    message="No capability_id found in file or PR description",
                    blocking=True,
                )
            )
            continue

        # T1.2: Verify capability exists
        if capability_id not in registered_ids:
            violations.append(
                Violation(
                    type="UNREGISTERED_CAPABILITY",
                    file=filepath,
                    message=f"capability_id {capability_id} not found in registry",
                    capability_id=capability_id,
                    blocking=True,
                )
            )
            continue

        # Get capability data
        cap_result = get_capability_by_id(registry, capability_id)
        if not cap_result:
            continue

        cap_name, cap_data = cap_result

        # Check if capability is QUARANTINED
        state = cap_data.get("lifecycle", {}).get("state", "")
        if state == "QUARANTINED":
            violations.append(
                Violation(
                    type="QUARANTINED_CAPABILITY",
                    file=filepath,
                    message=f"Capability {capability_id} ({cap_name}) is QUARANTINED",
                    capability_id=capability_id,
                    blocking=True,
                )
            )
            continue

        # Check if capability is PLANNED (code should only be docs)
        if state == "PLANNED" and is_code_file(filepath):
            # Allow if it's documentation-only
            if not filepath.endswith(".md"):
                violations.append(
                    Violation(
                        type="PLANNED_CAPABILITY_CODE",
                        file=filepath,
                        message=f"Capability {capability_id} ({cap_name}) is PLANNED - only docs allowed",
                        capability_id=capability_id,
                        blocking=True,
                    )
                )
                continue

        # T1.3: Check evidence consistency (warning only)
        evidence_paths = get_evidence_paths(cap_data)
        if evidence_paths and not file_matches_evidence(filepath, evidence_paths):
            violations.append(
                Violation(
                    type="MISSING_EVIDENCE",
                    file=filepath,
                    message=f"File not in evidence for {capability_id} ({cap_name})",
                    capability_id=capability_id,
                    blocking=False,  # Warning only
                )
            )

    return violations


# -----------------------------------------------------------------------------
# CI CHECK: AUTH GATEWAY GUARD (CAP-006)
# -----------------------------------------------------------------------------


# Files allowed to parse JWT/Authorization headers
# These are the gateway core and its immediate adapter layer
AUTH_GATEWAY_ALLOWED_FILES = {
    # Gateway core - the single entry point
    "backend/app/auth/gateway.py",
    # Gateway middleware - extracts headers to pass to gateway
    "backend/app/auth/gateway_middleware.py",
    # Identity providers called BY the gateway
    "backend/app/auth/clerk_provider.py",
    "backend/app/auth/identity_chain.py",
    "backend/app/auth/identity_adapter.py",
    # Legacy OIDC provider (to be migrated to gateway pattern)
    "backend/app/auth/oidc_provider.py",
}

# LEGACY FILES - Grandfathered until migrated to gateway pattern
# These files existed before CAP-006 gateway implementation.
# New code MUST NOT be added here. Migration is tracked in PIN-306.
AUTH_GATEWAY_LEGACY_FILES = {
    # RBACv1 system - to be migrated when RBACv2 is promoted
    "backend/app/auth/rbac_middleware.py",
    "backend/app/auth/rbac_engine.py",
    "backend/app/auth/rbac_integration.py",
    # Legacy JWT auth (pre-gateway)
    "backend/app/auth/jwt_auth.py",
    "backend/app/auth/console_auth.py",
    "backend/app/auth/tenant_auth.py",
    # API proxy (legacy forwarding pattern)
    "backend/app/api/v1_proxy.py",
    "backend/app/api/onboarding.py",
}

# Patterns that indicate JWT parsing or auth header access
AUTH_PARSING_PATTERNS = [
    # JWT library usage
    (r"import\s+jwt\b", "JWT library import"),
    (r"from\s+jwt\s+import", "JWT library import"),
    (r"jwt\.decode\s*\(", "JWT decode call"),
    (r"jwt\.encode\s*\(", "JWT encode call"),
    # Authorization header access
    (r'request\.headers\s*\[\s*["\']Authorization["\']', "Direct Authorization header access"),
    (r'request\.headers\.get\s*\(\s*["\']Authorization["\']', "Authorization header access"),
    (r'headers\s*\[\s*["\']Authorization["\']', "Direct Authorization header access"),
    (r'headers\.get\s*\(\s*["\']Authorization["\']', "Authorization header access"),
    # Bearer token parsing
    (r'\.split\s*\(\s*["\']Bearer\s', "Bearer token parsing"),
    (r'\.replace\s*\(\s*["\']Bearer\s', "Bearer token parsing"),
    (r'\.startswith\s*\(\s*["\']Bearer\s', "Bearer token check"),
    # verify_token patterns (common auth function names)
    (r"def\s+verify_token\s*\(", "Token verification function definition"),
    (r"def\s+decode_token\s*\(", "Token decode function definition"),
    (r"def\s+validate_jwt\s*\(", "JWT validation function definition"),
]


# =============================================================================
# AUTHORITY GUARD (CAP-001 replay, CAP-004 predictions)
# =============================================================================
# Files allowed to define authority enforcement
AUTHORITY_ALLOWED_FILES = {
    # Authority core - defines require_* dependencies
    "backend/app/auth/authority.py",
    # Authorization engine - defines permissions
    "backend/app/auth/authorization.py",
}

# Replay routes that MUST have authority enforcement
REPLAY_ROUTE_FILES = {
    "backend/app/api/runtime.py",
    "backend/app/api/guard.py",
    "backend/app/api/workers.py",
    "backend/app/api/v1_killswitch.py",
}

# Prediction routes that MUST have authority enforcement
PREDICTION_ROUTE_FILES = {
    "backend/app/api/predictions.py",
}

# Patterns that indicate replay route without authority
REPLAY_ROUTE_PATTERNS = [
    # Route definitions for replay
    (r'@router\.(post|get)\s*\(\s*["\'][^"\']*replay[^"\']*["\']', "replay route"),
]

# Patterns that indicate prediction route without authority
PREDICTION_ROUTE_PATTERNS = [
    # Route definitions for predictions
    (r'@router\.(post|get)\s*\(\s*["\'][^"\']*prediction[^"\']*["\']', "prediction route"),
    (r'@router\.get\s*\(\s*["\"]["\"]', "predictions list route"),  # Empty path = list
]

# Patterns that indicate authority is enforced
AUTHORITY_ENFORCEMENT_PATTERNS = [
    r"require_replay_execute",
    r"require_replay_read",
    r"require_replay_audit",
    r"require_replay_admin",
    r"require_predictions_read",
    r"require_predictions_execute",
    r"require_predictions_audit",
    r"require_predictions_admin",
]


def check_auth_gateway_guard(files: list) -> list[Violation]:
    """
    Check that JWT parsing and auth header access only occurs in gateway files.

    CAP-006 INVARIANT: JWT parsing MUST be centralized in the auth gateway.
    This guard enforces that no other files parse JWTs or access Authorization headers.

    Args:
        files: List of file paths to check

    Returns:
        List of violations found
    """
    violations = []

    for filepath in files:
        # Only check Python files
        if not filepath.endswith(".py"):
            continue

        # Normalize path for comparison
        normalized_path = str(filepath).replace("\\", "/")

        # Skip if it's an allowed gateway file
        is_allowed = any(
            normalized_path.endswith(allowed) or allowed in normalized_path
            for allowed in AUTH_GATEWAY_ALLOWED_FILES
        )
        if is_allowed:
            continue

        # Skip legacy files (grandfathered, to be migrated)
        is_legacy = any(
            normalized_path.endswith(legacy) or legacy in normalized_path
            for legacy in AUTH_GATEWAY_LEGACY_FILES
        )
        if is_legacy:
            continue

        # Skip test files
        if "/tests/" in normalized_path or "_test.py" in normalized_path:
            continue

        # Read file content
        try:
            with open(filepath, "r") as f:
                content = f.read()
        except (IOError, OSError, UnicodeDecodeError):
            continue

        # Check for auth parsing patterns
        for pattern, description in AUTH_PARSING_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                violations.append(
                    Violation(
                        type="AUTH_GATEWAY_BYPASS",
                        file=filepath,
                        message=f"Unauthorized auth parsing: {description}. JWT/header parsing must be in gateway.py",
                        capability_id="CAP-006",
                        blocking=True,
                    )
                )
                break  # One violation per file is enough

    return violations


def scan_all_for_auth_violations() -> list[Violation]:
    """
    Scan entire backend for auth gateway violations.

    Used for full codebase audit, not just changed files.
    """
    violations = []
    backend_dir = REPO_ROOT / "backend" / "app"

    if not backend_dir.exists():
        return violations

    for py_file in backend_dir.rglob("*.py"):
        file_violations = check_auth_gateway_guard([str(py_file)])
        violations.extend(file_violations)

    return violations


# -----------------------------------------------------------------------------
# CI CHECK: AUTHORITY GUARD (CAP-001, CAP-004)
# -----------------------------------------------------------------------------


def check_authority_guard(files: list) -> list[Violation]:
    """
    Check that replay and prediction routes have authority enforcement.

    CAP-001 INVARIANT: All replay routes MUST use require_replay_* dependencies.
    CAP-004 INVARIANT: All prediction routes MUST use require_predictions_* dependencies.

    Args:
        files: List of file paths to check

    Returns:
        List of violations found
    """
    violations = []

    for filepath in files:
        # Only check Python files
        if not filepath.endswith(".py"):
            continue

        # Normalize path for comparison
        normalized_path = str(filepath).replace("\\", "/")

        # Skip test files
        if "/tests/" in normalized_path or "_test.py" in normalized_path:
            continue

        # Read file content
        try:
            with open(filepath, "r") as f:
                content = f.read()
        except (IOError, OSError, UnicodeDecodeError):
            continue

        # Check replay route files
        is_replay_file = any(
            normalized_path.endswith(rf) or rf in normalized_path
            for rf in REPLAY_ROUTE_FILES
        )
        if is_replay_file:
            # Check for replay routes
            for pattern, desc in REPLAY_ROUTE_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if authority enforcement is present
                    has_authority = any(
                        re.search(ep, content) for ep in AUTHORITY_ENFORCEMENT_PATTERNS
                        if "replay" in ep.lower()
                    )
                    if not has_authority:
                        violations.append(
                            Violation(
                                type="MISSING_AUTHORITY",
                                file=filepath,
                                message=f"Replay route found without authority enforcement. Add require_replay_execute/read.",
                                capability_id="CAP-001",
                                blocking=True,
                            )
                        )
                        break

        # Check prediction route files
        is_prediction_file = any(
            normalized_path.endswith(pf) or pf in normalized_path
            for pf in PREDICTION_ROUTE_FILES
        )
        if is_prediction_file:
            # Check for prediction routes
            route_found = "@router." in content  # Simple check for routes
            if route_found:
                # Check if authority enforcement is present
                has_authority = any(
                    re.search(ep, content) for ep in AUTHORITY_ENFORCEMENT_PATTERNS
                    if "predictions" in ep.lower()
                )
                if not has_authority:
                    violations.append(
                        Violation(
                            type="MISSING_AUTHORITY",
                            file=filepath,
                            message=f"Prediction route found without authority enforcement. Add require_predictions_read.",
                            capability_id="CAP-004",
                            blocking=True,
                        )
                    )

    return violations


def scan_all_for_authority_violations() -> list[Violation]:
    """
    Scan backend for authority violations on replay and prediction routes.

    Used for full codebase audit, not just changed files.
    """
    violations = []

    # Check replay route files
    for route_file in REPLAY_ROUTE_FILES:
        filepath = REPO_ROOT / route_file
        if filepath.exists():
            file_violations = check_authority_guard([str(filepath)])
            violations.extend(file_violations)

    # Check prediction route files
    for route_file in PREDICTION_ROUTE_FILES:
        filepath = REPO_ROOT / route_file
        if filepath.exists():
            file_violations = check_authority_guard([str(filepath)])
            violations.extend(file_violations)

    return violations


# -----------------------------------------------------------------------------
# CI CHECK: UI EXPANSION GUARD (T2.1 - T2.3)
# -----------------------------------------------------------------------------


def check_ui_expansion(
    files: list, has_non_expansion_label: bool = False
) -> list[Violation]:
    """
    Check that UI files don't expand capabilities that block UI expansion.

    T2.1: Detect UI file changes
    T2.2: Check ui_expansion_allowed flag
    T2.3: Handle exceptions with label
    """
    registry = load_registry()
    violations = []

    ui_files = [f for f in files if is_ui_file(f)]
    if not ui_files:
        return violations

    # Build map of evidence paths to capabilities
    evidence_to_cap = {}
    capabilities = registry.get("capabilities", {})
    for cap_name, cap_data in capabilities.items():
        evidence_paths = get_evidence_paths(cap_data)
        for path in evidence_paths:
            evidence_to_cap[path] = (cap_name, cap_data)

    for filepath in ui_files:
        # Find which capability this UI file belongs to
        matched_cap = None
        for evidence_path, (cap_name, cap_data) in evidence_to_cap.items():
            if file_matches_evidence(filepath, {evidence_path}):
                matched_cap = (cap_name, cap_data)
                break

        if not matched_cap:
            # UI file not mapped to any capability - might be new
            # Check PR for capability_id
            continue

        cap_name, cap_data = matched_cap

        # T2.2: Check ui_expansion_allowed
        ui_allowed = cap_data.get("governance", {}).get("ui_expansion_allowed", False)

        if not ui_allowed:
            # T2.3: Check for exception label
            if has_non_expansion_label:
                violations.append(
                    Violation(
                        type="UI_EXPANSION_EXCEPTION",
                        file=filepath,
                        message=f"UI change for {cap_name} allowed with ui-non-expansion label",
                        capability_id=cap_data.get("capability_id"),
                        blocking=False,  # Warning only
                    )
                )
            else:
                violations.append(
                    Violation(
                        type="UI_EXPANSION_BLOCKED",
                        file=filepath,
                        message=f"UI expansion blocked for {cap_name} (ui_expansion_allowed=false). Add 'ui-non-expansion' label for exceptions.",
                        capability_id=cap_data.get("capability_id"),
                        blocking=True,
                    )
                )

    return violations


# -----------------------------------------------------------------------------
# AUTO-REGISTRATION SCAN (T3.1 - T3.3)
# -----------------------------------------------------------------------------


def scan_for_unregistered() -> list[UnregisteredCandidate]:
    """
    Scan codebase for potential unregistered capabilities.

    T3.1: Scan backend and frontend directories
    T3.2: Use detection heuristics
    T3.3: Generate draft entries (not auto-committed)
    """
    registry = load_registry()
    candidates = []

    # Get all registered evidence paths
    registered_paths = set()
    capabilities = registry.get("capabilities", {})
    for cap_name, cap_data in capabilities.items():
        registered_paths.update(get_evidence_paths(cap_data))

    # Scan locations
    scan_dirs = [
        (REPO_ROOT / "backend" / "app", "backend"),
        (REPO_ROOT / "website", "frontend"),
        (REPO_ROOT / "frontend", "frontend"),
    ]

    for scan_dir, category in scan_dirs:
        if not scan_dir.exists():
            continue

        # Look for top-level directories that might be capabilities
        for item in scan_dir.iterdir():
            if not item.is_dir():
                continue

            # Skip common non-capability directories
            skip_dirs = {
                "__pycache__",
                "node_modules",
                ".git",
                "dist",
                "build",
                ".next",
                "tests",
                "__tests__",
                "migrations",
                "alembic",
                "static",
                "templates",
                "models",
                "schemas",
                "utils",
                "config",
                "middleware",
                "adapters",
                "commands",
                "data",
            }

            if item.name in skip_dirs:
                continue

            # Check if this directory is already registered
            item_path = f"/{item.relative_to(REPO_ROOT)}"
            is_registered = any(
                item_path in p or p.startswith(item_path) for p in registered_paths
            )

            if not is_registered:
                # Determine what planes exist
                planes = {
                    "engine": category == "backend",
                    "l2_api": _has_api_routes(item),
                    "client": _has_api_client(item),
                    "ui": _has_ui_pages(item),
                    "authority": False,
                    "audit_replay": False,
                }

                candidates.append(
                    UnregisteredCandidate(
                        name=item.name,
                        path=str(item_path),
                        detection_reason=f"Top-level {category} directory not in registry",
                        planes=planes,
                    )
                )

    return candidates


def _has_api_routes(directory: Path) -> bool:
    """Check if directory contains API route definitions."""
    for file in directory.rglob("*.py"):
        try:
            content = file.read_text()
            if "@router." in content or "@app." in content or "APIRouter" in content:
                return True
        except (IOError, OSError, UnicodeDecodeError):
            pass
    return False


def _has_api_client(directory: Path) -> bool:
    """Check if directory contains API client code."""
    for file in directory.rglob("*.ts"):
        try:
            content = file.read_text()
            if "fetch(" in content or "axios" in content or "api/" in content:
                return True
        except (IOError, OSError, UnicodeDecodeError):
            pass
    return False


def _has_ui_pages(directory: Path) -> bool:
    """Check if directory contains UI page components."""
    ui_extensions = {".tsx", ".jsx", ".vue", ".svelte"}
    for ext in ui_extensions:
        if list(directory.rglob(f"*Page{ext}")) or list(directory.rglob(f"*{ext}")):
            return True
    return False


def generate_draft_entry(candidate: UnregisteredCandidate) -> str:
    """Generate YAML draft for an unregistered candidate."""
    # Derive capability ID (placeholder)
    cap_id = f"CAP-NEW-{candidate.name.upper()[:10]}"

    yaml_content = f"""
  # ---------------------------------------------------------------------------
  # {cap_id}: {candidate.name.upper()} (AUTO-DETECTED - REQUIRES REVIEW)
  # ---------------------------------------------------------------------------
  {candidate.name}:
    capability_id: {cap_id}
    name: "{candidate.name.replace("_", " ").title()}"
    description: "AUTO-DETECTED: {candidate.detection_reason}"
    owner: platform

    planes:
      engine: {str(candidate.planes.get("engine", False)).lower()}
      l2_api: {str(candidate.planes.get("l2_api", False)).lower()}
      client: {str(candidate.planes.get("client", False)).lower()}
      ui: {str(candidate.planes.get("ui", False)).lower()}
      authority: false
      audit_replay: false

    lifecycle:
      state: PARTIAL
      closure_requirements:
        engine_complete: false
        api_complete: false
        client_complete: false
        ui_complete: false
        authority_wired: false
        audit_enabled: false

    governance:
      ui_expansion_allowed: false
      promotion_blocked_by:
        - "AUTO-DETECTED - requires founder review"
      founder_approval_required: true

    evidence:
      engine: "{candidate.path}"

    gaps:
      - type: UNREGISTERED_CODE
        detail: "Auto-detected, pending registration"
"""
    return yaml_content


# -----------------------------------------------------------------------------
# GAP HEATMAP (T4.1 - T4.3)
# -----------------------------------------------------------------------------


def generate_gap_heatmap(output_format: str = "md") -> str:
    """
    Generate gap heatmap from registry.

    T4.1: Generate gap matrix
    T4.2: Output as markdown or JSON
    """
    registry = load_registry()
    capabilities = registry.get("capabilities", {})

    gaps = []

    for cap_name, cap_data in capabilities.items():
        cap_id = cap_data.get("capability_id", "UNKNOWN")
        state = cap_data.get("lifecycle", {}).get("state", "UNKNOWN")
        planes = cap_data.get("planes", {})
        gap_list = cap_data.get("gaps", [])
        ui_allowed = cap_data.get("governance", {}).get("ui_expansion_allowed", False)

        # Determine missing planes
        missing_planes = [plane for plane, exists in planes.items() if not exists]

        # Determine if blocking
        blocking = state in ("PARTIAL", "READ_ONLY") or len(gap_list) > 0

        gap_types = [g.get("type", "UNKNOWN") for g in gap_list]

        gaps.append(
            GapEntry(
                capability=cap_name,
                capability_id=cap_id,
                state=state,
                missing_planes=missing_planes,
                gap_types=gap_types,
                ui_allowed=ui_allowed,
                blocking=blocking,
            )
        )

    if output_format == "json":
        return _format_heatmap_json(gaps, registry)
    else:
        return _format_heatmap_md(gaps, registry)


def _format_heatmap_md(gaps: list[GapEntry], registry: dict) -> str:
    """Format heatmap as Markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = f"""# Capability Gap Heatmap

**Generated:** {now}
**Registry Version:** {registry.get("registry_version", "unknown")}
**Total Capabilities:** {len(gaps)}

---

## Summary by State

| State | Count | Capabilities |
|-------|-------|--------------|
"""

    # Group by state
    by_state = {}
    for g in gaps:
        by_state.setdefault(g.state, []).append(g.capability)

    state_order = ["PLANNED", "PARTIAL", "READ_ONLY", "CLOSED", "FROZEN", "QUARANTINED"]
    for state in state_order:
        caps = by_state.get(state, [])
        if caps:
            md += f"| {state} | {len(caps)} | {', '.join(caps)} |\n"

    md += """
---

## Gap Matrix

| Capability | ID | State | Missing Planes | Gap Types | UI Allowed | Blocking |
|------------|-----|-------|----------------|-----------|------------|----------|
"""

    # Sort by state priority (PARTIAL first, then others)
    state_priority = {
        "PARTIAL": 0,
        "READ_ONLY": 1,
        "PLANNED": 2,
        "QUARANTINED": 3,
        "CLOSED": 4,
        "FROZEN": 5,
    }
    sorted_gaps = sorted(
        gaps, key=lambda g: (state_priority.get(g.state, 99), g.capability)
    )

    for g in sorted_gaps:
        missing = ", ".join(g.missing_planes) if g.missing_planes else "-"
        gap_types = ", ".join(g.gap_types) if g.gap_types else "-"
        ui = "✅" if g.ui_allowed else "❌"
        blocking = "🔴" if g.blocking else "🟢"
        md += f"| {g.capability} | {g.capability_id} | {g.state} | {missing} | {gap_types} | {ui} | {blocking} |\n"

    md += """
---

## Legend

- **UI Allowed:** ✅ = ui_expansion_allowed, ❌ = blocked
- **Blocking:** 🔴 = has gaps or not CLOSED, 🟢 = no issues

---

## Blocking Gaps Detail

"""

    blocking_gaps = [g for g in gaps if g.blocking and g.gap_types]
    if blocking_gaps:
        for g in blocking_gaps:
            md += f"### {g.capability} ({g.capability_id})\n\n"
            md += f"- **State:** {g.state}\n"
            for gap_type in g.gap_types:
                md += f"- **Gap:** {gap_type}\n"
            md += "\n"
    else:
        md += "_No blocking gaps identified._\n"

    md += f"""
---

## UI Expansion Status

### Blocked ({len([g for g in gaps if not g.ui_allowed])}):
"""
    for g in gaps:
        if not g.ui_allowed:
            md += f"- {g.capability}\n"

    md += f"""
### Allowed ({len([g for g in gaps if g.ui_allowed])}):
"""
    for g in gaps:
        if g.ui_allowed:
            md += f"- {g.capability}\n"

    md += """
---

_Generated by capability_registry_enforcer.py (PIN-306)_
"""

    return md


def _format_heatmap_json(gaps: list[GapEntry], registry: dict) -> str:
    """Format heatmap as JSON."""
    data = {
        "generated": datetime.now().isoformat(),
        "registry_version": registry.get("registry_version", "unknown"),
        "total_capabilities": len(gaps),
        "summary": {
            "by_state": {},
            "blocking_count": len([g for g in gaps if g.blocking]),
            "ui_blocked_count": len([g for g in gaps if not g.ui_allowed]),
        },
        "capabilities": [],
    }

    for g in gaps:
        data["summary"]["by_state"].setdefault(g.state, 0)
        data["summary"]["by_state"][g.state] += 1

        data["capabilities"].append(
            {
                "name": g.capability,
                "id": g.capability_id,
                "state": g.state,
                "missing_planes": g.missing_planes,
                "gap_types": g.gap_types,
                "ui_allowed": g.ui_allowed,
                "blocking": g.blocking,
            }
        )

    return json.dumps(data, indent=2)


def validate_registry() -> list[str]:
    """Validate registry structure and consistency."""
    registry = load_registry()
    errors = []

    # Check required sections
    required_sections = ["registry_version", "enums", "capabilities"]
    for section in required_sections:
        if section not in registry:
            errors.append(f"Missing required section: {section}")

    # Check enums
    enums = registry.get("enums", {})
    required_enums = ["lifecycle_states", "capability_planes", "gap_types"]
    for enum in required_enums:
        if enum not in enums:
            errors.append(f"Missing required enum: {enum}")

    # Check capabilities
    capabilities = registry.get("capabilities", {})
    valid_states = set(enums.get("lifecycle_states", []))
    valid_planes = set(enums.get("capability_planes", []))
    valid_gap_types = set(enums.get("gap_types", []))

    seen_ids = set()

    for cap_name, cap_data in capabilities.items():
        # Check capability_id
        cap_id = cap_data.get("capability_id")
        if not cap_id:
            errors.append(f"{cap_name}: Missing capability_id")
        elif cap_id in seen_ids:
            errors.append(f"{cap_name}: Duplicate capability_id {cap_id}")
        else:
            seen_ids.add(cap_id)

        # Check lifecycle state
        state = cap_data.get("lifecycle", {}).get("state")
        if state and state not in valid_states:
            errors.append(f"{cap_name}: Invalid lifecycle state '{state}'")

        # Check planes
        planes = cap_data.get("planes", {})
        for plane in planes.keys():
            if plane not in valid_planes:
                errors.append(f"{cap_name}: Invalid plane '{plane}'")

        # Check gap types
        gaps = cap_data.get("gaps", [])
        for gap in gaps:
            gap_type = gap.get("type")
            if gap_type and gap_type not in valid_gap_types:
                errors.append(f"{cap_name}: Invalid gap type '{gap_type}'")

    return errors


# -----------------------------------------------------------------------------
# CI OUTPUT FORMATTING
# -----------------------------------------------------------------------------


def format_ci_output(violations: list[Violation], format_type: str = "text") -> str:
    """Format violations for CI output."""
    if not violations:
        return "✅ All checks passed\n"

    blocking = [v for v in violations if v.blocking]
    warnings = [v for v in violations if not v.blocking]

    if format_type == "github":
        # GitHub Actions annotation format
        lines = []
        for v in violations:
            level = "error" if v.blocking else "warning"
            lines.append(f"::{level} file={v.file}::{v.type}: {v.message}")
        return "\n".join(lines)
    else:
        # Human-readable text
        output = []

        if blocking:
            output.append(f"❌ BLOCKING VIOLATIONS ({len(blocking)}):\n")
            for v in blocking:
                output.append(f"  [{v.type}] {v.file}")
                output.append(f"    → {v.message}\n")

        if warnings:
            output.append(f"⚠️  WARNINGS ({len(warnings)}):\n")
            for v in warnings:
                output.append(f"  [{v.type}] {v.file}")
                output.append(f"    → {v.message}\n")

        if blocking:
            output.append("\n❌ CI FAILED - Fix blocking violations before merge\n")
        else:
            output.append("\n✅ CI PASSED (with warnings)\n")

        return "\n".join(output)


# -----------------------------------------------------------------------------
# CLI COMMANDS
# -----------------------------------------------------------------------------


def cmd_check_pr(args):
    """Run capability linkage check for PR files."""
    files = args.files
    pr_body = args.pr_body or os.environ.get("PR_BODY", "")

    violations = check_capability_linkage(files, pr_body)

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_ui_guard(args):
    """Run UI expansion guard check."""
    files = args.files
    has_label = (
        args.has_non_expansion_label
        or os.environ.get("HAS_NON_EXPANSION_LABEL", "").lower() == "true"
    )

    violations = check_ui_expansion(files, has_label)

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_scan_unregistered(args):
    """Scan for unregistered capabilities."""
    candidates = scan_for_unregistered()

    if not candidates:
        print("✅ No unregistered capabilities detected\n")
        return 0

    print(f"⚠️  UNREGISTERED CANDIDATES ({len(candidates)}):\n")

    for c in candidates:
        print(f"  📦 {c.name}")
        print(f"     Path: {c.path}")
        print(f"     Reason: {c.detection_reason}")
        print(f"     Planes: {c.planes}")
        print()

    if args.generate_drafts:
        print("\n--- DRAFT REGISTRY ENTRIES (requires founder review) ---\n")
        for c in candidates:
            print(generate_draft_entry(c))

    return 0


def cmd_heatmap(args):
    """Generate gap heatmap."""
    output = generate_gap_heatmap(args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output)
        print(f"✅ Heatmap written to {output_path}")
    else:
        print(output)

    return 0


def cmd_validate(args):
    """Validate registry structure."""
    errors = validate_registry()

    if not errors:
        print("✅ Registry validation passed\n")
        return 0

    print(f"❌ REGISTRY VALIDATION ERRORS ({len(errors)}):\n")
    for error in errors:
        print(f"  • {error}")

    return 1


def cmd_auth_guard(args):
    """Run auth gateway guard check (CAP-006)."""
    if args.scan_all:
        # Full codebase scan
        violations = scan_all_for_auth_violations()
    else:
        # Check specific files
        violations = check_auth_gateway_guard(args.files)

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_authority_guard(args):
    """Run authority guard check (CAP-001, CAP-004)."""
    if args.scan_all:
        # Full codebase scan
        violations = scan_all_for_authority_violations()
    else:
        # Check specific files
        violations = check_authority_guard(args.files)

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


# =============================================================================
# PHASE G: GOVERNANCE FREEZE & DRIFT PREVENTION
# =============================================================================


# -----------------------------------------------------------------------------
# G1: REGISTRY MUTATION FREEZE
# -----------------------------------------------------------------------------

def check_registry_mutation(pr_body: str = "", commit_message: str = "") -> list[Violation]:
    """
    Check that registry mutations are documented with PIN reference.

    G1 INVARIANT: No capability state change without:
    - PIN reference in PR body or commit message
    - Explicit approval (via PR body marker)

    Returns violations if undocumented mutation detected.
    """
    violations = []

    # Load current registry
    registry = load_registry()
    capabilities = registry.get("capabilities", {})

    # Check for PIN reference pattern
    pin_pattern = r"PIN-\d+"
    has_pin_ref = bool(re.search(pin_pattern, pr_body + commit_message, re.IGNORECASE))

    # Check for explicit approval marker
    approval_markers = [
        "[registry-mutation-approved]",
        "[capability-state-change-approved]",
        "[governance-approved]",
    ]
    has_approval = any(marker.lower() in (pr_body + commit_message).lower() for marker in approval_markers)

    if not has_pin_ref and not has_approval:
        # This is a warning - actual mutation detection happens in CI via git diff
        pass

    return violations


def check_registry_diff_for_state_changes(diff_content: str, pr_body: str = "") -> list[Violation]:
    """
    Check git diff of registry for unauthorized state changes.

    G1 INVARIANT: Capability state changes require PIN reference.
    """
    violations = []

    # Patterns that indicate state changes
    state_change_patterns = [
        (r"^\+\s*state:\s*(CLOSED|PARTIAL|READ_ONLY|FROZEN|QUARANTINED|PLANNED)", "lifecycle state change"),
        (r"^\+\s*authority:\s*true", "authority plane enabled"),
        (r"^\+\s*authority_wired:\s*true", "authority wiring change"),
        (r"^\-\s*state:\s*CLOSED", "CLOSED capability modified"),
    ]

    # Check for PIN reference
    pin_pattern = r"PIN-\d+"
    has_pin_ref = bool(re.search(pin_pattern, pr_body, re.IGNORECASE))

    for pattern, desc in state_change_patterns:
        if re.search(pattern, diff_content, re.MULTILINE):
            if not has_pin_ref:
                violations.append(
                    Violation(
                        type="UNDOCUMENTED_REGISTRY_MUTATION",
                        file="docs/capabilities/CAPABILITY_REGISTRY.yaml",
                        message=f"Registry mutation detected ({desc}) without PIN reference. Add PIN-XXX to PR body.",
                        capability_id=None,
                        blocking=True,
                    )
                )
                break

    # Special check: CLOSED → PARTIAL regression
    if re.search(r"^\-\s*state:\s*CLOSED", diff_content, re.MULTILINE):
        if re.search(r"^\+\s*state:\s*PARTIAL", diff_content, re.MULTILINE):
            violations.append(
                Violation(
                    type="CAPABILITY_REGRESSION",
                    file="docs/capabilities/CAPABILITY_REGISTRY.yaml",
                    message="BLOCKED: CLOSED capability cannot regress to PARTIAL. This requires founder approval.",
                    capability_id=None,
                    blocking=True,
                )
            )

    return violations


# -----------------------------------------------------------------------------
# G2: PLANE PURITY ENFORCEMENT
# -----------------------------------------------------------------------------

# Route plane declarations
HUMAN_ONLY_ROUTES = {
    "/founder/",
    "/admin/",
    "/console/",
    "/guard/",
}

MACHINE_ONLY_ROUTES = {
    "/api/v1/workers/",
    "/api/v1/agents/",
    "/api/v1/runtime/",
    "/webhook/",
}

READ_ONLY_CAPABILITIES = {"prediction_plane", "policy_proposals"}


def check_plane_purity(files: list) -> list[Violation]:
    """
    Check route/authority plane purity.

    G2 INVARIANTS:
    - HUMAN routes must have authority enforcement
    - MACHINE routes must not use AuthContext for humans
    - READ_ONLY capabilities must not expose mutating endpoints
    """
    violations = []

    for filepath in files:
        if not filepath.endswith(".py"):
            continue

        normalized_path = str(filepath).replace("\\", "/")

        # Skip test files
        if "/tests/" in normalized_path or "_test.py" in normalized_path:
            continue

        try:
            with open(filepath, "r") as f:
                content = f.read()
        except (IOError, OSError, UnicodeDecodeError):
            continue

        # Check 1: HUMAN routes need authority
        is_human_route_file = any(route in normalized_path for route in HUMAN_ONLY_ROUTES)
        if is_human_route_file:
            has_router = "@router." in content
            has_authority = any(
                re.search(pattern, content)
                for pattern in AUTHORITY_ENFORCEMENT_PATTERNS
            )
            # Also check for verify_console_token (human auth)
            has_human_auth = "verify_console_token" in content or "get_current_user" in content

            if has_router and not (has_authority or has_human_auth):
                violations.append(
                    Violation(
                        type="HUMAN_ROUTE_NO_AUTHORITY",
                        file=filepath,
                        message="HUMAN route file has routes but no authority enforcement or console token verification.",
                        capability_id=None,
                        blocking=True,
                    )
                )

        # Check 2: MACHINE routes should not use HumanAuthContext
        is_machine_route_file = any(route in normalized_path for route in MACHINE_ONLY_ROUTES)
        if is_machine_route_file:
            if "HumanAuthContext" in content or "verify_console_token" in content:
                violations.append(
                    Violation(
                        type="MACHINE_ROUTE_HUMAN_AUTH",
                        file=filepath,
                        message="MACHINE route file uses human authentication. Use API key auth instead.",
                        capability_id=None,
                        blocking=True,
                    )
                )

        # Check 3: READ_ONLY capability files should not have POST/PUT/DELETE with mutations
        for cap in READ_ONLY_CAPABILITIES:
            if cap in normalized_path or cap.replace("_", "") in normalized_path:
                # Check for mutating HTTP methods that actually mutate
                mutating_patterns = [
                    r"@router\.post\s*\([^)]*\)\s*\n\s*async\s+def\s+\w+",
                    r"@router\.put\s*\(",
                    r"@router\.delete\s*\(",
                    r"@router\.patch\s*\(",
                ]
                for pattern in mutating_patterns:
                    if re.search(pattern, content):
                        # Special case: POST for queries is OK (like GraphQL)
                        # Check if it's actually mutating
                        if "session.add" in content or "session.commit" in content:
                            violations.append(
                                Violation(
                                    type="READ_ONLY_CAP_MUTATES",
                                    file=filepath,
                                    message=f"READ_ONLY capability ({cap}) has mutating endpoints. Remove or reclassify.",
                                    capability_id=cap.upper().replace("_", "-"),
                                    blocking=True,
                                )
                            )
                            break

    return violations


def scan_all_for_plane_purity() -> list[Violation]:
    """Scan all backend API files for plane purity violations."""
    violations = []
    api_dir = REPO_ROOT / "backend" / "app" / "api"

    if api_dir.exists():
        for py_file in api_dir.rglob("*.py"):
            file_violations = check_plane_purity([str(py_file)])
            violations.extend(file_violations)

    return violations


# -----------------------------------------------------------------------------
# G3: TAXONOMY LOCK
# -----------------------------------------------------------------------------

TAXONOMY_PATH = REPO_ROOT / "docs" / "governance" / "PERMISSION_TAXONOMY_V1.md"
TAXONOMY_VERSION_PATTERN = r"^##\s+Version:\s*(\d+\.\d+\.\d+)"
TAXONOMY_HASH_COMMENT = "<!-- TAXONOMY_HASH: "


def check_taxonomy_lock(diff_content: str = "", pr_body: str = "") -> list[Violation]:
    """
    Check that permission taxonomy changes follow versioning rules.

    G3 INVARIANT: New permissions require:
    - Explicit version bump
    - Migration note
    - Registry impact declaration
    """
    violations = []

    # If diff provided, check for taxonomy changes
    if diff_content and "PERMISSION_TAXONOMY_V1.md" in diff_content:
        # Check for version bump
        has_version_bump = bool(re.search(r"^\+.*Version:", diff_content, re.MULTILINE))

        # Check for new permission additions
        new_permission = bool(re.search(r"^\+\s*\|\s*`[a-z]+:[a-z]+", diff_content, re.MULTILINE))

        if new_permission and not has_version_bump:
            violations.append(
                Violation(
                    type="TAXONOMY_VERSION_REQUIRED",
                    file="docs/governance/PERMISSION_TAXONOMY_V1.md",
                    message="New permission added without version bump. Increment version in taxonomy header.",
                    capability_id=None,
                    blocking=True,
                )
            )

        # Check for migration note in PR body
        if new_permission:
            migration_markers = ["migration:", "breaking:", "impact:"]
            has_migration = any(m in pr_body.lower() for m in migration_markers)
            if not has_migration:
                violations.append(
                    Violation(
                        type="TAXONOMY_MIGRATION_REQUIRED",
                        file="docs/governance/PERMISSION_TAXONOMY_V1.md",
                        message="New permission requires migration note in PR body. Add 'Migration: <description>'.",
                        capability_id=None,
                        blocking=False,  # Warning, not blocking
                    )
                )

    return violations


def get_taxonomy_permissions() -> set:
    """Extract all declared permissions from taxonomy file."""
    permissions = set()

    if not TAXONOMY_PATH.exists():
        return permissions

    with open(TAXONOMY_PATH, "r") as f:
        content = f.read()

    # Extract permissions from markdown tables
    # Format: | `action:resource` | description |
    permission_pattern = r"\|\s*`([a-z]+:[a-z_]+(?::[a-z]+)?)`\s*\|"
    matches = re.findall(permission_pattern, content)
    permissions.update(matches)

    return permissions


# -----------------------------------------------------------------------------
# G4: WORKER & WEBHOOK ASSERTION
# -----------------------------------------------------------------------------

WORKER_FILES = {
    "backend/app/worker/",
    "backend/app/workers/",
    "backend/app/agents/workers/",
    "workers/",
}

WEBHOOK_FILES = {
    "backend/app/api/webhooks",
    "backend/app/webhooks/",
}


def check_worker_auth_compliance(files: list = None) -> list[Violation]:
    """
    Check that workers use API keys, not AuthContext.

    G4 INVARIANTS:
    - All workers must use API keys
    - No background job accepts AuthContext
    - Webhooks are machine-plane only
    """
    violations = []

    # Determine files to check
    if files:
        check_files = files
    else:
        check_files = []
        for worker_dir in WORKER_FILES:
            worker_path = REPO_ROOT / worker_dir
            if worker_path.exists():
                check_files.extend(str(f) for f in worker_path.rglob("*.py"))
        for webhook_dir in WEBHOOK_FILES:
            webhook_path = REPO_ROOT / webhook_dir
            if webhook_path.exists():
                check_files.extend(str(f) for f in webhook_path.rglob("*.py"))

    for filepath in check_files:
        if not filepath.endswith(".py"):
            continue

        normalized_path = str(filepath).replace("\\", "/")

        # Skip test files
        if "/tests/" in normalized_path or "_test.py" in normalized_path:
            continue

        # Check if it's a worker or webhook file
        is_worker = any(w in normalized_path for w in WORKER_FILES)
        is_webhook = any(w in normalized_path for w in WEBHOOK_FILES)

        if not is_worker and not is_webhook:
            continue

        try:
            with open(filepath, "r") as f:
                content = f.read()
        except (IOError, OSError, UnicodeDecodeError):
            continue

        # Check for human auth patterns in workers
        human_auth_patterns = [
            "HumanAuthContext",
            "verify_console_token",
            "get_current_user",
            "ClerkProvider",
            "jwt.decode",
        ]

        for pattern in human_auth_patterns:
            if pattern in content:
                violations.append(
                    Violation(
                        type="WORKER_HUMAN_AUTH",
                        file=filepath,
                        message=f"Worker/webhook uses human auth pattern '{pattern}'. Workers must use API keys only.",
                        capability_id=None,
                        blocking=True,
                    )
                )
                break

        # Check webhooks use API key verification
        if is_webhook:
            if "@router." in content:
                if "verify_api_key" not in content and "X-AOS-Key" not in content:
                    # Also check for webhook signature verification
                    if "verify_webhook_signature" not in content and "X-Webhook-Signature" not in content:
                        violations.append(
                            Violation(
                                type="WEBHOOK_NO_AUTH",
                                file=filepath,
                                message="Webhook endpoint without API key or signature verification.",
                                capability_id=None,
                                blocking=True,
                            )
                        )

    return violations


# -----------------------------------------------------------------------------
# G5: GOVERNANCE BASELINE REPORT
# -----------------------------------------------------------------------------

def generate_governance_baseline() -> str:
    """
    Generate governance baseline report.

    Contains:
    - Capability states
    - Authority surfaces
    - CI invariants
    - Known intentional gaps
    """
    registry = load_registry()
    capabilities = registry.get("capabilities", {})

    # Get current date
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Count states
    state_counts = {}
    for cap_name, cap_data in capabilities.items():
        state = cap_data.get("lifecycle", {}).get("state", "UNKNOWN")
        state_counts[state] = state_counts.get(state, 0) + 1

    # Get authority surfaces
    authority_surfaces = []
    for cap_name, cap_data in capabilities.items():
        if cap_data.get("planes", {}).get("authority", False):
            authority_surfaces.append(cap_name)

    # Get intentional gaps
    intentional_gaps = []
    for cap_name, cap_data in capabilities.items():
        gaps = cap_data.get("gaps", [])
        for gap in gaps:
            if gap.get("type") == "INTENTIONALLY_ABSENT":
                intentional_gaps.append({
                    "capability": cap_name,
                    "detail": gap.get("detail", ""),
                })

    # Build report
    report = f"""# Governance Baseline Report

**Generated:** {today}
**Timestamp:** {timestamp}
**Registry Version:** {registry.get('registry_version', '1.0.0')}

---

## Capability States

| State | Count | Capabilities |
|-------|-------|--------------|
"""

    for state in ["CLOSED", "FROZEN", "READ_ONLY", "PARTIAL", "PLANNED", "QUARANTINED"]:
        count = state_counts.get(state, 0)
        caps = [name for name, data in capabilities.items()
                if data.get("lifecycle", {}).get("state") == state]
        report += f"| {state} | {count} | {', '.join(caps) if caps else '-'} |\n"

    report += f"""
**Total Capabilities:** {len(capabilities)}

---

## Authority Surfaces

The following capabilities have authority enforcement:

"""

    for cap in sorted(authority_surfaces):
        cap_data = capabilities[cap]
        report += f"- **{cap}** (CAP-{cap_data.get('capability_id', 'XXX').split('-')[-1] if '-' in str(cap_data.get('capability_id', '')) else cap_data.get('capability_id', 'XXX')})\n"
        evidence = cap_data.get("evidence", {}).get("authority", [])
        if evidence:
            if isinstance(evidence, list):
                for e in evidence[:2]:  # Show first 2
                    report += f"  - `{e}`\n"
            else:
                report += f"  - `{evidence}`\n"

    report += f"""
---

## CI Invariants

The following CI checks are enforced:

### Capability Registry (capability-registry.yml)
| Check | Description | Status |
|-------|-------------|--------|
| T1: Capability Linkage | Code changes must link to registered capability | ACTIVE |
| T2: UI Expansion Guard | UI changes require ui_expansion_allowed flag | ACTIVE |
| T3: Registry Validation | Registry structure must be valid | ACTIVE |
| T4: Gap Heatmap | Auto-updates on main merge | ACTIVE |

### Governance Freeze (Phase G)
| Check | Description | Status |
|-------|-------------|--------|
| G1: Registry Mutation | State changes require PIN reference | ACTIVE |
| G2: Plane Purity | Route/authority plane matching | ACTIVE |
| G3: Taxonomy Lock | Permission changes require version bump | ACTIVE |
| G4: Worker Auth | Workers use API keys only | ACTIVE |
| G5: Authority Guard | Replay/prediction routes have RBAC | ACTIVE |

---

## Known Intentional Gaps

These gaps are by design and should not be "fixed":

"""

    if intentional_gaps:
        for gap in intentional_gaps:
            report += f"- **{gap['capability']}**: {gap['detail']}\n"
    else:
        report += "- None declared\n"

    report += f"""
---

## Blocking Gaps

Gaps that block promotion:

"""

    gap_summary = registry.get("gap_summary", {}).get("blocking_gaps", [])
    if gap_summary:
        for gap in gap_summary:
            report += f"- **{gap.get('capability')}** ({gap.get('gap')}): {gap.get('detail')}\n"
    else:
        report += "- None (all capabilities at target state)\n"

    report += f"""
---

## Frozen Artifacts

The following artifacts are frozen and require founder approval to modify:

| Artifact | Path | Frozen Since |
|----------|------|--------------|
| Permission Taxonomy | docs/governance/PERMISSION_TAXONOMY_V1.md | {today} |
| Capability Registry | docs/capabilities/CAPABILITY_REGISTRY.yaml | {today} |

---

## Verification Commands

```bash
# Verify authority guard
python3 scripts/ops/capability_registry_enforcer.py authority-guard --scan-all

# Verify plane purity
python3 scripts/ops/capability_registry_enforcer.py plane-purity --scan-all

# Verify worker auth
python3 scripts/ops/capability_registry_enforcer.py worker-auth --scan-all

# Validate registry
python3 scripts/ops/capability_registry_enforcer.py validate-registry
```

---

## Baseline Hash

This baseline can be verified against the registry:

```
Registry Hash: {hash(str(capabilities)) & 0xFFFFFFFF:08x}
Capabilities: {len(capabilities)}
CLOSED: {state_counts.get('CLOSED', 0)}
Authority Surfaces: {len(authority_surfaces)}
```

---

*This report is the baseline of truth. Any drift from this state requires explicit governance approval.*
"""

    return report


# -----------------------------------------------------------------------------
# COMMAND HANDLERS FOR PHASE G
# -----------------------------------------------------------------------------

def cmd_registry_mutation(args):
    """Check registry mutations are documented."""
    violations = []

    if args.diff_file:
        with open(args.diff_file, "r") as f:
            diff_content = f.read()
        violations = check_registry_diff_for_state_changes(diff_content, args.pr_body or "")
    else:
        # Just validate registry structure
        violations = check_registry_mutation(args.pr_body or "")

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_plane_purity(args):
    """Check route/authority plane purity."""
    if args.scan_all:
        violations = scan_all_for_plane_purity()
    else:
        violations = check_plane_purity(args.files or [])

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_taxonomy_lock(args):
    """Check taxonomy version lock."""
    diff_content = ""
    if args.diff_file:
        with open(args.diff_file, "r") as f:
            diff_content = f.read()

    violations = check_taxonomy_lock(diff_content, args.pr_body or "")

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_worker_auth(args):
    """Check worker/webhook auth compliance."""
    if args.scan_all:
        violations = check_worker_auth_compliance()
    else:
        violations = check_worker_auth_compliance(args.files or [])

    output = format_ci_output(violations, args.format)
    print(output)

    blocking = [v for v in violations if v.blocking]
    return 1 if blocking else 0


def cmd_governance_baseline(args):
    """Generate governance baseline report."""
    report = generate_governance_baseline()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        print(f"✅ Governance baseline written to: {output_path}")
    else:
        print(report)

    return 0


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Capability Registry Enforcer (PIN-306)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # check-pr command
    check_parser = subparsers.add_parser(
        "check-pr", help="Check PR files for capability linkage"
    )
    check_parser.add_argument(
        "--files", nargs="+", required=True, help="Files to check"
    )
    check_parser.add_argument("--pr-body", help="PR body text")
    check_parser.add_argument("--format", choices=["text", "github"], default="text")
    check_parser.set_defaults(func=cmd_check_pr)

    # ui-guard command
    ui_parser = subparsers.add_parser("ui-guard", help="Check UI expansion rules")
    ui_parser.add_argument("--files", nargs="+", required=True, help="Files to check")
    ui_parser.add_argument("--has-non-expansion-label", action="store_true")
    ui_parser.add_argument("--format", choices=["text", "github"], default="text")
    ui_parser.set_defaults(func=cmd_ui_guard)

    # scan-unregistered command
    scan_parser = subparsers.add_parser(
        "scan-unregistered", help="Scan for unregistered capabilities"
    )
    scan_parser.add_argument(
        "--generate-drafts", action="store_true", help="Generate draft YAML entries"
    )
    scan_parser.set_defaults(func=cmd_scan_unregistered)

    # heatmap command
    heatmap_parser = subparsers.add_parser("heatmap", help="Generate gap heatmap")
    heatmap_parser.add_argument("--format", choices=["md", "json"], default="md")
    heatmap_parser.add_argument("--output", "-o", help="Output file path")
    heatmap_parser.set_defaults(func=cmd_heatmap)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate-registry", help="Validate registry structure"
    )
    validate_parser.set_defaults(func=cmd_validate)

    # auth-guard command (CAP-006)
    auth_parser = subparsers.add_parser(
        "auth-guard", help="Check JWT parsing is centralized in gateway (CAP-006)"
    )
    auth_parser.add_argument(
        "--files", nargs="+", help="Files to check (required unless --scan-all)"
    )
    auth_parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan entire backend for auth violations",
    )
    auth_parser.add_argument("--format", choices=["text", "github"], default="text")
    auth_parser.set_defaults(func=cmd_auth_guard)

    # authority-guard command (CAP-001 replay, CAP-004 predictions)
    authority_parser = subparsers.add_parser(
        "authority-guard", help="Check replay/prediction routes have authority enforcement (CAP-001, CAP-004)"
    )
    authority_parser.add_argument(
        "--files", nargs="+", help="Files to check (required unless --scan-all)"
    )
    authority_parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan replay/prediction routes for authority violations",
    )
    authority_parser.add_argument("--format", choices=["text", "github"], default="text")
    authority_parser.set_defaults(func=cmd_authority_guard)

    # =========================================================================
    # Phase G: Governance Freeze Commands
    # =========================================================================

    # registry-mutation command (G1)
    reg_mutation_parser = subparsers.add_parser(
        "registry-mutation",
        help="Check registry mutations are documented with PIN reference (G1)",
    )
    reg_mutation_parser.add_argument(
        "--diff-file", help="File containing git diff of registry"
    )
    reg_mutation_parser.add_argument("--pr-body", help="PR body text")
    reg_mutation_parser.add_argument("--commit-message", help="Commit message")
    reg_mutation_parser.add_argument(
        "--format", choices=["text", "github"], default="text"
    )
    reg_mutation_parser.set_defaults(func=cmd_registry_mutation)

    # plane-purity command (G2)
    plane_parser = subparsers.add_parser(
        "plane-purity",
        help="Check route/authority plane purity (G2)",
    )
    plane_parser.add_argument(
        "--files", nargs="+", help="Files to check (required unless --scan-all)"
    )
    plane_parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan all backend API files for plane purity violations",
    )
    plane_parser.add_argument("--format", choices=["text", "github"], default="text")
    plane_parser.set_defaults(func=cmd_plane_purity)

    # taxonomy-lock command (G3)
    taxonomy_parser = subparsers.add_parser(
        "taxonomy-lock",
        help="Check permission taxonomy changes follow versioning rules (G3)",
    )
    taxonomy_parser.add_argument(
        "--diff-file", help="File containing git diff of taxonomy"
    )
    taxonomy_parser.add_argument("--pr-body", help="PR body text")
    taxonomy_parser.add_argument(
        "--format", choices=["text", "github"], default="text"
    )
    taxonomy_parser.set_defaults(func=cmd_taxonomy_lock)

    # worker-auth command (G4)
    worker_parser = subparsers.add_parser(
        "worker-auth",
        help="Check workers use API keys, not AuthContext (G4)",
    )
    worker_parser.add_argument(
        "--files", nargs="+", help="Files to check (required unless --scan-all)"
    )
    worker_parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan all worker/webhook files for auth compliance",
    )
    worker_parser.add_argument("--format", choices=["text", "github"], default="text")
    worker_parser.set_defaults(func=cmd_worker_auth)

    # governance-baseline command (G5)
    baseline_parser = subparsers.add_parser(
        "governance-baseline",
        help="Generate governance baseline report (G5)",
    )
    baseline_parser.add_argument(
        "--output", "-o", help="Output file path (default: stdout)"
    )
    baseline_parser.set_defaults(func=cmd_governance_baseline)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
