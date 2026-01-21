# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 export and scope resolution governance requirements (GAP-026, GAP-028)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-007: Export and Scope Resolution Tests (GAP-026, GAP-028)

Tests the export and scope resolution features:
- GAP-026: Executive debrief export - non-technical summary for leadership
- GAP-028: Scope resolution at run start - explicit scope resolution, snapshot stored

Key Principles:
> Executive debriefs provide leadership-appropriate summaries without technical jargon.
> Scope resolution happens BEFORE run starts and is frozen into the policy snapshot.
"""

from datetime import datetime, timezone

import pytest

from app.models.export_bundles import (
    EvidenceBundle,
    ExecutiveDebriefBundle,
    ExportBundleRequest,
    ExportBundleResponse,
    PolicyContext,
    SOC2Bundle,
    SOC2ControlMapping,
    TraceStepEvidence,
)
from app.policy.scope_resolver import (
    RunContext,
    ScopeResolutionResult,
    ScopeResolver,
    get_scope_resolver,
)
from app.models.policy_scope import PolicyScope, ScopeType


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestExportScopeImports:
    """Verify all export and scope resolution imports are accessible."""

    def test_executive_debrief_bundle_import(self) -> None:
        """Test ExecutiveDebriefBundle model is importable."""
        assert ExecutiveDebriefBundle is not None

    def test_evidence_bundle_import(self) -> None:
        """Test EvidenceBundle model is importable."""
        assert EvidenceBundle is not None

    def test_soc2_bundle_import(self) -> None:
        """Test SOC2Bundle model is importable."""
        assert SOC2Bundle is not None

    def test_scope_resolver_import(self) -> None:
        """Test ScopeResolver class is importable."""
        assert ScopeResolver is not None

    def test_run_context_import(self) -> None:
        """Test RunContext dataclass is importable."""
        assert RunContext is not None

    def test_scope_resolution_result_import(self) -> None:
        """Test ScopeResolutionResult dataclass is importable."""
        assert ScopeResolutionResult is not None


# ===========================================================================
# GAP-026: Executive Debrief Export
# ===========================================================================


class TestGAP026ExecutiveDebrief:
    """
    GAP-026: Executive Debrief Export

    CURRENT: Declared
    REQUIRED: Verified working

    Tests the executive debrief bundle for non-technical leadership summaries.
    """

    def test_executive_debrief_has_incident_summary(self) -> None:
        """ExecutiveDebriefBundle has incident_summary field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test summary",
            business_impact="No impact",
            risk_level="low",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
        )
        assert bundle.incident_summary == "Test summary"

    def test_executive_debrief_has_business_impact(self) -> None:
        """ExecutiveDebriefBundle has business_impact field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="System downtime prevented",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
        )
        assert bundle.business_impact == "System downtime prevented"

    def test_executive_debrief_has_risk_level(self) -> None:
        """ExecutiveDebriefBundle has risk_level field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="high",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
        )
        assert bundle.risk_level == "high"

    def test_executive_debrief_has_recommended_actions(self) -> None:
        """ExecutiveDebriefBundle has recommended_actions field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
            recommended_actions=["Review policy", "Adjust thresholds"],
        )
        assert len(bundle.recommended_actions) == 2
        assert "Review policy" in bundle.recommended_actions

    def test_executive_debrief_has_time_to_detect(self) -> None:
        """ExecutiveDebriefBundle has time_to_detect_seconds field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
            time_to_detect_seconds=5,
        )
        assert bundle.time_to_detect_seconds == 5

    def test_executive_debrief_has_cost_incurred(self) -> None:
        """ExecutiveDebriefBundle has cost_incurred_cents field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
            cost_incurred_cents=500,
        )
        assert bundle.cost_incurred_cents == 500

    def test_executive_debrief_has_cost_prevented(self) -> None:
        """ExecutiveDebriefBundle has cost_prevented_cents field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
            cost_prevented_cents=5000,
        )
        assert bundle.cost_prevented_cents == 5000

    def test_executive_debrief_has_remediation_status(self) -> None:
        """ExecutiveDebriefBundle has remediation_status field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
        )
        assert bundle.remediation_status == "pending"

    def test_executive_debrief_has_classification(self) -> None:
        """ExecutiveDebriefBundle has classification field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
            classification="CONFIDENTIAL",
        )
        assert bundle.classification == "CONFIDENTIAL"

    def test_executive_debrief_has_prepared_for(self) -> None:
        """ExecutiveDebriefBundle has prepared_for field."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
            prepared_for="CEO, CFO",
        )
        assert bundle.prepared_for == "CEO, CFO"

    def test_executive_debrief_bundle_type(self) -> None:
        """ExecutiveDebriefBundle has correct bundle_type."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
        )
        assert bundle.bundle_type == "executive_debrief"

    def test_executive_debrief_bundle_id_prefix(self) -> None:
        """ExecutiveDebriefBundle has EXEC- bundle_id prefix."""
        bundle = ExecutiveDebriefBundle(
            incident_summary="Test",
            business_impact="Test impact",
            risk_level="medium",
            run_id="RUN-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_violated="Test Policy",
            violation_time=datetime.now(timezone.utc),
            detection_time=datetime.now(timezone.utc),
        )
        assert bundle.bundle_id.startswith("EXEC-")


