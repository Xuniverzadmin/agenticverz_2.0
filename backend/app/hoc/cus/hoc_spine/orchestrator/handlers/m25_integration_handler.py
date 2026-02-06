# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: M25 Integration domain handler — routes M25 operations to L6 drivers via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.policies.L6_drivers (lazy)
# Forbidden Imports: L1, L2, L5, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), L2 first-principles purity
# artifact_class: CODE

"""
M25 Integration Handler (L4 Orchestrator)

Routes M25 integration domain operations to L6 drivers.
Registers operations:
  - m25.read_stages → get_loop_stages
  - m25.read_checkpoint → get_checkpoint
  - m25.read_stats → get integration stats (6 queries combined)
  - m25.read_simulation_state → get simulation state
  - m25.read_timeline → get prevention timeline data (4 queries combined)
  - m25.write_prevention → insert prevention record
  - m25.write_regret → insert regret event + upsert summary
  - m25.write_timeline_view → insert timeline view
  - m25.write_graduation_history → insert graduation history
  - m25.update_graduation_status → update graduation status
"""

from datetime import datetime
from typing import Any

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class M25ReadStagesHandler:
    """Handler for m25.read_stages operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_read_driver import (
            get_m25_integration_read_driver,
        )

        incident_id = ctx.params.get("incident_id")
        if not incident_id:
            return OperationResult.fail(
                "Missing 'incident_id' in params", "MISSING_PARAM"
            )

        driver = get_m25_integration_read_driver(ctx.session)
        stages = await driver.get_loop_stages(incident_id)

        return OperationResult.ok([
            {
                "stage": s.stage,
                "details": s.details,
                "failure_state": s.failure_state,
                "confidence_band": s.confidence_band,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in stages
        ])


class M25ReadCheckpointHandler:
    """Handler for m25.read_checkpoint operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_read_driver import (
            get_m25_integration_read_driver,
        )

        checkpoint_id = ctx.params.get("checkpoint_id")
        if not checkpoint_id:
            return OperationResult.fail(
                "Missing 'checkpoint_id' in params", "MISSING_PARAM"
            )

        driver = get_m25_integration_read_driver(ctx.session)
        checkpoint = await driver.get_checkpoint(checkpoint_id, ctx.tenant_id)

        if not checkpoint:
            return OperationResult.fail("Checkpoint not found", "NOT_FOUND")

        return OperationResult.ok({
            "id": checkpoint.id,
            "checkpoint_type": checkpoint.checkpoint_type,
            "incident_id": checkpoint.incident_id,
            "stage": checkpoint.stage,
            "target_id": checkpoint.target_id,
            "description": checkpoint.description,
            "options": checkpoint.options,
            "created_at": checkpoint.created_at.isoformat() if checkpoint.created_at else None,
            "resolved_at": checkpoint.resolved_at.isoformat() if checkpoint.resolved_at else None,
            "resolved_by": checkpoint.resolved_by,
            "resolution": checkpoint.resolution,
        })


class M25ReadStatsHandler:
    """Handler for m25.read_stats operation — combines all 6 stats queries."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_read_driver import (
            get_m25_integration_read_driver,
        )

        cutoff = ctx.params.get("cutoff")
        if not cutoff:
            return OperationResult.fail("Missing 'cutoff' in params", "MISSING_PARAM")

        # cutoff should be a datetime object
        if isinstance(cutoff, str):
            cutoff = datetime.fromisoformat(cutoff)

        driver = get_m25_integration_read_driver(ctx.session)

        loops = await driver.get_loop_stats(ctx.tenant_id, cutoff)
        patterns = await driver.get_pattern_stats(ctx.tenant_id, cutoff)
        recoveries = await driver.get_recovery_stats(ctx.tenant_id, cutoff)
        policies = await driver.get_policy_stats(cutoff)
        routing = await driver.get_routing_stats(cutoff)
        checkpoints = await driver.get_checkpoint_stats(ctx.tenant_id, cutoff)

        return OperationResult.ok({
            "loops": {
                "total": loops.total,
                "complete": loops.complete,
                "avg_time_ms": loops.avg_time_ms,
            },
            "patterns": {
                "total": patterns.total,
                "strong": patterns.strong,
                "weak": patterns.weak,
                "novel": patterns.novel,
            },
            "recoveries": {
                "total": recoveries.total,
                "applied": recoveries.applied,
                "rejected": recoveries.rejected,
            },
            "policies": {
                "total": policies.total,
                "shadow": policies.shadow,
                "active": policies.active,
            },
            "routing": {
                "total": routing.total,
                "rolled_back": routing.rolled_back,
            },
            "checkpoints": {
                "pending": checkpoints.pending,
                "resolved": checkpoints.resolved,
            },
        })


class M25ReadSimulationStateHandler:
    """Handler for m25.read_simulation_state operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_read_driver import (
            get_m25_integration_read_driver,
        )

        driver = get_m25_integration_read_driver(ctx.session)
        sim = await driver.get_simulation_state()

        return OperationResult.ok({
            "sim_gate1": sim.sim_gate1,
            "sim_gate2": sim.sim_gate2,
            "sim_gate3": sim.sim_gate3,
        })


