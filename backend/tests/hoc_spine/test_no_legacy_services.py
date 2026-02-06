# Layer: L0 — CI / Test
# AUDIENCE: INTERNAL
# Role: Pytest guard — no legacy app.services imports in HOC/worker/startup
# Reference: PIN-520 ITER3.5
# artifact_class: TEST

"""
Test guard: Verify HOC/worker/startup trees have zero legacy app.services imports.

Mirrors CI check 32 (check_no_legacy_services_imports) as a pytest-runnable guard.
"""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _collect_legacy_imports():
    """Scan HOC/worker/startup for legacy app.services imports."""
    violations = []
    scan_dirs = [
        BACKEND_ROOT / "app" / "hoc",
        BACKEND_ROOT / "app" / "worker",
        BACKEND_ROOT / "app" / "startup",
    ]
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            try:
                source = py_file.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(source.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "from app.services" in line or "import app.services" in line:
                    rel = py_file.relative_to(BACKEND_ROOT)
                    violations.append(f"{rel}:{i}: {line.strip()[:80]}")
                if "from ..services" in line and "worker" in str(py_file):
                    rel = py_file.relative_to(BACKEND_ROOT)
                    violations.append(f"{rel}:{i}: {line.strip()[:80]}")
    return violations


def test_no_legacy_services_imports():
    """HOC/worker/startup must not import from legacy app.services."""
    violations = _collect_legacy_imports()
    assert violations == [], (
        f"Found {len(violations)} legacy app.services import(s):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


def test_no_relative_services_imports_in_worker():
    """Worker files must not use relative imports from ..services."""
    worker_dir = BACKEND_ROOT / "app" / "worker"
    violations = []
    if not worker_dir.exists():
        return
    for py_file in worker_dir.rglob("*.py"):
        try:
            source = py_file.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "from ..services" in line:
                rel = py_file.relative_to(BACKEND_ROOT)
                violations.append(f"{rel}:{i}: {line.strip()[:80]}")
    assert violations == [], (
        f"Found {len(violations)} relative ..services import(s) in worker/:\n"
        + "\n".join(f"  {v}" for v in violations)
    )
