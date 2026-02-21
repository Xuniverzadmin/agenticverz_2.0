# capability_id: CAP-008
# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Resolve capability IDs to endpoints via AURORA registry
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml, AURORA_L2_CAPABILITY_REGISTRY

"""
Panel Capability Resolver — Binds panels to capabilities, not endpoints.

Core principle:
    Panels bind to capability IDs (semantic).
    Endpoints are resolved via AURORA capability registry (reality).
    Only OBSERVED/TRUSTED capabilities may be called.

This enforces:
    - GAP 6 fix: Capability registry now used
    - GAP 4 fix: SDSR observation status checked before calls
    - Clean separation: spec = meaning, registry = plumbing
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("nova.panel_adapter.capability_resolver")

# Path to AURORA capability registry (canonical source of truth for endpoints)
# __file__ is at: backend/app/services/ai_console_panel_adapter/panel_capability_resolver.py
# parents[4] = agenticverz2.0 (repo root)
REPO_ROOT = Path(__file__).resolve().parents[4]
CAPABILITY_REGISTRY_DIR = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"


class CapabilityStatus(str, Enum):
    """4-state capability model from AURORA (plus transitional states)."""
    DISCOVERED = "DISCOVERED"  # Auto-seeded, action name exists → NOT callable
    DECLARED = "DECLARED"      # Backend claims it exists → NOT callable
    ASSUMED = "ASSUMED"        # Assumed to exist but not verified → NOT callable
    OBSERVED = "OBSERVED"      # SDSR proved behavior → CALLABLE
    TRUSTED = "TRUSTED"        # CI-enforced, stable → CALLABLE
    DEPRECATED = "DEPRECATED"  # No longer valid → NOT callable


# Which statuses allow API calls
CALLABLE_STATUSES = {CapabilityStatus.OBSERVED, CapabilityStatus.TRUSTED}


@dataclass
class ResolvedCapability:
    """Resolution result for a capability lookup."""
    capability_id: str
    status: CapabilityStatus
    endpoint: Optional[str]
    method: str
    domain: str
    is_callable: bool
    reason: Optional[str] = None
    observation: Optional[Dict[str, Any]] = None


@dataclass
class CapabilityRegistryEntry:
    """Parsed capability registry entry."""
    capability_id: str
    status: CapabilityStatus
    endpoint: Optional[str]
    method: str
    domain: str
    source_panels: List[str]
    observation: Optional[Dict[str, Any]]
    coherency: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


class PanelCapabilityResolver:
    """
    Resolves capability IDs to endpoints via AURORA registry.

    Usage:
        resolver = PanelCapabilityResolver()
        result = resolver.resolve("activity.summary")
        if result.is_callable:
            # Safe to call result.endpoint with result.method
        else:
            # Capability not OBSERVED/TRUSTED — cannot call
    """

    def __init__(
        self,
        registry_dir: Optional[Path] = None,
        strict_mode: bool = True,
    ):
        """
        Args:
            registry_dir: Path to capability registry. Defaults to canonical location.
            strict_mode: If True, unresolved capabilities are errors. If False, warnings.
        """
        self.registry_dir = registry_dir or CAPABILITY_REGISTRY_DIR
        self.strict_mode = strict_mode
        self._registry: Dict[str, CapabilityRegistryEntry] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all capability entries from registry."""
        if self._loaded:
            return

        if not self.registry_dir.exists():
            logger.warning(f"Capability registry not found: {self.registry_dir}")
            self._loaded = True
            return

        yaml_files = list(self.registry_dir.glob("AURORA_L2_CAPABILITY_*.yaml"))
        # Exclude deprecated entries
        yaml_files = [f for f in yaml_files if "LEGACY_DEPRECATED" not in str(f)]

        logger.info(f"Loading {len(yaml_files)} capability entries from {self.registry_dir}")

        for yaml_file in yaml_files:
            try:
                entry = self._load_entry(yaml_file)
                if entry:
                    self._registry[entry.capability_id] = entry
            except Exception as e:
                logger.error(f"Failed to load capability entry {yaml_file}: {e}")

        self._loaded = True
        logger.info(
            f"Loaded {len(self._registry)} capabilities. "
            f"Callable: {sum(1 for e in self._registry.values() if e.status in CALLABLE_STATUSES)}"
        )

    def _load_entry(self, yaml_file: Path) -> Optional[CapabilityRegistryEntry]:
        """Parse a single capability YAML file."""
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        capability_id = data.get("capability_id")
        if not capability_id:
            return None

        # Get endpoint from either top-level or assumption block
        endpoint = data.get("endpoint")
        if not endpoint:
            assumption = data.get("assumption", {})
            endpoint = assumption.get("endpoint")

        # Get method similarly
        method = data.get("method", "GET")
        if not method:
            assumption = data.get("assumption", {})
            method = assumption.get("method", "GET")

        # Parse status
        status_str = data.get("status", "DISCOVERED")
        try:
            status = CapabilityStatus(status_str)
        except ValueError:
            logger.warning(f"Unknown status '{status_str}' for {capability_id}, defaulting to DISCOVERED")
            status = CapabilityStatus.DISCOVERED

        return CapabilityRegistryEntry(
            capability_id=capability_id,
            status=status,
            endpoint=endpoint,
            method=method,
            domain=data.get("domain", "UNKNOWN"),
            source_panels=data.get("source_panels", []),
            observation=data.get("observation"),
            coherency=data.get("coherency"),
            metadata=data.get("metadata", {}),
        )

    def resolve(self, capability_id: str) -> ResolvedCapability:
        """
        Resolve a capability ID to its endpoint.

        Returns ResolvedCapability with is_callable=True only if:
        - Capability exists in registry
        - Status is OBSERVED or TRUSTED
        - Endpoint is defined

        Args:
            capability_id: The capability to resolve (e.g., "activity.summary")

        Returns:
            ResolvedCapability with resolution result
        """
        self.load()

        entry = self._registry.get(capability_id)

        if not entry:
            reason = f"Capability not found in registry: {capability_id}"
            if self.strict_mode:
                logger.error(reason)
            else:
                logger.warning(reason)

            return ResolvedCapability(
                capability_id=capability_id,
                status=CapabilityStatus.DISCOVERED,
                endpoint=None,
                method="GET",
                domain="UNKNOWN",
                is_callable=False,
                reason=reason,
            )

        # Check if callable
        if entry.status not in CALLABLE_STATUSES:
            reason = (
                f"Capability '{capability_id}' status is {entry.status.value}. "
                f"Only OBSERVED/TRUSTED capabilities may be called."
            )
            logger.warning(reason)

            return ResolvedCapability(
                capability_id=capability_id,
                status=entry.status,
                endpoint=entry.endpoint,
                method=entry.method,
                domain=entry.domain,
                is_callable=False,
                reason=reason,
                observation=entry.observation,
            )

        if not entry.endpoint:
            reason = f"Capability '{capability_id}' has no endpoint defined"
            logger.warning(reason)

            return ResolvedCapability(
                capability_id=capability_id,
                status=entry.status,
                endpoint=None,
                method=entry.method,
                domain=entry.domain,
                is_callable=False,
                reason=reason,
                observation=entry.observation,
            )

        # Callable!
        return ResolvedCapability(
            capability_id=capability_id,
            status=entry.status,
            endpoint=entry.endpoint,
            method=entry.method,
            domain=entry.domain,
            is_callable=True,
            observation=entry.observation,
        )

    def resolve_all(self, capability_ids: List[str]) -> Dict[str, ResolvedCapability]:
        """Resolve multiple capabilities at once."""
        return {cap_id: self.resolve(cap_id) for cap_id in capability_ids}

    def get_callable_capabilities(self) -> List[str]:
        """Get list of all callable capability IDs."""
        self.load()
        return [
            cap_id
            for cap_id, entry in self._registry.items()
            if entry.status in CALLABLE_STATUSES and entry.endpoint
        ]

    def get_capabilities_by_domain(self, domain: str) -> List[CapabilityRegistryEntry]:
        """Get all capabilities for a domain."""
        self.load()
        return [
            entry
            for entry in self._registry.values()
            if entry.domain.upper() == domain.upper()
        ]

    def get_capability_entry(self, capability_id: str) -> Optional[CapabilityRegistryEntry]:
        """Get raw registry entry for a capability."""
        self.load()
        return self._registry.get(capability_id)

    def get_status_summary(self) -> Dict[str, int]:
        """Get count of capabilities by status."""
        self.load()
        summary: Dict[str, int] = {}
        for entry in self._registry.values():
            status = entry.status.value
            summary[status] = summary.get(status, 0) + 1
        return summary


# Singleton
_resolver: Optional[PanelCapabilityResolver] = None


def get_capability_resolver() -> PanelCapabilityResolver:
    """Get singleton capability resolver."""
    global _resolver
    if _resolver is None:
        _resolver = PanelCapabilityResolver()
    return _resolver
