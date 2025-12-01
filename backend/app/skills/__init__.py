# NOVA Skills Package
# Pluggable skill adapters for agent execution

from .registry import (
    # Core functions
    get_skill,
    get_skill_entry,
    register_skill,
    list_skills,
    get_skill_manifest,
    skill_exists,
    # Factory functions
    create_skill_instance,
    create_skill_with_config,
    # Configuration
    set_skill_config,
    get_skill_config,
    get_skills_by_tag,
    # Types
    SkillInterface,
    SkillEntry,
    # Decorator
    skill,
)

# Import skills to trigger registration
from .http_call import HttpCallSkill
from .calendar_write import CalendarWriteSkill
from .llm_invoke import LLMInvokeSkill
from .json_transform import JsonTransformSkill
from .postgres_query import PostgresQuerySkill

__all__ = [
    # Core
    "get_skill",
    "get_skill_entry",
    "register_skill",
    "list_skills",
    "get_skill_manifest",
    "skill_exists",
    # Factory
    "create_skill_instance",
    "create_skill_with_config",
    # Config
    "set_skill_config",
    "get_skill_config",
    "get_skills_by_tag",
    # Types
    "SkillInterface",
    "SkillEntry",
    # Decorator
    "skill",
    # Skills
    "HttpCallSkill",
    "CalendarWriteSkill",
    "LLMInvokeSkill",
    "JsonTransformSkill",
    "PostgresQuerySkill",
]
