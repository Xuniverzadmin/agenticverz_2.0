# NOVA Skills Package
# Pluggable skill adapters for agent execution
#
# IMPORT HYGIENE: This module uses lazy imports to avoid pulling heavy
# dependencies (httpx, anthropic, etc.) when only metadata is needed.
# Skills are loaded on-demand via load_skill() or load_all_skills().

from typing import TYPE_CHECKING

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

# Type hints only - no runtime import
if TYPE_CHECKING:
    from .http_call import HttpCallSkill
    from .calendar_write import CalendarWriteSkill
    from .llm_invoke import LLMInvokeSkill
    from .json_transform import JsonTransformSkill
    from .postgres_query import PostgresQuerySkill
    from .email_send import EmailSendSkill
    # M11 Skills
    from .kv_store import KVStoreSkill
    from .slack_send import SlackSendSkill
    from .webhook_send import WebhookSendSkill
    from .voyage_embed import VoyageEmbedSkill


# Skill module paths for lazy loading
_SKILL_MODULES = {
    "HttpCallSkill": ".http_call",
    "CalendarWriteSkill": ".calendar_write",
    "LLMInvokeSkill": ".llm_invoke",
    "JsonTransformSkill": ".json_transform",
    "PostgresQuerySkill": ".postgres_query",
    "EmailSendSkill": ".email_send",
    # M11 Skills
    "KVStoreSkill": ".kv_store",
    "SlackSendSkill": ".slack_send",
    "WebhookSendSkill": ".webhook_send",
    "VoyageEmbedSkill": ".voyage_embed",
}

_loaded_skills = {}


def load_skill(name: str):
    """
    Lazy-load a skill class by name.

    Args:
        name: Skill class name (e.g., "HttpCallSkill")

    Returns:
        The skill class

    Raises:
        ImportError: If skill not found
    """
    if name in _loaded_skills:
        return _loaded_skills[name]

    if name not in _SKILL_MODULES:
        raise ImportError(f"Unknown skill: {name}. Available: {list(_SKILL_MODULES.keys())}")

    import importlib
    module = importlib.import_module(_SKILL_MODULES[name], package="app.skills")
    skill_class = getattr(module, name)
    _loaded_skills[name] = skill_class
    return skill_class


def load_all_skills():
    """
    Load all registered skills. Call this when you need all skills registered.

    This triggers the @skill decorator for each skill class, registering them
    with the skill registry.
    """
    for name in _SKILL_MODULES:
        load_skill(name)


def __getattr__(name: str):
    """
    Module-level __getattr__ for lazy skill loading.

    Allows `from app.skills import HttpCallSkill` to work without
    eagerly importing all skills.
    """
    if name in _SKILL_MODULES:
        return load_skill(name)
    raise AttributeError(f"module 'app.skills' has no attribute '{name}'")


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
    # Lazy loaders
    "load_skill",
    "load_all_skills",
    # Skills (lazy-loaded)
    "HttpCallSkill",
    "CalendarWriteSkill",
    "LLMInvokeSkill",
    "JsonTransformSkill",
    "PostgresQuerySkill",
    "EmailSendSkill",
    # M11 Skills
    "KVStoreSkill",
    "SlackSendSkill",
    "WebhookSendSkill",
    "VoyageEmbedSkill",
]
