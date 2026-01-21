# NOVA Skills Package
# Pluggable skill adapters for agent execution
#
# IMPORT HYGIENE: This module uses lazy imports to avoid pulling heavy
# dependencies (httpx, anthropic, etc.) when only metadata is needed.
# Skills are loaded on-demand via load_skill() or load_all_skills().
#
# GAP-066: Skill Registry Filter Integration
# In governed environments, ungoverned skills are filtered from the registry
# to prevent unsafe operations (raw SQL, raw HTTP, shell execution, etc.)

from typing import TYPE_CHECKING, Optional
import logging

_logger = logging.getLogger("nova.skills")

from .registry import (
    SkillEntry,
    # Types
    SkillInterface,
    # Factory functions
    create_skill_instance,
    create_skill_with_config,
    # Core functions
    get_skill,
    get_skill_config,
    get_skill_entry,
    get_skill_manifest,
    get_skills_by_tag,
    list_skills,
    register_skill,
    # Configuration
    set_skill_config,
    # Decorator
    skill,
    skill_exists,
)

# Type hints only - no runtime import
if TYPE_CHECKING:
    from .calendar_write import CalendarWriteSkill
    from .email_send import EmailSendSkill
    from .http_call import HttpCallSkill
    from .json_transform import JsonTransformSkill

    # M11 Skills
    from .kv_store import KVStoreSkill
    from .llm_invoke import LLMInvokeSkill
    from .postgres_query import PostgresQuerySkill
    from .slack_send import SlackSendSkill
    from .voyage_embed import VoyageEmbedSkill
    from .webhook_send import WebhookSendSkill


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
    # SDSR Testing Skills
    "SDSRFailTriggerSkill": ".sdsr_fail_trigger",
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


# =============================================================================
# GAP-066: Skill Registry Filter for Governance
# =============================================================================

# Track governance filtering state
_governance_filter_applied = False
_governance_profile: Optional[str] = None


def apply_governance_filter(profile: str = "strict") -> dict:
    """
    Apply governance filtering to the skill registry.

    This function filters ungoverned skills from the registry based on
    the governance profile. In strict mode, unsafe skills are removed.

    Args:
        profile: Governance profile ("strict", "permissive", "audit_only")

    Returns:
        dict with filter results including removed skills and warnings

    GAP-066: Skill Registry Filter Integration
    """
    global _governance_filter_applied, _governance_profile

    if _governance_filter_applied:
        _logger.debug(
            "governance_filter_already_applied",
            extra={"profile": _governance_profile},
        )
        return {
            "already_applied": True,
            "profile": _governance_profile,
        }

    try:
        from .skill_registry_filter import (
            filter_skills_for_governance,
            UNGOVERNED_SKILLS,
        )

        # Get current registry state
        from .registry import _skill_registry

        result = filter_skills_for_governance(
            registry=_skill_registry,
            governance_profile=profile,
        )

        _governance_filter_applied = True
        _governance_profile = profile

        _logger.info(
            "governance_filter_applied",
            extra={
                "profile": profile,
                "removed_count": len(result.removed_skills),
                "warning_count": len(result.warnings),
                "removed_skills": list(result.removed_skills),
            },
        )

        return {
            "applied": True,
            "profile": profile,
            "removed_skills": list(result.removed_skills),
            "warnings": result.warnings,
            "remaining_skills": list(result.allowed_skills),
        }

    except ImportError as e:
        _logger.warning(
            "governance_filter_import_failed",
            extra={"error": str(e)},
        )
        return {
            "applied": False,
            "error": f"Filter module not available: {e}",
        }
    except Exception as e:
        _logger.error(
            "governance_filter_failed",
            extra={"error": str(e)},
        )
        return {
            "applied": False,
            "error": str(e),
        }


def is_governance_filter_active() -> bool:
    """Check if governance filtering is active."""
    return _governance_filter_applied


def get_governance_profile() -> Optional[str]:
    """Get the active governance profile."""
    return _governance_profile


def list_governed_skills() -> list[dict]:
    """
    List skills available under current governance profile.

    If no governance filter is applied, returns all registered skills.
    Returns list of skill dicts with name, version, description, etc.
    """
    all_skills = list_skills()

    if not _governance_filter_applied:
        return all_skills

    try:
        from .skill_registry_filter import UNGOVERNED_SKILLS

        # Filter out ungoverned skills by name
        return [s for s in all_skills if s.get("name") not in UNGOVERNED_SKILLS]
    except ImportError:
        return all_skills


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
    # GAP-066: Governance Filter
    "apply_governance_filter",
    "is_governance_filter_active",
    "get_governance_profile",
    "list_governed_skills",
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
