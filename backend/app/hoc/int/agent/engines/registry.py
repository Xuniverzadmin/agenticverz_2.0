# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Protocol defining the skill interface.
# Skills Registry
# Central registry for pluggable skill adapters with decorator-based registration

import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

from pydantic import BaseModel

logger = logging.getLogger("nova.skills.registry")


# ====================
# Skill Protocol
# ====================


@runtime_checkable
class SkillInterface(Protocol):
    """Protocol defining the skill interface.

    All skills must implement this interface.
    """

    VERSION: str
    DESCRIPTION: str

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill with given parameters.

        Args:
            params: Skill-specific parameters

        Returns:
            Result dict with 'skill', 'skill_version', 'result', 'duration', etc.
        """
        ...

    @classmethod
    def get_input_schema(cls) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for input validation."""
        ...

    @classmethod
    def get_output_schema(cls) -> Optional[Type[BaseModel]]:
        """Get the Pydantic model for output validation."""
        ...


# ====================
# Skill Entry
# ====================


class SkillEntry:
    """Registry entry for a registered skill."""

    def __init__(
        self,
        name: str,
        cls: Type,
        version: str,
        description: str,
        input_schema: Optional[Type[BaseModel]] = None,
        output_schema: Optional[Type[BaseModel]] = None,
        config_schema: Optional[Type[BaseModel]] = None,
        tags: Optional[List[str]] = None,
        default_config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.cls = cls
        self.version = version
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.config_schema = config_schema
        self.tags = tags or []
        self.default_config = default_config or {}

    def create_instance(self, config: Optional[Dict[str, Any]] = None) -> Any:
        """Create an instance of the skill with given config.

        Args:
            config: Configuration dict (merged with defaults)

        Returns:
            Skill instance
        """
        merged_config = {**self.default_config, **(config or {})}

        # Validate config if schema exists
        if self.config_schema and merged_config:
            try:
                validated = self.config_schema(**merged_config)
                merged_config = validated.model_dump()
            except Exception as e:
                logger.warning("skill_config_validation_failed", extra={"skill": self.name, "error": str(e)})
                # Fall through with unvalidated config

        try:
            return self.cls(**merged_config)
        except TypeError:
            # Class doesn't accept kwargs, try no-arg init
            return self.cls()

    def to_manifest(self) -> Dict[str, Any]:
        """Convert to manifest dict for planner consumption."""
        manifest = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
        }

        # Include JSON schema for input if available
        if self.input_schema:
            manifest["input_schema"] = self.input_schema.model_json_schema()

        return manifest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to simple dict (backwards compatible)."""
        return {
            "class": self.cls,
            "version": self.version,
            "name": self.name,
            "description": self.description,
        }


# ====================
# Global Registry
# ====================

_REGISTRY: Dict[str, SkillEntry] = {}

# Type variable for skill class
T = TypeVar("T")


def skill(
    name: str,
    *,
    version: Optional[str] = None,
    description: Optional[str] = None,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    config_schema: Optional[Type[BaseModel]] = None,
    tags: Optional[List[str]] = None,
    default_config: Optional[Dict[str, Any]] = None,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a skill class.

    Usage:
        @skill("http_call", input_schema=HttpCallInput)
        class HttpCallSkill:
            VERSION = "0.2.0"
            ...

    Args:
        name: Unique skill identifier
        version: Override VERSION class attribute
        description: Override DESCRIPTION class attribute
        input_schema: Pydantic model for input validation
        output_schema: Pydantic model for output validation
        config_schema: Pydantic model for config validation
        tags: List of tags for categorization
        default_config: Default configuration values

    Returns:
        Decorator function
    """

    def decorator(cls: Type[T]) -> Type[T]:
        skill_version = version or getattr(cls, "VERSION", "0.0.0")
        skill_description = description or getattr(cls, "DESCRIPTION", f"Skill: {name}")

        # Check for schema methods on class
        actual_input = input_schema
        actual_output = output_schema
        if hasattr(cls, "get_input_schema") and actual_input is None:
            actual_input = cls.get_input_schema()
        if hasattr(cls, "get_output_schema") and actual_output is None:
            actual_output = cls.get_output_schema()

        entry = SkillEntry(
            name=name,
            cls=cls,
            version=skill_version,
            description=skill_description,
            input_schema=actual_input,
            output_schema=actual_output,
            config_schema=config_schema,
            tags=tags,
            default_config=default_config,
        )

        _REGISTRY[name] = entry

        logger.info(
            "skill_registered",
            extra={
                "skill": name,
                "version": skill_version,
                "has_input_schema": actual_input is not None,
                "has_output_schema": actual_output is not None,
            },
        )

        return cls

    return decorator


