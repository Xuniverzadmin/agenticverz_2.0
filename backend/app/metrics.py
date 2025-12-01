"""
Prometheus metrics for NOVA Agent Manager.

Supports multiprocess mode via PROMETHEUS_MULTIPROC_DIR environment variable.
When set, uses a shared directory for metric aggregation across processes.
"""
import os
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY
from prometheus_client import multiprocess, generate_latest, CONTENT_TYPE_LATEST

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
nova_runs_total = Counter(
    "nova_runs_total",
    "Total runs processed",
    ["status", "planner"]
)
nova_runs_failed_total = Counter("nova_runs_failed_total", "Total failed runs")

# Skill-level metrics
nova_skill_attempts_total = Counter(
    "nova_skill_attempts_total",
    "Skill executions",
    ["skill"]
)

nova_skill_duration_seconds = Histogram(
    "nova_skill_duration_seconds",
    "Skill execution duration (seconds)",
    ["skill"]
)

# Worker pool gauge
nova_worker_pool_size = Gauge(
    "nova_worker_pool_size",
    "Configured worker pool concurrency"
)

# Queue depth gauge
nova_runs_queued = Gauge(
    "nova_runs_queued",
    "Number of runs currently queued or retrying"
)

# =====================
# LLM Metrics
# =====================

# Token usage counters
nova_llm_tokens_total = Counter(
    "nova_llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "model", "token_type"]  # token_type: input, output
)

# Cost tracking
nova_llm_cost_cents_total = Counter(
    "nova_llm_cost_cents_total",
    "Total LLM cost in cents",
    ["provider", "model"]
)

# LLM invocation latency
nova_llm_duration_seconds = Histogram(
    "nova_llm_duration_seconds",
    "LLM invocation latency (seconds)",
    ["provider", "model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# LLM invocation counter
nova_llm_invocations_total = Counter(
    "nova_llm_invocations_total",
    "Total LLM invocations",
    ["provider", "model", "status"]  # status: success, error
)

# =====================
# Planner Metrics
# =====================

# Planner latency
nova_planner_duration_seconds = Histogram(
    "nova_planner_duration_seconds",
    "Planner latency (seconds)",
    ["planner"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# Plans generated
nova_plans_generated_total = Counter(
    "nova_plans_generated_total",
    "Total plans generated",
    ["planner", "status"]  # status: success, fallback, stub, error
)

# Plan step counts
nova_plan_steps_total = Counter(
    "nova_plan_steps_total",
    "Total plan steps generated",
    ["planner"]
)