class M25ReadTimelineHandler:
    """Handler for m25.read_timeline operation — combines incident + events + preventions + regrets."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_read_driver import (
            get_m25_integration_read_driver,
        )

        incident_id = ctx.params.get("incident_id")
        if not incident_id:
            return OperationResult.fail(
                "Missing 'incident_id' in params", "MISSING_PARAM"
            )

        driver = get_m25_integration_read_driver(ctx.session)

        incident = await driver.get_incident(incident_id)
        if not incident:
            return OperationResult.fail("Incident not found", "NOT_FOUND")

        if incident.tenant_id != ctx.tenant_id:
            return OperationResult.fail("Access denied", "FORBIDDEN")

        events = await driver.get_loop_events_for_timeline(incident_id)
        preventions = await driver.get_prevention_records(incident_id)
        regrets = await driver.get_regret_events_for_incident(incident_id)

        return OperationResult.ok({
            "incident": {
                "id": incident.id,
                "tenant_id": incident.tenant_id,
                "title": incident.title,
                "severity": incident.severity,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
            },
            "events": [
                {
                    "stage": e.stage,
                    "details": e.details,
                    "confidence_band": e.confidence_band,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
            "preventions": [
                {
                    "id": p.id,
                    "blocked_incident_id": p.blocked_incident_id,
                    "policy_id": p.policy_id,
                    "pattern_id": p.pattern_id,
                    "signature_match_confidence": p.signature_match_confidence,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in preventions
            ],
            "regrets": [
                {
                    "id": r.id,
                    "policy_id": r.policy_id,
                    "regret_type": r.regret_type,
                    "description": r.description,
                    "severity": r.severity,
                    "was_auto_rolled_back": r.was_auto_rolled_back,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in regrets
            ],
        })


class M25WritePreventionHandler:
    """Handler for m25.write_prevention operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_write_driver import (
            PreventionRecordInput,
            get_m25_integration_write_driver,
        )

        driver = get_m25_integration_write_driver(ctx.session)
        data = PreventionRecordInput(
            id=ctx.params["id"],
            policy_id=ctx.params["policy_id"],
            pattern_id=ctx.params["pattern_id"],
            original_incident_id=ctx.params["original_incident_id"],
            blocked_incident_id=ctx.params["blocked_incident_id"],
            tenant_id=ctx.tenant_id,
            confidence=ctx.params["confidence"],
            is_simulated=ctx.params.get("is_simulated", True),
        )
        await driver.insert_prevention_record(data)

        # L4 owns transaction boundary - commit after successful write
        if ctx.params.get("commit", True):
            await ctx.session.commit()

        return OperationResult.ok({"inserted": True})