def register_skill(name: str, cls: Type, version: Optional[str] = None, **kwargs):
    """Register a skill class in the registry (legacy function).

    This is the original registration function, kept for backwards
    compatibility. Prefer using the @skill decorator.

    Args:
        name: Unique skill identifier
        cls: Skill class implementing SkillInterface
        version: Optional version override (defaults to cls.VERSION)
        **kwargs: Additional arguments passed to SkillEntry
    """
    skill_version = version or getattr(cls, "VERSION", "0.0.0")
    skill_description = kwargs.get("description") or getattr(cls, "DESCRIPTION", f"Skill: {name}")

    entry = SkillEntry(
        name=name,
        cls=cls,
        version=skill_version,
        description=skill_description,
        **{k: v for k, v in kwargs.items() if k not in ("description",)},
    )

    _REGISTRY[name] = entry

    logger.info("skill_registered", extra={"skill": name, "version": skill_version})


# ====================
# Registry Access
# ====================


def get_skill(name: str) -> Optional[Dict[str, Any]]:
    """Get a skill entry from the registry (legacy format).

    Args:
        name: Skill identifier

    Returns:
        Dict with 'class', 'version', 'name' or None if not found
    """
    entry = _REGISTRY.get(name)
    if not entry:
        logger.warning("skill_not_found", extra={"skill": name})
        return None
    return entry.to_dict()


def get_skill_entry(name: str) -> Optional[SkillEntry]:
    """Get the full SkillEntry from the registry.

    Args:
        name: Skill identifier

    Returns:
        SkillEntry or None if not found
    """
    entry = _REGISTRY.get(name)
    if not entry:
        logger.warning("skill_not_found", extra={"skill": name})
        return None
    return entry


def create_skill_instance(name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """Create an instance of a skill from the registry.

    This is the factory function that replaces hardcoded instantiation.

    Args:
        name: Skill identifier
        config: Configuration to pass to skill constructor

    Returns:
        Skill instance or None if not found
    """
    entry = get_skill_entry(name)
    if not entry:
        return None
    return entry.create_instance(config)


def list_skills() -> List[Dict[str, Any]]:
    """List all registered skills.

    Returns:
        List of skill metadata dicts
    """
    return [{"name": name, "version": entry.version} for name, entry in _REGISTRY.items()]


def get_skill_manifest() -> List[Dict[str, Any]]:
    """Get skill manifest for planner context.

    Returns:
        List of skill descriptions for planner
    """
    return [entry.to_manifest() for entry in _REGISTRY.values()]


def get_skills_by_tag(tag: str) -> List[SkillEntry]:
    """Get all skills with a specific tag.

    Args:
        tag: Tag to filter by

    Returns:
        List of matching SkillEntry objects
    """
    return [entry for entry in _REGISTRY.values() if tag in entry.tags]


def skill_exists(name: str) -> bool:
    """Check if a skill is registered.

    Args:
        name: Skill identifier

    Returns:
        True if skill exists
    """
    return name in _REGISTRY


# ====================
# Skill Configuration
# ====================

# Global skill configurations (can be loaded from env/config file)
_SKILL_CONFIGS: Dict[str, Dict[str, Any]] = {}


def set_skill_config(name: str, config: Dict[str, Any]):
    """Set configuration for a skill.

    Args:
        name: Skill identifier
        config: Configuration dict
    """
    _SKILL_CONFIGS[name] = config
    logger.info("skill_config_set", extra={"skill": name, "config_keys": list(config.keys())})


def get_skill_config(name: str) -> Dict[str, Any]:
    """Get configuration for a skill.

    Args:
        name: Skill identifier

    Returns:
        Configuration dict (empty if not set)
    """
    return _SKILL_CONFIGS.get(name, {})


def create_skill_with_config(name: str) -> Optional[Any]:
    """Create a skill instance using global configuration.

    This combines registry lookup with global skill config.

    Args:
        name: Skill identifier

    Returns:
        Configured skill instance or None
    """
    config = get_skill_config(name)
    return create_skill_instance(name, config)
