# capability_id: CAP-009
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide (Recovery API)
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: recovery_candidates, suggestion_action, suggestion_input, suggestion_provenance
#   Writes: none
# Database:
#   Scope: domain (recovery)
#   Models: RecoveryCandidate, SuggestionAction, SuggestionInput, SuggestionProvenance
# Role: DB read driver for Recovery APIs (DB boundary crossing) — L6 DOES NOT COMMIT
# Callers: L4 handlers via registry dispatch
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: L2 first-principles purity — move session.execute() out of L2
# artifact_class: CODE

"""
Recovery Read Driver - DB read operations for Recovery APIs.

Extracted from hoc/api/cus/recovery/recovery.py to achieve L2 first-principles purity.

Constraints (enforced by PIN-250):
- Read-only: No write operations, no policy logic
- No cross-service calls
- SQL text preserved exactly (no changes)
- L6 drivers DO NOT COMMIT
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session


class RecoveryReadDriver:
    """
    Sync DB read operations for Recovery APIs.

    Read-only driver. No writes, no policy logic.
    Raw SQL preserved exactly as extracted from API files.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_candidate_detail(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed recovery candidate by ID.

        SQL preserved exactly from recovery.py get_candidate_detail endpoint.

        Args:
            candidate_id: Candidate ID to fetch

        Returns:
            Dict with candidate data or None if not found
        """
        result = self.session.execute(
            text(
                """
                SELECT
                    rc.id, rc.failure_match_id, rc.suggestion, rc.confidence,
                    rc.explain, rc.decision, rc.occurrence_count, rc.last_occurrence_at,
                    rc.created_at, rc.approved_by_human, rc.approved_at, rc.review_note,
                    rc.error_code, rc.source, rc.selected_action_id, rc.rules_evaluated,
                    rc.execution_status, rc.executed_at, rc.execution_result
                FROM recovery_candidates rc
                WHERE rc.id = :id
            """
            ),
            {"id": candidate_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "failure_match_id": str(row[1]),
            "suggestion": row[2],
            "confidence": row[3],
            "explain": json.loads(row[4]) if isinstance(row[4], str) else (row[4] or {}),
            "decision": row[5],
            "occurrence_count": row[6],
            "last_occurrence_at": row[7].isoformat() if row[7] else None,
            "created_at": row[8].isoformat() if row[8] else None,
            "approved_by_human": row[9],
            "approved_at": row[10].isoformat() if row[10] else None,
            "review_note": row[11],
            "error_code": row[12],
            "source": row[13],
            "selected_action_id": row[14],
            "rules_evaluated": json.loads(row[15]) if isinstance(row[15], str) else (row[15] or []),
            "execution_status": row[16],
            "executed_at": row[17].isoformat() if row[17] else None,
            "execution_result": json.loads(row[18]) if isinstance(row[18], str) else row[18],
        }

    def get_selected_action(self, action_id: int) -> Optional[Dict[str, Any]]:
        """
        Get selected action by ID.

        SQL preserved exactly from recovery.py get_candidate_detail endpoint.

        Args:
            action_id: Action ID to fetch

        Returns:
            Dict with action data or None if not found
        """
        result = self.session.execute(
            text(
                """
                SELECT id, action_code, name, description, action_type, template,
                       applies_to_error_codes, applies_to_skills, success_rate,
                       total_applications, is_automated, requires_approval, priority, is_active
                FROM m10_recovery.suggestion_action
                WHERE id = :id
            """
            ),
            {"id": action_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "action_code": row[1],
            "name": row[2],
            "description": row[3],
            "action_type": row[4],
            "template": json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {}),
            "applies_to_error_codes": row[6] or [],
            "applies_to_skills": row[7] or [],
            "success_rate": row[8],
            "total_applications": row[9],
            "is_automated": row[10],
            "requires_approval": row[11],
            "priority": row[12],
            "is_active": row[13],
        }

    def get_suggestion_inputs(self, suggestion_id: int) -> List[Dict[str, Any]]:
        """
        Get inputs for a suggestion.

        SQL preserved exactly from recovery.py get_candidate_detail endpoint.

        Args:
            suggestion_id: Suggestion/candidate ID

        Returns:
            List of input dicts (empty list if table doesn't exist or no inputs)
        """
        try:
            result = self.session.execute(
                text(
                    """
                    SELECT id, input_type, raw_value, normalized_value, parsed_data,
                           confidence, weight, source, created_at
                    FROM m10_recovery.suggestion_input
                    WHERE suggestion_id = :id
                    ORDER BY created_at ASC
                """
                ),
                {"id": suggestion_id},
            )
            inputs = []
            for inp_row in result.fetchall():
                inputs.append(
                    {
                        "id": inp_row[0],
                        "input_type": inp_row[1],
                        "raw_value": inp_row[2],
                        "normalized_value": inp_row[3],
                        "parsed_data": json.loads(inp_row[4])
                        if isinstance(inp_row[4], str)
                        else (inp_row[4] or {}),
                        "confidence": inp_row[5],
                        "weight": inp_row[6],
                        "source": inp_row[7],
                        "created_at": inp_row[8].isoformat() if inp_row[8] else None,
                    }
                )
            return inputs
        except Exception:
            return []  # Table may not exist yet

    def get_suggestion_provenance(self, suggestion_id: int) -> List[Dict[str, Any]]:
        """
        Get provenance history for a suggestion.

        SQL preserved exactly from recovery.py get_candidate_detail endpoint.

        Args:
            suggestion_id: Suggestion/candidate ID

        Returns:
            List of provenance dicts (empty list if table doesn't exist or no provenance)
        """
        try:
            result = self.session.execute(
                text(
                    """
                    SELECT id, event_type, details, rule_id, action_id,
                           confidence_before, confidence_after, actor, actor_type,
                           created_at, duration_ms
                    FROM m10_recovery.suggestion_provenance
                    WHERE suggestion_id = :id
                    ORDER BY created_at ASC
                """
                ),
                {"id": suggestion_id},
            )
            provenance = []
            for prov_row in result.fetchall():
                provenance.append(
                    {
                        "id": prov_row[0],
                        "event_type": prov_row[1],
                        "details": json.loads(prov_row[2])
                        if isinstance(prov_row[2], str)
                        else (prov_row[2] or {}),
                        "rule_id": prov_row[3],
                        "action_id": prov_row[4],
                        "confidence_before": prov_row[5],
                        "confidence_after": prov_row[6],
                        "actor": prov_row[7],
                        "actor_type": prov_row[8],
                        "created_at": prov_row[9].isoformat() if prov_row[9] else None,
                        "duration_ms": prov_row[10],
                    }
                )
            return provenance
        except Exception:
            return []  # Table may not exist yet

    def candidate_exists(self, candidate_id: int) -> Tuple[bool, Optional[float]]:
        """
        Check if candidate exists and return its confidence.

        SQL preserved exactly from recovery.py update_candidate endpoint.

        Args:
            candidate_id: Candidate ID to check

        Returns:
            Tuple of (exists: bool, confidence: Optional[float])
        """
        result = self.session.execute(
            text("SELECT id, confidence FROM recovery_candidates WHERE id = :id"),
            {"id": candidate_id},
        )
        row = result.fetchone()
        if row:
            return (True, row[1])
        return (False, None)

    def list_actions(
        self,
        action_type: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List recovery actions from catalog.

        SQL preserved exactly from recovery.py list_actions endpoint.

        Args:
            action_type: Optional filter by action type
            active_only: Only return active actions
            limit: Maximum results

        Returns:
            List of action dicts
        """
        query = """
            SELECT id, action_code, name, description, action_type, template,
                   applies_to_error_codes, applies_to_skills, success_rate,
                   total_applications, is_automated, requires_approval, priority, is_active
            FROM m10_recovery.suggestion_action
            WHERE 1=1
        """
        params: Dict[str, Any] = {"limit": limit}

        if active_only:
            query += " AND is_active = TRUE"

        if action_type:
            query += " AND action_type = :action_type"
            params["action_type"] = action_type

        query += " ORDER BY priority DESC, name ASC LIMIT :limit"

        result = self.session.execute(text(query), params)
        actions = []

        for row in result.fetchall():
            actions.append(
                {
                    "id": row[0],
                    "action_code": row[1],
                    "name": row[2],
                    "description": row[3],
                    "action_type": row[4],
                    "template": json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {}),
                    "applies_to_error_codes": row[6] or [],
                    "applies_to_skills": row[7] or [],
                    "success_rate": row[8],
                    "total_applications": row[9],
                    "is_automated": row[10],
                    "requires_approval": row[11],
                    "priority": row[12],
                    "is_active": row[13],
                }
            )

        return actions
