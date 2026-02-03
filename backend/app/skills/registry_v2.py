# skills/registry_v2.py
"""
Skill Registry v2 (M2)

Enhanced registry that integrates with M1 runtime interfaces:
- SkillDescriptor from runtime/core.py
- Versioned skill resolution
- Async handler registration
- Persistence layer support (sqlite for dev, Postgres adapter for prod)

This registry maintains backwards compatibility with registry.py while
providing the new machine-native interfaces.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
)

_runtime_path = str(Path(__file__).parent.parent / "worker" / "runtime")

    sys.path.insert(0, _runtime_path)

from core import SkillDescriptor

logger = logging.getLogger("aos.skills.registry")


# Type alias for async skill handlers
SkillHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, Any]]


@dataclass
class SkillVersion:
    """Semantic version for skills."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_str: str) -> "SkillVersion":
        """Parse version string like '1.2.3'."""
        parts = version_str.split(".")
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 0,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
        )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "SkillVersion") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SkillVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))


@dataclass
class SkillRegistration:
    """
    Complete skill registration including descriptor, handler, and metadata.

    This is the internal representation used by the registry.
    """

    descriptor: SkillDescriptor
    handler: SkillHandler
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_stub: bool = False
    tags: List[str] = field(default_factory=list)

    @property
    def skill_id(self) -> str:
        return self.descriptor.skill_id

    @property
    def version(self) -> str:
        return self.descriptor.version

    @property
    def versioned_key(self) -> str:
        """Key for versioned storage: skill_id:version"""
        return f"{self.skill_id}:{self.version}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for persistence (excludes handler)."""
        return {
            "descriptor": self.descriptor.to_dict(),
            "registered_at": self.registered_at,
            "is_stub": self.is_stub,
            "tags": self.tags,
        }


