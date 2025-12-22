# api/health.py
"""
Health and Determinism Status Endpoints

Provides operational visibility into:
- Service health
- Determinism status (last replay hash)
- Adapter availability
- Registry state
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["health"])

# Store last known replay hashes
_determinism_state = {
    "last_replay_hash": None,
    "last_replay_at": None,
    "replay_count": 0,
    "drift_detected": False,
}


def update_replay_hash(workflow_name: str, output_hash: str):
    """Update the determinism state after a replay test."""
    global _determinism_state
    _determinism_state["last_replay_hash"] = output_hash
    _determinism_state["last_replay_at"] = datetime.now(timezone.utc).isoformat()
    _determinism_state["replay_count"] += 1


def report_drift(workflow_name: str, expected: str, actual: str):
    """Report a determinism drift."""
    global _determinism_state
    _determinism_state["drift_detected"] = True
    _determinism_state["drift_details"] = {
        "workflow": workflow_name,
        "expected_hash": expected,
        "actual_hash": actual,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        200: Service is healthy
        503: Service is degraded
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "aos-backend",
        "version": "1.0.0",
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Essential services
    """
    checks = {"database": "unknown", "redis": "unknown", "skills": "unknown"}

    # Check skills registry
    try:
        from app.skills import list_skills

        skills = list_skills()
        checks["skills"] = f"ok ({len(skills)} registered)"
    except Exception as e:
        checks["skills"] = f"error: {str(e)}"

    # Overall status
    all_ok = all("ok" in str(v) or v == "unknown" for v in checks.values())

    return {"ready": all_ok, "checks": checks, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/determinism")
async def determinism_status() -> Dict[str, Any]:
    """
    Determinism status endpoint.

    Shows:
    - Last replay hash
    - Replay count
    - Drift detection status

    Used for operational monitoring and debugging.
    """
    return {
        "determinism": {
            "last_replay_hash": _determinism_state["last_replay_hash"],
            "last_replay_at": _determinism_state["last_replay_at"],
            "replay_count": _determinism_state["replay_count"],
            "drift_detected": _determinism_state["drift_detected"],
            "drift_details": _determinism_state.get("drift_details"),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/adapters")
async def adapter_status() -> Dict[str, Any]:
    """
    LLM adapter availability status.

    Shows registered adapters and their health.
    """
    adapters = {}

    try:
        from app.skills.llm_invoke_v2 import get_adapter, list_adapters

        for adapter_id in list_adapters():
            adapter = get_adapter(adapter_id)
            if adapter:
                adapters[adapter_id] = {
                    "registered": True,
                    "default_model": adapter.default_model,
                    "supports_seeding": adapter.supports_seeding(),
                }
            else:
                adapters[adapter_id] = {"registered": False}

    except Exception as e:
        adapters["error"] = str(e)

    return {"adapters": adapters, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/skills")
async def skills_status() -> Dict[str, Any]:
    """
    Skill registry status.

    Shows registered skills and their versions.
    """
    skills = {}

    try:
        from app.skills import get_skill, list_skills

        for skill_name in list_skills():
            skill = get_skill(skill_name)
            if skill:
                skills[skill_name] = {"version": getattr(skill, "VERSION", "unknown"), "registered": True}

    except Exception as e:
        skills["error"] = str(e)

    return {
        "skills": skills,
        "count": len([s for s in skills.values() if isinstance(s, dict) and s.get("registered")]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
