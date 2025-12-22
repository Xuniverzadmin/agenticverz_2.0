# NOVA Schemas Package
# Pydantic models for Plan, Skills, Agents, and Artifacts
# JSON Schemas for M0 machine-native contracts

import json
from pathlib import Path

from .agent import (
    AgentCapabilities,
    AgentConfig,
    PlannerConfig,
)
from .artifact import (
    Artifact,
    ArtifactType,
)
from .plan import (
    OnErrorPolicy,
    Plan,
    PlanMetadata,
    PlanStep,
    StepStatus,
)
from .retry import (
    BackoffStrategy,
    RetryPolicy,
)
from .skill import (
    HttpCallInput,
    HttpCallOutput,
    LLMInvokeInput,
    LLMInvokeOutput,
    SkillInputBase,
    SkillOutputBase,
)

# M0: JSON Schema loaders for machine-native contracts
_SCHEMA_DIR = Path(__file__).parent


def load_json_schema(name: str) -> dict:
    """Load a JSON schema by name (without .schema.json extension)."""
    schema_path = _SCHEMA_DIR / f"{name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {name}")
    with open(schema_path, "r") as f:
        return json.load(f)


def get_structured_outcome_schema() -> dict:
    """Get the StructuredOutcome JSON schema."""
    return load_json_schema("structured_outcome")


def get_skill_metadata_schema() -> dict:
    """Get the SkillMetadata JSON schema."""
    return load_json_schema("skill_metadata")


def get_resource_contract_schema() -> dict:
    """Get the ResourceContract JSON schema."""
    return load_json_schema("resource_contract")


def get_agent_profile_schema() -> dict:
    """Get the AgentProfile JSON schema."""
    return load_json_schema("agent_profile")


__all__ = [
    # Plan
    "Plan",
    "PlanStep",
    "StepStatus",
    "OnErrorPolicy",
    "PlanMetadata",
    # Skill I/O
    "SkillInputBase",
    "SkillOutputBase",
    "HttpCallInput",
    "HttpCallOutput",
    "LLMInvokeInput",
    "LLMInvokeOutput",
    # Agent
    "AgentCapabilities",
    "AgentConfig",
    "PlannerConfig",
    # Artifact
    "Artifact",
    "ArtifactType",
    # Retry
    "RetryPolicy",
    "BackoffStrategy",
    # M0: JSON Schema loaders
    "load_json_schema",
    "get_structured_outcome_schema",
    "get_skill_metadata_schema",
    "get_resource_contract_schema",
    "get_agent_profile_schema",
]
