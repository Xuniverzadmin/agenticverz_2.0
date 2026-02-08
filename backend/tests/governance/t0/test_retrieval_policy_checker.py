# Layer: L8 — Tests
# Product: system-wide
# Reference: Knowledge Planes Phase 6 (policy snapshot gate)

import contextlib

import pytest

from app.hoc.cus.hoc_spine.services.retrieval_policy_checker_engine import (
    DbPolicySnapshotPolicyChecker,
    _extract_allowed_plane_ids,
)


class _FakeScalars:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return _FakeScalars(self._value)


class _FakeSession:
    async def execute(self, _stmt):
        return _FakeResult(None)


@contextlib.asynccontextmanager
async def _fake_async_session_context():
    yield _FakeSession()


def test_extract_allowed_plane_ids_supports_multiple_keys():
    assert _extract_allowed_plane_ids({"allowed_plane_ids": ["kp_a", "kp_b"]}) == ["kp_a", "kp_b"]
    assert _extract_allowed_plane_ids({"allowed_rag_sources": ["kp_c"]}) == ["kp_c"]
    assert _extract_allowed_plane_ids({"allowed_knowledge_planes": ["kp_d"]}) == ["kp_d"]
    assert _extract_allowed_plane_ids({"knowledge_access": {"allowed_planes": ["kp_e"]}}) == ["kp_e"]
    assert _extract_allowed_plane_ids({}) == []


@pytest.mark.asyncio
async def test_policy_checker_denies_when_run_missing(monkeypatch):
    # Patch the module-level session context used by the checker.
    import app.hoc.cus.hoc_spine.services.retrieval_policy_checker_engine as mod

    monkeypatch.setattr(mod, "get_async_session_context", _fake_async_session_context)

    checker = DbPolicySnapshotPolicyChecker()
    decision = await checker.check_access(
        tenant_id="t1",
        run_id="run_missing",
        plane_id="kp_x",
        action="query",
    )

    assert decision.allowed is False
    assert "Run not found" in decision.reason