# ===========================================================================
# GAP-028: Scope Resolution at Run Start
# ===========================================================================


class TestGAP028ScopeResolution:
    """
    GAP-028: Scope Resolution at Run Start

    CURRENT: Implicit
    REQUIRED: Explicit scope resolution, snapshot stored

    Tests the scope resolution mechanism that determines which policies apply.
    """

    def test_run_context_has_tenant_id(self) -> None:
        """RunContext has tenant_id field."""
        context = RunContext(tenant_id="tenant-001")
        assert context.tenant_id == "tenant-001"

    def test_run_context_has_agent_id(self) -> None:
        """RunContext has agent_id field."""
        context = RunContext(
            tenant_id="tenant-001",
            agent_id="agent-001",
        )
        assert context.agent_id == "agent-001"

    def test_run_context_has_api_key_id(self) -> None:
        """RunContext has api_key_id field."""
        context = RunContext(
            tenant_id="tenant-001",
            api_key_id="key-001",
        )
        assert context.api_key_id == "key-001"

    def test_run_context_has_human_actor_id(self) -> None:
        """RunContext has human_actor_id field."""
        context = RunContext(
            tenant_id="tenant-001",
            human_actor_id="user-001",
        )
        assert context.human_actor_id == "user-001"

    def test_run_context_has_run_id(self) -> None:
        """RunContext has run_id field."""
        context = RunContext(
            tenant_id="tenant-001",
            run_id="RUN-001",
        )
        assert context.run_id == "RUN-001"

    def test_scope_resolution_result_has_matching_policies(self) -> None:
        """ScopeResolutionResult has matching_policy_ids field."""
        context = RunContext(tenant_id="tenant-001")
        result = ScopeResolutionResult(
            matching_policy_ids=["POL-001", "POL-002"],
            all_runs_policies=["POL-001"],
            agent_policies=[],
            api_key_policies=[],
            human_actor_policies=["POL-002"],
            context=context,
            scopes_evaluated=5,
            resolution_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert len(result.matching_policy_ids) == 2
        assert "POL-001" in result.matching_policy_ids

    def test_scope_resolution_result_categorizes_by_type(self) -> None:
        """ScopeResolutionResult categorizes policies by scope type."""
        context = RunContext(tenant_id="tenant-001", agent_id="agent-001")
        result = ScopeResolutionResult(
            matching_policy_ids=["POL-001", "POL-002", "POL-003"],
            all_runs_policies=["POL-001"],
            agent_policies=["POL-002"],
            api_key_policies=[],
            human_actor_policies=["POL-003"],
            context=context,
            scopes_evaluated=10,
            resolution_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert result.all_runs_policies == ["POL-001"]
        assert result.agent_policies == ["POL-002"]
        assert result.human_actor_policies == ["POL-003"]

    def test_scope_resolution_result_has_to_snapshot(self) -> None:
        """ScopeResolutionResult has to_snapshot method."""
        context = RunContext(tenant_id="tenant-001")
        result = ScopeResolutionResult(
            matching_policy_ids=["POL-001"],
            all_runs_policies=["POL-001"],
            agent_policies=[],
            api_key_policies=[],
            human_actor_policies=[],
            context=context,
            scopes_evaluated=1,
            resolution_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert hasattr(result, "to_snapshot")
        assert callable(result.to_snapshot)

    def test_scope_resolution_snapshot_structure(self) -> None:
        """ScopeResolutionResult.to_snapshot returns correct structure."""
        context = RunContext(
            tenant_id="tenant-001",
            agent_id="agent-001",
            api_key_id="key-001",
        )
        result = ScopeResolutionResult(
            matching_policy_ids=["POL-001"],
            all_runs_policies=["POL-001"],
            agent_policies=[],
            api_key_policies=[],
            human_actor_policies=[],
            context=context,
            scopes_evaluated=3,
            resolution_timestamp="2024-01-01T00:00:00+00:00",
        )
        snapshot = result.to_snapshot()

        assert "matching_policy_ids" in snapshot
        assert "all_runs_policies" in snapshot
        assert "agent_policies" in snapshot
        assert "api_key_policies" in snapshot
        assert "human_actor_policies" in snapshot
        assert "context" in snapshot
        assert "scopes_evaluated" in snapshot
        assert "resolution_timestamp" in snapshot

    def test_scope_resolution_snapshot_includes_context(self) -> None:
        """ScopeResolutionResult.to_snapshot includes full context."""
        context = RunContext(
            tenant_id="tenant-001",
            agent_id="agent-001",
            api_key_id="key-001",
            human_actor_id="user-001",
        )
        result = ScopeResolutionResult(
            matching_policy_ids=["POL-001"],
            all_runs_policies=["POL-001"],
            agent_policies=[],
            api_key_policies=[],
            human_actor_policies=[],
            context=context,
            scopes_evaluated=1,
            resolution_timestamp="2024-01-01T00:00:00+00:00",
        )
        snapshot = result.to_snapshot()

        assert snapshot["context"]["tenant_id"] == "tenant-001"
        assert snapshot["context"]["agent_id"] == "agent-001"
        assert snapshot["context"]["api_key_id"] == "key-001"
        assert snapshot["context"]["human_actor_id"] == "user-001"

    def test_scope_resolver_has_resolve_method(self) -> None:
        """ScopeResolver has resolve_applicable_policies method."""
        resolver = ScopeResolver()
        assert hasattr(resolver, "resolve_applicable_policies")
        assert callable(resolver.resolve_applicable_policies)

    def test_scope_resolver_has_get_scope_for_policy(self) -> None:
        """ScopeResolver has get_scope_for_policy method."""
        resolver = ScopeResolver()
        assert hasattr(resolver, "get_scope_for_policy")
        assert callable(resolver.get_scope_for_policy)

    def test_scope_resolver_singleton(self) -> None:
        """get_scope_resolver returns singleton instance."""
        resolver1 = get_scope_resolver()
        resolver2 = get_scope_resolver()
        assert resolver1 is resolver2


# ===========================================================================
# Test: Scope Types
# ===========================================================================


class TestScopeTypes:
    """Test ScopeType enum for policy scope targeting."""

    def test_all_runs_scope(self) -> None:
        """ALL_RUNS scope exists."""
        assert ScopeType.ALL_RUNS is not None
        assert ScopeType.ALL_RUNS.value == "all_runs"

    def test_agent_scope(self) -> None:
        """AGENT scope exists."""
        assert ScopeType.AGENT is not None
        assert ScopeType.AGENT.value == "agent"

    def test_api_key_scope(self) -> None:
        """API_KEY scope exists."""
        assert ScopeType.API_KEY is not None
        assert ScopeType.API_KEY.value == "api_key"

    def test_human_actor_scope(self) -> None:
        """HUMAN_ACTOR scope exists."""
        assert ScopeType.HUMAN_ACTOR is not None
        assert ScopeType.HUMAN_ACTOR.value == "human_actor"


# ===========================================================================
# Test: Evidence Bundle Structure
# ===========================================================================


class TestEvidenceBundle:
    """Test EvidenceBundle model for export completeness."""

    def test_evidence_bundle_has_cross_domain_links(self) -> None:
        """EvidenceBundle has cross-domain linking fields."""
        bundle = EvidenceBundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            incident_id="INC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(
                policy_snapshot_id="SNAP-001",
            ),
        )
        assert bundle.run_id == "RUN-001"
        assert bundle.trace_id == "TRC-001"
        assert bundle.incident_id == "INC-001"

    def test_evidence_bundle_has_policy_context(self) -> None:
        """EvidenceBundle has policy_context field."""
        policy_ctx = PolicyContext(
            policy_snapshot_id="SNAP-001",
            violated_policy_id="POL-001",
            violated_policy_name="Token Limit",
            violation_type="token_limit",
        )
        bundle = EvidenceBundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=policy_ctx,
        )
        assert bundle.policy_context.violated_policy_id == "POL-001"
        assert bundle.policy_context.violation_type == "token_limit"

    def test_evidence_bundle_has_trace_steps(self) -> None:
        """EvidenceBundle has steps field."""
        steps = [
            TraceStepEvidence(
                step_index=0,
                timestamp=datetime.now(timezone.utc),
                step_type="skill_call",
                tokens=100,
                status="ok",
            ),
            TraceStepEvidence(
                step_index=1,
                timestamp=datetime.now(timezone.utc),
                step_type="skill_call",
                tokens=200,
                status="violation",
                is_inflection=True,
            ),
        ]
        bundle = EvidenceBundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
            steps=steps,
        )
        assert len(bundle.steps) == 2
        assert bundle.steps[1].is_inflection is True

    def test_evidence_bundle_has_content_hash(self) -> None:
        """EvidenceBundle has content_hash field for integrity."""
        bundle = EvidenceBundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
            content_hash="abc123def456",
        )
        assert bundle.content_hash == "abc123def456"

    def test_evidence_bundle_id_prefix(self) -> None:
        """EvidenceBundle has EVD- bundle_id prefix."""
        bundle = EvidenceBundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
        )
        assert bundle.bundle_id.startswith("EVD-")


