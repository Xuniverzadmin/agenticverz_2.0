# Execution Plan for Business Builder Worker
# Defines stages that map to M4 execution engine
"""
Execution plan with governance-aware stages.

Each stage:
1. Routes via CARE (M17) based on complexity
2. Validates via Policy (M19/M20)
3. Recovers via M9/M10 on failure
4. Updates reputation via M18

Stages execute in governance order (SAFETY -> PRIVACY -> OPERATIONAL -> ROUTING -> CUSTOM)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum, auto
from datetime import datetime, timezone
import hashlib


class StageStatus(Enum):
    """Status of an execution stage."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    RECOVERED = auto()
    SKIPPED = auto()


class StageCategory(str, Enum):
    """
    Stage categories matching M19 policy categories.

    Execution order: SAFETY -> PRIVACY -> OPERATIONAL -> ROUTING -> CUSTOM
    """
    SAFETY = "SAFETY"           # Pre-flight checks
    PRIVACY = "PRIVACY"         # Data handling
    OPERATIONAL = "OPERATIONAL" # Core business logic
    ROUTING = "ROUTING"         # Agent selection
    CUSTOM = "CUSTOM"           # Custom stages


@dataclass
class StageResult:
    """Result of a single stage execution."""
    stage_id: str
    status: StageStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None
    recovery_applied: Optional[str] = None
    latency_ms: float = 0.0
    step_count: int = 0
    policy_violations: List[Dict[str, Any]] = field(default_factory=list)
    drift_score: Optional[float] = None
    agent_used: Optional[str] = None


@dataclass
class ExecutionStage:
    """
    A single stage in the execution plan.

    Maps to:
    - M4: Deterministic execution
    - M17: CARE routing (complexity-based agent selection)
    - M19: Policy governance (pre/post validation)
    """
    id: str
    name: str
    category: StageCategory
    description: str

    # Agent routing
    primary_agent: str  # SBA agent ID for this stage
    fallback_agents: List[str] = field(default_factory=list)

    # I/O
    inputs: List[str] = field(default_factory=list)  # Output IDs from previous stages
    outputs: List[str] = field(default_factory=list)  # Output artifacts

    # Routing hints for CARE (M17)
    difficulty: str = "medium"  # low, medium, high
    risk_policy: str = "balanced"  # strict, balanced, fast
    requires_brand_check: bool = False  # M18 drift detection

    # Governance (M19/M20)
    pre_policies: List[str] = field(default_factory=list)  # Policy names to check before
    post_policies: List[str] = field(default_factory=list)  # Policy names to check after

    # Recovery (M9/M10)
    recoverable: bool = True  # Can this stage recover from failure?
    max_retries: int = 2

    # Execution
    timeout_seconds: int = 300
    budget_tokens: Optional[int] = None


