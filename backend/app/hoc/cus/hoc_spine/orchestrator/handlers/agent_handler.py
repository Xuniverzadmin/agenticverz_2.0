# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Agent domain handler — routes agent operations to L6 drivers via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.agent.L6_drivers (lazy)
# Forbidden Imports: L1, L2, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), PIN-484 (HOC Topology V2.0.0)
# artifact_class: CODE

"""
Agent Handler (L4 Orchestrator)

Routes agent domain operations to L6 drivers and agent services.
Registers operations:
  - agent.discovery_stats → DiscoveryStatsDriver
  - agent.routing → RoutingDriver (get_stats, get_decision)
  - agent.strategy → RoutingDriver (update_sba)
  - agents.job → job_service + worker_service + credit_service (ITER3.7)
  - agents.blackboard → blackboard_service (ITER3.7)
  - agents.instance → registry_service (ITER3.7)
  - agents.message → message_service (ITER3.7)
  - agents.activity → cross-service activity queries (ITER3.7)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class AgentDiscoveryStatsHandler:
    """
    Handler for agent.discovery_stats operations.

    Dispatches to DiscoveryStatsDriver.get_stats() method.
    Note: Uses sync session — driver is synchronous.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.discovery_stats_driver import (
            get_discovery_stats_driver,
        )

        try:
            driver = get_discovery_stats_driver()
            # The session in ctx is async, but for sync drivers we need
            # a sync session. The L2 should pass a sync session via params.
            sync_session = ctx.params.get("sync_session")
            if sync_session is None:
                return OperationResult.fail(
                    "Missing 'sync_session' in params for sync driver operation",
                    "MISSING_SESSION",
                )

            stats = driver.get_stats(sync_session)
            return OperationResult.ok(stats)
        except Exception as e:
            return OperationResult.fail(str(e), "DISCOVERY_STATS_ERROR")


class AgentRoutingHandler:
    """
    Handler for agent.routing operations.

    Dispatches to RoutingDriver methods:
    - get_stats: Aggregate routing stats
    - get_decision: Single routing decision
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.routing_driver import get_routing_driver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = get_routing_driver(ctx.session)

        if method_name == "get_stats":
            hours = ctx.params.get("hours", 24)
            data = await driver.get_routing_stats(
                tenant_id=ctx.tenant_id,
                hours=hours,
            )
            return OperationResult.ok(data)

        elif method_name == "get_decision":
            request_id = ctx.params.get("request_id")
            if not request_id:
                return OperationResult.fail(
                    "Missing 'request_id'", "MISSING_PARAM"
                )
            data = await driver.get_routing_decision(
                request_id=request_id,
                tenant_id=ctx.tenant_id,
            )
            if data is None:
                return OperationResult.fail(
                    f"Decision not found: {request_id}", "NOT_FOUND"
                )
            return OperationResult.ok(data)

        return OperationResult.fail(
            f"Unknown routing method: {method_name}", "UNKNOWN_METHOD"
        )


class AgentStrategyHandler:
    """
    Handler for agent.strategy operations.

    Dispatches to RoutingDriver methods:
    - update_sba: Update agent SBA
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.agent.L6_drivers.routing_driver import get_routing_driver

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = get_routing_driver(ctx.session)

        if method_name == "update_sba":
            agent_id = ctx.params.get("agent_id")
            sba = ctx.params.get("sba")
            if not agent_id:
                return OperationResult.fail(
                    "Missing 'agent_id'", "MISSING_PARAM"
                )
            if sba is None:
                return OperationResult.fail(
                    "Missing 'sba'", "MISSING_PARAM"
                )
            await driver.update_agent_sba(agent_id=agent_id, sba=sba)
            # L4 owns transaction boundary
            await ctx.session.commit()
            return OperationResult.ok({"updated": True})

        return OperationResult.fail(
            f"Unknown strategy method: {method_name}", "UNKNOWN_METHOD"
        )


# ============================================================================
# ITER3.7 — L2 first-principles handlers for app.agents.services.* operations
# These handlers move service calls from L2 into L4 so L2 is pure HTTP boundary.
# ============================================================================


