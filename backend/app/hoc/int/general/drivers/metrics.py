# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time, runtime increment
#   Execution: sync
# Role: Prometheus metrics definitions and multiprocess support
# Callers: All modules that emit metrics
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Observability

"""
Prometheus metrics for NOVA Agent Manager.

Supports multiprocess mode via PROMETHEUS_MULTIPROC_DIR environment variable.
When set, uses a shared directory for metric aggregation across processes.
"""

import os

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)

# Check if multiprocess mode is enabled
MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR")


def get_registry() -> CollectorRegistry:
    """Get the appropriate registry for the current mode."""
    if MULTIPROC_DIR:
        # Multiprocess mode: create a new registry and merge from all workers
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    return REGISTRY


def generate_metrics() -> bytes:
    """Generate metrics output for /metrics endpoint."""
    return generate_latest(get_registry())


def get_content_type() -> str:
    """Get the content type for metrics response."""
    return CONTENT_TYPE_LATEST


# Run metrics - with planner label for tracking different planners
nova_runs_total = Counter("nova_runs_total", "Total runs processed", ["status", "planner"])
nova_runs_failed_total = Counter("nova_runs_failed_total", "Total failed runs")

# Skill-level metrics
nova_skill_attempts_total = Counter("nova_skill_attempts_total", "Skill executions", ["skill"])

nova_skill_duration_seconds = Histogram("nova_skill_duration_seconds", "Skill execution duration (seconds)", ["skill"])

# Worker pool gauge
nova_worker_pool_size = Gauge("nova_worker_pool_size", "Configured worker pool concurrency")

# Queue depth gauge
nova_runs_queued = Gauge("nova_runs_queued", "Number of runs currently queued or retrying")

# =====================
# LLM Metrics (M11 - with tenant/agent labels for billing & throttling)
# =====================

# Token usage counters - by tenant/agent for billing
nova_llm_tokens_total = Counter(
    "nova_llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "model", "token_type", "tenant_id", "agent_id"],  # token_type: input, output
)

# Cost tracking - by tenant for billing
nova_llm_cost_cents_total = Counter(
    "nova_llm_cost_cents_total", "Total LLM cost in cents", ["provider", "model", "tenant_id", "agent_id"]
)

