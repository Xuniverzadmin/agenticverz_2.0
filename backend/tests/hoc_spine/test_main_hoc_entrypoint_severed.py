# Layer: L0 — Test
# AUDIENCE: INTERNAL
# Role: Pytest guard — main.py must not import HOC routers directly (Phase 5 severance)
# Reference: master_plan_hoc_surfacing_L2.1.md, PHASE5_backend_app_hoc_app_py.md

"""
Phase 5 Severance Guard — main.py entrypoint.

Ensures backend/app/main.py delegates all HOC router inclusion to
app.hoc.app.include_hoc(app) and never imports individual routers
or calls app.include_router() directly.
"""

import re
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent.parent / "app" / "main.py"


def _read_main() -> list[str]:
    return MAIN_PY.read_text().splitlines()


class TestMainHocEntrypointSevered:
    """Phase 5 severance: main.py must not act as router directory."""

    def test_no_relative_hoc_api_imports(self):
        """main.py must not contain 'from .hoc.api' imports."""
        pat = re.compile(r"^from \.hoc\.api")
        matches = [
            (i, line)
            for i, line in enumerate(_read_main(), 1)
            if not line.lstrip().startswith("#") and pat.search(line.lstrip())
        ]
        assert matches == [], (
            f"main.py has {len(matches)} relative HOC router import(s): "
            + "; ".join(f"L{i}: {l.strip()}" for i, l in matches)
        )

    def test_no_absolute_hoc_api_imports(self):
        """main.py must not contain 'from app.hoc.api' imports."""
        pat = re.compile(r"^from app\.hoc\.api")
        matches = [
            (i, line)
            for i, line in enumerate(_read_main(), 1)
            if not line.lstrip().startswith("#") and pat.search(line.lstrip())
        ]
        assert matches == [], (
            f"main.py has {len(matches)} absolute HOC router import(s): "
            + "; ".join(f"L{i}: {l.strip()}" for i, l in matches)
        )

    def test_no_direct_include_router_calls(self):
        """main.py must not call app.include_router() directly."""
        pat = re.compile(r"\bapp\.include_router\(")
        matches = [
            (i, line)
            for i, line in enumerate(_read_main(), 1)
            if not line.lstrip().startswith("#") and pat.search(line)
        ]
        assert matches == [], (
            f"main.py has {len(matches)} direct app.include_router() call(s): "
            + "; ".join(f"L{i}: {l.strip()}" for i, l in matches)
        )