class M25WriteRegretHandler:
    """Handler for m25.write_regret operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_write_driver import (
            RegretEventInput,
            get_m25_integration_write_driver,
        )

        driver = get_m25_integration_write_driver(ctx.session)
        data = RegretEventInput(
            id=ctx.params["id"],
            policy_id=ctx.params["policy_id"],
            tenant_id=ctx.tenant_id,
            regret_type=ctx.params["regret_type"],
            description=ctx.params["description"],
            severity=ctx.params["severity"],
            is_simulated=ctx.params.get("is_simulated", True),
        )
        await driver.insert_regret_event(data)

        # Also upsert policy regret summary
        score = ctx.params["severity"] * 0.5
        await driver.upsert_policy_regret_summary(ctx.params["policy_id"], score)

        # L4 owns transaction boundary - commit after successful write
        if ctx.params.get("commit", True):
            await ctx.session.commit()

        return OperationResult.ok({"inserted": True})


class M25WriteTimelineViewHandler:
    """Handler for m25.write_timeline_view operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_write_driver import (
            TimelineViewInput,
            get_m25_integration_write_driver,
        )

        driver = get_m25_integration_write_driver(ctx.session)
        data = TimelineViewInput(
            id=ctx.params["id"],
            incident_id=ctx.params["incident_id"],
            tenant_id=ctx.tenant_id,
            user_id=ctx.params["user_id"],
            has_prevention=ctx.params.get("has_prevention", False),
            has_rollback=ctx.params.get("has_rollback", False),
            is_simulated=ctx.params.get("is_simulated", False),
            session_id=ctx.params["session_id"],
        )
        await driver.insert_timeline_view(data)

        # L4 owns transaction boundary - commit after successful write
        if ctx.params.get("commit", True):
            await ctx.session.commit()

        return OperationResult.ok({"inserted": True})


class M25WriteGraduationHistoryHandler:
    """Handler for m25.write_graduation_history operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_write_driver import (
            GraduationHistoryInput,
            get_m25_integration_write_driver,
        )

        driver = get_m25_integration_write_driver(ctx.session)
        data = GraduationHistoryInput(
            level=ctx.params["level"],
            gates_json=ctx.params["gates_json"],
            is_degraded=ctx.params["is_degraded"],
            degraded_from=ctx.params.get("degraded_from"),
            degradation_reason=ctx.params.get("degradation_reason"),
            evidence_snapshot=ctx.params["evidence_snapshot"],
        )
        await driver.insert_graduation_history(data)

        # L4 owns transaction boundary - commit after successful write
        if ctx.params.get("commit", True):
            await ctx.session.commit()

        return OperationResult.ok({"inserted": True})


class M25UpdateGraduationStatusHandler:
    """Handler for m25.update_graduation_status operation."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.policies.L6_drivers.m25_integration_write_driver import (
            GraduationStatusUpdateInput,
            get_m25_integration_write_driver,
        )

        driver = get_m25_integration_write_driver(ctx.session)
        data = GraduationStatusUpdateInput(
            status_label=ctx.params["status_label"],
            is_graduated=ctx.params["is_graduated"],
            gate1_passed=ctx.params["gate1_passed"],
            gate2_passed=ctx.params["gate2_passed"],
            gate3_passed=ctx.params["gate3_passed"],
        )
        await driver.update_graduation_status(data)

        # L4 owns transaction boundary - commit after successful write
        if ctx.params.get("commit", True):
            await ctx.session.commit()

        return OperationResult.ok({"updated": True})


def register(registry: OperationRegistry) -> None:
    """Register M25 integration operations with the registry."""
    # Read operations
    registry.register("m25.read_stages", M25ReadStagesHandler())
    registry.register("m25.read_checkpoint", M25ReadCheckpointHandler())
    registry.register("m25.read_stats", M25ReadStatsHandler())
    registry.register("m25.read_simulation_state", M25ReadSimulationStateHandler())
    registry.register("m25.read_timeline", M25ReadTimelineHandler())
    # Write operations
    registry.register("m25.write_prevention", M25WritePreventionHandler())
    registry.register("m25.write_regret", M25WriteRegretHandler())
    registry.register("m25.write_timeline_view", M25WriteTimelineViewHandler())
    registry.register("m25.write_graduation_history", M25WriteGraduationHistoryHandler())
    registry.register("m25.update_graduation_status", M25UpdateGraduationStatusHandler())