# ===========================================================================
# Test: SOC2 Bundle Structure
# ===========================================================================


class TestSOC2Bundle:
    """Test SOC2Bundle model for compliance exports."""

    def test_soc2_bundle_extends_evidence(self) -> None:
        """SOC2Bundle extends EvidenceBundle."""
        assert issubclass(SOC2Bundle, EvidenceBundle)

    def test_soc2_bundle_has_control_mappings(self) -> None:
        """SOC2Bundle has control_mappings field."""
        bundle = SOC2Bundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
            control_mappings=[
                SOC2ControlMapping(
                    control_id="CC7.2",
                    control_name="Incident Response",
                    control_description="Test",
                    evidence_provided="Test evidence",
                ),
            ],
        )
        assert len(bundle.control_mappings) == 1
        assert bundle.control_mappings[0].control_id == "CC7.2"

    def test_soc2_bundle_has_attestation(self) -> None:
        """SOC2Bundle has attestation_statement field."""
        bundle = SOC2Bundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
            attestation_statement="This is certified evidence.",
        )
        assert bundle.attestation_statement == "This is certified evidence."

    def test_soc2_bundle_has_compliance_period(self) -> None:
        """SOC2Bundle has compliance period fields."""
        start = datetime.now(timezone.utc)
        end = datetime.now(timezone.utc)
        bundle = SOC2Bundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
            compliance_period_start=start,
            compliance_period_end=end,
        )
        assert bundle.compliance_period_start == start
        assert bundle.compliance_period_end == end

    def test_soc2_bundle_has_review_status(self) -> None:
        """SOC2Bundle has review_status field."""
        bundle = SOC2Bundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
            review_status="APPROVED",
        )
        assert bundle.review_status == "APPROVED"

    def test_soc2_bundle_id_prefix(self) -> None:
        """SOC2Bundle has SOC2- bundle_id prefix."""
        bundle = SOC2Bundle(
            run_id="RUN-001",
            trace_id="TRC-001",
            tenant_id="tenant-001",
            policy_context=PolicyContext(policy_snapshot_id="SNAP-001"),
        )
        assert bundle.bundle_id.startswith("SOC2-")


