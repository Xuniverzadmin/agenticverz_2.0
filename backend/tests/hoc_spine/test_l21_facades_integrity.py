# Layer: L0 — Test
# AUDIENCE: INTERNAL
# Role: Pytest guard — L2.1 facade integrity (canonical 10 CUS domains)
# Reference: L2.1_design_hoc.md, HOC_LAYER_TOPOLOGY_V2.0.0.md

"""
L2.1 Facade Integrity Guard.

Enforces:
  A. All 10 canonical CUS domain facade files exist on disk.
  B. The facades package exports CANONICAL_CUS_DOMAINS matching the design doc.
  C. ALL_CUS_ROUTERS is a non-empty list of APIRouter instances.
"""

from pathlib import Path

import pytest
from fastapi import APIRouter

FACADES_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "app"
    / "hoc"
    / "api"
    / "facades"
    / "cus"
)

CANONICAL_10 = (
    "overview",
    "activity",
    "incidents",
    "policies",
    "controls",
    "logs",
    "analytics",
    "integrations",
    "api_keys",
    "account",
)

CANONICAL_FACADE_FILES = {
    "overview": "overview/overview_fac.py",
    "activity": "activity/activity_fac.py",
    "incidents": "incidents/incidents_fac.py",
    "policies": "policies/policies_fac.py",
    "controls": "controls/controls_fac.py",
    "logs": "logs/logs_fac.py",
    "analytics": "analytics/analytics_fac.py",
    "integrations": "integrations/integrations_fac.py",
    "api_keys": "api_keys/api_keys_fac.py",
    "account": "account/account_fac.py",
}


class TestL21FacadesIntegrity:
    """L2.1 facade integrity: canonical 10 CUS domains."""

    @pytest.mark.parametrize("domain", CANONICAL_10)
    def test_facade_file_exists(self, domain: str):
        """Test A: Each canonical domain facade file must exist on disk."""
        facade_file = FACADES_DIR / CANONICAL_FACADE_FILES[domain]
        assert facade_file.is_file(), (
            f"Missing L2.1 facade: {facade_file.relative_to(FACADES_DIR.parent.parent.parent.parent.parent)}"
        )

    def test_canonical_cus_domains_tuple(self):
        """Test B: facades.CANONICAL_CUS_DOMAINS equals the canonical 10-tuple."""
        import app.hoc.api.facades.cus as facades

        assert hasattr(facades, "CANONICAL_CUS_DOMAINS"), (
            "facades/cus/__init__.py must export CANONICAL_CUS_DOMAINS"
        )
        assert facades.CANONICAL_CUS_DOMAINS == CANONICAL_10, (
            f"CANONICAL_CUS_DOMAINS mismatch:\n"
            f"  expected: {CANONICAL_10}\n"
            f"  actual:   {facades.CANONICAL_CUS_DOMAINS}"
        )

    def test_all_cus_routers_bundle(self):
        """Test C: ALL_CUS_ROUTERS is non-empty and contains only APIRouter instances."""
        import app.hoc.api.facades.cus as facades

        assert hasattr(facades, "ALL_CUS_ROUTERS"), (
            "facades/cus/__init__.py must export ALL_CUS_ROUTERS"
        )
        routers = facades.ALL_CUS_ROUTERS
        assert len(routers) > 0, "ALL_CUS_ROUTERS must be non-empty"
        for i, r in enumerate(routers):
            assert isinstance(r, APIRouter), (
                f"ALL_CUS_ROUTERS[{i}] is {type(r).__name__}, expected APIRouter"
            )