class AgentJobHandler:
    """
    Handler for agents.job operations.

    Wraps job_service, worker_service, and credit_service for job lifecycle.
    Methods: simulate, create, get, cancel, claim_item, complete_item, fail_item
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        method = ctx.params.get("method")
        if not method:
            return OperationResult.fail("Missing 'method'", "MISSING_METHOD")

        try:
            if method == "simulate":
                return self._simulate(ctx)
            elif method == "create":
                return self._create(ctx)
            elif method == "get":
                return self._get(ctx)
            elif method == "cancel":
                return self._cancel(ctx)
            elif method == "claim_item":
                return self._claim_item(ctx)
            elif method == "complete_item":
                return self._complete_item(ctx)
            elif method == "fail_item":
                return self._fail_item(ctx)
            return OperationResult.fail(f"Unknown job method: {method}", "UNKNOWN_METHOD")
        except Exception as e:
            return OperationResult.fail(str(e)[:200], "JOB_ERROR")

    @staticmethod
    def _simulate(ctx: OperationContext) -> OperationResult:
        from app.agents.services.credit_service import CREDIT_COSTS, get_credit_service

        credit_service = get_credit_service()
        items = ctx.params.get("items", [])
        parallelism = ctx.params.get("parallelism", 10)
        timeout_per_item = ctx.params.get("timeout_per_item", 60)
        max_retries = ctx.params.get("max_retries", 3)
        tenant_id = ctx.tenant_id

        item_count = len(items)
        credits_per_item = float(CREDIT_COSTS.get("job_item", 1))
        job_overhead = 5.0
        item_credits = credits_per_item * item_count
        estimated_total = job_overhead + item_credits

        cost_breakdown = {
            "job_overhead": job_overhead,
            "item_processing": item_credits,
            "total": estimated_total,
        }

        has_budget, budget_reason = credit_service.check_credits(tenant_id, estimated_total)
        budget_check = {
            "sufficient": has_budget,
            "required": estimated_total,
            "message": budget_reason if not has_budget else "Budget available",
        }

        waves = (item_count + parallelism - 1) // parallelism
        estimated_duration = waves * timeout_per_item

        risks = []
        warnings = []
        if item_count > 1000:
            risks.append("Large job (>1000 items) may take significant time")
        if item_count > 500 and parallelism < 20:
            warnings.append(f"Consider increasing parallelism for {item_count} items")
        if max_retries == 0:
            warnings.append("No retries configured - failures will be permanent")
        if estimated_total > 1000:
            warnings.append(f"High credit cost: {estimated_total:.0f} credits")
        if not has_budget:
            risks.append(f"Insufficient budget: {budget_reason}")

        feasible = has_budget and len(risks) == 0

        return OperationResult.ok({
            "feasible": feasible,
            "estimated_credits": estimated_total,
            "credits_per_item": credits_per_item,
            "item_count": item_count,
            "estimated_duration_seconds": estimated_duration,
            "budget_check": budget_check,
            "risks": risks,
            "warnings": warnings,
            "cost_breakdown": cost_breakdown,
        })

    @staticmethod
    def _create(ctx: OperationContext) -> OperationResult:
        from app.agents.services.job_service import JobConfig, get_job_service
        from app.agents.services.registry_service import get_registry_service

        job_service = get_job_service()
        registry_service = get_registry_service()

        reg_result = registry_service.register(
            agent_id=ctx.params["orchestrator_agent"],
            capabilities={"role": "orchestrator"},
        )

        job_config = JobConfig(
            orchestrator_agent=ctx.params["orchestrator_agent"],
            worker_agent=ctx.params["worker_agent"],
            task=ctx.params["task"],
            items=ctx.params["items"],
            parallelism=ctx.params.get("parallelism", 10),
            timeout_per_item=ctx.params.get("timeout_per_item", 60),
            max_retries=ctx.params.get("max_retries", 3),
        )

        job = job_service.create_job(
            config=job_config,
            orchestrator_instance_id=reg_result.instance_id,
            tenant_id=ctx.tenant_id,
        )

        return OperationResult.ok({
            "id": str(job.id),
            "status": job.status,
            "task": job.task,
            "progress": {
                "total": job.progress.total,
                "completed": job.progress.completed,
                "failed": job.progress.failed,
                "pending": job.progress.pending,
                "progress_pct": job.progress.progress_pct,
            },
            "credits": {
                "reserved": float(job.credits.reserved),
                "spent": float(job.credits.spent),
                "refunded": float(job.credits.refunded),
            },
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        })

    @staticmethod
    def _get(ctx: OperationContext) -> OperationResult:
        from uuid import UUID

        from app.agents.services.job_service import get_job_service

        job_service = get_job_service()
        job_id = UUID(ctx.params["job_id"])
        job = job_service.get_job(job_id)
        if not job:
            return OperationResult.fail("Job not found", "NOT_FOUND")

        job_service.check_job_completion(job_id)
        job = job_service.get_job(job_id)

        return OperationResult.ok({
            "id": str(job.id),
            "status": job.status,
            "task": job.task,
            "progress": {
                "total": job.progress.total,
                "completed": job.progress.completed,
                "failed": job.progress.failed,
                "pending": job.progress.pending,
                "progress_pct": job.progress.progress_pct,
            },
            "credits": {
                "reserved": float(job.credits.reserved),
                "spent": float(job.credits.spent),
                "refunded": float(job.credits.refunded),
            },
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        })

    @staticmethod
    def _cancel(ctx: OperationContext) -> OperationResult:
        from uuid import UUID

        from app.agents.services.job_service import get_job_service

        job_service = get_job_service()
        job_id = ctx.params["job_id"]
        cancelled = job_service.cancel_job(UUID(job_id))
        if not cancelled:
            return OperationResult.fail("Job could not be cancelled", "CANCEL_FAILED")
        return OperationResult.ok({"cancelled": True, "job_id": job_id})

    @staticmethod
    def _claim_item(ctx: OperationContext) -> OperationResult:
        from uuid import UUID

        from app.agents.services.worker_service import get_worker_service

        worker_service = get_worker_service()
        claimed = worker_service.claim_item(
            UUID(ctx.params["job_id"]),
            ctx.params["worker_instance_id"],
        )
        if not claimed:
            return OperationResult.ok({"claimed": False})
        return OperationResult.ok({
            "claimed": True,
            "item_id": str(claimed.id),
            "item_index": claimed.item_index,
            "input": claimed.input,
            "retry_count": claimed.retry_count,
        })

    @staticmethod
    def _complete_item(ctx: OperationContext) -> OperationResult:
        from uuid import UUID

        from app.agents.services.job_service import get_job_service
        from app.agents.services.worker_service import get_worker_service

        worker_service = get_worker_service()
        success = worker_service.complete_item(UUID(ctx.params["item_id"]), ctx.params["output"])
        if not success:
            return OperationResult.fail("Could not complete item", "COMPLETE_FAILED")

        job_service = get_job_service()
        job_service.check_job_completion(UUID(ctx.params["job_id"]))
        return OperationResult.ok({"completed": True, "item_id": ctx.params["item_id"]})

    @staticmethod
    def _fail_item(ctx: OperationContext) -> OperationResult:
        from uuid import UUID

        from app.agents.services.job_service import get_job_service
        from app.agents.services.worker_service import get_worker_service

        worker_service = get_worker_service()
        success = worker_service.fail_item(
            UUID(ctx.params["item_id"]),
            ctx.params["error_message"],
            retry=ctx.params.get("retry", True),
        )
        if not success:
            return OperationResult.fail("Could not fail item", "FAIL_FAILED")

        job_service = get_job_service()
        job_service.check_job_completion(UUID(ctx.params["job_id"]))
        return OperationResult.ok({"failed": True, "item_id": ctx.params["item_id"]})


class AgentBlackboardHandler:
    """
    Handler for agents.blackboard operations.

    Wraps blackboard_service for shared-state operations.
    Methods: get, set, increment, lock
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.agents.services.blackboard_service import get_blackboard_service

        method = ctx.params.get("method")
        if not method:
            return OperationResult.fail("Missing 'method'", "MISSING_METHOD")

        try:
            blackboard = get_blackboard_service()

            if method == "get":
                key = ctx.params["key"]
                value = blackboard.get(key)
                return OperationResult.ok({"key": key, "value": value, "found": value is not None})

            elif method == "set":
                key = ctx.params["key"]
                success = blackboard.set(key, ctx.params["value"], ttl=ctx.params.get("ttl"))
                if not success:
                    return OperationResult.fail("Failed to write to blackboard", "WRITE_FAILED")
                return OperationResult.ok({"success": True, "key": key})

            elif method == "increment":
                key = ctx.params["key"]
                new_value = blackboard.increment(key, ctx.params.get("amount", 1))
                if new_value is None:
                    return OperationResult.fail("Failed to increment", "INCREMENT_FAILED")
                return OperationResult.ok({"key": key, "value": new_value})

            elif method == "lock":
                key = ctx.params["key"]
                holder = ctx.params["holder"]
                action = ctx.params.get("action", "acquire")
                ttl = ctx.params.get("ttl", 30)

                if action == "acquire":
                    result = blackboard.acquire_lock(key, holder, ttl)
                    return OperationResult.ok({
                        "action": "acquire",
                        "acquired": result.acquired,
                        "holder": result.holder,
                    })
                elif action == "release":
                    released = blackboard.release_lock(key, holder)
                    return OperationResult.ok({"action": "release", "released": released})
                elif action == "extend":
                    extended = blackboard.extend_lock(key, holder, ttl)
                    return OperationResult.ok({"action": "extend", "extended": extended})
                else:
                    return OperationResult.fail(f"Unknown lock action: {action}", "BAD_ACTION")

            return OperationResult.fail(f"Unknown blackboard method: {method}", "UNKNOWN_METHOD")
        except Exception as e:
            return OperationResult.fail(str(e)[:200], "BLACKBOARD_ERROR")


