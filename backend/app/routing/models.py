# M17 CARE - Routing Models
# Pydantic models for Cascade-Aware Routing Engine

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SuccessMetric(str, Enum):
    """Success metrics derived from winning aspiration."""
    COST = "cost"           # Minimize cost/resource usage
    LATENCY = "latency"     # Minimize response time
    ACCURACY = "accuracy"   # Maximize correctness
    RISK_MIN = "risk_min"   # Minimize risk exposure
    BALANCED = "balanced"   # Balance all factors


class OrchestratorMode(str, Enum):
    """Orchestrator execution modes."""
    PARALLEL = "parallel"           # Independent tasks scattered to workers
    HIERARCHICAL = "hierarchical"   # Parent delegates to sub-agents
    BLACKBOARD = "blackboard"       # Shared memory, opportunistic picking
    SEQUENTIAL = "sequential"       # One-by-one execution


class RoutingStage(str, Enum):
    """CARE pipeline stages."""
    ASPIRATION = "aspiration"       # Stage 1: Success metric selection
    DOMAIN_FILTER = "domain_filter" # Stage 2: Where-to-play filter
    STRATEGY = "strategy"           # Stage 3: How-to-win expansion
    CAPABILITY = "capability"       # Stage 4: Capability/capacity gate
    ORCHESTRATOR = "orchestrator"   # Stage 5: Mode selection


class RiskPolicy(str, Enum):
    """Risk policies for execution."""
    STRICT = "strict"       # Extra validation, retry on failure
    BALANCED = "balanced"   # Standard validation
    FAST = "fast"           # Skip validation, no retry


class DifficultyLevel(str, Enum):
    """Task difficulty levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =============================================================================
# Capability Probe Models
# =============================================================================

class ProbeType(str, Enum):
    """Types of capability probes."""
    SMTP = "smtp"
    DNS = "dns"
    API_KEY = "api_key"
    S3 = "s3"
    HTTP = "http"
    REDIS = "redis"
    DATABASE = "database"
    AGENT = "agent"
    SERVICE = "service"


class CapabilityProbeResult(BaseModel):
    """Result of a single capability probe."""
    probe_type: ProbeType
    name: str
    available: bool
    latency_ms: float = Field(default=0.0, description="Probe latency in ms")
    error: Optional[str] = None
    fix_instruction: Optional[str] = None
    cached: bool = False
    checked_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "probe_type": self.probe_type.value,
            "name": self.name,
            "available": self.available,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "fix_instruction": self.fix_instruction,
            "cached": self.cached,
            "checked_at": self.checked_at.isoformat(),
        }


class CapabilityCheckResult(BaseModel):
    """Aggregated capability check results."""
    passed: bool
    probes: List[CapabilityProbeResult] = Field(default_factory=list)
    failed_probes: List[CapabilityProbeResult] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "probes": [p.to_dict() for p in self.probes],
            "failed_probes": [p.to_dict() for p in self.failed_probes],
            "total_latency_ms": self.total_latency_ms,
            "error_summary": self.error_summary,
        }


# =============================================================================
# Routing Decision Models
# =============================================================================

class StageResult(BaseModel):
    """Result of a single CARE pipeline stage."""
    stage: RoutingStage
    passed: bool
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0


class RouteEvaluationResult(BaseModel):
    """Evaluation of a single agent for routing."""
    agent_id: str
    agent_name: Optional[str] = None
    eligible: bool
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Routing score 0-1")
    success_metric: SuccessMetric = SuccessMetric.BALANCED
    orchestrator_mode: OrchestratorMode = OrchestratorMode.SEQUENTIAL
    risk_policy: RiskPolicy = RiskPolicy.BALANCED
    stage_results: List[StageResult] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    rejection_stage: Optional[RoutingStage] = None
    capability_check: Optional[CapabilityCheckResult] = None

    def get_stage_result(self, stage: RoutingStage) -> Optional[StageResult]:
        """Get result for a specific stage."""
        for sr in self.stage_results:
            if sr.stage == stage:
                return sr
        return None


class RoutingRequest(BaseModel):
    """Request for CARE routing."""
    task_description: str = Field(..., min_length=1)
    task_domain: Optional[str] = None
    required_tools: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    risk_tolerance: RiskPolicy = RiskPolicy.BALANCED
    prefer_metric: Optional[SuccessMetric] = None
    max_agents: int = Field(default=10, ge=1, le=100)
    tenant_id: str = "default"


class RoutingDecision(BaseModel):
    """Final routing decision from CARE."""
    request_id: str
    task_description: str
    selected_agent_id: Optional[str] = None
    selected_agent_name: Optional[str] = None
    success_metric: SuccessMetric = SuccessMetric.BALANCED
    orchestrator_mode: OrchestratorMode = OrchestratorMode.SEQUENTIAL
    risk_policy: RiskPolicy = RiskPolicy.BALANCED

    # All evaluated agents
    evaluated_agents: List[RouteEvaluationResult] = Field(default_factory=list)
    eligible_agents: List[str] = Field(default_factory=list)

    # Routing metadata
    routed: bool = False
    error: Optional[str] = None
    actionable_fix: Optional[str] = None

    # Timing
    total_latency_ms: float = 0.0
    stage_latencies: Dict[str, float] = Field(default_factory=dict)

    # Audit
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    decision_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/logging."""
        return {
            "request_id": self.request_id,
            "task_description": self.task_description[:100],
            "selected_agent_id": self.selected_agent_id,
            "selected_agent_name": self.selected_agent_name,
            "success_metric": self.success_metric.value,
            "orchestrator_mode": self.orchestrator_mode.value,
            "risk_policy": self.risk_policy.value,
            "eligible_agents": self.eligible_agents,
            "routed": self.routed,
            "error": self.error,
            "actionable_fix": self.actionable_fix,
            "total_latency_ms": self.total_latency_ms,
            "stage_latencies": self.stage_latencies,
            "decided_at": self.decided_at.isoformat(),
            "decision_reason": self.decision_reason,
        }


