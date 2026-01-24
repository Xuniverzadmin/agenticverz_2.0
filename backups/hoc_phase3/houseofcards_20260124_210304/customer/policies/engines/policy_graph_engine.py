# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Policy conflict detection and dependency graph computation
# Callers: policies.py, policy_layer.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-411 (Gap Closure), DFT-O4, DFT-O5

"""
Policy Graph Engine — Conflict Detection & Dependency Analysis

This module implements:
- PolicyConflictEngine: Detects logical contradictions between policies (DFT-O4)
- PolicyDependencyEngine: Computes structural relationships between policies (DFT-O5)

These engines answer STATIC governance questions, not runtime enforcement.
They must be deterministic, explainable, and replayable.

Reference: PIN-411 Gap Closure Spec (Part A)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Enums (LOCKED - from spec)
# =============================================================================


class ConflictType(str, Enum):
    """Conflict taxonomy (LOCKED)."""

    SCOPE_OVERLAP = "SCOPE_OVERLAP"  # Same scope, incompatible behavior
    THRESHOLD_CONTRADICTION = "THRESHOLD_CONTRADICTION"  # Limits cannot both be satisfied
    TEMPORAL_CONFLICT = "TEMPORAL_CONFLICT"  # Time windows clash
    PRIORITY_OVERRIDE = "PRIORITY_OVERRIDE"  # Lower-priority nullifies higher-priority


class ConflictSeverity(str, Enum):
    """Conflict severity levels."""

    BLOCKING = "BLOCKING"  # Activation must be prevented
    WARNING = "WARNING"  # Allowed but requires review


class DependencyType(str, Enum):
    """Dependency types (LOCKED)."""

    EXPLICIT = "EXPLICIT"  # Declared via requires_policy_id
    IMPLICIT_SCOPE = "IMPLICIT_SCOPE"  # Same scope, rely on each other
    IMPLICIT_LIMIT = "IMPLICIT_LIMIT"  # Limit-based dependency


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PolicyConflict:
    """A detected conflict between two policies."""

    policy_a_id: str
    policy_b_id: str
    policy_a_name: str
    policy_b_name: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    explanation: str
    recommended_action: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_a_id": self.policy_a_id,
            "policy_b_id": self.policy_b_id,
            "policy_a_name": self.policy_a_name,
            "policy_b_name": self.policy_b_name,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class PolicyDependency:
    """A dependency relationship between policies."""

    policy_id: str
    depends_on_id: str
    policy_name: str
    depends_on_name: str
    dependency_type: DependencyType
    reason: str
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "depends_on_id": self.depends_on_id,
            "policy_name": self.policy_name,
            "depends_on_name": self.depends_on_name,
            "dependency_type": self.dependency_type.value,
            "reason": self.reason,
            "is_active": self.is_active,
        }


@dataclass
class PolicyNode:
    """A node in the dependency graph."""

    id: str
    name: str
    rule_type: str  # SYSTEM, SAFETY, ETHICAL, TEMPORAL
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    status: str  # ACTIVE, RETIRED
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    depends_on: list[dict] = field(default_factory=list)
    required_by: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type,
            "scope": self.scope,
            "status": self.status,
            "enforcement_mode": self.enforcement_mode,
            "depends_on": self.depends_on,
            "required_by": self.required_by,
        }


@dataclass
class DependencyGraphResult:
    """Result of dependency graph computation."""

    nodes: list[PolicyNode]
    edges: list[PolicyDependency]
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "computed_at": self.computed_at.isoformat(),
        }


@dataclass
class ConflictDetectionResult:
    """Result of conflict detection."""

    conflicts: list[PolicyConflict]
    unresolved_count: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflicts": [c.to_dict() for c in self.conflicts],
            "total": len(self.conflicts),
            "unresolved_count": self.unresolved_count,
            "computed_at": self.computed_at.isoformat(),
        }


# =============================================================================
# Policy Conflict Engine (DFT-O4)
# =============================================================================


class PolicyConflictEngine:
    """
    Detects logical contradictions, overlaps, or unsafe coexistence between policies.

    This engine prevents:
    - Mutually exclusive policies being active together
    - Silent overrides
    - Temporal deadlocks

    Conflicts are TYPED, not inferred.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def detect_conflicts(
        self,
        session: AsyncSession,
        policy_id: Optional[str] = None,
        severity_filter: Optional[ConflictSeverity] = None,
        include_resolved: bool = False,
    ) -> ConflictDetectionResult:
        """
        Detect conflicts between policies.

        Args:
            session: Database session
            policy_id: Optional - filter to conflicts involving this policy
            severity_filter: Optional - filter by severity (BLOCKING, WARNING)
            include_resolved: Include already-resolved conflicts

        Returns:
            ConflictDetectionResult with all detected conflicts
        """
        conflicts: list[PolicyConflict] = []

        # Fetch all active policies for this tenant
        policies = await self._fetch_policies(session)

        if not policies:
            return ConflictDetectionResult(conflicts=[], unresolved_count=0)

        # Filter to specific policy if requested
        if policy_id:
            policies = [p for p in policies if p["id"] == policy_id or self._involves_policy(p, policy_id)]

        # Detect each conflict type
        conflicts.extend(await self._detect_scope_overlaps(policies))
        conflicts.extend(await self._detect_threshold_contradictions(session))
        conflicts.extend(await self._detect_temporal_conflicts(policies))
        conflicts.extend(await self._detect_priority_overrides(policies))

        # Apply severity filter
        if severity_filter:
            conflicts = [c for c in conflicts if c.severity == severity_filter]

        # Filter out resolved if not requested
        if not include_resolved:
            # Check against persisted resolutions
            resolved_pairs = await self._get_resolved_conflicts(session)
            conflicts = [
                c
                for c in conflicts
                if (c.policy_a_id, c.policy_b_id) not in resolved_pairs
                and (c.policy_b_id, c.policy_a_id) not in resolved_pairs
            ]

        unresolved = len([c for c in conflicts if c.severity == ConflictSeverity.BLOCKING])

        return ConflictDetectionResult(conflicts=conflicts, unresolved_count=unresolved)

    async def _fetch_policies(self, session: AsyncSession) -> list[dict]:
        """Fetch all active policies for tenant."""
        result = await session.execute(
            text("""
                SELECT id, name, rule_type, scope, scope_id, enforcement_mode,
                       conditions, source, status
                FROM policy_rules
                WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
                ORDER BY created_at DESC
            """),
            {"tenant_id": self.tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "rule_type": row[2] or "SYSTEM",
                "scope": row[3] or "GLOBAL",
                "scope_id": row[4],
                "enforcement_mode": row[5] or "WARN",
                "conditions": row[6] or {},
                "source": row[7] or "MANUAL",
                "status": row[8] or "ACTIVE",
            }
            for row in rows
        ]

    async def _detect_scope_overlaps(self, policies: list[dict]) -> list[PolicyConflict]:
        """
        Detect SCOPE_OVERLAP conflicts.

        Two policies apply to the same scope but define incompatible behavior.
        Example: ALLOW model=X for tenant=T vs DENY model=X for tenant=T
        """
        conflicts = []

        # Group policies by scope
        scope_groups: dict[str, list[dict]] = {}
        for p in policies:
            scope_key = f"{p['scope']}:{p['scope_id'] or 'global'}"
            if scope_key not in scope_groups:
                scope_groups[scope_key] = []
            scope_groups[scope_key].append(p)

        # Check each scope group for conflicts
        for scope_key, group in scope_groups.items():
            if len(group) < 2:
                continue

            # Check pairs for contradictions
            for i, p1 in enumerate(group):
                for p2 in group[i + 1 :]:
                    # Skip if same rule_type (complementary, not conflicting)
                    if p1["rule_type"] == p2["rule_type"]:
                        continue

                    # Check enforcement mode contradictions
                    if p1["enforcement_mode"] == "BLOCK" and p2["enforcement_mode"] == "DISABLED":
                        conflicts.append(
                            PolicyConflict(
                                policy_a_id=p1["id"],
                                policy_b_id=p2["id"],
                                policy_a_name=p1["name"],
                                policy_b_name=p2["name"],
                                conflict_type=ConflictType.SCOPE_OVERLAP,
                                severity=ConflictSeverity.WARNING,
                                explanation=f"Policy '{p1['name']}' blocks while '{p2['name']}' is disabled on same scope",
                                recommended_action="Review enforcement modes for consistency",
                            )
                        )

                    # Check for ALLOW vs DENY in conditions
                    cond1 = p1.get("conditions") or {}
                    cond2 = p2.get("conditions") or {}
                    if self._has_contradicting_conditions(cond1, cond2):
                        conflicts.append(
                            PolicyConflict(
                                policy_a_id=p1["id"],
                                policy_b_id=p2["id"],
                                policy_a_name=p1["name"],
                                policy_b_name=p2["name"],
                                conflict_type=ConflictType.SCOPE_OVERLAP,
                                severity=ConflictSeverity.BLOCKING,
                                explanation=f"Policies have contradicting conditions on scope '{scope_key}'",
                                recommended_action="Resolve contradicting conditions before activation",
                            )
                        )

        return conflicts

    async def _detect_threshold_contradictions(self, session: AsyncSession) -> list[PolicyConflict]:
        """
        Detect THRESHOLD_CONTRADICTION conflicts.

        Limits that cannot both be satisfied.
        Example: TOKENS_PER_DAY ≤ 10k vs TOKENS_PER_DAY ≥ 20k
        """
        conflicts = []

        # Fetch all active limits for tenant
        result = await session.execute(
            text("""
                SELECT id, name, limit_type, limit_value, scope, scope_id
                FROM limits
                WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
                ORDER BY limit_type, scope
            """),
            {"tenant_id": self.tenant_id},
        )
        rows = result.fetchall()
        limits = [
            {
                "id": str(row[0]),
                "name": row[1],
                "limit_type": row[2],
                "limit_value": row[3],
                "scope": row[4],
                "scope_id": row[5],
            }
            for row in rows
        ]

        # Group by limit_type and scope
        limit_groups: dict[str, list[dict]] = {}
        for lim in limits:
            group_key = f"{lim['limit_type']}:{lim['scope']}:{lim['scope_id'] or 'global'}"
            if group_key not in limit_groups:
                limit_groups[group_key] = []
            limit_groups[group_key].append(lim)

        # Check for contradictions within groups
        for group_key, group in limit_groups.items():
            if len(group) < 2:
                continue

            # Find min and max values
            values = [lim["limit_value"] for lim in group if lim["limit_value"] is not None]
            if len(values) >= 2:
                min_val = min(values)
                max_val = max(values)

                # If spread is > 50%, flag as potential contradiction
                if max_val > 0 and (max_val - min_val) / max_val > 0.5:
                    conflicts.append(
                        PolicyConflict(
                            policy_a_id=group[0]["id"],
                            policy_b_id=group[-1]["id"],
                            policy_a_name=group[0]["name"],
                            policy_b_name=group[-1]["name"],
                            conflict_type=ConflictType.THRESHOLD_CONTRADICTION,
                            severity=ConflictSeverity.WARNING,
                            explanation=f"Limits for {group_key.split(':')[0]} have wide range ({min_val} to {max_val})",
                            recommended_action="Review threshold values for consistency",
                        )
                    )

        return conflicts

    async def _detect_temporal_conflicts(self, policies: list[dict]) -> list[PolicyConflict]:
        """
        Detect TEMPORAL_CONFLICT conflicts.

        Time windows or cooldowns that clash.
        Example: Policy A active 09:00-18:00, Policy B enforces cooldown during same window
        """
        conflicts = []

        # Check temporal rules for overlapping windows
        temporal_policies = [p for p in policies if p["rule_type"] == "TEMPORAL"]

        for i, p1 in enumerate(temporal_policies):
            for p2 in temporal_policies[i + 1 :]:
                cond1 = p1.get("conditions") or {}
                cond2 = p2.get("conditions") or {}

                # Check for overlapping time windows
                if "time_window" in cond1 and "time_window" in cond2:
                    if self._time_windows_overlap(cond1["time_window"], cond2["time_window"]):
                        conflicts.append(
                            PolicyConflict(
                                policy_a_id=p1["id"],
                                policy_b_id=p2["id"],
                                policy_a_name=p1["name"],
                                policy_b_name=p2["name"],
                                conflict_type=ConflictType.TEMPORAL_CONFLICT,
                                severity=ConflictSeverity.WARNING,
                                explanation="Time windows overlap between temporal policies",
                                recommended_action="Review temporal constraints for exclusivity",
                            )
                        )

        return conflicts

    async def _detect_priority_overrides(self, policies: list[dict]) -> list[PolicyConflict]:
        """
        Detect PRIORITY_OVERRIDE conflicts.

        Lower-priority rule nullifies higher-priority rule.
        Example: SYSTEM rule overridden by LEARNED rule
        """
        conflicts = []

        # Priority order: SYSTEM > SAFETY > ETHICAL > TEMPORAL > (LEARNED)
        priority_order = {"SYSTEM": 1, "SAFETY": 2, "ETHICAL": 3, "TEMPORAL": 4}

        # Group by scope
        scope_groups: dict[str, list[dict]] = {}
        for p in policies:
            scope_key = f"{p['scope']}:{p['scope_id'] or 'global'}"
            if scope_key not in scope_groups:
                scope_groups[scope_key] = []
            scope_groups[scope_key].append(p)

        for scope_key, group in scope_groups.items():
            if len(group) < 2:
                continue

            for i, p1 in enumerate(group):
                for p2 in group[i + 1 :]:
                    p1_priority = priority_order.get(p1["rule_type"], 99)
                    p2_priority = priority_order.get(p2["rule_type"], 99)

                    # Check if lower priority can override higher
                    if p1["source"] == "LEARNED" and p1_priority > p2_priority:
                        if p1["enforcement_mode"] in ("BLOCK", "WARN") and p2["enforcement_mode"] == "DISABLED":
                            conflicts.append(
                                PolicyConflict(
                                    policy_a_id=p1["id"],
                                    policy_b_id=p2["id"],
                                    policy_a_name=p1["name"],
                                    policy_b_name=p2["name"],
                                    conflict_type=ConflictType.PRIORITY_OVERRIDE,
                                    severity=ConflictSeverity.BLOCKING,
                                    explanation=f"LEARNED policy '{p1['name']}' may override {p2['rule_type']} policy",
                                    recommended_action="Review priority and enforcement settings",
                                )
                            )

        return conflicts

    def _has_contradicting_conditions(self, cond1: dict, cond2: dict) -> bool:
        """Check if two condition sets have explicit contradictions."""
        # Check for allow vs deny on same key
        for key in cond1:
            if key in cond2:
                val1 = cond1[key]
                val2 = cond2[key]
                # Simple check: boolean opposites
                if isinstance(val1, bool) and isinstance(val2, bool) and val1 != val2:
                    return True
        return False

    def _time_windows_overlap(self, tw1: dict, tw2: dict) -> bool:
        """Check if two time windows overlap."""
        # Simple overlap check (hour-based)
        start1 = tw1.get("start_hour", 0)
        end1 = tw1.get("end_hour", 24)
        start2 = tw2.get("start_hour", 0)
        end2 = tw2.get("end_hour", 24)

        return not (end1 <= start2 or end2 <= start1)

    def _involves_policy(self, policy: dict, policy_id: str) -> bool:
        """Check if a conflict involves a specific policy."""
        return policy.get("id") == policy_id

    async def _get_resolved_conflicts(self, session: AsyncSession) -> set[tuple[str, str]]:
        """Get set of resolved conflict pairs from database."""
        try:
            result = await session.execute(
                text("""
                    SELECT policy_a, policy_b FROM policy.policy_conflicts
                    WHERE resolved = true
                """)
            )
            return {(str(row[0]), str(row[1])) for row in result.fetchall()}
        except Exception:
            return set()