# ===========================================================================
# Test: Policy Context
# ===========================================================================


class TestPolicyContext:
    """Test PolicyContext model for policy information in exports."""

    def test_policy_context_has_snapshot_id(self) -> None:
        """PolicyContext has policy_snapshot_id field."""
        ctx = PolicyContext(policy_snapshot_id="SNAP-001")
        assert ctx.policy_snapshot_id == "SNAP-001"

    def test_policy_context_has_active_policies(self) -> None:
        """PolicyContext has active_policies field."""
        ctx = PolicyContext(
            policy_snapshot_id="SNAP-001",
            active_policies=[{"id": "POL-001", "name": "Token Limit"}],
        )
        assert len(ctx.active_policies) == 1

    def test_policy_context_has_violated_policy(self) -> None:
        """PolicyContext has violated_policy_id field."""
        ctx = PolicyContext(
            policy_snapshot_id="SNAP-001",
            violated_policy_id="POL-001",
            violated_policy_name="Token Limit",
        )
        assert ctx.violated_policy_id == "POL-001"
        assert ctx.violated_policy_name == "Token Limit"

    def test_policy_context_has_violation_type(self) -> None:
        """PolicyContext has violation_type field."""
        ctx = PolicyContext(
            policy_snapshot_id="SNAP-001",
            violation_type="token_limit",
        )
        assert ctx.violation_type == "token_limit"

    def test_policy_context_has_threshold_values(self) -> None:
        """PolicyContext has threshold and actual value fields."""
        ctx = PolicyContext(
            policy_snapshot_id="SNAP-001",
            threshold_value="1000",
            actual_value="1050",
        )
        assert ctx.threshold_value == "1000"
        assert ctx.actual_value == "1050"


