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

Usage:
    python capability_registry_enforcer.py check-pr --files file1.py file2.py
    python capability_registry_enforcer.py ui-guard --files page1.tsx page2.tsx
    python capability_registry_enforcer.py scan-unregistered
    python capability_registry_enforcer.py heatmap [--format md|json]
    python capability_registry_enforcer.py validate-registry
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
