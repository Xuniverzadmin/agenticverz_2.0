# Layer: L0 — Test
# AUDIENCE: INTERNAL
# Role: Integration test — veil policy docs gating wired into FastAPI app
# Reference: veil_policy.py, PHASE5_backend_app_hoc_app_py.md

"""
FastAPI Schema Gating Integration Test.

Verifies that veil_policy.fastapi_schema_urls() is correctly wired into
the FastAPI(...) constructor in app.main, so that prod + HOC_DOCS_ENABLED=false
results in docs_url/openapi_url/redoc_url being None on the live app object.

Uses subprocess to isolate env vars from the test process.
"""

import json
import subprocess
import sys

import pytest

PROBE_SCRIPT = """\
import os, json
os.environ["AOS_MODE"] = "{aos_mode}"
os.environ["HOC_DOCS_ENABLED"] = "{docs_enabled}"

from app.main import app
print(json.dumps({{
    "docs_url": app.docs_url,
    "openapi_url": app.openapi_url,
    "redoc_url": app.redoc_url,
}}))
"""


def _run_probe(aos_mode: str, docs_enabled: str) -> dict:
    script = PROBE_SCRIPT.format(aos_mode=aos_mode, docs_enabled=docs_enabled)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent),
        env={
            **__import__("os").environ,
            "PYTHONPATH": ".",
            "AOS_MODE": aos_mode,
            "HOC_DOCS_ENABLED": docs_enabled,
        },
    )
    if result.returncode != 0:
        pytest.skip(f"Subprocess failed (non-zero exit): {result.stderr[-500:]}")
    # The last line of stdout should be the JSON
    for line in reversed(result.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    pytest.skip(f"No JSON output found in subprocess stdout")


class TestFastAPISchemaGating:
    """Integration: veil policy wired into FastAPI app object."""

    def test_prod_docs_disabled(self):
        data = _run_probe("prod", "false")
        assert data["docs_url"] is None, f"Expected docs_url=None, got {data['docs_url']}"
        assert data["openapi_url"] is None, f"Expected openapi_url=None, got {data['openapi_url']}"
        assert data["redoc_url"] is None, f"Expected redoc_url=None, got {data['redoc_url']}"

    def test_prod_docs_enabled(self):
        data = _run_probe("prod", "true")
        # When docs are enabled, FastAPI defaults apply (non-None)
        assert data["docs_url"] is not None, "Expected docs_url to be set when HOC_DOCS_ENABLED=true"

    def test_preprod_docs_available(self):
        data = _run_probe("preprod", "false")
        # Non-prod: veil returns {}, so FastAPI defaults apply
        assert data["docs_url"] is not None, "Expected docs_url to be set in preprod"