@dataclass
class ExecutionPlan:
    """
    Complete execution plan for Business Builder Worker.

    Integrates:
    - M4: Golden replay via plan serialization
    - M17: Per-stage CARE routing
    - M19: Governance validation
    - M9/M10: Failure patterns & recovery
    """
    plan_id: str = ""
    name: str = "Business Builder"
    version: str = "0.2"

    # Stages execute in order within category, then by category priority
    stages: List[ExecutionStage] = field(default_factory=list)

    # Global constraints
    total_budget_tokens: Optional[int] = None
    strict_mode: bool = False  # If True, any policy violation stops execution

    # Context
    brand_context: Dict[str, Any] = field(default_factory=dict)
    request_context: Dict[str, Any] = field(default_factory=dict)

    # Results
    stage_results: List[StageResult] = field(default_factory=list)
    final_status: StageStatus = StageStatus.PENDING

    # Timing
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Golden replay (M4)
    seed: int = 0
    replay_token: Optional[str] = None

    def __post_init__(self):
        if not self.plan_id:
            self.plan_id = self._generate_plan_id()
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        if self.seed == 0:
            # Deterministic seed from inputs
            self.seed = self._generate_seed()

    def _generate_plan_id(self) -> str:
        """Generate deterministic plan ID."""
        content = f"{self.name}:{self.version}:{len(self.stages)}"
        return f"plan_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    def _generate_seed(self) -> int:
        """Generate deterministic seed from context."""
        content = f"{self.brand_context}:{self.request_context}"
        return int(hashlib.sha256(content.encode()).hexdigest()[:8], 16)

    def get_stages_by_category(self, category: StageCategory) -> List[ExecutionStage]:
        """Get stages filtered by category."""
        return [s for s in self.stages if s.category == category]

    def get_execution_order(self) -> List[ExecutionStage]:
        """
        Get stages in governance execution order.

        Order: SAFETY -> PRIVACY -> OPERATIONAL -> ROUTING -> CUSTOM
        Within category: preserve definition order
        """
        category_order = [
            StageCategory.SAFETY,
            StageCategory.PRIVACY,
            StageCategory.OPERATIONAL,
            StageCategory.ROUTING,
            StageCategory.CUSTOM,
        ]

        ordered = []
        for cat in category_order:
            ordered.extend(self.get_stages_by_category(cat))

        return ordered

    def add_stage(self, stage: ExecutionStage) -> None:
        """Add a stage to the plan."""
        self.stages.append(stage)

    def get_stage(self, stage_id: str) -> Optional[ExecutionStage]:
        """Get stage by ID."""
        for s in self.stages:
            if s.id == stage_id:
                return s
        return None

    def get_stage_result(self, stage_id: str) -> Optional[StageResult]:
        """Get result for a stage."""
        for r in self.stage_results:
            if r.stage_id == stage_id:
                return r
        return None

    def get_output(self, output_id: str) -> Optional[Any]:
        """Get output value by ID from any completed stage."""
        for result in self.stage_results:
            if output_id in result.outputs:
                return result.outputs[output_id]
        return None

    def to_replay_token(self) -> Dict[str, Any]:
        """
        Generate Golden Replay token (M4).

        This allows exact re-execution of the plan.
        """
        return {
            "plan_id": self.plan_id,
            "seed": self.seed,
            "version": self.version,
            "stages": [s.id for s in self.stages],
            "brand_context_hash": hashlib.sha256(
                str(self.brand_context).encode()
            ).hexdigest()[:16],
            "request_context_hash": hashlib.sha256(
                str(self.request_context).encode()
            ).hexdigest()[:16],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_yaml(self) -> str:
        """Serialize plan to YAML for storage/replay."""
        import yaml
        data = {
            "plan_id": self.plan_id,
            "name": self.name,
            "version": self.version,
            "seed": self.seed,
            "total_budget_tokens": self.total_budget_tokens,
            "strict_mode": self.strict_mode,
            "stages": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category.value,
                    "primary_agent": s.primary_agent,
                    "fallback_agents": s.fallback_agents,
                    "inputs": s.inputs,
                    "outputs": s.outputs,
                    "difficulty": s.difficulty,
                    "risk_policy": s.risk_policy,
                    "requires_brand_check": s.requires_brand_check,
                }
                for s in self.stages
            ],
        }
        return yaml.dump(data, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ExecutionPlan":
        """Load plan from YAML."""
        import yaml
        data = yaml.safe_load(yaml_str)

        stages = []
        for s in data.get("stages", []):
            stages.append(ExecutionStage(
                id=s["id"],
                name=s["name"],
                category=StageCategory(s["category"]),
                description=s.get("description", ""),
                primary_agent=s["primary_agent"],
                fallback_agents=s.get("fallback_agents", []),
                inputs=s.get("inputs", []),
                outputs=s.get("outputs", []),
                difficulty=s.get("difficulty", "medium"),
                risk_policy=s.get("risk_policy", "balanced"),
                requires_brand_check=s.get("requires_brand_check", False),
            ))

        return cls(
            plan_id=data.get("plan_id", ""),
            name=data.get("name", "Business Builder"),
            version=data.get("version", "0.2"),
            seed=data.get("seed", 0),
            total_budget_tokens=data.get("total_budget_tokens"),
            strict_mode=data.get("strict_mode", False),
            stages=stages,
        )


def create_business_builder_plan(
    brand_context: Dict[str, Any],
    budget: Optional[int] = None,
    strict_mode: bool = False,
) -> ExecutionPlan:
    """
    Create the default Business Builder execution plan.

    Stages:
    1. SAFETY: Pre-flight validation
    2. OPERATIONAL: Research -> Strategy -> Copy -> UX
    3. ROUTING: Consistency check
    4. CUSTOM: Bundle packaging
    """
    plan = ExecutionPlan(
        name="Business Builder",
        version="0.2",
        brand_context=brand_context,
        total_budget_tokens=budget,
        strict_mode=strict_mode,
    )

    # Stage 1: Pre-flight validation (SAFETY)
    plan.add_stage(ExecutionStage(
        id="preflight",
        name="Pre-flight Validation",
        category=StageCategory.SAFETY,
        description="Validate inputs and check constraints before execution",
        primary_agent="validator_agent",
        outputs=["validation_result", "constraint_flags"],
        difficulty="low",
        risk_policy="strict",
        pre_policies=["budget_check", "forbidden_claims_check"],
        timeout_seconds=60,
    ))

    # Stage 2: Market Research (OPERATIONAL)
    plan.add_stage(ExecutionStage(
        id="research",
        name="Market Research",
        category=StageCategory.OPERATIONAL,
        description="Gather market intelligence and competitor analysis",
        primary_agent="researcher_agent",
        fallback_agents=["basic_researcher_agent"],
        inputs=["validation_result"],
        outputs=["market_report", "competitor_matrix", "trend_analysis"],
        difficulty="high",
        risk_policy="balanced",
        requires_brand_check=False,  # Research is objective
        timeout_seconds=300,
        budget_tokens=10000,
    ))

    # Stage 3: Strategy Development (OPERATIONAL)
    plan.add_stage(ExecutionStage(
        id="strategy",
        name="Strategy Development",
        category=StageCategory.OPERATIONAL,
        description="Develop positioning and brand strategy",
        primary_agent="strategist_agent",
        inputs=["market_report", "competitor_matrix"],
        outputs=["positioning", "messaging_framework", "tone_guidelines"],
        difficulty="high",
        risk_policy="balanced",
        requires_brand_check=True,  # Must align with brand
        post_policies=["brand_alignment_check"],
        timeout_seconds=300,
        budget_tokens=8000,
    ))

    # Stage 4: Copy Generation (OPERATIONAL)
    plan.add_stage(ExecutionStage(
        id="copy",
        name="Copy Generation",
        category=StageCategory.OPERATIONAL,
        description="Generate landing page copy, blogs, and marketing content",
        primary_agent="copywriter_agent",
        fallback_agents=["basic_copywriter_agent"],
        inputs=["positioning", "messaging_framework", "tone_guidelines"],
        outputs=["landing_copy", "blog_drafts", "email_sequence", "social_copy"],
        difficulty="medium",
        risk_policy="balanced",
        requires_brand_check=True,
        pre_policies=["tone_check"],
        post_policies=["forbidden_claims_check", "brand_drift_check"],
        timeout_seconds=300,
        budget_tokens=12000,
    ))

    # Stage 5: UX/Layout Generation (OPERATIONAL)
    plan.add_stage(ExecutionStage(
        id="ux",
        name="UX Layout Generation",
        category=StageCategory.OPERATIONAL,
        description="Generate HTML/CSS landing page structure",
        primary_agent="ux_agent",
        inputs=["landing_copy", "positioning"],
        outputs=["landing_html", "landing_css", "component_map"],
        difficulty="medium",
        risk_policy="balanced",
        requires_brand_check=True,
        timeout_seconds=180,
        budget_tokens=5000,
    ))

    # Stage 6: Consistency Check (ROUTING)
    plan.add_stage(ExecutionStage(
        id="consistency",
        name="Consistency Check",
        category=StageCategory.ROUTING,
        description="Validate consistency across all outputs",
        primary_agent="strategist_agent",
        inputs=["landing_copy", "landing_html", "blog_drafts", "positioning"],
        outputs=["consistency_score", "violations", "corrections"],
        difficulty="medium",
        risk_policy="strict",
        requires_brand_check=True,
        post_policies=["consistency_threshold"],
        timeout_seconds=120,
    ))

    # Stage 7: Recovery/Normalization (ROUTING)
    plan.add_stage(ExecutionStage(
        id="recovery",
        name="Recovery & Normalization",
        category=StageCategory.ROUTING,
        description="Apply corrections from consistency check",
        primary_agent="recovery_agent",
        inputs=["consistency_score", "violations", "corrections"],
        outputs=["normalized_copy", "normalized_html", "recovery_log"],
        difficulty="low",
        risk_policy="strict",
        timeout_seconds=120,
    ))

    # Stage 8: Bundle Packaging (CUSTOM)
    plan.add_stage(ExecutionStage(
        id="bundle",
        name="Bundle Packaging",
        category=StageCategory.CUSTOM,
        description="Package all artifacts into final bundle",
        primary_agent="governor_agent",
        inputs=[
            "market_report", "positioning", "normalized_copy",
            "normalized_html", "blog_drafts", "recovery_log"
        ],
        outputs=["bundle_zip", "cost_report", "replay_token"],
        difficulty="low",
        risk_policy="balanced",
        timeout_seconds=60,
    ))

    return plan