# ===========================================================================
# Test: Trace Step Evidence
# ===========================================================================


class TestTraceStepEvidence:
    """Test TraceStepEvidence model for step-level evidence."""

    def test_trace_step_has_required_fields(self) -> None:
        """TraceStepEvidence has all required fields."""
        step = TraceStepEvidence(
            step_index=0,
            timestamp=datetime.now(timezone.utc),
            step_type="skill_call",
            status="ok",
        )
        assert step.step_index == 0
        assert step.step_type == "skill_call"
        assert step.status == "ok"

    def test_trace_step_has_metrics(self) -> None:
        """TraceStepEvidence has metric fields."""
        step = TraceStepEvidence(
            step_index=0,
            timestamp=datetime.now(timezone.utc),
            step_type="skill_call",
            status="ok",
            tokens=500,
            cost_cents=2.5,
            duration_ms=150.0,
        )
        assert step.tokens == 500
        assert step.cost_cents == 2.5
        assert step.duration_ms == 150.0

    def test_trace_step_has_inflection_marker(self) -> None:
        """TraceStepEvidence has is_inflection field."""
        step = TraceStepEvidence(
            step_index=5,
            timestamp=datetime.now(timezone.utc),
            step_type="skill_call",
            status="violation",
            is_inflection=True,
        )
        assert step.is_inflection is True

    def test_trace_step_has_content_hash(self) -> None:
        """TraceStepEvidence has content_hash field."""
        step = TraceStepEvidence(
            step_index=0,
            timestamp=datetime.now(timezone.utc),
            step_type="skill_call",
            status="ok",
            content_hash="sha256abc123",
        )
        assert step.content_hash == "sha256abc123"


# ===========================================================================
# Test: Export Request/Response Models
# ===========================================================================