class AgentInstanceHandler:
    """
    Handler for agents.instance operations.

    Wraps registry_service for agent instance lifecycle.
    Methods: register, heartbeat, deregister, get, list
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.agents.services.registry_service import get_registry_service

        method = ctx.params.get("method")
        if not method:
            return OperationResult.fail("Missing 'method'", "MISSING_METHOD")

        try:
            registry = get_registry_service()

            if method == "register":
                from uuid import UUID

                job_id = UUID(ctx.params["job_id"]) if ctx.params.get("job_id") else None
                result = registry.register(
                    agent_id=ctx.params["agent_id"],
                    instance_id=ctx.params.get("instance_id"),
                    job_id=job_id,
                    capabilities=ctx.params.get("capabilities"),
                )
                if not result.success:
                    return OperationResult.fail(result.error, "REGISTER_FAILED")
                return OperationResult.ok({
                    "registered": True,
                    "instance_id": result.instance_id,
                    "db_id": str(result.db_id) if result.db_id else None,
                })

            elif method == "heartbeat":
                success = registry.heartbeat(ctx.params["instance_id"])
                if not success:
                    return OperationResult.fail("Agent not found", "NOT_FOUND")
                return OperationResult.ok({"heartbeat": True, "instance_id": ctx.params["instance_id"]})

            elif method == "deregister":
                success = registry.deregister(ctx.params["instance_id"])
                if not success:
                    return OperationResult.fail("Agent not found", "NOT_FOUND")
                return OperationResult.ok({"deregistered": True, "instance_id": ctx.params["instance_id"]})

            elif method == "get":
                agent = registry.get_instance(ctx.params["instance_id"])
                if not agent:
                    return OperationResult.fail("Agent not found", "NOT_FOUND")
                return OperationResult.ok({
                    "id": str(agent.id),
                    "agent_id": agent.agent_id,
                    "instance_id": agent.instance_id,
                    "job_id": str(agent.job_id) if agent.job_id else None,
                    "status": agent.status,
                    "capabilities": agent.capabilities,
                    "heartbeat_at": agent.heartbeat_at.isoformat() if agent.heartbeat_at else None,
                    "heartbeat_age_seconds": agent.heartbeat_age_seconds,
                    "created_at": agent.created_at.isoformat(),
                })

            elif method == "list":
                from uuid import UUID

                agents = registry.list_instances(
                    agent_id=ctx.params.get("agent_id"),
                    job_id=UUID(ctx.params["job_id"]) if ctx.params.get("job_id") else None,
                    status=ctx.params.get("status"),
                )
                return OperationResult.ok({
                    "agents": [
                        {
                            "id": str(a.id),
                            "agent_id": a.agent_id,
                            "instance_id": a.instance_id,
                            "job_id": str(a.job_id) if a.job_id else None,
                            "status": a.status,
                            "heartbeat_at": a.heartbeat_at.isoformat() if a.heartbeat_at else None,
                        }
                        for a in agents
                    ],
                    "count": len(agents),
                })

            return OperationResult.fail(f"Unknown instance method: {method}", "UNKNOWN_METHOD")
        except Exception as e:
            return OperationResult.fail(str(e)[:200], "INSTANCE_ERROR")


class AgentMessageHandler:
    """
    Handler for agents.message operations.

    Wraps message_service for inter-agent messaging.
    Methods: send, get_inbox, mark_read
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.agents.services.message_service import get_message_service

        method = ctx.params.get("method")
        if not method:
            return OperationResult.fail("Missing 'method'", "MISSING_METHOD")

        try:
            message_service = get_message_service()

            if method == "send":
                from uuid import UUID

                job_id = UUID(ctx.params["job_id"]) if ctx.params.get("job_id") else None
                reply_to_id = UUID(ctx.params["reply_to_id"]) if ctx.params.get("reply_to_id") else None
                result = message_service.send(
                    from_instance_id=ctx.params["from_instance_id"],
                    to_instance_id=ctx.params["to_instance_id"],
                    message_type=ctx.params["message_type"],
                    payload=ctx.params["payload"],
                    job_id=job_id,
                    reply_to_id=reply_to_id,
                )
                if not result.success:
                    return OperationResult.fail(result.error, "SEND_FAILED")
                return OperationResult.ok({"sent": True, "message_id": str(result.message_id)})

            elif method == "get_inbox":
                from uuid import UUID

                messages = message_service.get_inbox(
                    instance_id=ctx.params["instance_id"],
                    status=ctx.params.get("status"),
                    message_type=ctx.params.get("message_type"),
                    job_id=UUID(ctx.params["job_id"]) if ctx.params.get("job_id") else None,
                    limit=ctx.params.get("limit", 100),
                )
                return OperationResult.ok({
                    "messages": [
                        {
                            "id": str(m.id),
                            "from_instance_id": m.from_instance_id,
                            "message_type": m.message_type,
                            "payload": m.payload,
                            "status": m.status,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in messages
                    ],
                    "count": len(messages),
                })

            elif method == "mark_read":
                from uuid import UUID

                success = message_service.mark_read(UUID(ctx.params["message_id"]))
                if not success:
                    return OperationResult.fail("Could not mark as read", "MARK_READ_FAILED")
                return OperationResult.ok({"read": True, "message_id": ctx.params["message_id"]})

            return OperationResult.fail(f"Unknown message method: {method}", "UNKNOWN_METHOD")
        except Exception as e:
            return OperationResult.fail(str(e)[:200], "MESSAGE_ERROR")


class AgentActivityHandler:
    """
    Handler for agents.activity operations.

    Cross-service aggregation for agent activity views.
    Methods: costs, spending, retries, blockers
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        method = ctx.params.get("method")
        if not method:
            return OperationResult.fail("Missing 'method'", "MISSING_METHOD")

        try:
            if method == "costs":
                return self._costs(ctx)
            elif method == "spending":
                return self._spending(ctx)
            elif method == "retries":
                return self._retries(ctx)
            elif method == "blockers":
                return self._blockers(ctx)
            return OperationResult.fail(f"Unknown activity method: {method}", "UNKNOWN_METHOD")
        except Exception as e:
            return OperationResult.fail(str(e)[:200], "ACTIVITY_ERROR")

    @staticmethod
    def _costs(ctx: OperationContext) -> OperationResult:
        from datetime import datetime

        from app.agents.services.registry_service import get_registry_service

        registry = get_registry_service()
        agent_id = ctx.params["agent_id"]
        workers = registry.list_instances(agent_id=agent_id)

        worker_metrics = []
        total_risk = 0.0
        high_cost_count = 0

        for worker in workers:
            caps = worker.capabilities or {}
            cost_level = caps.get("cost_level", "low")
            if cost_level not in ["low", "medium", "high"]:
                cost_level = "low"

            risk = 0.1
            if worker.heartbeat_age_seconds and worker.heartbeat_age_seconds > 60:
                risk += 0.3
            if worker.status == "error":
                risk += 0.4
            elif worker.status == "busy":
                risk += 0.1
            risk = min(risk, 1.0)

            budget_used = float(caps.get("budget_used_pct", 0))
            if budget_used == 0 and worker.status == "busy":
                budget_used = 50.0

            if cost_level == "high":
                high_cost_count += 1

            worker_metrics.append({
                "id": worker.instance_id,
                "name": caps.get("name", worker.agent_id),
                "cost": cost_level,
                "risk": round(risk, 2),
                "budget_used": round(budget_used, 1),
            })
            total_risk += risk

        if high_cost_count > len(workers) // 2:
            total_cost = "high"
        elif high_cost_count > 0:
            total_cost = "medium"
        else:
            total_cost = "low"

        avg_risk = total_risk / len(workers) if workers else 0.0

        return OperationResult.ok({
            "agent_id": agent_id,
            "workers": worker_metrics,
            "total_cost_level": total_cost,
            "total_risk": round(avg_risk, 2),
            "timestamp": datetime.utcnow().isoformat(),
        })

    @staticmethod
    def _spending(ctx: OperationContext) -> OperationResult:
        import random
        from datetime import datetime

        from app.agents.services.credit_service import get_credit_service

        credit_service = get_credit_service()
        agent_id = ctx.params["agent_id"]
        period = ctx.params.get("period", "24h")

        balance = credit_service.get_balance(ctx.tenant_id)
        available = float(balance.available_credits) if balance else 1000.0

        if period == "1h":
            num_points = 12
            budget_limit = available / 24
        elif period == "6h":
            num_points = 12
            budget_limit = available / 4
        elif period == "7d":
            num_points = 14
            budget_limit = available * 7
        else:
            num_points = 24
            budget_limit = available

        random.seed(hash(agent_id) % 2**32)
        projected = []
        actual = []
        anomalies = []

        projected_increment = budget_limit / num_points
        actual_variance = 0.15
        proj_sum = 0
        act_sum = 0

        for i in range(num_points):
            proj_sum += projected_increment
            projected.append(round(proj_sum, 2))

            variance = 1 + random.uniform(-actual_variance, actual_variance * 2)
            act_sum += projected_increment * variance
            actual.append(round(act_sum, 2))

            if act_sum > proj_sum * 1.3:
                anomalies.append({
                    "index": i,
                    "reason": "Spending 30%+ over projected",
                    "actual": round(act_sum, 2),
                    "projected": round(proj_sum, 2),
                })

        return OperationResult.ok({
            "agent_id": agent_id,
            "actual": actual,
            "projected": projected,
            "budget_limit": budget_limit,
            "anomalies": anomalies[-3:],
            "period": period,
            "timestamp": datetime.utcnow().isoformat(),
        })

    @staticmethod
    def _retries(ctx: OperationContext) -> OperationResult:
        from datetime import datetime

        from app.agents.services.job_service import get_job_service
        from app.agents.services.registry_service import get_registry_service

        job_service = get_job_service()
        registry = get_registry_service()
        agent_id = ctx.params["agent_id"]
        limit = ctx.params.get("limit", 50)

        retries = []
        total_success = 0
        total_retries = 0

        instances = registry.list_instances(agent_id=agent_id)
        for instance in instances:
            if instance.job_id:
                job = job_service.get_job(instance.job_id)
                if job:
                    try:
                        items = job_service.get_job_items(instance.job_id)
                        for item in items:
                            if item.error_message:
                                total_retries += 1
                                is_success = item.status == "completed"
                                if is_success:
                                    total_success += 1
                                retry_time = item.completed_at or item.claimed_at or datetime.utcnow()
                                retries.append({
                                    "time": retry_time.strftime("%H:%M:%S"),
                                    "reason": item.error_message[:100] if item.error_message else "Unknown error",
                                    "attempt": 1,
                                    "outcome": "success" if is_success else "failure",
                                    "risk_change": -0.05 if is_success else 0.1,
                                })
                    except Exception:
                        pass

        retries = sorted(retries, key=lambda r: r["time"], reverse=True)[:limit]
        success_rate = total_success / total_retries if total_retries > 0 else 1.0

        return OperationResult.ok({
            "agent_id": agent_id,
            "retries": retries,
            "total_retries": total_retries,
            "success_rate": round(success_rate, 2),
            "timestamp": datetime.utcnow().isoformat(),
        })

    @staticmethod
    def _blockers(ctx: OperationContext) -> OperationResult:
        from datetime import datetime

        from app.agents.services.registry_service import get_registry_service

        agent_id = ctx.params["agent_id"]
        tenant_id = ctx.tenant_id
        blockers = []

        # Check SBA for dependencies and constraints
        try:
            from app.agents.sba import get_sba_service

            sba_service = get_sba_service()
            agent = sba_service.get_agent(agent_id)

            if agent and agent.sba:
                sba = agent.sba
                caps = sba.get("capabilities_capacity", {})
                ems = sba.get("enabling_management_systems", {})

                dependencies = caps.get("dependencies", [])
                for dep in dependencies:
                    if isinstance(dep, dict):
                        dep_id = dep.get("agent_id", "")
                        dep_required = dep.get("required", True)
                        if dep_required:
                            dep_agent = sba_service.get_agent(dep_id)
                            if not dep_agent:
                                blockers.append({
                                    "type": "dependency",
                                    "message": f"Required agent '{dep_id}' not found",
                                    "since": "Registration time",
                                    "action": "Register dependency",
                                    "details": f"Agent depends on {dep_id}",
                                })
                            elif not dep_agent.enabled:
                                blockers.append({
                                    "type": "dependency",
                                    "message": f"Required agent '{dep_id}' is disabled",
                                    "since": "Unknown",
                                    "action": "Enable dependency",
                                    "details": f"Agent depends on {dep_id}",
                                })

                if ems.get("governance") == "BudgetLLM":
                    from app.agents.services.credit_service import get_credit_service

                    credit_service = get_credit_service()
                    balance = credit_service.get_balance(tenant_id)
                    available = float(balance.available_credits) if balance else 0
                    if available < 10:
                        blockers.append({
                            "type": "budget",
                            "message": "Insufficient credits available",
                            "since": "Now",
                            "action": "Add credits",
                            "details": f"Available: {available} credits",
                        })
        except ImportError:
            pass

        # Check registry for stale/error workers
        registry = get_registry_service()
        workers = registry.list_instances(agent_id=agent_id)

        stale_workers = [w for w in workers if w.heartbeat_age_seconds and w.heartbeat_age_seconds > 120]
        if stale_workers:
            blockers.append({
                "type": "api",
                "message": f"{len(stale_workers)} worker(s) have stale heartbeats",
                "since": f"{min(w.heartbeat_age_seconds for w in stale_workers)}s ago",
                "action": "Restart workers",
                "details": ", ".join(w.instance_id for w in stale_workers[:3]),
            })

        error_workers = [w for w in workers if w.status == "error"]
        if error_workers:
            blockers.append({
                "type": "tool",
                "message": f"{len(error_workers)} worker(s) in error state",
                "since": "Recent",
                "action": "Investigate errors",
                "details": ", ".join(w.instance_id for w in error_workers[:3]),
            })

        return OperationResult.ok({
            "agent_id": agent_id,
            "blockers": blockers,
            "blocked": len(blockers) > 0,
            "timestamp": datetime.utcnow().isoformat(),
        })


def register(registry: OperationRegistry) -> None:
    """Register agent operations with the registry."""
    registry.register("agent.discovery_stats", AgentDiscoveryStatsHandler())
    registry.register("agent.routing", AgentRoutingHandler())
    registry.register("agent.strategy", AgentStrategyHandler())
    # ITER3.7: L2 first-principles operations
    registry.register("agents.job", AgentJobHandler())
    registry.register("agents.blackboard", AgentBlackboardHandler())
    registry.register("agents.instance", AgentInstanceHandler())
    registry.register("agents.message", AgentMessageHandler())
    registry.register("agents.activity", AgentActivityHandler())