class SkillRegistry:
    """
    M2 Skill Registry with versioning and persistence support.

    Features:
    - In-memory registry with read-write API
    - Optional persistence layer (sqlite for dev)
    - Versioning: skill_id:version resolution
    - Integration with M1 runtime interfaces
    """

    def __init__(self, persistence_path: Optional[str] = None):
        """
        Initialize registry.

        Args:
            persistence_path: Path to sqlite db for persistence (None for in-memory only)
        """
        # In-memory registries
        self._by_id: Dict[str, SkillRegistration] = {}  # skill_id -> latest version
        self._by_versioned_key: Dict[str, SkillRegistration] = {}  # skill_id:version -> registration
        self._handlers: Dict[str, SkillHandler] = {}  # skill_id -> handler (for runtime)

        # Persistence
        self._persistence_path = persistence_path
        self._db: Optional[sqlite3.Connection] = None

        if persistence_path:
            self._init_persistence()

    def _init_persistence(self) -> None:
        """Initialize sqlite persistence layer."""
        self._db = sqlite3.connect(self._persistence_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT NOT NULL,
                version TEXT NOT NULL,
                descriptor_json TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                is_stub INTEGER NOT NULL DEFAULT 0,
                tags_json TEXT NOT NULL DEFAULT '[]',
                PRIMARY KEY (skill_id, version)
            )
        """
        )
        self._db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_skills_id ON skills(skill_id)
        """
        )
        self._db.commit()

    def register(
        self,
        descriptor: SkillDescriptor,
        handler: SkillHandler,
        is_stub: bool = False,
        tags: Optional[List[str]] = None,
    ) -> SkillRegistration:
        """
        Register a skill with its descriptor and handler.

        Args:
            descriptor: Skill metadata
            handler: Async function that executes the skill
            is_stub: Whether this is a stub implementation
            tags: Optional tags for categorization

        Returns:
            SkillRegistration object

        Raises:
            ValueError: If skill_id:version already registered
        """
        registration = SkillRegistration(descriptor=descriptor, handler=handler, is_stub=is_stub, tags=tags or [])

        # Check for duplicate versioned registration
        if registration.versioned_key in self._by_versioned_key:
            raise ValueError(f"Skill already registered: {registration.versioned_key}")

        # Store in memory
        self._by_versioned_key[registration.versioned_key] = registration
        self._by_id[descriptor.skill_id] = registration  # Latest version
        self._handlers[descriptor.skill_id] = handler

        # Persist if configured
        if self._db:
            self._persist_registration(registration)

        logger.info(
            "skill_registered",
            extra={"skill_id": descriptor.skill_id, "version": descriptor.version, "is_stub": is_stub},
        )

        return registration

    def _persist_registration(self, reg: SkillRegistration) -> None:
        """Persist registration to sqlite."""
        if not self._db:
            return

        self._db.execute(
            """
            INSERT OR REPLACE INTO skills
            (skill_id, version, descriptor_json, registered_at, is_stub, tags_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reg.skill_id,
                reg.version,
                json.dumps(reg.descriptor.to_dict()),
                reg.registered_at,
                1 if reg.is_stub else 0,
                json.dumps(reg.tags),
            ),
        )
        self._db.commit()

    def deregister(self, skill_id: str, version: Optional[str] = None) -> bool:
        """
        Remove a skill from the registry.

        Args:
            skill_id: Skill identifier
            version: Specific version (None = all versions)

        Returns:
            True if skill was removed
        """
        removed = False

        if version:
            # Remove specific version
            key = f"{skill_id}:{version}"
            if key in self._by_versioned_key:
                del self._by_versioned_key[key]
                removed = True
                # Update latest if needed
                remaining = [r for r in self._by_versioned_key.values() if r.skill_id == skill_id]
                if remaining:
                    latest = max(remaining, key=lambda r: SkillVersion.parse(r.version))
                    self._by_id[skill_id] = latest
                    self._handlers[skill_id] = latest.handler
                else:
                    self._by_id.pop(skill_id, None)
                    self._handlers.pop(skill_id, None)
        else:
            # Remove all versions
            keys_to_remove = [k for k in self._by_versioned_key if k.startswith(f"{skill_id}:")]
            for key in keys_to_remove:
                del self._by_versioned_key[key]
                removed = True
            self._by_id.pop(skill_id, None)
            self._handlers.pop(skill_id, None)

        # Persist removal
        if removed and self._db:
            if version:
                self._db.execute("DELETE FROM skills WHERE skill_id = ? AND version = ?", (skill_id, version))
            else:
                self._db.execute("DELETE FROM skills WHERE skill_id = ?", (skill_id,))
            self._db.commit()

        return removed

    def resolve(self, skill_id: str, version: Optional[str] = None) -> Optional[SkillRegistration]:
        """
        Resolve a skill by ID and optional version.

        Args:
            skill_id: Skill identifier
            version: Specific version (None = latest)

        Returns:
            SkillRegistration or None
        """
        if version:
            return self._by_versioned_key.get(f"{skill_id}:{version}")
        return self._by_id.get(skill_id)

    def get_handler(self, skill_id: str) -> Optional[SkillHandler]:
        """Get handler for a skill (for runtime integration)."""
        return self._handlers.get(skill_id)

    def get_descriptor(self, skill_id: str) -> Optional[SkillDescriptor]:
        """Get descriptor for a skill."""
        reg = self._by_id.get(skill_id)
        return reg.descriptor if reg else None

    def list(self) -> List[SkillRegistration]:
        """List all registered skills (latest versions only)."""
        return list(self._by_id.values())

    def list_all_versions(self) -> List[SkillRegistration]:
        """List all registered skills including all versions."""
        return list(self._by_versioned_key.values())

    def list_by_tag(self, tag: str) -> List[SkillRegistration]:
        """List skills with a specific tag."""
        return [r for r in self._by_id.values() if tag in r.tags]

    def exists(self, skill_id: str, version: Optional[str] = None) -> bool:
        """Check if a skill is registered."""
        if version:
            return f"{skill_id}:{version}" in self._by_versioned_key
        return skill_id in self._by_id

    def get_all_skill_ids(self) -> List[str]:
        """Get list of all registered skill IDs."""
        return list(self._by_id.keys())

    def get_manifest(self) -> List[Dict[str, Any]]:
        """Get skill manifest for planner context."""
        return [
            {
                "skill_id": reg.skill_id,
                "name": reg.descriptor.name,
                "version": reg.version,
                "is_stub": reg.is_stub,
                "cost_model": reg.descriptor.cost_model,
                "failure_modes": list(reg.descriptor.failure_modes),
                "tags": reg.tags,
            }
            for reg in self._by_id.values()
        ]

    def close(self) -> None:
        """Close persistence connection."""
        if self._db:
            self._db.close()
            self._db = None


# Global registry instance
_GLOBAL_REGISTRY: Optional[SkillRegistry] = None


def get_global_registry() -> SkillRegistry:
    """Get the global registry instance (creates if needed)."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = SkillRegistry()
    return _GLOBAL_REGISTRY


def set_global_registry(registry: SkillRegistry) -> None:
    """Set the global registry instance."""
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = registry


def register_skill(
    descriptor: SkillDescriptor, handler: SkillHandler, is_stub: bool = False, tags: Optional[List[str]] = None
) -> SkillRegistration:
    """Register a skill in the global registry."""
    return get_global_registry().register(descriptor, handler, is_stub, tags)


def get_skill_handler(skill_id: str) -> Optional[SkillHandler]:
    """Get a skill handler from the global registry."""
    return get_global_registry().get_handler(skill_id)


def get_skill_descriptor(skill_id: str) -> Optional[SkillDescriptor]:
    """Get a skill descriptor from the global registry."""
    return get_global_registry().get_descriptor(skill_id)


# =============================================================================
# Version-Gating + Contract Diffing
# =============================================================================


@dataclass
class ContractDiff:
    """
    Represents differences between two skill contracts.

    Used for:
    - Version compatibility checks
    - Breaking change detection
    - Migration planning
    """

    skill_id: str
    old_version: str
    new_version: str
    breaking_changes: List[Dict[str, Any]] = field(default_factory=list)
    non_breaking_changes: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return len(self.breaking_changes) > 0

    @property
    def is_compatible(self) -> bool:
        """Check if new version is backwards compatible."""
        return not self.has_breaking_changes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "skill_id": self.skill_id,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "breaking_changes": self.breaking_changes,
            "non_breaking_changes": self.non_breaking_changes,
            "warnings": self.warnings,
            "is_compatible": self.is_compatible,
        }


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two semantic versions.

    Returns:
        -1 if v1 < v2
        0 if v1 == v2
        1 if v1 > v2
    """
    sv1 = SkillVersion.parse(v1.split("-")[0])  # Strip suffix like "-stub"
    sv2 = SkillVersion.parse(v2.split("-")[0])

    if sv1 < sv2:
        return -1
    elif sv1 == sv2:
        return 0
    return 1


def diff_contracts(old_descriptor: SkillDescriptor, new_descriptor: SkillDescriptor) -> ContractDiff:
    """
    Compare two skill descriptors and identify changes.

    Breaking changes:
    - Removing required input fields
    - Adding required input fields
    - Changing stable_fields from DETERMINISTIC to non-deterministic
    - Removing failure_modes (consumers may depend on them)

    Non-breaking changes:
    - Adding optional input fields
    - Adding new failure_modes
    - Increasing constraints (more permissive)
    - Version bump within same major version

    Args:
        old_descriptor: Previous version descriptor
        new_descriptor: New version descriptor

    Returns:
        ContractDiff with change analysis
    """
    diff = ContractDiff(
        skill_id=new_descriptor.skill_id, old_version=old_descriptor.version, new_version=new_descriptor.version
    )

    # Check major version bump
    old_major = SkillVersion.parse(old_descriptor.version.split("-")[0]).major
    new_major = SkillVersion.parse(new_descriptor.version.split("-")[0]).major

    if new_major > old_major:
        diff.warnings.append(f"Major version bump from {old_major} to {new_major} - breaking changes expected")

    # Check stable_fields changes
    old_stable = set(old_descriptor.stable_fields.keys())
    new_stable = set(new_descriptor.stable_fields.keys())

    removed_stable = old_stable - new_stable
    if removed_stable:
        diff.breaking_changes.append(
            {
                "type": "stable_field_removed",
                "fields": list(removed_stable),
                "message": f"Stable fields removed: {removed_stable}",
            }
        )

    # Check for determinism changes
    for field_name in old_stable & new_stable:
        old_val = old_descriptor.stable_fields.get(field_name)
        new_val = new_descriptor.stable_fields.get(field_name)
        if old_val == "DETERMINISTIC" and new_val != "DETERMINISTIC":
            diff.breaking_changes.append(
                {
                    "type": "determinism_weakened",
                    "field": field_name,
                    "message": f"Field {field_name} changed from DETERMINISTIC to {new_val}",
                }
            )

    # Check failure_modes
    old_modes = {fm.get("code") for fm in old_descriptor.failure_modes if isinstance(fm, dict)}
    new_modes = {fm.get("code") for fm in new_descriptor.failure_modes if isinstance(fm, dict)}

    removed_modes = old_modes - new_modes
    if removed_modes:
        diff.breaking_changes.append(
            {
                "type": "failure_mode_removed",
                "codes": list(removed_modes),
                "message": f"Failure modes removed: {removed_modes}",
            }
        )

    added_modes = new_modes - old_modes
    if added_modes:
        diff.non_breaking_changes.append(
            {"type": "failure_mode_added", "codes": list(added_modes), "message": f"New failure modes: {added_modes}"}
        )

    # Check constraints
    old_constraints = old_descriptor.constraints or {}
    new_constraints = new_descriptor.constraints or {}

    for key in old_constraints:
        if key in new_constraints:
            old_val = old_constraints[key]
            new_val = new_constraints[key]
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                if new_val < old_val:
                    diff.breaking_changes.append(
                        {
                            "type": "constraint_tightened",
                            "constraint": key,
                            "old_value": old_val,
                            "new_value": new_val,
                            "message": f"Constraint {key} reduced from {old_val} to {new_val}",
                        }
                    )

    # Check cost_model changes (informational)
    old_cost = old_descriptor.cost_model or {}
    new_cost = new_descriptor.cost_model or {}
    if old_cost != new_cost:
        diff.non_breaking_changes.append(
            {"type": "cost_model_changed", "old": old_cost, "new": new_cost, "message": "Cost model has changed"}
        )

    return diff


def is_version_compatible(required_version: str, actual_version: str, strict: bool = False) -> bool:
    """
    Check if actual version satisfies the required version.

    Version compatibility rules:
    - Exact match always compatible
    - Within same major version: compatible (unless strict)
    - Different major version: incompatible

    Args:
        required_version: Version required by consumer
        actual_version: Version of registered skill
        strict: If True, require exact match

    Returns:
        True if compatible
    """
    if required_version == actual_version:
        return True

    if strict:
        return False

    # Parse versions (strip suffixes like "-stub")
    req = SkillVersion.parse(required_version.split("-")[0])
    act = SkillVersion.parse(actual_version.split("-")[0])

    # Same major version is compatible
    return req.major == act.major


def resolve_skill_with_version(
    registry: SkillRegistry, skill_id: str, required_version: Optional[str] = None, strict: bool = False
) -> Optional[SkillRegistration]:
    """
    Resolve a skill with version compatibility checking.

    Args:
        registry: Skill registry
        skill_id: Skill identifier
        required_version: Required version (None = latest)
        strict: Require exact version match

    Returns:
        Compatible SkillRegistration or None

    Raises:
        ValueError: If skill exists but version is incompatible
    """
    if required_version is None:
        # Return latest version
        return registry.resolve(skill_id)

    # Try exact version first
    exact = registry.resolve(skill_id, required_version)
    if exact:
        return exact

    # Try to find compatible version
    if not strict:
        latest = registry.resolve(skill_id)
        if latest and is_version_compatible(required_version, latest.version):
            return latest

        # Check all versions for compatibility
        all_versions = [reg for reg in registry.list_all_versions() if reg.skill_id == skill_id]

        for reg in sorted(all_versions, key=lambda r: SkillVersion.parse(r.version.split("-")[0]), reverse=True):
            if is_version_compatible(required_version, reg.version):
                return reg

    return None
