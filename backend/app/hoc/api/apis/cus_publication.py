# Layer: L2 — API Publication Endpoints
# AUDIENCE: SYSTEM
# Role: Grouped CUS domain publication views (ledger + swagger/OpenAPI)
# artifact_class: CODE
# capability_id: CAP-011
"""
CUS Publication Router

Provides domain-grouped views of the CUS API surface:
- /apis/ledger/cus           — full CUS ledger (all 10 domains)
- /apis/ledger/cus/{domain}  — per-domain ledger subset
- /apis/swagger/cus          — CUS-only OpenAPI spec
- /apis/swagger/cus/{domain} — per-domain OpenAPI spec

All endpoints are read-only and derive from:
1. docs/api/HOC_CUS_API_LEDGER.json (authoritative ledger)
2. Source-scanned CUS routers (fallback)
3. Runtime FastAPI OpenAPI (for swagger views)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.hoc.api.facades.cus import CANONICAL_CUS_DOMAINS

router = APIRouter(prefix="/apis", tags=["CUS Publication"])

_REPO_ROOT = Path(__file__).resolve().parents[5]
_LEDGER_FILE = _REPO_ROOT / "docs" / "api" / "HOC_CUS_API_LEDGER.json"

# ── Legacy-prefix → domain mappings for routes that don't use /cus/{domain} prefix ──
_LEGACY_PREFIX_DOMAIN: dict[str, str] = {
    "/controls": "controls",
    "/policies": "policies",
    "/integrations": "integrations",
    "/telemetry": "integrations",
    "/connectors": "integrations",
    "/datasources": "integrations",
    "/v1": "integrations",
    "/session": "integrations",
    "/feedback": "analytics",
    "/predictions": "analytics",
    "/scenarios": "analytics",
    "/costsim": "analytics",
    "/traces": "logs",
    "/cost": "logs",
    "/incidents": "incidents",
    "/tenant/api-keys": "api_keys",
    "/embedding": "api_keys",
    "/memory": "account",
    "/alerts": "policies",
    "/governance": "policies",
    "/detection": "policies",
    "/compliance": "policies",
    "/monitors": "policies",
    "/rate-limits": "policies",
    "/policy": "policies",
    "/policy-layer": "policies",
    "/policy-proposals": "policies",
    "/replay": "policies",
    "/runtime": "policies",
    "/scheduler": "policies",
    "/lifecycle": "policies",
    "/notifications": "policies",
    "/enforcement": "policies",
    "/evidence": "policies",
    "/rbac": "policies",
    "/retrieval": "policies",
    "/limits": "policies",
    "/customer": "policies",
    "/status_history": "policies",
    "/workers/business-builder": "policies",
    "/integration": "policies",
}


_SEGMENT_TO_DOMAIN: dict[str, str] = {
    # Exact canonical domain names
    **{d: d for d in CANONICAL_CUS_DOMAINS},
    # Variant segments found in normalised ledger paths
    "accounts": "account",
    "api-keys": "api_keys",
    "runs": "activity",
    "guard": "policies",
    "tenant": "account",
    # Legacy segments that appear after /hoc/api/cus/ normalisation
    "policy-layer": "policies",
    "policy": "policies",
    "policy-proposals": "policies",
    "alerts": "policies",
    "governance": "policies",
    "detection": "policies",
    "compliance": "policies",
    "monitors": "policies",
    "rate-limits": "policies",
    "replay": "policies",
    "runtime": "policies",
    "scheduler": "policies",
    "lifecycle": "policies",
    "notifications": "policies",
    "enforcement": "policies",
    "evidence": "policies",
    "rbac": "policies",
    "retrieval": "policies",
    "limits": "policies",
    "customer": "policies",
    "status_history": "policies",
    "workers": "policies",
    "integration": "policies",
    "connectors": "integrations",
    "datasources": "integrations",
    "v1": "integrations",
    "session": "integrations",
    "telemetry": "integrations",
    "feedback": "analytics",
    "predictions": "analytics",
    "scenarios": "analytics",
    "costsim": "analytics",
    "traces": "logs",
    "cost": "logs",
    "embedding": "api_keys",
    "memory": "account",
}


def _resolve_domain(path: str) -> str | None:
    """Resolve a runtime or ledger-normalised path to its CUS domain."""
    # Normalised /hoc/api/cus/{segment}/... form
    if path.startswith("/hoc/api/cus/"):
        segment = path[len("/hoc/api/cus/"):].split("/")[0]
        if segment in _SEGMENT_TO_DOMAIN:
            return _SEGMENT_TO_DOMAIN[segment]
    # /cus/{domain} form
    if path.startswith("/cus/"):
        segment = path[len("/cus/"):].split("/")[0]
        if segment in _SEGMENT_TO_DOMAIN:
            return _SEGMENT_TO_DOMAIN[segment]
    # Legacy prefix match (longest match first)
    for prefix, domain in sorted(_LEGACY_PREFIX_DOMAIN.items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix):
            return domain
    return None


def _load_ledger() -> list[dict[str, Any]]:
    """Load CUS ledger from JSON file."""
    if not _LEDGER_FILE.exists():
        return []
    try:
        data = json.loads(_LEDGER_FILE.read_text())
        return data.get("endpoints", [])
    except (json.JSONDecodeError, OSError):
        return []


def _ledger_by_domain() -> dict[str, list[dict[str, Any]]]:
    """Group ledger endpoints by domain."""
    endpoints = _load_ledger()
    grouped: dict[str, list[dict[str, Any]]] = {d: [] for d in CANONICAL_CUS_DOMAINS}
    for ep in endpoints:
        path = ep.get("path", "")
        domain = _resolve_domain(path)
        if domain and domain in grouped:
            grouped[domain].append(ep)
    return grouped


# ── Ledger Endpoints ──


@router.get("/ledger/cus")
async def cus_ledger_global():
    """GET /apis/ledger/cus — Full CUS domain ledger (all 10 domains)."""
    endpoints = _load_ledger()
    grouped = _ledger_by_domain()
    domain_counts = {d: len(eps) for d, eps in grouped.items()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(endpoints),
        "unique_method_path": len({(e.get("method", ""), e.get("path", "")) for e in endpoints}),
        "domains": list(CANONICAL_CUS_DOMAINS),
        "domain_counts": domain_counts,
        "endpoints": endpoints,
    }


@router.get("/ledger/cus/{domain}")
async def cus_ledger_domain(domain: str):
    """GET /apis/ledger/cus/{domain} — Per-domain CUS ledger."""
    if domain not in CANONICAL_CUS_DOMAINS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown CUS domain: {domain}. Valid: {', '.join(CANONICAL_CUS_DOMAINS)}",
        )
    grouped = _ledger_by_domain()
    eps = grouped.get(domain, [])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "total": len(eps),
        "unique_method_path": len({(e.get("method", ""), e.get("path", "")) for e in eps}),
        "endpoints": eps,
    }


# ── Swagger/OpenAPI Endpoints ──


def _extract_cus_openapi(app_openapi: dict[str, Any], domain: str | None = None) -> dict[str, Any]:
    """Filter full OpenAPI spec to CUS-only paths, optionally for one domain."""
    paths = app_openapi.get("paths", {})
    filtered_paths: dict[str, Any] = {}
    for path, methods in paths.items():
        resolved = _resolve_domain(path)
        if resolved is None:
            continue
        if domain is not None and resolved != domain:
            continue
        filtered_paths[path] = methods

    # Build minimal OpenAPI doc
    spec: dict[str, Any] = {
        "openapi": app_openapi.get("openapi", "3.1.0"),
        "info": {
            "title": f"AOS CUS API{f' — {domain}' if domain else ''}",
            "version": app_openapi.get("info", {}).get("version", "0.0.0"),
        },
        "paths": filtered_paths,
    }
    # Include referenced schemas
    schemas = app_openapi.get("components", {}).get("schemas", {})
    if schemas:
        spec["components"] = {"schemas": schemas}
    return spec


@router.get("/swagger/cus")
async def cus_swagger_global(request: Request):
    """GET /apis/swagger/cus — CUS-only OpenAPI spec (all 10 domains)."""
    app_openapi = request.app.openapi()
    spec = _extract_cus_openapi(app_openapi)
    return JSONResponse(content=spec)


@router.get("/swagger/cus/{domain}")
async def cus_swagger_domain(request: Request, domain: str):
    """GET /apis/swagger/cus/{domain} — Per-domain CUS OpenAPI spec."""
    if domain not in CANONICAL_CUS_DOMAINS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown CUS domain: {domain}. Valid: {', '.join(CANONICAL_CUS_DOMAINS)}",
        )
    app_openapi = request.app.openapi()
    spec = _extract_cus_openapi(app_openapi, domain=domain)
    return JSONResponse(content=spec)