# LLM invocation latency - by tenant for throttling
nova_llm_duration_seconds = Histogram(
    "nova_llm_duration_seconds",
    "LLM invocation latency (seconds)",
    ["provider", "model", "tenant_id"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# LLM invocation counter - by tenant/agent for throttling
nova_llm_invocations_total = Counter(
    "nova_llm_invocations_total",
    "Total LLM invocations",
    ["provider", "model", "status", "tenant_id", "agent_id"],  # status: success, error
)

# Tenant-level rate limit gauge
nova_llm_tenant_rate_limit = Gauge(
    "nova_llm_tenant_rate_limit", "Current rate limit (requests per minute) for tenant", ["tenant_id"]
)

# Tenant-level budget remaining gauge
nova_llm_tenant_budget_remaining_cents = Gauge(
    "nova_llm_tenant_budget_remaining_cents", "Remaining LLM budget in cents for tenant", ["tenant_id"]
)

# =====================
# Planner Metrics
# =====================

# Planner latency
nova_planner_duration_seconds = Histogram(
    "nova_planner_duration_seconds",
    "Planner latency (seconds)",
    ["planner"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# Plans generated
nova_plans_generated_total = Counter(
    "nova_plans_generated_total",
    "Total plans generated",
    ["planner", "status"],  # status: success, fallback, stub, error
)

# Plan step counts
nova_plan_steps_total = Counter("nova_plan_steps_total", "Total plan steps generated", ["planner"])

# =====================
# M10 Recovery Metrics
# =====================

# Recovery suggestion counters
recovery_suggestions_total = Counter(
    "recovery_suggestions_total", "Total recovery suggestions generated", ["source", "decision"]
)

recovery_suggestions_latency_seconds = Histogram(
    "recovery_suggestions_latency_seconds",
    "Recovery suggestion generation latency (seconds)",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# Recovery approval counters
recovery_approvals_total = Counter(
    "recovery_approvals_total", "Total recovery candidate approvals/rejections", ["decision"]
)

# Recovery candidate gauge
recovery_candidates_pending = Gauge(
    "recovery_candidates_pending", "Number of pending recovery candidates awaiting review"
)

# =====================
# M10 Ingest Metrics
# =====================

# Ingest request counters
recovery_ingest_total = Counter(
    "recovery_ingest_total",
    "Total recovery ingest requests",
    ["status", "source"],  # status: accepted, duplicate, error
)

# Ingest latency histogram
recovery_ingest_latency_seconds = Histogram(
    "recovery_ingest_latency_seconds",
    "Recovery ingest endpoint latency (seconds)",
    ["status"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

# Duplicate detection counters
recovery_ingest_duplicates_total = Counter(
    "recovery_ingest_duplicates_total",
    "Total duplicate ingests detected",
    ["detection_method"],  # idempotency_key, failure_match_id, integrity_error
)

# Enqueue success/failure
recovery_ingest_enqueue_total = Counter(
    "recovery_ingest_enqueue_total",
    "Total enqueue attempts for evaluation",
    ["status"],  # success, failed, skipped
)

# Queue depth gauge (Redis-based)
recovery_evaluation_queue_depth = Gauge("recovery_evaluation_queue_depth", "Number of candidates in evaluation queue")

# =====================
# M10 Queue & Worker Metrics
# =====================

# Redis stream metrics
recovery_stream_length = Gauge("recovery_stream_length", "Number of messages in Redis evaluation stream")

recovery_stream_pending = Gauge("recovery_stream_pending", "Number of pending (unacknowledged) messages in stream")

recovery_stream_consumers = Gauge("recovery_stream_consumers", "Number of active stream consumers")

# DB fallback queue metrics
recovery_db_queue_depth = Gauge("recovery_db_queue_depth", "Number of items in DB fallback queue")

recovery_db_queue_stalled = Gauge(
    "recovery_db_queue_stalled", "Number of stalled items in DB queue (claimed but not processed)"
)

# Worker metrics
recovery_worker_claimed_total = Counter(
    "recovery_worker_claimed_total",
    "Total work items claimed by workers",
    ["source"],  # redis_stream, db_queue
)

recovery_worker_processed_total = Counter(
    "recovery_worker_processed_total",
    "Total work items processed by workers",
    ["status", "source"],  # status: success, failed
)

recovery_worker_processing_seconds = Histogram(
    "recovery_worker_processing_seconds",
    "Work item processing duration (seconds)",
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# =====================
# M10 Matview Freshness Metrics
# =====================

recovery_matview_last_refresh_timestamp = Gauge(
    "recovery_matview_last_refresh_timestamp", "Unix timestamp of last successful matview refresh", ["view_name"]
)

recovery_matview_refresh_duration_seconds = Histogram(
    "recovery_matview_refresh_duration_seconds",
    "Matview refresh duration (seconds)",
    ["view_name"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

recovery_matview_refresh_total = Counter(
    "recovery_matview_refresh_total",
    "Total matview refresh attempts",
    ["view_name", "status"],  # status: success, failed
)

recovery_matview_age_seconds = Gauge(
    "recovery_matview_age_seconds", "Age of matview since last refresh (seconds)", ["view_name"]
)

# Dead-letter stream metrics
recovery_dead_letter_length = Gauge("recovery_dead_letter_length", "Number of messages in the dead-letter stream")

recovery_dead_letter_added_total = Counter(
    "recovery_dead_letter_added_total", "Total messages moved to dead-letter stream", ["reason"]
)

recovery_dead_letter_replayed_total = Counter(
    "recovery_dead_letter_replayed_total", "Total messages replayed from dead-letter stream"
)

# =====================
# M10 Phase 6: Lock, Archive, Outbox Metrics
# =====================

# Distributed lock metrics
m10_lock_acquired_total = Counter("m10_lock_acquired_total", "Total distributed lock acquisitions", ["lock_name"])

m10_lock_failed_total = Counter(
    "m10_lock_failed_total", "Total distributed lock acquisition failures (contention)", ["lock_name"]
)

m10_lock_released_total = Counter("m10_lock_released_total", "Total distributed lock releases", ["lock_name"])

m10_lock_duration_seconds = Histogram(
    "m10_lock_duration_seconds",
    "Duration lock was held (seconds)",
    ["lock_name"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

m10_lock_active = Gauge("m10_lock_active", "Number of currently held locks", ["lock_name"])

# Dead-letter archive metrics
m10_archive_total = Counter(
    "m10_archive_total",
    "Total dead-letter messages archived to DB",
    ["source"],  # stream_trim, manual, replay_skip
)

m10_archive_size = Gauge("m10_archive_size", "Total rows in dead_letter_archive table")

m10_archive_retention_deleted_total = Counter(
    "m10_archive_retention_deleted_total", "Total archive rows deleted by retention cleanup"
)

# Replay log metrics
m10_replay_log_size = Gauge("m10_replay_log_size", "Total rows in replay_log table")

m10_replay_log_retention_deleted_total = Counter(
    "m10_replay_log_retention_deleted_total", "Total replay_log rows deleted by retention cleanup"
)

# Outbox metrics
m10_outbox_published_total = Counter(
    "m10_outbox_published_total", "Total events published to outbox", ["aggregate_type", "event_type"]
)

m10_outbox_processed_total = Counter(
    "m10_outbox_processed_total", "Total outbox events processed successfully", ["aggregate_type", "event_type"]
)

m10_outbox_failed_total = Counter(
    "m10_outbox_failed_total", "Total outbox events that failed processing", ["aggregate_type", "event_type"]
)

m10_outbox_pending = Gauge("m10_outbox_pending", "Number of pending (unprocessed) outbox events")

m10_outbox_processing_seconds = Histogram(
    "m10_outbox_processing_seconds",
    "Outbox event processing duration (seconds)",
    ["event_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

m10_outbox_retry_count = Histogram(
    "m10_outbox_retry_count", "Number of retries before outbox event succeeded", buckets=(0, 1, 2, 3, 4, 5)
)

m10_outbox_lag_seconds = Gauge("m10_outbox_lag_seconds", "Age of oldest unprocessed outbox event (seconds)")

# Reclaim GC metrics
m10_reclaim_gc_cleaned_total = Counter(
    "m10_reclaim_gc_cleaned_total", "Total stale reclaim attempt entries cleaned by GC"
)

m10_reclaim_gc_checked_total = Counter("m10_reclaim_gc_checked_total", "Total entries checked by reclaim GC")

# =====================
# M11 Skill Execution Metrics
# =====================

# Skill execution counters (extends nova_skill_attempts_total with more labels)
m11_skill_executions_total = Counter(
    "m11_skill_executions_total",
    "Total M11 skill executions",
    ["skill", "status", "tenant_id"],  # status: ok, error, stubbed, circuit_open
)

m11_skill_execution_seconds = Histogram(
    "m11_skill_execution_seconds",
    "M11 skill execution latency (seconds)",
    ["skill"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# Idempotency metrics
m11_skill_idempotency_hits_total = Counter(
    "m11_skill_idempotency_hits_total", "Total idempotency cache hits (duplicate requests)", ["skill"]
)

m11_skill_idempotency_conflicts_total = Counter(
    "m11_skill_idempotency_conflicts_total", "Total idempotency conflicts (same key, different params)", ["skill"]
)

# =====================
# M11 Circuit Breaker Metrics
# =====================

m11_circuit_breaker_state = Gauge(
    "m11_circuit_breaker_state", "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)", ["target"]
)

m11_circuit_breaker_failures_total = Counter(
    "m11_circuit_breaker_failures_total", "Total failures recorded by circuit breaker", ["target"]
)

m11_circuit_breaker_successes_total = Counter(
    "m11_circuit_breaker_successes_total", "Total successes recorded by circuit breaker", ["target"]
)

m11_circuit_breaker_opens_total = Counter(
    "m11_circuit_breaker_opens_total", "Total times circuit breaker opened", ["target"]
)

m11_circuit_breaker_closes_total = Counter(
    "m11_circuit_breaker_closes_total", "Total times circuit breaker closed (recovered)", ["target"]
)

m11_circuit_breaker_rejected_total = Counter(
    "m11_circuit_breaker_rejected_total", "Total requests rejected due to open circuit", ["target"]
)

# =====================
# M11 Replay & Audit Metrics
# =====================

m11_audit_ops_total = Counter(
    "m11_audit_ops_total",
    "Total operations recorded to audit log",
    ["skill", "status"],  # status: pending, completed, failed
)

m11_replay_runs_total = Counter(
    "m11_replay_runs_total",
    "Total replay runs executed",
    ["mode", "status"],  # mode: verify, dry_run, rehydrate; status: success, failed
)

m11_replay_ops_verified_total = Counter("m11_replay_ops_verified_total", "Total operations verified during replay")

m11_replay_ops_mismatched_total = Counter(
    "m11_replay_ops_mismatched_total", "Total operations with mismatches during replay"
)

m11_replay_verification_seconds = Histogram(
    "m11_replay_verification_seconds",
    "Replay verification duration (seconds)",
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# =====================
# M10 Metric Aliases (for test compatibility)
# =====================
# These provide UPPERCASE aliases matching test expectations

# Create dedicated gauges for alert-compatible metric names
m10_queue_depth = Gauge("m10_queue_depth", "Number of items in M10 recovery evaluation queue")

m10_dead_letter_count = Gauge("m10_dead_letter_count", "Number of messages in M10 dead-letter queue")

m10_matview_age_seconds = Gauge("m10_matview_age_seconds", "Age of M10 materialized view since last refresh (seconds)")

m10_consumer_count = Gauge("m10_consumer_count", "Number of active M10 stream consumers")

m10_reclaim_count = Gauge("m10_reclaim_count", "Number of reclaim attempts in progress")

# Aliases for test imports (UPPERCASE names)
M10_QUEUE_DEPTH = m10_queue_depth
M10_DEAD_LETTER_COUNT = m10_dead_letter_count
M10_OUTBOX_PENDING = m10_outbox_pending
M10_OUTBOX_PROCESSED = m10_outbox_processed_total
M10_MATVIEW_AGE = m10_matview_age_seconds
M10_CONSUMER_COUNT = m10_consumer_count
M10_RECLAIM_COUNT = m10_reclaim_count

# =====================
# M12 Multi-Agent System Metrics
# =====================

# Job metrics
m12_jobs_started_total = Counter("m12_jobs_started_total", "Total jobs started", ["task", "tenant_id"])

m12_jobs_completed_total = Counter(
    "m12_jobs_completed_total",
    "Total jobs completed",
    ["task", "status", "tenant_id"],  # status: completed, failed, cancelled
)

m12_job_duration_seconds = Histogram(
    "m12_job_duration_seconds",
    "Job duration (seconds)",
    ["task"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

# Job item metrics
m12_job_items_total = Counter(
    "m12_job_items_total",
    "Total job items processed",
    ["status"],  # completed, failed
)

m12_job_items_claimed_total = Counter("m12_job_items_claimed_total", "Total job items claimed by workers")

m12_job_item_duration_seconds = Histogram(
    "m12_job_item_duration_seconds",
    "Job item processing duration (seconds)",
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# Agent metrics
m12_agent_registrations_total = Counter("m12_agent_registrations_total", "Total agent registrations", ["agent_id"])

m12_agent_heartbeats_total = Counter("m12_agent_heartbeats_total", "Total agent heartbeats received")

m12_active_agents = Gauge(
    "m12_active_agents",
    "Number of currently active agents",
    ["status"],  # running, idle, stale
)

m12_stale_agents_marked_total = Counter("m12_stale_agents_marked_total", "Total agents marked as stale")

# Invocation metrics
m12_agent_invoke_total = Counter(
    "m12_agent_invoke_total",
    "Total agent invocations",
    ["status"],  # success, timeout, failed
)

m12_agent_invoke_latency_seconds = Histogram(
    "m12_agent_invoke_latency_seconds",
    "Agent invocation latency (seconds)",
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# Blackboard metrics
m12_blackboard_ops_total = Counter(
    "m12_blackboard_ops_total",
    "Total blackboard operations",
    ["operation"],  # get, set, increment, lock_acquire, lock_release
)

m12_blackboard_lock_contention_total = Counter(
    "m12_blackboard_lock_contention_total", "Total lock acquisition failures due to contention"
)

# Message metrics
m12_messages_sent_total = Counter("m12_messages_sent_total", "Total P2P messages sent", ["message_type"])

m12_messages_delivered_total = Counter("m12_messages_delivered_total", "Total P2P messages delivered")

m12_message_latency_seconds = Histogram(
    "m12_message_latency_seconds",
    "P2P message delivery latency (seconds)",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Credit metrics
m12_credits_reserved_total = Counter("m12_credits_reserved_total", "Total credits reserved", ["tenant_id"])

m12_credits_spent_total = Counter("m12_credits_spent_total", "Total credits spent", ["skill", "tenant_id"])

m12_credits_refunded_total = Counter("m12_credits_refunded_total", "Total credits refunded", ["tenant_id"])

# M12 Metric Aliases (UPPERCASE)
M12_JOBS_STARTED = m12_jobs_started_total
M12_JOBS_COMPLETED = m12_jobs_completed_total
M12_JOB_ITEMS = m12_job_items_total
M12_AGENT_INVOKE_LATENCY = m12_agent_invoke_latency_seconds
M12_BLACKBOARD_OPS = m12_blackboard_ops_total
M12_CREDITS_SPENT = m12_credits_spent_total
M12_MESSAGE_LATENCY = m12_message_latency_seconds

# =====================
# M18 CARE-L + SBA Evolution Metrics
# =====================

# Agent Reputation Metrics
m18_reputation_score = Gauge("m18_reputation_score", "Agent reputation score (0.0-1.0)", ["agent_id"])

m18_reputation_updates_total = Counter(
    "m18_reputation_updates_total",
    "Total reputation score updates",
    ["agent_id", "direction"],  # direction: up, down, stable
)

# Quarantine Metrics
m18_quarantine_state = Gauge(
    "m18_quarantine_state", "Agent quarantine state (0=active, 1=probation, 2=quarantined)", ["agent_id"]
)

m18_quarantine_entries_total = Counter(
    "m18_quarantine_entries_total", "Total times agents entered quarantine", ["agent_id"]
)

m18_quarantine_exits_total = Counter(
    "m18_quarantine_exits_total",
    "Total times agents exited quarantine",
    ["agent_id", "reason"],  # reason: cooloff, manual, recovered
)

m18_quarantine_duration_seconds = Histogram(
    "m18_quarantine_duration_seconds",
    "Duration of quarantine periods (seconds)",
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400),
)

# Hysteresis Metrics
m18_hysteresis_switches_total = Counter(
    "m18_hysteresis_switches_total", "Total routing switches (passed hysteresis check)"
)

m18_hysteresis_blocked_total = Counter("m18_hysteresis_blocked_total", "Total routing switches blocked by hysteresis")

# Drift Detection Metrics
m18_drift_signals_total = Counter(
    "m18_drift_signals_total",
    "Total drift signals detected",
    ["agent_id", "drift_type"],  # drift_type: data, domain, behavior, boundary
)

m18_drift_severity = Gauge("m18_drift_severity", "Current drift severity (0.0-1.0)", ["agent_id", "drift_type"])

m18_drift_acknowledged_total = Counter("m18_drift_acknowledged_total", "Total drift signals acknowledged", ["agent_id"])

# Boundary Violation Metrics
m18_boundary_violations_total = Counter(
    "m18_boundary_violations_total",
    "Total boundary violations detected",
    ["agent_id", "violation_type"],  # violation_type: domain, tool, context, risk
)

m18_boundary_auto_reported_total = Counter(
    "m18_boundary_auto_reported_total", "Total violations self-reported by agents"
)

# Strategy Adjustment Metrics
m18_strategy_adjustments_total = Counter(
    "m18_strategy_adjustments_total", "Total strategy adjustments made", ["agent_id", "trigger", "adjustment_type"]
)

m18_strategy_success_rate_before = Gauge(
    "m18_strategy_success_rate_before", "Success rate before last strategy adjustment", ["agent_id"]
)

m18_strategy_success_rate_after = Gauge(
    "m18_strategy_success_rate_after", "Success rate after last strategy adjustment", ["agent_id"]
)

# Governor/Stabilization Metrics
m18_governor_state = Gauge("m18_governor_state", "Governor state (0=stable, 1=cautious, 2=frozen)")

m18_governor_freezes_total = Counter("m18_governor_freezes_total", "Total system freezes triggered")

m18_governor_rollbacks_total = Counter("m18_governor_rollbacks_total", "Total auto-rollbacks triggered")

m18_adjustments_per_hour = Gauge("m18_adjustments_per_hour", "Number of adjustments in the last hour", ["agent_id"])

# Feedback Loop Metrics
m18_feedback_loop_iterations_total = Counter("m18_feedback_loop_iterations_total", "Total feedback loop iterations")

m18_feedback_loop_latency_seconds = Histogram(
    "m18_feedback_loop_latency_seconds",
    "Feedback loop processing latency (seconds)",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

# SLA Scoring Metrics
m18_sla_score = Gauge("m18_sla_score", "Agent SLA score", ["agent_id"])

m18_sla_gap = Gauge("m18_sla_gap", "Gap between actual and target SLA", ["agent_id"])

# Inter-Agent Coordination Metrics
m18_successor_recommendations_total = Counter(
    "m18_successor_recommendations_total", "Total successor agent recommendations"
)

m18_capability_redistributions_total = Counter(
    "m18_capability_redistributions_total", "Total capability redistributions between agents"
)

# Batch Learning Metrics
m18_batch_learning_runs_total = Counter(
    "m18_batch_learning_runs_total",
    "Total batch learning runs",
    ["status"],  # status: success, failed
)

m18_batch_learning_duration_seconds = Histogram(
    "m18_batch_learning_duration_seconds",
    "Batch learning run duration (seconds)",
    buckets=(10, 30, 60, 120, 300, 600, 1800),
)

m18_parameters_tuned_total = Counter("m18_parameters_tuned_total", "Total parameters tuned via batch learning")

# Explainability Metrics
m18_explain_requests_total = Counter("m18_explain_requests_total", "Total routing explanation requests")

# M18 Metric Aliases (UPPERCASE)
M18_REPUTATION_SCORE = m18_reputation_score
M18_QUARANTINE_STATE = m18_quarantine_state
M18_GOVERNOR_STATE = m18_governor_state
M18_DRIFT_SIGNALS = m18_drift_signals_total
M18_BOUNDARY_VIOLATIONS = m18_boundary_violations_total

# =====================
# Cross-Domain Governance Metrics (CROSS_DOMAIN_GOVERNANCE.md)
# =====================
#
# DOCTRINE: Governance must throw. These metrics track when it does.
# A quiet system with governance_invariant_violations_total = 0 is healthy.
# Any non-zero value indicates a GovernanceError was raised.

governance_invariant_violations_total = Counter(
    "governance_invariant_violations_total",
    "Total governance invariant violations (GovernanceError raised)",
    ["domain", "operation"],
    # domain: Activity, Analytics, Policies
    # operation: create_incident_from_cost_anomaly, record_limit_breach, etc.
)

governance_incidents_created_total = Counter(
    "governance_incidents_created_total",
    "Total incidents created via mandatory governance",
    ["domain", "source_type"],
    # domain: Activity, Analytics
    # source_type: run_failure, cost_anomaly
)

governance_limit_breaches_recorded_total = Counter(
    "governance_limit_breaches_recorded_total",
    "Total limit breaches recorded via mandatory governance",
    ["breach_type"],
    # breach_type: BREACHED, EXHAUSTED, THROTTLED, VIOLATED
)

# =====================
# Customer Integration Metrics (Phase 6 - Evidence Signal Wiring)
# Namespace: cus_llm_*, cus_enforcement_*, cus_integration_*
# Reference: CUSTOMER_INTEGRATIONS_ARCHITECTURE.md Section 16
# =====================

# LLM Usage Counters (from cus_llm_usage evidence)
cus_llm_calls_total = Counter(
    "cus_llm_calls_total",
    "Total customer LLM calls",
    ["tenant_id", "integration_id", "provider", "model"],
)

cus_llm_tokens_total = Counter(
    "cus_llm_tokens_total",
    "Total customer LLM tokens",
    ["tenant_id", "integration_id", "token_type"],  # token_type: input, output
)

cus_llm_cost_cents_total = Counter(
    "cus_llm_cost_cents_total",
    "Total customer LLM cost in cents",
    ["tenant_id", "integration_id"],
)

cus_llm_latency_seconds = Histogram(
    "cus_llm_latency_seconds",
    "Customer LLM call latency (seconds)",
    ["tenant_id", "integration_id"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

cus_llm_errors_total = Counter(
    "cus_llm_errors_total",
    "Total customer LLM errors",
    ["tenant_id", "integration_id", "error_code"],
)

# Enforcement Decision Counters (from enforcement service)
cus_enforcement_decisions_total = Counter(
    "cus_enforcement_decisions_total",
    "Total enforcement decisions",
    ["tenant_id", "integration_id", "result"],  # result: allowed, warned, throttled, blocked, hard_blocked
)

cus_enforcement_blocked_total = Counter(
    "cus_enforcement_blocked_total",
    "Total blocked enforcement decisions",
    ["tenant_id", "integration_id", "reason"],  # reason: budget, token, rate, disabled
)

cus_policy_results_total = Counter(
    "cus_policy_results_total",
    "Total policy evaluation results",
    ["tenant_id", "integration_id", "result"],  # result: allowed, warned, blocked
)

# Integration Health Gauges
cus_integration_health_state = Gauge(
    "cus_integration_health_state",
    "Integration health state (0=unknown, 1=healthy, 2=degraded, 3=failing)",
    ["tenant_id", "integration_id"],
)

cus_integration_status = Gauge(
    "cus_integration_status",
    "Integration status (0=created, 1=enabled, 2=disabled, 3=error)",
    ["tenant_id", "integration_id"],
)

# Budget Utilization Gauges
cus_budget_used_cents = Gauge(
    "cus_budget_used_cents",
    "Current budget used in cents",
    ["tenant_id", "integration_id"],
)

cus_budget_limit_cents = Gauge(
    "cus_budget_limit_cents",
    "Budget limit in cents (0 = unlimited)",
    ["tenant_id", "integration_id"],
)

cus_budget_utilization_ratio = Gauge(
    "cus_budget_utilization_ratio",
    "Budget utilization ratio (0.0 to 1.0+)",
    ["tenant_id", "integration_id"],
)

# Token Utilization Gauges
cus_tokens_used_month = Gauge(
    "cus_tokens_used_month",
    "Tokens used this month",
    ["tenant_id", "integration_id"],
)

cus_token_limit_month = Gauge(
    "cus_token_limit_month",
    "Monthly token limit (0 = unlimited)",
    ["tenant_id", "integration_id"],
)

# Rate Metrics
cus_rate_current_rpm = Gauge(
    "cus_rate_current_rpm",
    "Current requests per minute",
    ["tenant_id", "integration_id"],
)

cus_rate_limit_rpm = Gauge(
    "cus_rate_limit_rpm",
    "Rate limit (requests per minute, 0 = unlimited)",
    ["tenant_id", "integration_id"],
)

# Aliases for test imports (UPPERCASE names)
CUS_LLM_CALLS = cus_llm_calls_total
CUS_LLM_COST = cus_llm_cost_cents_total
CUS_ENFORCEMENT_DECISIONS = cus_enforcement_decisions_total
CUS_ENFORCEMENT_BLOCKED = cus_enforcement_blocked_total
CUS_INTEGRATION_HEALTH = cus_integration_health_state
CUS_BUDGET_UTILIZATION = cus_budget_utilization_ratio
