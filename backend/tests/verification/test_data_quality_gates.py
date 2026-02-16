# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Tests for data quality gate behavior
# artifact_class: TEST

"""
Data Quality Gates — Test Suite (BA-19)

Validates that:
- The schema drift and data quality gate scripts exist and are runnable
- The models directory is populated
- No duplicate __tablename__ values exist across model files
- ID fields follow nullability conventions
"""

import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BACKEND_DIR / "app" / "models"
SCRIPTS_DIR = BACKEND_DIR / "scripts" / "verification"

SCHEMA_DRIFT_SCRIPT = SCRIPTS_DIR / "check_schema_drift.py"
DATA_QUALITY_SCRIPT = SCRIPTS_DIR / "check_data_quality.py"

# ---------------------------------------------------------------------------
# Regex patterns (mirrored from check_schema_drift.py for independent validation)
# ---------------------------------------------------------------------------

RE_CLASS_SQLMODEL = re.compile(
    r"^class\s+(\w+)\s*\(\s*SQLModel\b[^)]*table\s*=\s*True[^)]*\)\s*:",
    re.MULTILINE,
)
RE_CLASS_BASE = re.compile(
    r"^class\s+(\w+)\s*\(\s*Base\s*\)\s*:",
    re.MULTILINE,
)
RE_TABLENAME = re.compile(
    r'__tablename__\s*=\s*["\'](\w+)["\']',
)
RE_ANY_CLASS = re.compile(
    r"^class\s+(\w+)\s*\([^)]*\)\s*:",
    re.MULTILINE,
)

SKIP_FILES = {"__init__.py"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _collect_table_models() -> list[dict]:
    """Parse model files and return list of {class_name, tablename, file}."""
    results = []
    for pyfile in sorted(MODELS_DIR.glob("*.py")):
        if pyfile.name in SKIP_FILES or pyfile.name.startswith("__"):
            continue
        source = pyfile.read_text(encoding="utf-8")

        for regex in (RE_CLASS_SQLMODEL, RE_CLASS_BASE):
            for m in regex.finditer(source):
                class_name = m.group(1)
                # Find __tablename__ in class body
                next_class = RE_ANY_CLASS.search(source, m.start() + 1)
                end = next_class.start() if next_class else len(source)
                body = source[m.start():end]
                tn_match = RE_TABLENAME.search(body)
                tablename = tn_match.group(1) if tn_match else None
                results.append({
                    "class_name": class_name,
                    "tablename": tablename,
                    "file": pyfile.name,
                })
    return results


def _collect_id_fields() -> list[dict]:
    """Parse model files and return list of ID field metadata."""
    results = []
    re_field = re.compile(
        r"^\s+(\w+_id)\s*:\s*(.+?)\s*=\s*(.+)$",
        re.MULTILINE,
    )
    for pyfile in sorted(MODELS_DIR.glob("*.py")):
        if pyfile.name in SKIP_FILES or pyfile.name.startswith("__"):
            continue
        source = pyfile.read_text(encoding="utf-8")
        for m in re_field.finditer(source):
            fname = m.group(1)
            ftype = m.group(2)
            is_optional = "Optional" in ftype
            results.append({
                "name": fname,
                "type": ftype.strip(),
                "is_optional": is_optional,
                "file": pyfile.name,
            })
    return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScriptExistence:
    """Verify that gate scripts exist on disk."""

    def test_schema_drift_checker_exists(self):
        """BA-19-1: check_schema_drift.py must exist."""
        assert SCHEMA_DRIFT_SCRIPT.is_file(), (
            f"Schema drift script not found at {SCHEMA_DRIFT_SCRIPT}"
        )

    def test_data_quality_checker_exists(self):
        """BA-19-2: check_data_quality.py must exist."""
        assert DATA_QUALITY_SCRIPT.is_file(), (
            f"Data quality script not found at {DATA_QUALITY_SCRIPT}"
        )


class TestScriptExecution:
    """Run gate scripts and verify exit codes."""

    def test_schema_drift_exits_zero(self):
        """BA-19-3: check_schema_drift.py must exit 0 (no critical drift)."""
        result = subprocess.run(
            [sys.executable, str(SCHEMA_DRIFT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"check_schema_drift.py exited with {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    def test_data_quality_exits_zero(self):
        """BA-19-4: check_data_quality.py must exit 0 (no failures)."""
        result = subprocess.run(
            [sys.executable, str(DATA_QUALITY_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"check_data_quality.py exited with {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestModelsDirectory:
    """Verify the models directory is populated and healthy."""

    def test_models_directory_exists(self):
        """BA-19-5: app/models/ must exist and contain Python files."""
        assert MODELS_DIR.is_dir(), f"Models directory not found: {MODELS_DIR}"
        py_files = list(MODELS_DIR.glob("*.py"))
        # Exclude __init__.py and __pycache__
        model_files = [f for f in py_files if not f.name.startswith("__")]
        assert len(model_files) > 0, (
            f"No model files found in {MODELS_DIR}"
        )


class TestSchemaIntegrity:
    """Independent schema integrity checks (no subprocess)."""

    def test_no_duplicate_table_names(self):
        """BA-19-6: No two model classes may share the same __tablename__."""
        models = _collect_table_models()
        assert len(models) > 0, "No table models found"

        tablename_map: dict[str, list[str]] = defaultdict(list)
        for mdl in models:
            if mdl["tablename"]:
                tablename_map[mdl["tablename"]].append(
                    f"{mdl['class_name']} ({mdl['file']})"
                )

        duplicates = {
            tname: owners
            for tname, owners in tablename_map.items()
            if len(owners) > 1
        }
        assert not duplicates, (
            f"Duplicate __tablename__ values detected:\n"
            + "\n".join(
                f"  '{tname}': {', '.join(owners)}"
                for tname, owners in duplicates.items()
            )
        )

    def test_id_fields_are_not_optional(self):
        """BA-19-7: tenant_id fields should not be Optional (sample check)."""
        id_fields = _collect_id_fields()
        assert len(id_fields) > 0, "No ID fields found"

        # Focus on tenant_id fields specifically — these are the most critical
        # FK and must be non-nullable for tenant isolation.
        tenant_id_fields = [f for f in id_fields if f["name"] == "tenant_id"]
        assert len(tenant_id_fields) > 0, "No tenant_id fields found"

        optional_tenant_ids = [
            f for f in tenant_id_fields if f["is_optional"]
        ]

        # AuditLog.tenant_id is legitimately Optional (system-level audit entries)
        # SystemRecord.tenant_id is legitimately Optional (system-wide events)
        # Filter out known allowlisted files
        allowlisted_files = {"tenant.py", "logs_records.py"}
        violations = [
            f for f in optional_tenant_ids
            if f["file"] not in allowlisted_files
        ]

        assert not violations, (
            f"tenant_id fields should not be Optional:\n"
            + "\n".join(
                f"  {f['file']}: tenant_id declared as {f['type']}"
                for f in violations
            )
        )