# =============================================================================
# Policy Dependency Engine (DFT-O5)
# =============================================================================


class PolicyDependencyEngine:
    """
    Computes structural relationships between policies.

    Exposes dependencies so that:
    - Deletions don't break enforcement
    - Activations are ordered
    - Impact analysis is possible

    The graph is a computed view (DAG), not persisted edges.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def compute_dependency_graph(
        self,
        session: AsyncSession,
        policy_id: Optional[str] = None,
    ) -> DependencyGraphResult:
        """
        Compute the policy dependency graph.

        Args:
            session: Database session
            policy_id: Optional - filter to dependencies involving this policy

        Returns:
            DependencyGraphResult with nodes and edges
        """
        nodes: list[PolicyNode] = []
        edges: list[PolicyDependency] = []

        # Fetch all policies
        policies = await self._fetch_policies(session)
        limits = await self._fetch_limits(session)

        # Build policy nodes
        policy_map: dict[str, dict] = {}
        for p in policies:
            node = PolicyNode(
                id=p["id"],
                name=p["name"],
                rule_type=p["rule_type"],
                scope=p["scope"],
                status=p["status"],
                enforcement_mode=p["enforcement_mode"],
            )
            nodes.append(node)
            policy_map[p["id"]] = p

        # Detect EXPLICIT dependencies
        explicit_deps = await self._detect_explicit_dependencies(session, policies)
        edges.extend(explicit_deps)

        # Detect IMPLICIT_SCOPE dependencies
        implicit_scope_deps = self._detect_implicit_scope_dependencies(policies)
        edges.extend(implicit_scope_deps)

        # Detect IMPLICIT_LIMIT dependencies
        implicit_limit_deps = self._detect_implicit_limit_dependencies(policies, limits)
        edges.extend(implicit_limit_deps)

        # Filter to specific policy if requested
        if policy_id:
            edges = [e for e in edges if e.policy_id == policy_id or e.depends_on_id == policy_id]
            involved_ids = {policy_id}
            for e in edges:
                involved_ids.add(e.policy_id)
                involved_ids.add(e.depends_on_id)
            nodes = [n for n in nodes if n.id in involved_ids]

        # Populate depends_on and required_by on nodes
        for node in nodes:
            node.depends_on = [
                {"policy_id": e.depends_on_id, "policy_name": e.depends_on_name, "type": e.dependency_type.value, "reason": e.reason}
                for e in edges
                if e.policy_id == node.id
            ]
            node.required_by = [
                {"policy_id": e.policy_id, "policy_name": e.policy_name, "type": e.dependency_type.value, "reason": e.reason}
                for e in edges
                if e.depends_on_id == node.id
            ]

        return DependencyGraphResult(nodes=nodes, edges=edges)

    async def _fetch_policies(self, session: AsyncSession) -> list[dict]:
        """Fetch all policies for tenant."""
        result = await session.execute(
            text("""
                SELECT id, name, rule_type, scope, scope_id, enforcement_mode,
                       conditions, source, status, parent_rule_id
                FROM policy_rules
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
            """),
            {"tenant_id": self.tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "rule_type": row[2] or "SYSTEM",
                "scope": row[3] or "GLOBAL",
                "scope_id": row[4],
                "enforcement_mode": row[5] or "WARN",
                "conditions": row[6] or {},
                "source": row[7] or "MANUAL",
                "status": row[8] or "ACTIVE",
                "parent_rule_id": str(row[9]) if row[9] else None,
            }
            for row in rows
        ]

    async def _fetch_limits(self, session: AsyncSession) -> list[dict]:
        """Fetch all limits for tenant."""
        result = await session.execute(
            text("""
                SELECT id, name, limit_type, limit_value, scope, scope_id, status
                FROM limits
                WHERE tenant_id = :tenant_id
                ORDER BY limit_type
            """),
            {"tenant_id": self.tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "limit_type": row[2],
                "limit_value": row[3],
                "scope": row[4],
                "scope_id": row[5],
                "status": row[6],
            }
            for row in rows
        ]

    async def _detect_explicit_dependencies(
        self, session: AsyncSession, policies: list[dict]
    ) -> list[PolicyDependency]:
        """
        Detect EXPLICIT dependencies.

        These are declared via parent_rule_id or requires_policy_id in conditions.
        """
        deps = []
        policy_map = {p["id"]: p for p in policies}

        for p in policies:
            # Check parent_rule_id (explicit inheritance)
            if p.get("parent_rule_id") and p["parent_rule_id"] in policy_map:
                parent = policy_map[p["parent_rule_id"]]
                deps.append(
                    PolicyDependency(
                        policy_id=p["id"],
                        depends_on_id=parent["id"],
                        policy_name=p["name"],
                        depends_on_name=parent["name"],
                        dependency_type=DependencyType.EXPLICIT,
                        reason="Inherits from parent policy",
                    )
                )

            # Check conditions for requires_policy_id
            conditions = p.get("conditions") or {}
            if "requires_policy_id" in conditions:
                req_id = conditions["requires_policy_id"]
                if req_id in policy_map:
                    req_policy = policy_map[req_id]
                    deps.append(
                        PolicyDependency(
                            policy_id=p["id"],
                            depends_on_id=req_id,
                            policy_name=p["name"],
                            depends_on_name=req_policy["name"],
                            dependency_type=DependencyType.EXPLICIT,
                            reason="Explicitly requires policy",
                        )
                    )

        return deps

    def _detect_implicit_scope_dependencies(self, policies: list[dict]) -> list[PolicyDependency]:
        """
        Detect IMPLICIT_SCOPE dependencies.

        Policies on same scope that rely on each other's assumptions.
        Example: Rate limit assumes budget exists.
        """
        deps = []

        # Group by scope
        scope_groups: dict[str, list[dict]] = {}
        for p in policies:
            scope_key = f"{p['scope']}:{p['scope_id'] or 'global'}"
            if scope_key not in scope_groups:
                scope_groups[scope_key] = []
            scope_groups[scope_key].append(p)

        # Detect implicit dependencies within scope groups
        for scope_key, group in scope_groups.items():
            if len(group) < 2:
                continue

            # SAFETY rules depend on SYSTEM rules being present
            system_rules = [p for p in group if p["rule_type"] == "SYSTEM"]
            safety_rules = [p for p in group if p["rule_type"] == "SAFETY"]

            for safety in safety_rules:
                for system in system_rules:
                    deps.append(
                        PolicyDependency(
                            policy_id=safety["id"],
                            depends_on_id=system["id"],
                            policy_name=safety["name"],
                            depends_on_name=system["name"],
                            dependency_type=DependencyType.IMPLICIT_SCOPE,
                            reason=f"SAFETY rule on {scope_key} depends on SYSTEM baseline",
                        )
                    )

            # ETHICAL rules depend on SAFETY rules
            ethical_rules = [p for p in group if p["rule_type"] == "ETHICAL"]
            for ethical in ethical_rules:
                for safety in safety_rules:
                    deps.append(
                        PolicyDependency(
                            policy_id=ethical["id"],
                            depends_on_id=safety["id"],
                            policy_name=ethical["name"],
                            depends_on_name=safety["name"],
                            dependency_type=DependencyType.IMPLICIT_SCOPE,
                            reason=f"ETHICAL rule on {scope_key} depends on SAFETY baseline",
                        )
                    )

        return deps

    def _detect_implicit_limit_dependencies(
        self, policies: list[dict], limits: list[dict]
    ) -> list[PolicyDependency]:
        """
        Detect IMPLICIT_LIMIT dependencies.

        Limit-based dependencies.
        Example: Cooldown depends on run quota definition.
        """
        deps = []

        # Cooldown limits depend on run quotas
        cooldown_limits = [l for l in limits if l["limit_type"] == "COOLDOWN"]
        run_limits = [l for l in limits if l["limit_type"] and l["limit_type"].startswith("RUNS_")]

        for cooldown in cooldown_limits:
            for run_limit in run_limits:
                # Same scope
                if cooldown["scope"] == run_limit["scope"] and cooldown["scope_id"] == run_limit["scope_id"]:
                    deps.append(
                        PolicyDependency(
                            policy_id=cooldown["id"],
                            depends_on_id=run_limit["id"],
                            policy_name=cooldown["name"],
                            depends_on_name=run_limit["name"],
                            dependency_type=DependencyType.IMPLICIT_LIMIT,
                            reason="Cooldown relies on run quota definition",
                        )
                    )

        # Token limits may depend on run limits
        token_limits = [l for l in limits if l["limit_type"] and l["limit_type"].startswith("TOKENS_")]
        for token in token_limits:
            for run_limit in run_limits:
                if token["scope"] == run_limit["scope"] and token["scope_id"] == run_limit["scope_id"]:
                    deps.append(
                        PolicyDependency(
                            policy_id=token["id"],
                            depends_on_id=run_limit["id"],
                            policy_name=token["name"],
                            depends_on_name=run_limit["name"],
                            dependency_type=DependencyType.IMPLICIT_LIMIT,
                            reason="Token quota operates within run quota context",
                        )
                    )

        return deps

    async def check_can_delete(
        self, session: AsyncSession, policy_id: str
    ) -> tuple[bool, list[str]]:
        """
        Check if a policy can be deleted.

        Returns:
            (can_delete, list of blocking policy names)
        """
        graph = await self.compute_dependency_graph(session, policy_id)

        # Find the node
        node = next((n for n in graph.nodes if n.id == policy_id), None)
        if not node:
            return True, []

        # Check if any active policies require this one
        blocking = [dep["policy_name"] for dep in node.required_by if dep.get("is_active", True)]

        return len(blocking) == 0, blocking

    async def check_can_activate(
        self, session: AsyncSession, policy_id: str
    ) -> tuple[bool, list[str]]:
        """
        Check if a policy can be activated.

        Returns:
            (can_activate, list of missing dependency names)
        """
        graph = await self.compute_dependency_graph(session, policy_id)

        # Find the node
        node = next((n for n in graph.nodes if n.id == policy_id), None)
        if not node:
            return True, []

        # Check if all dependencies are active
        missing = []
        for dep in node.depends_on:
            dep_node = next((n for n in graph.nodes if n.id == dep["policy_id"]), None)
            if dep_node and dep_node.status != "ACTIVE":
                missing.append(dep["policy_name"])

        return len(missing) == 0, missing


# =============================================================================
# Factory Functions
# =============================================================================


def get_conflict_engine(tenant_id: str) -> PolicyConflictEngine:
    """Get a PolicyConflictEngine instance for a tenant."""
    return PolicyConflictEngine(tenant_id)


def get_dependency_engine(tenant_id: str) -> PolicyDependencyEngine:
    """Get a PolicyDependencyEngine instance for a tenant."""
    return PolicyDependencyEngine(tenant_id)