# =============================================================================
# Routing Configuration
# =============================================================================

class RoutingConfig(BaseModel):
    """
    M17 Routing configuration extension for SBA.

    This extends the base SBA schema with routing-specific settings.
    """
    # Derived from winning_aspiration
    success_metric: SuccessMetric = SuccessMetric.BALANCED

    # How-to-win extensions
    difficulty_threshold: DifficultyLevel = DifficultyLevel.MEDIUM
    risk_policy: RiskPolicy = RiskPolicy.BALANCED
    task_patterns: List[str] = Field(default_factory=list)

    # Orchestrator mode (from enabling_management_systems)
    orchestrator_mode: OrchestratorMode = OrchestratorMode.SEQUENTIAL

    # Capacity limits
    max_parallel_tasks: int = Field(default=3, ge=1, le=100)
    max_tokens_per_task: int = Field(default=100000, ge=1000)

    # Escalation rules
    escalation_enabled: bool = True
    escalation_threshold: float = Field(default=0.3, ge=0.0, le=1.0)


# =============================================================================
# Aspiration to Metric Mapping
# =============================================================================

ASPIRATION_METRIC_KEYWORDS: Dict[SuccessMetric, List[str]] = {
    SuccessMetric.COST: [
        "cost", "budget", "cheap", "efficient", "economical", "save", "minimize spend",
        "resource", "token", "credit", "affordable"
    ],
    SuccessMetric.LATENCY: [
        "fast", "quick", "speed", "latency", "response time", "real-time", "instant",
        "immediate", "rapid", "urgent", "low latency"
    ],
    SuccessMetric.ACCURACY: [
        "accurate", "correct", "precise", "quality", "reliable", "thorough", "complete",
        "valid", "verify", "check", "ensure", "careful"
    ],
    SuccessMetric.RISK_MIN: [
        "safe", "secure", "risk", "cautious", "careful", "protect", "prevent",
        "avoid", "compliance", "audit", "governance"
    ],
}


def infer_success_metric(aspiration: str) -> SuccessMetric:
    """
    Infer success metric from winning aspiration text.

    Stage 1 of CARE pipeline.
    """
    aspiration_lower = aspiration.lower()

    scores: Dict[SuccessMetric, int] = {metric: 0 for metric in SuccessMetric}

    for metric, keywords in ASPIRATION_METRIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in aspiration_lower:
                scores[metric] += 1

    # Find highest scoring metric
    best_metric = max(scores, key=lambda m: scores[m])

    # If no keywords matched, return balanced
    if scores[best_metric] == 0:
        return SuccessMetric.BALANCED

    return best_metric


def infer_orchestrator_mode(orchestrator: str, agent_type: str) -> OrchestratorMode:
    """
    Infer orchestrator mode from orchestrator name and agent type.

    Stage 5 of CARE pipeline.
    """
    orchestrator_lower = orchestrator.lower()

    if "parallel" in orchestrator_lower or "swarm" in orchestrator_lower:
        return OrchestratorMode.PARALLEL

    if "hierarchical" in orchestrator_lower or "tree" in orchestrator_lower:
        return OrchestratorMode.HIERARCHICAL

    if "blackboard" in orchestrator_lower or "shared" in orchestrator_lower:
        return OrchestratorMode.BLACKBOARD

    # Infer from agent type
    if agent_type == "orchestrator":
        return OrchestratorMode.HIERARCHICAL

    if agent_type == "aggregator":
        return OrchestratorMode.BLACKBOARD

    return OrchestratorMode.SEQUENTIAL