class TestExportAPIModels:
    """Test export API request and response models."""

    def test_export_bundle_request_fields(self) -> None:
        """ExportBundleRequest has required fields."""
        request = ExportBundleRequest(
            incident_id="INC-001",
            bundle_type="evidence",
        )
        assert request.incident_id == "INC-001"
        assert request.bundle_type == "evidence"

    def test_export_bundle_request_optional_fields(self) -> None:
        """ExportBundleRequest has optional fields."""
        request = ExportBundleRequest(
            incident_id="INC-001",
            bundle_type="executive_debrief",
            export_reason="Monthly review",
            include_raw_steps=False,
            prepared_for="CEO",
        )
        assert request.export_reason == "Monthly review"
        assert request.include_raw_steps is False
        assert request.prepared_for == "CEO"

    def test_export_bundle_response_fields(self) -> None:
        """ExportBundleResponse has required fields."""
        response = ExportBundleResponse(
            bundle_id="EVD-abc123",
            bundle_type="evidence",
            created_at=datetime.now(timezone.utc),
            run_id="RUN-001",
        )
        assert response.bundle_id == "EVD-abc123"
        assert response.bundle_type == "evidence"

    def test_export_bundle_response_status(self) -> None:
        """ExportBundleResponse has status field."""
        response = ExportBundleResponse(
            bundle_id="EVD-abc123",
            bundle_type="evidence",
            created_at=datetime.now(timezone.utc),
            run_id="RUN-001",
            status="generating",
        )
        assert response.status == "generating"

    def test_export_bundle_response_download_url(self) -> None:
        """ExportBundleResponse has download_url field."""
        response = ExportBundleResponse(
            bundle_id="EVD-abc123",
            bundle_type="evidence",
            created_at=datetime.now(timezone.utc),
            run_id="RUN-001",
            download_url="https://example.com/bundles/EVD-abc123",
        )
        assert response.download_url is not None


# ===========================================================================
# Test: PolicyScope Model
# ===========================================================================


class TestPolicyScopeModel:
    """Test PolicyScope model for scope configuration."""

    def test_policy_scope_has_matches_method(self) -> None:
        """PolicyScope has matches method."""
        scope = PolicyScope(
            policy_id="POL-001",
            tenant_id="tenant-001",
            scope_type=ScopeType.ALL_RUNS.value,
        )
        assert hasattr(scope, "matches")
        assert callable(scope.matches)

    def test_all_runs_scope_matches_any_context(self) -> None:
        """ALL_RUNS scope matches any run context."""
        scope = PolicyScope(
            policy_id="POL-001",
            tenant_id="tenant-001",
            scope_type=ScopeType.ALL_RUNS.value,
        )
        # ALL_RUNS should match regardless of agent/key/human
        assert scope.matches() is True
        assert scope.matches(agent_id="any-agent") is True
        assert scope.matches(api_key_id="any-key") is True

    def test_agent_scope_matches_specific_agent(self) -> None:
        """AGENT scope matches specific agent_id."""
        # Use factory method to create properly configured scope
        scope = PolicyScope.create_agent_scope(
            policy_id="POL-001",
            tenant_id="tenant-001",
            agent_ids=["agent-001"],
        )
        assert scope.matches(agent_id="agent-001") is True
        assert scope.matches(agent_id="agent-002") is False

    def test_api_key_scope_matches_specific_key(self) -> None:
        """API_KEY scope matches specific api_key_id."""
        # Use factory method to create properly configured scope
        scope = PolicyScope.create_api_key_scope(
            policy_id="POL-001",
            tenant_id="tenant-001",
            api_key_ids=["key-001"],
        )
        assert scope.matches(api_key_id="key-001") is True
        assert scope.matches(api_key_id="key-002") is False

    def test_human_actor_scope_matches_specific_user(self) -> None:
        """HUMAN_ACTOR scope matches specific human_actor_id."""
        # Use factory method to create properly configured scope
        scope = PolicyScope.create_human_actor_scope(
            policy_id="POL-001",
            tenant_id="tenant-001",
            human_actor_ids=["user-001"],
        )
        assert scope.matches(human_actor_id="user-001") is True
        assert scope.matches(human_actor_id="user-002") is False
