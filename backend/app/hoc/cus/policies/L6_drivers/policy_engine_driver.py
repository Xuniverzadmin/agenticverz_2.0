# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: evaluations, violations, ethical_constraints, risk_ceilings, safety_rules, business_rules, policy_versions
#   Writes: evaluations, violations, risk_ceilings, safety_rules, policy_versions
# Database:
#   Scope: domain (policies)
#   Models: PolicyEvaluation, PolicyViolation, EthicalConstraint, RiskCeiling, SafetyRule, BusinessRule, PolicyVersion
# Role: Policy Engine data access operations
# Callers: engine.py (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-468 (Phase-2.5A)
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-24)
# - Extracted from engine.py (was 40+ inline DB operations)
# - Engine retains all business logic
# - Driver handles pure persistence
#
# ============================================================================
# L6 DRIVER INVARIANT — POLICY ENGINE (LOCKED)
# ============================================================================
# This file MUST contain ONLY data access operations.
# No business logic, no validation, no decisions.
# Any violation is a Phase-2.5 regression.
# ============================================================================

"""
Policy Engine Driver (L6)

Pure data access for PolicyEngine operations.
No business logic - only DB operations.

Authority: POLICY_ENGINE_PERSISTENCE
Tables:
  - policy.evaluations (write)
  - policy.violations (read/write)
  - policy.ethical_constraints (read)
  - policy.risk_ceilings (read/write)
  - policy.safety_rules (read/write)
  - policy.business_rules (read)
  - policy.policy_versions (read/write)
  - policy.policy_provenance (read/write)
  - policy.policy_dependencies (read/write)
  - policy.policy_conflicts (read/write)
  - policy.temporal_policies (read/write)
  - policy.temporal_metric_events (read/write)
  - policy.temporal_metric_windows (read/write)
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine


class PolicyEngineDriver:
    """
    L6 driver for PolicyEngine data access.

    INVARIANTS (L6):
    - No business branching
    - No validation
    - No cross-domain calls
    - Pure persistence operations only
    """

    def __init__(self, db_url: str):
        """Initialize with database URL."""
        self._db_url = db_url
        self._engine: Optional[Engine] = None
        self._managed_conn: Optional[Connection] = None

    def _get_engine(self) -> Engine:
        """Lazy-load engine."""
        if self._engine is None:
            self._engine = create_engine(self._db_url)
        return self._engine

    def get_engine(self) -> Engine:
        """Expose the SQLAlchemy engine for L4 transaction management.

        L4 handlers call engine.begin() to open a transaction, then pass the
        connection to managed_connection(conn).  L6 never calls begin() itself.
        """
        return self._get_engine()

    # =========================================================================
    # CONFIGURATION LOAD OPERATIONS (READ)
    # =========================================================================

    def fetch_ethical_constraints(self, conn: Connection) -> List[Dict[str, Any]]:
        """
        Fetch all active ethical constraints.

        Returns:
            List of ethical constraint dicts
        """
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, constraint_type,
                       forbidden_patterns, required_disclosures,
                       enforcement_level, violation_action,
                       applies_to, tenant_id, is_active
                FROM policy.ethical_constraints
                WHERE is_active = true
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    def fetch_risk_ceilings(self, conn: Connection) -> List[Dict[str, Any]]:
        """
        Fetch all active risk ceilings.

        Returns:
            List of risk ceiling dicts
        """
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, metric, max_value,
                       current_value, window_seconds, applies_to,
                       tenant_id, breach_action, is_active
                FROM policy.risk_ceilings
                WHERE is_active = true
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    def fetch_safety_rules(self, conn: Connection) -> List[Dict[str, Any]]:
        """
        Fetch all active safety rules.

        Returns:
            List of safety rule dicts
        """
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, rule_type, condition,
                       action, cooldown_seconds, applies_to, tenant_id,
                       priority, is_active
                FROM policy.safety_rules
                WHERE is_active = true
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    def fetch_business_rules(self, conn: Connection) -> List[Dict[str, Any]]:
        """
        Fetch all active business rules.

        Returns:
            List of business rule dicts
        """
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, rule_type, condition,
                       constraint, tenant_id, customer_tier, priority, is_active
                FROM policy.business_rules
                WHERE is_active = true
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    # =========================================================================
    # EVALUATION PERSISTENCE (WRITE)
    # =========================================================================

    def insert_evaluation(
        self,
        conn: Connection,
        evaluation_id: str,
        action_type: str,
        agent_id: Optional[str],
        tenant_id: Optional[str],
        request_context: str,
        decision: str,
        decision_reason: str,
        modifications: str,
        evaluation_ms: float,
        policies_checked: int,
        rules_matched: int,
        evaluated_at: datetime,
    ) -> None:
        """
        Insert policy evaluation record.

        Args:
            conn: Database connection
            evaluation_id: Unique evaluation ID
            action_type: Type of action evaluated
            agent_id: Agent ID (optional)
            tenant_id: Tenant ID (optional)
            request_context: Request context (JSON string)
            decision: Evaluation decision (ALLOW/DENY/etc)
            decision_reason: Reason for decision
            modifications: Applied modifications (JSON string)
            evaluation_ms: Time taken in milliseconds
            policies_checked: Number of policies checked
            rules_matched: Number of rules matched
            evaluated_at: Timestamp of evaluation
        """
        conn.execute(
            text(
                """
                INSERT INTO policy.evaluations (
                    id, action_type, agent_id, tenant_id,
                    request_context, decision, decision_reason,
                    modifications, evaluation_ms, policies_checked,
                    rules_matched, evaluated_at
                ) VALUES (
                    CAST(:id AS UUID), :action_type, :agent_id, :tenant_id,
                    CAST(:context AS JSONB), :decision, :reason,
                    CAST(:modifications AS JSONB), :eval_ms, :policies,
                    :rules, :evaluated_at
                )
                """
            ),
            {
                "id": evaluation_id,
                "action_type": action_type,
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "context": request_context,
                "decision": decision,
                "reason": decision_reason,
                "modifications": modifications,
                "eval_ms": evaluation_ms,
                "policies": policies_checked,
                "rules": rules_matched,
                "evaluated_at": evaluated_at,
            },
        )

    def insert_violation(
        self,
        conn: Connection,
        violation_id: str,
        evaluation_id: str,
        policy_name: str,
        violation_type: str,
        severity: str,
        description: str,
        evidence: str,
        agent_id: Optional[str],
        tenant_id: Optional[str],
        action_attempted: str,
        routed_to_governor: bool,
        governor_action: Optional[str],
        detected_at: datetime,
    ) -> None:
        """
        Insert policy violation record.

        Args:
            conn: Database connection
            violation_id: Unique violation ID
            evaluation_id: Parent evaluation ID
            policy_name: Name of violated policy
            violation_type: Type of violation
            severity: Violation severity
            description: Violation description
            evidence: Evidence (JSON string)
            agent_id: Agent ID (optional)
            tenant_id: Tenant ID (optional)
            action_attempted: Action that was attempted
            routed_to_governor: Whether routed to governor
            governor_action: Action taken by governor (optional)
            detected_at: Timestamp of detection
        """
        conn.execute(
            text(
                """
                INSERT INTO policy.violations (
                    id, evaluation_id, policy_name, violation_type,
                    severity, description, evidence, agent_id,
                    tenant_id, action_attempted, routed_to_governor,
                    governor_action, detected_at
                ) VALUES (
                    CAST(:id AS UUID), CAST(:eval_id AS UUID), :policy,
                    :type, :severity, :description, CAST(:evidence AS JSONB),
                    :agent_id, :tenant_id, :action, :routed,
                    :gov_action, :detected_at
                )
                """
            ),
            {
                "id": violation_id,
                "eval_id": evaluation_id,
                "policy": policy_name,
                "type": violation_type,
                "severity": severity,
                "description": description,
                "evidence": evidence,
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "action": action_attempted,
                "routed": routed_to_governor,
                "gov_action": governor_action,
                "detected_at": detected_at,
            },
        )

    # =========================================================================
    # VIOLATION QUERIES (READ)
    # =========================================================================

    def fetch_violations(
        self,
        conn: Connection,
        violation_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        severity_min: Optional[float] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch violations with optional filters.

        Args:
            conn: Database connection
            violation_type: Filter by violation type (optional)
            agent_id: Filter by agent (optional)
            tenant_id: Filter by tenant (optional)
            severity_min: Filter by minimum severity (optional)
            since: Filter by time (optional)
            limit: Max results

        Returns:
            List of violation dicts
        """
        sql = """
            SELECT id, policy_name, violation_type, severity, description,
                   evidence, agent_id, tenant_id, action_attempted,
                   routed_to_governor, governor_action, detected_at
            FROM policy.violations
            WHERE 1=1
        """
        params: Dict[str, Any] = {}

        if violation_type:
            sql += " AND violation_type = :vtype"
            params["vtype"] = violation_type
        if agent_id:
            sql += " AND agent_id = :agent_id"
            params["agent_id"] = agent_id
        if tenant_id:
            sql += " AND tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id
        if severity_min is not None:
            sql += " AND severity >= :severity_min"
            params["severity_min"] = severity_min
        if since:
            sql += " AND detected_at >= :since"
            params["since"] = since

        sql += " ORDER BY detected_at DESC LIMIT :limit"
        params["limit"] = limit

        rows = conn.execute(text(sql), params)
        return [dict(row._mapping) for row in rows]

    def fetch_violation_by_id(
        self,
        conn: Connection,
        violation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single violation by ID.

        Args:
            conn: Database connection
            violation_id: Violation ID

        Returns:
            Violation dict or None
        """
        row = conn.execute(
            text(
                """
                SELECT id, policy_name, violation_type, severity, description,
                       evidence, agent_id, tenant_id, action_attempted,
                       routed_to_governor, governor_action, detected_at
                FROM policy.violations
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {"id": violation_id},
        ).first()
        return dict(row._mapping) if row else None

    def update_violation_acknowledged(
        self,
        conn: Connection,
        violation_id: str,
        notes: Optional[str] = None,
    ) -> int:
        """
        Acknowledge a violation.

        Args:
            conn: Database connection
            violation_id: Violation ID
            notes: Acknowledgement notes (optional)

        Returns:
            Number of rows updated
        """
        result = conn.execute(
            text(
                """
                UPDATE policy.violations
                SET acknowledged_at = NOW(),
                    acknowledgement_notes = :notes
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {"id": violation_id, "notes": notes},
        )
        return result.rowcount

    # =========================================================================
    # RISK CEILING OPERATIONS (READ/WRITE)
    # =========================================================================

    def update_risk_ceiling(
        self,
        conn: Connection,
        ceiling_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """
        Update a risk ceiling.

        Args:
            conn: Database connection
            ceiling_id: Ceiling ID
            updates: Dict of field -> value to update
        """
        set_clauses = []
        params = {"id": ceiling_id}

        for key, value in updates.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

        if set_clauses:
            conn.execute(
                text(
                    f"""
                    UPDATE policy.risk_ceilings
                    SET {", ".join(set_clauses)}
                    WHERE id = CAST(:id AS UUID)
                    """
                ),
                params,
            )

    def reset_risk_ceiling(
        self,
        conn: Connection,
        ceiling_id: str,
    ) -> int:
        """
        Reset a risk ceiling's current value to 0.

        Args:
            conn: Database connection
            ceiling_id: Ceiling ID

        Returns:
            Number of rows updated
        """
        result = conn.execute(
            text(
                """
                UPDATE policy.risk_ceilings
                SET current_value = 0
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {"id": ceiling_id},
        )
        return result.rowcount

    # =========================================================================
    # SAFETY RULE OPERATIONS (WRITE)
    # =========================================================================

    def update_safety_rule(
        self,
        conn: Connection,
        rule_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """
        Update a safety rule.

        Args:
            conn: Database connection
            rule_id: Rule ID
            updates: Dict of field -> value to update
                     Note: 'condition' field value should already be JSON string
        """
        set_clauses = []
        params = {"id": rule_id}

        for key, value in updates.items():
            if key == "condition":
                # condition is JSONB - value should already be JSON string
                set_clauses.append(f"{key} = CAST(:{key} AS JSONB)")
                params[key] = value
            else:
                set_clauses.append(f"{key} = :{key}")
                params[key] = value

        if set_clauses:
            conn.execute(
                text(
                    f"""
                    UPDATE policy.safety_rules
                    SET {", ".join(set_clauses)}
                    WHERE id = CAST(:id AS UUID)
                    """
                ),
                params,
            )

    # =========================================================================
    # VERSION MANAGEMENT (READ/WRITE)
    # =========================================================================

    def fetch_policy_versions(
        self,
        conn: Connection,
        include_inactive: bool = False,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch policy versions.

        Args:
            conn: Database connection
            include_inactive: Include rolled back versions
            limit: Max results

        Returns:
            List of version dicts
        """
        sql = """
            SELECT id, version, policy_hash, created_by, created_at,
                   description, is_active, rolled_back_at
            FROM policy.policy_versions
        """
        if not include_inactive:
            sql += " WHERE rolled_back_at IS NULL"
        sql += " ORDER BY created_at DESC LIMIT :limit"

        rows = conn.execute(text(sql), {"limit": limit})
        return [dict(row._mapping) for row in rows]

    def fetch_current_active_version(
        self,
        conn: Connection,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch the currently active policy version.

        Args:
            conn: Database connection

        Returns:
            Version dict or None
        """
        row = conn.execute(
            text(
                """
                SELECT id, version, policy_hash, created_by, created_at, description
                FROM policy.policy_versions
                WHERE is_active = true
                ORDER BY created_at DESC LIMIT 1
                """
            )
        ).first()
        return dict(row._mapping) if row else None

    def fetch_policy_version_by_id(
        self,
        conn: Connection,
        version_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a policy version by ID.

        Args:
            conn: Database connection
            version_id: Version ID

        Returns:
            Version dict or None
        """
        row = conn.execute(
            text(
                """
                SELECT id, version, policy_hash, created_by, created_at, description
                FROM policy.policy_versions
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {"id": version_id},
        ).first()
        return dict(row._mapping) if row else None

    def fetch_policy_version_by_id_or_version(
        self,
        conn: Connection,
        version_id: str,
    ) -> Optional[Tuple]:
        """
        Fetch a policy version by ID or version string.

        Args:
            conn: Database connection
            version_id: Version ID or version string

        Returns:
            Tuple of (id, version, policy_hash, is_active) or None
        """
        row = conn.execute(
            text(
                """
                SELECT id, version, policy_hash, is_active
                FROM policy.policy_versions
                WHERE id = CAST(:id AS UUID) OR version = :id
                """
            ),
            {"id": version_id},
        ).first()
        return (row[0], row[1], row[2], row[3]) if row else None

    def deactivate_all_versions(self, conn: Connection) -> None:
        """Deactivate all policy versions."""
        conn.execute(text("UPDATE policy.policy_versions SET is_active = false"))

    def insert_policy_version(
        self,
        conn: Connection,
        version_id: str,
        version: str,
        policy_hash: str,
        created_by: str,
        description: str,
    ) -> None:
        """
        Insert a new policy version.

        Args:
            conn: Database connection
            version_id: Version ID
            version: Version string
            policy_hash: Hash of policy content
            created_by: Creator
            description: Version description
        """
        conn.execute(
            text(
                """
                INSERT INTO policy.policy_versions
                (id, version, policy_hash, created_by, description, is_active)
                VALUES (CAST(:id AS UUID), :version, :hash, :by, :desc, true)
                """
            ),
            {
                "id": version_id,
                "version": version,
                "hash": policy_hash,
                "by": created_by,
                "desc": description,
            },
        )

    def fetch_version_for_rollback(
        self,
        conn: Connection,
        version: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch version with snapshots for rollback.

        Args:
            conn: Database connection
            version: Target version string

        Returns:
            Version dict with snapshots or None
        """
        row = conn.execute(
            text(
                """
                SELECT id, version, policies_snapshot, risk_ceilings_snapshot,
                       safety_rules_snapshot, ethical_constraints_snapshot
                FROM policy.policy_versions
                WHERE version = :version
                """
            ),
            {"version": version},
        ).first()
        return dict(row._mapping) if row else None

    def mark_version_rolled_back(
        self,
        conn: Connection,
        by: str,
    ) -> None:
        """
        Mark current active version as rolled back.

        Args:
            conn: Database connection
            by: Who initiated rollback
        """
        conn.execute(
            text(
                """
                UPDATE policy.policy_versions
                SET rolled_back_at = NOW(), rolled_back_by = :by
                WHERE is_active = true
                """
            ),
            {"by": by},
        )

    def activate_version(
        self,
        conn: Connection,
        version: str,
    ) -> None:
        """
        Activate a specific version.

        Args:
            conn: Database connection
            version: Version string to activate
        """
        conn.execute(
            text(
                """
                UPDATE policy.policy_versions
                SET is_active = true
                WHERE version = :version
                """
            ),
            {"version": version},
        )

    # =========================================================================
    # PROVENANCE (READ/WRITE)
    # =========================================================================

    def insert_provenance(
        self,
        conn: Connection,
        policy_id: str,
        policy_type: str,
        action: str,
        changed_by: str,
        policy_version: str,
        reason: str,
    ) -> None:
        """
        Insert provenance record.

        Args:
            conn: Database connection
            policy_id: Policy ID
            policy_type: Type of policy
            action: Action performed
            changed_by: Who made the change
            policy_version: Version at time of change
            reason: Reason for change
        """
        conn.execute(
            text(
                """
                INSERT INTO policy.policy_provenance
                (policy_id, policy_type, action, changed_by, policy_version, reason)
                VALUES (:policy_id, :policy_type, :action, :changed_by, :policy_version, :reason)
                """
            ),
            {
                "policy_id": policy_id,
                "policy_type": policy_type,
                "action": action,
                "changed_by": changed_by,
                "policy_version": policy_version,
                "reason": reason,
            },
        )

    def fetch_provenance(
        self,
        conn: Connection,
        policy_version: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch policy provenance records.

        Args:
            conn: Database connection
            policy_version: Filter by policy version (optional)
            limit: Max results

        Returns:
            List of provenance dicts
        """
        sql = """
            SELECT policy_type, action, changed_by, changed_at, reason
            FROM policy.policy_provenance
        """
        params: Dict[str, Any] = {"limit": limit}

        if policy_version:
            sql += " WHERE policy_version = :version"
            params["version"] = policy_version

        sql += " ORDER BY changed_at DESC LIMIT :limit"

        rows = conn.execute(text(sql), params)
        return [dict(row._mapping) for row in rows]

    # =========================================================================
    # DEPENDENCIES (READ/WRITE)
    # =========================================================================

    def fetch_dependencies(
        self,
        conn: Connection,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all policy dependencies.

        Returns:
            List of dependency dicts
        """
        rows = conn.execute(
            text(
                """
                SELECT id, source_policy, target_policy, dependency_type,
                       resolution_strategy, priority, description
                FROM policy.policy_dependencies
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    def fetch_dependency_edges(
        self,
        conn: Connection,
        active_only: bool = True,
    ) -> List[Tuple[str, str]]:
        """
        Fetch dependency edges for cycle detection.

        Args:
            conn: Database connection
            active_only: Only return active dependencies (default True)

        Returns:
            List of (source, target) tuples
        """
        sql = "SELECT source_policy, target_policy FROM policy.policy_dependencies"
        if active_only:
            sql += " WHERE is_active = true"
        rows = conn.execute(text(sql))
        return [(row[0], row[1]) for row in rows]

    def fetch_dependency_edges_with_type(
        self,
        conn: Connection,
    ) -> List[Tuple[str, str, str]]:
        """
        Fetch active dependency edges with dependency type for DAG validation.

        Returns:
            List of (source, target, dependency_type) tuples
        """
        rows = conn.execute(
            text(
                """
                SELECT source_policy, target_policy, dependency_type
                FROM policy.policy_dependencies
                WHERE is_active = true
                """
            )
        )
        return [(row[0], row[1], row[2]) for row in rows]

    def insert_dependency(
        self,
        conn: Connection,
        source_policy: str,
        target_policy: str,
        dependency_type: str,
        resolution_strategy: str,
        priority: int,
        description: str,
    ) -> None:
        """
        Insert a policy dependency.

        Args:
            conn: Database connection
            source_policy: Source policy name
            target_policy: Target policy name
            dependency_type: Type of dependency
            resolution_strategy: How to resolve conflicts
            priority: Dependency priority
            description: Description
        """
        conn.execute(
            text(
                """
                INSERT INTO policy.policy_dependencies
                (source_policy, target_policy, dependency_type, resolution_strategy, priority, description)
                VALUES (:source, :target, :dep_type, :strategy, :priority, :desc)
                """
            ),
            {
                "source": source_policy,
                "target": target_policy,
                "dep_type": dependency_type,
                "strategy": resolution_strategy,
                "priority": priority,
                "desc": description,
            },
        )

    # =========================================================================
    # CONFLICTS (READ/WRITE)
    # =========================================================================

    def fetch_conflicts(
        self,
        conn: Connection,
        include_resolved: bool = False,
        severity_min: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch policy conflicts.

        Args:
            conn: Database connection
            include_resolved: Include resolved conflicts
            severity_min: Minimum severity filter (optional)

        Returns:
            List of conflict dicts
        """
        sql = "SELECT * FROM policy.policy_conflicts WHERE 1=1"
        params: Dict[str, Any] = {}

        if not include_resolved:
            sql += " AND resolved = false"
        if severity_min is not None:
            sql += " AND severity >= :severity_min"
            params["severity_min"] = severity_min

        rows = conn.execute(text(sql), params)
        return [dict(row._mapping) for row in rows]

    def fetch_unresolved_conflicts(
        self,
        conn: Connection,
    ) -> List[Dict[str, Any]]:
        """
        Fetch unresolved conflicts for integrity check.

        Returns:
            List of unresolved conflict dicts
        """
        rows = conn.execute(
            text(
                """
                SELECT policy_a, policy_b, conflict_type, severity, description
                FROM policy.policy_conflicts
                WHERE resolved = false
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    def resolve_conflict(
        self,
        conn: Connection,
        conflict_id: str,
        resolution: str,
        resolved_by: str,
    ) -> int:
        """
        Resolve a policy conflict.

        Args:
            conn: Database connection
            conflict_id: Conflict ID
            resolution: Resolution description
            resolved_by: Who resolved

        Returns:
            Number of rows updated
        """
        result = conn.execute(
            text(
                """
                UPDATE policy.policy_conflicts
                SET resolved = true, resolution = :res, resolved_by = :by, resolved_at = NOW()
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {"id": conflict_id, "res": resolution, "by": resolved_by},
        )
        return result.rowcount

    # =========================================================================
    # TEMPORAL POLICIES (READ/WRITE)
    # =========================================================================

    def fetch_temporal_policies(
        self,
        conn: Connection,
        metric: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch temporal policies.

        Args:
            conn: Database connection
            metric: Filter by metric type
            include_inactive: Include inactive policies (default False = active only)

        Returns:
            List of temporal policy dicts
        """
        sql = "SELECT * FROM policy.temporal_policies WHERE 1=1"
        params: Dict[str, Any] = {}

        if not include_inactive:
            sql += " AND is_active = true"
        if metric:
            sql += " AND metric = :metric"
            params["metric"] = metric

        rows = conn.execute(text(sql), params)
        return [dict(row._mapping) for row in rows]

    def insert_temporal_policy(
        self,
        conn: Connection,
        name: str,
        description: Optional[str],
        temporal_type: str,
        metric: str,
        max_value: float,
        window_seconds: int,
        breach_action: str,
        cooldown_on_breach: int,
    ) -> None:
        """
        Insert a temporal policy.

        Args:
            conn: Database connection
            name: Policy name
            description: Description
            temporal_type: Type of temporal policy
            metric: Metric being tracked
            max_value: Maximum allowed value
            window_seconds: Time window in seconds
            breach_action: Action on breach
            cooldown_on_breach: Cooldown seconds after breach
        """
        conn.execute(
            text(
                """
                INSERT INTO policy.temporal_policies
                (name, description, temporal_type, metric, max_value,
                 window_seconds, breach_action, cooldown_on_breach)
                VALUES (:name, :desc, :temporal_type, :metric, :max_value,
                        :window_seconds, :breach_action, :cooldown_on_breach)
                """
            ),
            {
                "name": name,
                "desc": description,
                "temporal_type": temporal_type,
                "metric": metric,
                "max_value": max_value,
                "window_seconds": window_seconds,
                "breach_action": breach_action,
                "cooldown_on_breach": cooldown_on_breach,
            },
        )

    def fetch_temporal_policy_for_utilization(
        self,
        conn: Connection,
        policy_id: str,
    ) -> Optional[Tuple[float, int]]:
        """
        Fetch temporal policy max_value and window for utilization check.

        Args:
            conn: Database connection
            policy_id: Policy ID

        Returns:
            Tuple of (max_value, window_seconds) or None
        """
        row = conn.execute(
            text(
                """
                SELECT max_value, window_seconds FROM policy.temporal_policies
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {"id": policy_id},
        ).first()
        return (row[0], row[1]) if row else None

    def fetch_temporal_metric_sum(
        self,
        conn: Connection,
        policy_id: str,
        window_seconds: int,
    ) -> float:
        """
        Fetch sum of temporal metric events in window.

        Args:
            conn: Database connection
            policy_id: Policy ID
            window_seconds: Window in seconds

        Returns:
            Sum of values in window
        """
        # window_seconds is an int, safe to interpolate into SQL
        # (placeholders don't work inside INTERVAL literal)
        sql = f"""
            SELECT COALESCE(SUM(value), 0) as total
            FROM policy.temporal_metric_events
            WHERE policy_id = CAST(:id AS UUID)
              AND occurred_at > NOW() - INTERVAL '{window_seconds} seconds'
        """
        row = conn.execute(text(sql), {"id": policy_id}).first()
        return float(row[0]) if row else 0.0

    # =========================================================================
    # TEMPORAL EVENTS GC (WRITE)
    # =========================================================================

    def delete_old_temporal_events(
        self,
        conn: Connection,
        retention_hours: int,
    ) -> int:
        """
        Delete temporal events older than retention period.

        Args:
            conn: Database connection
            retention_hours: Hours to retain

        Returns:
            Number of rows deleted
        """
        # retention_hours is an int, safe to interpolate
        # (placeholders don't work inside INTERVAL literal)
        sql = f"""
            DELETE FROM policy.temporal_metric_events
            WHERE occurred_at < NOW() - INTERVAL '{retention_hours} hours'
        """
        result = conn.execute(text(sql))
        return result.rowcount

    def compact_temporal_events(
        self,
        conn: Connection,
        compact_hours: int,
        retention_hours: int,
    ) -> int:
        """
        Compact old events into hourly aggregates.

        Args:
            conn: Database connection
            compact_hours: Hours threshold for compaction
            retention_hours: Maximum retention period

        Returns:
            Number of rows compacted
        """
        # compact_hours and retention_hours are ints, safe to interpolate
        # (placeholders don't work inside INTERVAL literal)

        # Insert aggregates
        insert_sql = f"""
            INSERT INTO policy.temporal_metric_windows
            (policy_id, agent_id, tenant_id, window_key, current_sum, current_count,
             current_max, window_start, window_end, updated_at)
            SELECT
                policy_id,
                agent_id,
                tenant_id,
                policy_id::text || ':' || COALESCE(agent_id, '') || ':' || date_trunc('hour', occurred_at)::text,
                SUM(value),
                COUNT(*),
                MAX(value),
                date_trunc('hour', occurred_at),
                date_trunc('hour', occurred_at) + INTERVAL '1 hour',
                NOW()
            FROM policy.temporal_metric_events
            WHERE occurred_at < NOW() - INTERVAL '{compact_hours} hours'
                AND occurred_at >= NOW() - INTERVAL '{retention_hours} hours'
            GROUP BY policy_id, agent_id, tenant_id, date_trunc('hour', occurred_at)
            ON CONFLICT (window_key) DO UPDATE
            SET current_sum = policy.temporal_metric_windows.current_sum + EXCLUDED.current_sum,
                current_count = policy.temporal_metric_windows.current_count + EXCLUDED.current_count,
                current_max = GREATEST(policy.temporal_metric_windows.current_max, EXCLUDED.current_max),
                updated_at = NOW()
        """
        conn.execute(text(insert_sql))

        # Delete compacted events
        delete_sql = f"""
            DELETE FROM policy.temporal_metric_events
            WHERE occurred_at < NOW() - INTERVAL '{compact_hours} hours'
                AND occurred_at >= NOW() - INTERVAL '{retention_hours} hours'
        """
        result = conn.execute(text(delete_sql))
        return result.rowcount

    def cap_temporal_events(
        self,
        conn: Connection,
        max_per_policy: int,
    ) -> int:
        """
        Cap events per policy to max limit.

        Args:
            conn: Database connection
            max_per_policy: Max events to keep per policy

        Returns:
            Number of rows deleted
        """
        result = conn.execute(
            text(
                """
                WITH ranked AS (
                    SELECT id, policy_id,
                           ROW_NUMBER() OVER (PARTITION BY policy_id ORDER BY occurred_at DESC) as rn
                    FROM policy.temporal_metric_events
                )
                DELETE FROM policy.temporal_metric_events
                WHERE id IN (SELECT id FROM ranked WHERE rn > :max_per_policy)
                """
            ),
            {"max_per_policy": max_per_policy},
        )
        return result.rowcount

    def fetch_temporal_stats(
        self,
        conn: Connection,
    ) -> Dict[str, int]:
        """
        Fetch temporal event statistics.

        Returns:
            Dict with event_count and window_count
        """
        row = conn.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM policy.temporal_metric_events) as event_count,
                    (SELECT COUNT(*) FROM policy.temporal_metric_windows) as window_count
                """
            )
        ).first()
        return {"event_count": row[0], "window_count": row[1]} if row else {"event_count": 0, "window_count": 0}

    def fetch_temporal_storage_stats(
        self,
        conn: Connection,
    ) -> Optional[Tuple]:
        """
        Fetch comprehensive temporal storage statistics.

        Returns:
            Tuple of (event_count, window_count, oldest_event, newest_event,
                     policies_with_events, events_size, windows_size) or None
        """
        row = conn.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM policy.temporal_metric_events) as event_count,
                    (SELECT COUNT(*) FROM policy.temporal_metric_windows) as window_count,
                    (SELECT MIN(occurred_at) FROM policy.temporal_metric_events) as oldest_event,
                    (SELECT MAX(occurred_at) FROM policy.temporal_metric_events) as newest_event,
                    (SELECT COUNT(DISTINCT policy_id) FROM policy.temporal_metric_events) as policies_with_events,
                    (SELECT pg_size_pretty(pg_total_relation_size('policy.temporal_metric_events'))) as events_size,
                    (SELECT pg_size_pretty(pg_total_relation_size('policy.temporal_metric_windows'))) as windows_size
                """
            )
        ).first()
        return row

    # =========================================================================
    # INTEGRITY CHECK QUERIES
    # =========================================================================

    def fetch_active_policies_for_integrity(
        self,
        conn: Connection,
        table: str,
        name_col: str,
    ) -> List[str]:
        """
        Fetch active policy names for integrity check.

        Args:
            conn: Database connection
            table: Table name (within policy schema)
            name_col: Column containing name

        Returns:
            List of policy names
        """
        rows = conn.execute(
            text(
                f"""
                SELECT {name_col} FROM policy.{table} WHERE is_active = true
                """
            )
        )
        return [row[0] for row in rows]

    def fetch_temporal_policies_for_integrity(
        self,
        conn: Connection,
    ) -> List[Dict[str, Any]]:
        """
        Fetch temporal policies for integrity check.

        Returns:
            List of temporal policy dicts with validation fields
        """
        rows = conn.execute(
            text(
                """
                SELECT name, metric, max_value, window_seconds, breach_action
                FROM policy.temporal_policies
                WHERE is_active = true
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    def fetch_ethical_constraints_for_integrity(
        self,
        conn: Connection,
    ) -> List[Dict[str, Any]]:
        """
        Fetch ethical constraints for integrity check.

        Returns:
            List of ethical constraint dicts with validation fields
        """
        rows = conn.execute(
            text(
                """
                SELECT name, enforcement_level, violation_action
                FROM policy.ethical_constraints
                WHERE is_active = true
                """
            )
        )
        return [dict(row._mapping) for row in rows]

    # =========================================================================
    # AUTO-CONNECTION CONTEXT MANAGER
    # =========================================================================

    @contextmanager
    def managed_connection(self, conn: Optional[Connection] = None):
        """L4 transaction context. All methods called during this context
        share a single connection.

        Args:
            conn: L4-owned connection (from engine.begin()). When provided,
                  L4 owns the transaction boundary. When None, opens a
                  read-only connection via engine.connect().
        """
        if conn is not None:
            # L4-provided connection — L4 owns begin/commit
            prev = self._managed_conn
            self._managed_conn = conn
            try:
                yield conn
            finally:
                self._managed_conn = prev
        else:
            # Read-only connection (no transaction boundary)
            engine = self._get_engine()
            with engine.connect() as c:
                prev = self._managed_conn
                self._managed_conn = c
                try:
                    yield c
                finally:
                    self._managed_conn = prev

    @contextmanager
    def _conn(self):
        """Read connection context — uses managed connection if available."""
        if self._managed_conn is not None:
            yield self._managed_conn
        else:
            engine = self._get_engine()
            with engine.connect() as conn:
                yield conn

    @contextmanager
    def _write_conn(self):
        """Write connection context — REQUIRES L4-owned transaction context.

        L4 must call managed_connection(conn) with an engine.begin() connection
        before invoking any write operation. Standalone writes are forbidden.

        Transaction Boundary Purity (PIN-520):
            L6 never calls begin()/commit()/rollback(). L4 owns all
            transaction boundaries via engine.begin() + managed_connection().
        """
        if self._managed_conn is not None:
            yield self._managed_conn
        else:
            raise RuntimeError(
                "PolicyEngine write requires L4-owned transaction context. "
                "Call driver.managed_connection(conn) with an engine.begin() "
                "connection before invoking write operations."
            )

    # =========================================================================
    # READ AUTO-CONNECTION WRAPPERS (*_auto)
    # =========================================================================

    def fetch_ethical_constraints_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_ethical_constraints."""
        with self._conn() as conn:
            return self.fetch_ethical_constraints(conn)

    def fetch_risk_ceilings_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_risk_ceilings."""
        with self._conn() as conn:
            return self.fetch_risk_ceilings(conn)

    def fetch_safety_rules_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_safety_rules."""
        with self._conn() as conn:
            return self.fetch_safety_rules(conn)

    def fetch_business_rules_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_business_rules."""
        with self._conn() as conn:
            return self.fetch_business_rules(conn)

    def fetch_violations_auto(
        self,
        violation_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        severity_min: Optional[float] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_violations."""
        with self._conn() as conn:
            return self.fetch_violations(
                conn,
                violation_type=violation_type,
                agent_id=agent_id,
                tenant_id=tenant_id,
                severity_min=severity_min,
                since=since,
                limit=limit,
            )

    def fetch_violation_by_id_auto(self, violation_id: str) -> Optional[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_violation_by_id."""
        with self._conn() as conn:
            return self.fetch_violation_by_id(conn, violation_id)

    def fetch_policy_versions_auto(
        self,
        include_inactive: bool = False,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_policy_versions."""
        with self._conn() as conn:
            return self.fetch_policy_versions(conn, include_inactive=include_inactive, limit=limit)

    def fetch_current_active_version_auto(self) -> Optional[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_current_active_version."""
        with self._conn() as conn:
            return self.fetch_current_active_version(conn)

    def fetch_policy_version_by_id_auto(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_policy_version_by_id."""
        with self._conn() as conn:
            return self.fetch_policy_version_by_id(conn, version_id)

    def fetch_policy_version_by_id_or_version_auto(self, version_id: str) -> Optional[Tuple]:
        """Auto-connection wrapper for fetch_policy_version_by_id_or_version."""
        with self._conn() as conn:
            return self.fetch_policy_version_by_id_or_version(conn, version_id)

    def fetch_version_for_rollback_auto(self, version: str) -> Optional[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_version_for_rollback."""
        with self._conn() as conn:
            return self.fetch_version_for_rollback(conn, version)

    def fetch_provenance_auto(
        self,
        policy_version: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_provenance."""
        with self._conn() as conn:
            return self.fetch_provenance(conn, policy_version=policy_version, limit=limit)

    def fetch_dependencies_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_dependencies."""
        with self._conn() as conn:
            return self.fetch_dependencies(conn)

    def fetch_dependency_edges_auto(self, active_only: bool = True) -> List[Tuple[str, str]]:
        """Auto-connection wrapper for fetch_dependency_edges."""
        with self._conn() as conn:
            return self.fetch_dependency_edges(conn, active_only=active_only)

    def fetch_dependency_edges_with_type_auto(self) -> List[Tuple[str, str, str]]:
        """Auto-connection wrapper for fetch_dependency_edges_with_type."""
        with self._conn() as conn:
            return self.fetch_dependency_edges_with_type(conn)

    def fetch_conflicts_auto(
        self,
        include_resolved: bool = False,
        severity_min: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_conflicts."""
        with self._conn() as conn:
            return self.fetch_conflicts(conn, include_resolved=include_resolved, severity_min=severity_min)

    def fetch_unresolved_conflicts_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_unresolved_conflicts."""
        with self._conn() as conn:
            return self.fetch_unresolved_conflicts(conn)

    def fetch_temporal_policies_auto(
        self,
        metric: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_temporal_policies."""
        with self._conn() as conn:
            return self.fetch_temporal_policies(conn, metric=metric, include_inactive=include_inactive)

    def fetch_temporal_policy_for_utilization_auto(self, policy_id: str) -> Optional[Tuple]:
        """Auto-connection wrapper for fetch_temporal_policy_for_utilization."""
        with self._conn() as conn:
            return self.fetch_temporal_policy_for_utilization(conn, policy_id)

    def fetch_temporal_metric_sum_auto(self, policy_id: str, window_seconds: int) -> float:
        """Auto-connection wrapper for fetch_temporal_metric_sum."""
        with self._conn() as conn:
            return self.fetch_temporal_metric_sum(conn, policy_id, window_seconds)

    def fetch_temporal_stats_auto(self) -> Dict[str, int]:
        """Auto-connection wrapper for fetch_temporal_stats."""
        with self._conn() as conn:
            return self.fetch_temporal_stats(conn)

    def fetch_temporal_storage_stats_auto(self) -> Optional[Tuple]:
        """Auto-connection wrapper for fetch_temporal_storage_stats."""
        with self._conn() as conn:
            return self.fetch_temporal_storage_stats(conn)

    def fetch_active_policies_for_integrity_auto(self, table: str, name_col: str) -> List[str]:
        """Auto-connection wrapper for fetch_active_policies_for_integrity."""
        with self._conn() as conn:
            return self.fetch_active_policies_for_integrity(conn, table, name_col)

    def fetch_temporal_policies_for_integrity_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_temporal_policies_for_integrity."""
        with self._conn() as conn:
            return self.fetch_temporal_policies_for_integrity(conn)

    def fetch_ethical_constraints_for_integrity_auto(self) -> List[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_ethical_constraints_for_integrity."""
        with self._conn() as conn:
            return self.fetch_ethical_constraints_for_integrity(conn)

    # =========================================================================
    # WRITE AUTO-CONNECTION WRAPPERS (*_committed)
    # PIN-520: L4 owns transaction boundaries.
    # When managed_connection() is active, these share the managed conn
    # and L4 commits. Otherwise _write_conn() auto-commits standalone.
    # =========================================================================

    def insert_evaluation_committed(
        self,
        evaluation_id: str,
        action_type: str,
        agent_id: Optional[str],
        tenant_id: Optional[str],
        request_context: str,
        decision: str,
        decision_reason: str,
        modifications: str,
        evaluation_ms: float,
        policies_checked: int,
        rules_matched: int,
        evaluated_at: datetime,
    ) -> None:
        """Write wrapper for insert_evaluation (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_evaluation(
                conn,
                evaluation_id=evaluation_id,
                action_type=action_type,
                agent_id=agent_id,
                tenant_id=tenant_id,
                request_context=request_context,
                decision=decision,
                decision_reason=decision_reason,
                modifications=modifications,
                evaluation_ms=evaluation_ms,
                policies_checked=policies_checked,
                rules_matched=rules_matched,
                evaluated_at=evaluated_at,
            )

    def insert_violation_committed(
        self,
        violation_id: str,
        evaluation_id: str,
        policy_name: str,
        violation_type: str,
        severity: str,
        description: str,
        evidence: str,
        agent_id: Optional[str],
        tenant_id: Optional[str],
        action_attempted: str,
        routed_to_governor: bool,
        governor_action: Optional[str],
        detected_at: datetime,
    ) -> None:
        """Write wrapper for insert_violation (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_violation(
                conn,
                violation_id=violation_id,
                evaluation_id=evaluation_id,
                policy_name=policy_name,
                violation_type=violation_type,
                severity=severity,
                description=description,
                evidence=evidence,
                agent_id=agent_id,
                tenant_id=tenant_id,
                action_attempted=action_attempted,
                routed_to_governor=routed_to_governor,
                governor_action=governor_action,
                detected_at=detected_at,
            )

    def update_violation_acknowledged_committed(
        self,
        violation_id: str,
        notes: Optional[str] = None,
    ) -> int:
        """Write wrapper for update_violation_acknowledged (L4 owns commit)."""
        with self._write_conn() as conn:
            return self.update_violation_acknowledged(conn, violation_id, notes=notes)

    def update_risk_ceiling_committed(
        self,
        ceiling_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """Write wrapper for update_risk_ceiling (L4 owns commit)."""
        with self._write_conn() as conn:
            self.update_risk_ceiling(conn, ceiling_id, updates)

    def reset_risk_ceiling_committed(self, ceiling_id: str) -> int:
        """Write wrapper for reset_risk_ceiling (L4 owns commit)."""
        with self._write_conn() as conn:
            return self.reset_risk_ceiling(conn, ceiling_id)

    def update_safety_rule_committed(
        self,
        rule_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """Write wrapper for update_safety_rule (L4 owns commit)."""
        with self._write_conn() as conn:
            self.update_safety_rule(conn, rule_id, updates)

    def deactivate_all_versions_committed(self) -> None:
        """Write wrapper for deactivate_all_versions (L4 owns commit)."""
        with self._write_conn() as conn:
            self.deactivate_all_versions(conn)

    def insert_policy_version_committed(
        self,
        version_id: str,
        version: str,
        policy_hash: str,
        created_by: str,
        description: str,
    ) -> None:
        """Write wrapper for insert_policy_version (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_policy_version(
                conn,
                version_id=version_id,
                version=version,
                policy_hash=policy_hash,
                created_by=created_by,
                description=description,
            )

    def mark_version_rolled_back_committed(self, by: str) -> None:
        """Write wrapper for mark_version_rolled_back (L4 owns commit)."""
        with self._write_conn() as conn:
            self.mark_version_rolled_back(conn, by)

    def activate_version_committed(self, version: str) -> None:
        """Write wrapper for activate_version (L4 owns commit)."""
        with self._write_conn() as conn:
            self.activate_version(conn, version)

    def insert_provenance_committed(
        self,
        policy_id: str,
        policy_type: str,
        action: str,
        changed_by: str,
        policy_version: str,
        reason: str,
    ) -> None:
        """Write wrapper for insert_provenance (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_provenance(
                conn,
                policy_id=policy_id,
                policy_type=policy_type,
                action=action,
                changed_by=changed_by,
                policy_version=policy_version,
                reason=reason,
            )

    def insert_dependency_committed(
        self,
        source_policy: str,
        target_policy: str,
        dependency_type: str,
        resolution_strategy: str,
        priority: int,
        description: str,
    ) -> None:
        """Write wrapper for insert_dependency (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_dependency(
                conn,
                source_policy=source_policy,
                target_policy=target_policy,
                dependency_type=dependency_type,
                resolution_strategy=resolution_strategy,
                priority=priority,
                description=description,
            )

    def resolve_conflict_committed(
        self,
        conflict_id: str,
        resolution: str,
        resolved_by: str,
    ) -> int:
        """Write wrapper for resolve_conflict (L4 owns commit)."""
        with self._write_conn() as conn:
            return self.resolve_conflict(conn, conflict_id, resolution, resolved_by)

    def insert_temporal_policy_committed(
        self,
        name: str,
        description: Optional[str],
        temporal_type: str,
        metric: str,
        max_value: float,
        window_seconds: int,
        breach_action: str,
        cooldown_on_breach: int,
    ) -> None:
        """Write wrapper for insert_temporal_policy (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_temporal_policy(
                conn,
                name=name,
                description=description,
                temporal_type=temporal_type,
                metric=metric,
                max_value=max_value,
                window_seconds=window_seconds,
                breach_action=breach_action,
                cooldown_on_breach=cooldown_on_breach,
            )

    def delete_old_temporal_events_committed(self, retention_hours: int) -> int:
        """Write wrapper for delete_old_temporal_events (L4 owns commit)."""
        with self._write_conn() as conn:
            return self.delete_old_temporal_events(conn, retention_hours)

    def compact_temporal_events_committed(self, compact_hours: int, retention_hours: int) -> int:
        """Write wrapper for compact_temporal_events (L4 owns commit)."""
        with self._write_conn() as conn:
            return self.compact_temporal_events(conn, compact_hours, retention_hours)

    def cap_temporal_events_committed(self, max_per_policy: int) -> int:
        """Write wrapper for cap_temporal_events (L4 owns commit)."""
        with self._write_conn() as conn:
            return self.cap_temporal_events(conn, max_per_policy)

    # =========================================================================
    # SNAPSHOT OPERATIONS (READ/WRITE)
    # =========================================================================

    def fetch_snapshot_by_id(self, conn: Connection, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Fetch policy snapshot by ID."""
        row = conn.execute(
            text("SELECT snapshot_id, policy_count, thresholds, policies, integrity_hash FROM policy.snapshots WHERE snapshot_id = :snapshot_id"),
            {"snapshot_id": snapshot_id},
        )
        result = row.mappings().first()
        return dict(result) if result else None

    def fetch_snapshot_by_id_auto(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Auto-connection wrapper for fetch_snapshot_by_id."""
        with self._conn() as conn:
            return self.fetch_snapshot_by_id(conn, snapshot_id)

    def insert_snapshot(self, conn: Connection, snapshot_id: str, tenant_id: str, policies: str, thresholds: str, policy_count: int, integrity_hash: str) -> None:
        """Insert a policy snapshot."""
        conn.execute(
            text("""
                INSERT INTO policy.snapshots (snapshot_id, tenant_id, policies, thresholds, policy_count, integrity_hash, created_at)
                VALUES (:snapshot_id, :tenant_id, CAST(:policies AS JSONB), CAST(:thresholds AS JSONB), :policy_count, :integrity_hash, NOW())
            """),
            {"snapshot_id": snapshot_id, "tenant_id": tenant_id, "policies": policies, "thresholds": thresholds, "policy_count": policy_count, "integrity_hash": integrity_hash},
        )

    def insert_snapshot_committed(self, snapshot_id: str, tenant_id: str, policies: str, thresholds: str, policy_count: int, integrity_hash: str) -> None:
        """Write wrapper for insert_snapshot (L4 owns commit)."""
        with self._write_conn() as conn:
            self.insert_snapshot(conn, snapshot_id, tenant_id, policies, thresholds, policy_count, integrity_hash)


def get_policy_engine_driver(db_url: str) -> PolicyEngineDriver:
    """Factory function for PolicyEngineDriver."""
    return PolicyEngineDriver(db_url)


__all__ = [
    "PolicyEngineDriver",
    "get_policy_engine_driver",
]
