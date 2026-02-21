# capability_id: CAP-008
# Layer: L4 — Domain Engine
# Product: product-builder
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Business builder agent definitions
# Callers: business_builder worker
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Business Builder

# Agent Definitions for Business Builder Worker
# Uses M15 SBA Schema for strategy-bound execution
"""
Each agent definition creates a complete Strategy Cascade:
- Winning Aspiration: WHY the agent exists
- Where to Play: BOUNDARIES
- How to Win: TASKS
- Capabilities & Capacity: DEPENDENCIES
- Enabling Management Systems: GOVERNANCE

These are registered with M12 and routed by M17.
"""

from typing import Dict, List

from app.agents.sba.schema import (
    CapabilitiesCapacity,
    Dependency,
    DependencyType,
    EnablingManagementSystems,
    EnvironmentRequirements,
    GovernanceProvider,
    HowToWin,
    SBASchema,
    WhereToPlay,
    WinningAspiration,
    create_api_dependency,
    create_tool_dependency,
)


def create_researcher_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    Research Analyst Agent.

    Produces truthful, high-signal market intelligence.
    """
    return SBASchema(
        agent_id="researcher_agent",
        winning_aspiration=WinningAspiration(
            description="Produce truthful, high-signal market intelligence by discovering patterns in public data and synthesizing them into actionable insights"
        ),
        where_to_play=WhereToPlay(
            domain="market-research",
            allowed_tools=["web_search", "data_aggregation", "summarization"],
            allowed_contexts=["job"],
            boundaries="Must not fabricate data or sources. Must cite sources when possible. Must not access paid databases without authorization.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Search publicly available market data",
                "Identify competitor landscape",
                "Extract market trends and patterns",
                "Synthesize findings into structured report",
            ],
            tests=[
                "Output contains at least 3 competitor mentions",
                "All claims are verifiable or marked as inferred",
                "Report structure matches template",
            ],
            fulfillment_metric=0.85,
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("llm_invoke"),
                create_tool_dependency("web_search"),
                create_api_dependency("openai", required=False),
            ],
            env=EnvironmentRequirements(
                budget_tokens=10000,
                timeout_seconds=300,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


def create_strategist_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    Brand Strategist Agent.

    Enforces brand consistency and develops positioning.
    """
    return SBASchema(
        agent_id="strategist_agent",
        winning_aspiration=WinningAspiration(
            description="Enforce brand consistency across all outputs and develop compelling market positioning that differentiates from competitors"
        ),
        where_to_play=WhereToPlay(
            domain="brand-strategy",
            allowed_tools=["llm_invoke", "embedding_compare", "tone_analysis"],
            allowed_contexts=["job"],
            boundaries="Must adhere to brand guidelines. Cannot contradict established brand voice. Must flag conflicts rather than resolve arbitrarily.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Analyze research findings for positioning opportunities",
                "Develop unique value proposition",
                "Create messaging framework aligned with brand",
                "Validate outputs against brand guidelines",
                "Detect and flag inconsistencies",
            ],
            tests=[
                "Positioning differentiates from top 3 competitors",
                "Messaging passes tone validation",
                "No forbidden claims present",
            ],
            fulfillment_metric=0.90,
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("llm_invoke"),
                create_tool_dependency("embedding_compare", required=False),
                Dependency(
                    type=DependencyType.AGENT,
                    name="researcher_agent",
                    required=False,
                ),
            ],
            env=EnvironmentRequirements(
                budget_tokens=8000,
                timeout_seconds=300,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


def create_copywriter_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    Copywriter Agent.

    Produces persuasive, brand-aligned copy.
    """
    return SBASchema(
        agent_id="copywriter_agent",
        winning_aspiration=WinningAspiration(
            description="Produce persuasive, conversion-focused copy that adheres to brand voice and passes all policy checks"
        ),
        where_to_play=WhereToPlay(
            domain="copywriting",
            allowed_tools=["llm_invoke", "tone_analysis"],
            allowed_contexts=["job"],
            boundaries="Must follow tone guidelines. Cannot use forbidden claims. Must be factually accurate about product claims.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Generate landing page hero section",
                "Write feature benefit copy",
                "Create call-to-action variants",
                "Draft blog outlines and intros",
                "Produce email sequence copy",
            ],
            tests=[
                "Copy passes forbidden claim check",
                "Tone matches brand guidelines",
                "All CTAs are actionable",
                "Reading level appropriate for audience",
            ],
            fulfillment_metric=0.88,
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("llm_invoke"),
                Dependency(
                    type=DependencyType.AGENT,
                    name="strategist_agent",
                    required=True,
                    fallback="basic_copywriter_agent",
                ),
            ],
            env=EnvironmentRequirements(
                budget_tokens=12000,
                timeout_seconds=300,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


def create_ux_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    UX Layout Designer Agent.

    Generates coherent HTML/CSS layouts.
    """
    return SBASchema(
        agent_id="ux_agent",
        winning_aspiration=WinningAspiration(
            description="Generate accessible, visually coherent layouts that follow brand guidelines and modern UX patterns"
        ),
        where_to_play=WhereToPlay(
            domain="ux-design",
            allowed_tools=["llm_invoke", "template_render"],
            allowed_contexts=["job"],
            boundaries="Must use semantic HTML. Must be accessible (WCAG AA). Must not include external scripts.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Generate HTML structure for landing page",
                "Create CSS styles matching brand",
                "Build responsive layout",
                "Map copy to components",
            ],
            tests=[
                "HTML is valid and semantic",
                "CSS uses brand colors",
                "Layout is responsive",
                "No accessibility errors",
            ],
            fulfillment_metric=0.82,
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("llm_invoke"),
                create_tool_dependency("template_render", required=False),
            ],
            env=EnvironmentRequirements(
                budget_tokens=5000,
                timeout_seconds=180,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


def create_recovery_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    Recovery Engineer Agent.

    Resolves workflow failure states using M9/M10.
    """
    return SBASchema(
        agent_id="recovery_agent",
        winning_aspiration=WinningAspiration(
            description="Resolve workflow failure states by matching patterns to the failure catalog and applying proven recovery strategies"
        ),
        where_to_play=WhereToPlay(
            domain="failure-recovery",
            allowed_tools=["llm_invoke", "failure_catalog", "recovery_suggest"],
            allowed_contexts=["job"],
            boundaries="Must not introduce new failures. Must log all recovery actions. Must escalate unrecoverable failures.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Identify failure pattern from catalog (M9)",
                "Match to recovery candidate (M10)",
                "Apply recovery with confidence score",
                "Validate recovery success",
                "Log recovery for learning (M18)",
            ],
            tests=[
                "Recovery resolves original failure",
                "No new failures introduced",
                "Recovery logged with trace",
            ],
            fulfillment_metric=0.75,  # Recovery is hard
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("llm_invoke"),
                create_tool_dependency("failure_catalog"),
                create_tool_dependency("recovery_suggest"),
            ],
            env=EnvironmentRequirements(
                budget_tokens=3000,
                timeout_seconds=120,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


def create_governor_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    Cost Governor Agent.

    Keeps execution under budget and packages final bundle.
    """
    return SBASchema(
        agent_id="governor_agent",
        winning_aspiration=WinningAspiration(
            description="Ensure execution stays within budget constraints while packaging all artifacts into the final deliverable bundle"
        ),
        where_to_play=WhereToPlay(
            domain="governance",
            allowed_tools=["cost_tracker", "bundle_packager"],
            allowed_contexts=["job"],
            boundaries="Must not exceed budget. Must include all required artifacts. Must generate valid replay token.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Track cost across all stages",
                "Enforce budget constraints",
                "Package artifacts into bundle",
                "Generate cost report",
                "Create replay token (M4)",
            ],
            tests=[
                "Total cost <= budget",
                "Bundle contains all artifacts",
                "Replay token is valid",
            ],
            fulfillment_metric=0.95,
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("cost_tracker"),
                create_tool_dependency("bundle_packager"),
            ],
            env=EnvironmentRequirements(
                budget_tokens=1000,
                timeout_seconds=60,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


def create_validator_agent(orchestrator: str = "business_builder_worker") -> SBASchema:
    """
    Pre-flight Validator Agent.

    Validates inputs before execution begins.
    """
    return SBASchema(
        agent_id="validator_agent",
        winning_aspiration=WinningAspiration(
            description="Ensure all inputs are valid and constraints are satisfiable before execution begins to prevent wasted compute"
        ),
        where_to_play=WhereToPlay(
            domain="validation",
            allowed_tools=["schema_validator", "policy_check"],
            allowed_contexts=["job"],
            boundaries="Must validate all required fields. Must check budget feasibility. Must enforce forbidden claim rules.",
        ),
        how_to_win=HowToWin(
            tasks=[
                "Validate brand schema",
                "Check budget feasibility",
                "Scan for forbidden claims in inputs",
                "Verify dependencies available",
            ],
            tests=[
                "All validations pass or fail with clear message",
                "Budget is sufficient for minimum execution",
                "No forbidden claims in inputs",
            ],
            fulfillment_metric=0.98,
        ),
        capabilities_capacity=CapabilitiesCapacity(
            dependencies=[
                create_tool_dependency("schema_validator"),
                create_tool_dependency("policy_check"),
            ],
            env=EnvironmentRequirements(
                budget_tokens=500,
                timeout_seconds=60,
            ),
        ),
        enabling_management_systems=EnablingManagementSystems(
            orchestrator=orchestrator,
            governance=GovernanceProvider.BUDGETLLM,
        ),
    )


# All worker agents
WORKER_AGENTS: Dict[str, SBASchema] = {
    "researcher_agent": create_researcher_agent(),
    "strategist_agent": create_strategist_agent(),
    "copywriter_agent": create_copywriter_agent(),
    "ux_agent": create_ux_agent(),
    "recovery_agent": create_recovery_agent(),
    "governor_agent": create_governor_agent(),
    "validator_agent": create_validator_agent(),
}


def register_all_agents(
    orchestrator: str = "business_builder_worker",
    tenant_id: str = "default",
) -> List[str]:
    """
    Register all worker agents with M12 agent registry.

    Returns list of registered agent IDs.
    """
    registered = []

    try:
        from app.agents.sba.service import get_sba_service

        sba_service = get_sba_service()

        for agent_id, agent_def in WORKER_AGENTS.items():
            # Update orchestrator
            agent_def.enabling_management_systems.orchestrator = orchestrator

            try:
                sba_service.register_agent(
                    agent_id=agent_id,
                    agent_name=agent_id.replace("_", " ").title(),
                    agent_type="worker_agent",
                    sba=agent_def.to_dict(),
                    tenant_id=tenant_id,
                )
                registered.append(agent_id)
            except Exception:
                # Agent may already exist
                pass

    except ImportError:
        # SBA service not available, agents will be registered lazily
        pass

    return registered
