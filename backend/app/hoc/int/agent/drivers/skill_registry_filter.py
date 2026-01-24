# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: startup (registry initialization)
#   Execution: sync
# Role: Filter skill registry based on governance profile
# Callers: skills/__init__.py, skill execution
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-066

"""
Module: skill_registry_filter
Purpose: Filter skill registry based on governance profile.

Ungoverned skills (e.g., raw LLM invocation, raw HTTP, raw SQL) are
removed from the registry in governed environments.

Imports (Dependencies):
    - None (standalone, governance profile passed as parameter)

Exports (Provides):
    - filter_skills_for_governance(registry, profile) -> FilteredRegistry
    - validate_skill_governance(skill_name) -> bool
    - UNGOVERNED_SKILLS: Set of skills to exclude in governed mode
    - GOVERNED_REPLACEMENTS: Map of ungoverned -> governed skills

Wiring Points:
    - Called from: skills/__init__.py at startup
    - Called from: skill execution for runtime validation

Acceptance Criteria:
    - [x] AC-066-01: llm_invoke not in STRICT registry
    - [x] AC-066-02: llm_invoke_governed available
    - [x] AC-066-03: OBSERVE_ONLY keeps all skills
    - [x] AC-066-04: Removal logged
    - [x] AC-066-05: Plans use governed skill
"""

from typing import Any, Dict, Set, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger("nova.skills.skill_registry_filter")


class GovernanceProfile(str, Enum):
    """Governance profile levels."""
    STRICT = "strict"          # All ungoverned skills removed
    STANDARD = "standard"      # Most ungoverned skills removed
    OBSERVE_ONLY = "observe_only"  # All skills kept (for debugging)


# Skills that bypass governance - MUST be excluded in governed environments
UNGOVERNED_SKILLS: Set[str] = {
    "llm_invoke",           # Ungoverned LLM invocation
    "raw_http_call",        # Ungoverned HTTP (arbitrary URLs)
    "raw_sql_query",        # Ungoverned SQL (arbitrary queries)
    "shell_execute",        # Ungoverned shell execution
    "file_system_access",   # Ungoverned filesystem access
}

# Governed replacements - map ungoverned skill to its governed counterpart
GOVERNED_REPLACEMENTS: Dict[str, str] = {
    "llm_invoke": "llm_invoke_governed",
    "raw_http_call": "http_connector",
    "raw_sql_query": "sql_gateway",
    "shell_execute": "shell_execute_governed",
    "file_system_access": "file_access_governed",
}

# Skills that require explicit approval even in governed mode
APPROVAL_REQUIRED_SKILLS: Set[str] = {
    "shell_execute_governed",
    "file_access_governed",
    "database_write",
}


@dataclass
class FilterResult:
    """Result of skill registry filtering."""
    filtered_registry: Dict[str, Any]
    removed_skills: List[str]
    replaced_skills: Dict[str, str]  # removed -> replacement
    warnings: List[str]


def filter_skills_for_governance(
    registry: Dict[str, Any],
    governance_profile: str,
) -> FilterResult:
    """
    Filter skill registry based on governance profile.

    In STRICT or STANDARD profiles:
    - Remove ungoverned skills
    - Log removal for audit
    - Track replacements

    In OBSERVE_ONLY profile:
    - Keep all skills (for debugging/development)
    - Log warning about ungoverned access

    Args:
        registry: Original skill registry
        governance_profile: STRICT, STANDARD, or OBSERVE_ONLY

    Returns:
        FilterResult with filtered registry and audit info
    """
    # Normalize profile
    try:
        profile = GovernanceProfile(governance_profile.lower())
    except ValueError:
        logger.warning("skill_registry_filter.invalid_profile", extra={
            "profile": governance_profile,
            "defaulting_to": GovernanceProfile.STRICT.value,
        })
        profile = GovernanceProfile.STRICT

    if profile == GovernanceProfile.OBSERVE_ONLY:
        # Keep all skills but log warning
        ungoverned_present = UNGOVERNED_SKILLS & set(registry.keys())
        if ungoverned_present:
            logger.warning("skill_registry_filter.observe_only_mode", extra={
                "ungoverned_skills_available": list(ungoverned_present),
                "warning": "Ungoverned skills are accessible in OBSERVE_ONLY mode",
            })

        return FilterResult(
            filtered_registry=registry.copy(),
            removed_skills=[],
            replaced_skills={},
            warnings=[
                f"OBSERVE_ONLY: Ungoverned skills available: {list(ungoverned_present)}"
            ] if ungoverned_present else [],
        )

    # STRICT or STANDARD: Remove ungoverned skills
    filtered: Dict[str, Any] = {}
    removed: List[str] = []
    replaced: Dict[str, str] = {}
    warnings: List[str] = []

    for skill_name, skill in registry.items():
        if skill_name in UNGOVERNED_SKILLS:
            removed.append(skill_name)

            # Check if governed replacement exists
            replacement = GOVERNED_REPLACEMENTS.get(skill_name)
            if replacement:
                if replacement in registry:
                    replaced[skill_name] = replacement
                    logger.info("skill_registry_filter.replaced", extra={
                        "removed": skill_name,
                        "replacement": replacement,
                        "profile": profile.value,
                    })
                else:
                    warnings.append(
                        f"Replacement '{replacement}' for '{skill_name}' not found in registry"
                    )
                    logger.warning("skill_registry_filter.replacement_missing", extra={
                        "removed": skill_name,
                        "expected_replacement": replacement,
                    })
        else:
            filtered[skill_name] = skill

    if removed:
        logger.info("skill_registry_filter.filtered", extra={
            "removed_skills": removed,
            "replaced_count": len(replaced),
            "governance_profile": profile.value,
            "remaining_count": len(filtered),
        })

    return FilterResult(
        filtered_registry=filtered,
        removed_skills=removed,
        replaced_skills=replaced,
        warnings=warnings,
    )


def validate_skill_governance(skill_name: str) -> bool:
    """
    Check if a skill is governed (safe to use in governed mode).

    Args:
        skill_name: Name of the skill to check

    Returns:
        True if the skill is governed, False if ungoverned
    """
    return skill_name not in UNGOVERNED_SKILLS


def get_governed_replacement(skill_name: str) -> Optional[str]:
    """
    Get the governed replacement for an ungoverned skill.

    Args:
        skill_name: Name of the ungoverned skill

    Returns:
        Name of governed replacement, or None if no replacement exists
    """
    return GOVERNED_REPLACEMENTS.get(skill_name)


def is_approval_required(skill_name: str) -> bool:
    """
    Check if a skill requires explicit approval.

    Some governed skills still require approval (e.g., shell execution).

    Args:
        skill_name: Name of the skill

    Returns:
        True if approval is required
    """
    return skill_name in APPROVAL_REQUIRED_SKILLS


def get_skill_governance_info(skill_name: str) -> Dict[str, Any]:
    """
    Get comprehensive governance info for a skill.

    Args:
        skill_name: Name of the skill

    Returns:
        Dictionary with governance information
    """
    is_governed = skill_name not in UNGOVERNED_SKILLS
    replacement = GOVERNED_REPLACEMENTS.get(skill_name) if not is_governed else None
    requires_approval = skill_name in APPROVAL_REQUIRED_SKILLS

    return {
        "skill_name": skill_name,
        "is_governed": is_governed,
        "replacement": replacement,
        "requires_approval": requires_approval,
        "can_use_in_strict_mode": is_governed,
    }
