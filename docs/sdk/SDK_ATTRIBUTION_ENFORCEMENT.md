# SDK Attribution Enforcement — Implementation Guide

**Status:** READY FOR IMPLEMENTATION
**Effective:** Post Phase-3 Rollout
**Reference:** AOS_SDK_ATTRIBUTION_CONTRACT.md, ATTRIBUTION_ARCHITECTURE.md

---

## Purpose

This document provides **concrete implementation code** for attribution enforcement in AOS SDKs. All SDK implementations (Python, JavaScript, future languages) MUST implement this logic identically.

---

## 1. Error Codes (Canonical)

```python
# Python: aos_sdk/errors.py

from enum import Enum

class AttributionErrorCode(str, Enum):
    """
    Attribution validation error codes.
    These codes are contractual — do not change without governance approval.
    """
    ATTR_AGENT_MISSING = "ATTR_AGENT_MISSING"
    ATTR_ACTOR_TYPE_MISSING = "ATTR_ACTOR_TYPE_MISSING"
    ATTR_ACTOR_TYPE_INVALID = "ATTR_ACTOR_TYPE_INVALID"
    ATTR_ACTOR_ID_REQUIRED = "ATTR_ACTOR_ID_REQUIRED"
    ATTR_ACTOR_ID_FORBIDDEN = "ATTR_ACTOR_ID_FORBIDDEN"
    ATTR_ORIGIN_SYSTEM_MISSING = "ATTR_ORIGIN_SYSTEM_MISSING"


class AttributionError(Exception):
    """
    Raised when attribution validation fails.

    This error is BLOCKING — the run will not be created.
    SDK consumers must fix their code, not catch and ignore.
    """

    def __init__(self, code: AttributionErrorCode, message: str, field: str):
        self.code = code
        self.message = message
        self.field = field
        super().__init__(f"[{code.value}] {message}")

    def to_dict(self) -> dict:
        return {
            "error_type": "attribution_validation",
            "code": self.code.value,
            "message": self.message,
            "field": self.field,
        }
```

```typescript
// JavaScript: aos-sdk/src/errors.ts

export enum AttributionErrorCode {
  ATTR_AGENT_MISSING = "ATTR_AGENT_MISSING",
  ATTR_ACTOR_TYPE_MISSING = "ATTR_ACTOR_TYPE_MISSING",
  ATTR_ACTOR_TYPE_INVALID = "ATTR_ACTOR_TYPE_INVALID",
  ATTR_ACTOR_ID_REQUIRED = "ATTR_ACTOR_ID_REQUIRED",
  ATTR_ACTOR_ID_FORBIDDEN = "ATTR_ACTOR_ID_FORBIDDEN",
  ATTR_ORIGIN_SYSTEM_MISSING = "ATTR_ORIGIN_SYSTEM_MISSING",
}

export class AttributionError extends Error {
  readonly code: AttributionErrorCode;
  readonly field: string;

  constructor(code: AttributionErrorCode, message: string, field: string) {
    super(`[${code}] ${message}`);
    this.name = "AttributionError";
    this.code = code;
    this.field = field;
  }

  toJSON() {
    return {
      error_type: "attribution_validation",
      code: this.code,
      message: this.message,
      field: this.field,
    };
  }
}
```

---

## 2. Actor Types (Closed Set)

```python
# Python: aos_sdk/types.py

from enum import Enum
from typing import Literal

class ActorType(str, Enum):
    """
    Actor classification. This is a CLOSED SET.
    Adding new values requires governance approval.
    """
    HUMAN = "HUMAN"      # Real human user with identity
    SYSTEM = "SYSTEM"    # Automated process (cron, scheduler, policy trigger)
    SERVICE = "SERVICE"  # Service-to-service call (internal API, worker)

# Type alias for strict typing
ActorTypeLiteral = Literal["HUMAN", "SYSTEM", "SERVICE"]
VALID_ACTOR_TYPES = frozenset({"HUMAN", "SYSTEM", "SERVICE"})
```

```typescript
// JavaScript: aos-sdk/src/types.ts

export type ActorType = "HUMAN" | "SYSTEM" | "SERVICE";

export const VALID_ACTOR_TYPES: ReadonlySet<string> = new Set([
  "HUMAN",
  "SYSTEM",
  "SERVICE",
]);
```

---

## 3. Attribution Context (Input Type)

```python
# Python: aos_sdk/attribution.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

@dataclass(frozen=True)
class AttributionContext:
    """
    Attribution context for run creation.

    This is the ONLY way to provide attribution.
    All fields are validated before any network call.
    """
    agent_id: str                          # REQUIRED: Executing agent identifier
    actor_type: str                        # REQUIRED: HUMAN | SYSTEM | SERVICE
    origin_system_id: str                  # REQUIRED: Originating system identifier
    actor_id: Optional[str] = None         # REQUIRED iff actor_type == HUMAN
    origin_ts: Optional[datetime] = None   # Auto-set if not provided
    origin_ip: Optional[str] = None        # Best effort, not validated

    def __post_init__(self):
        # Validation happens in validate_attribution(), not here
        pass
```

```typescript
// JavaScript: aos-sdk/src/attribution.ts

export interface AttributionContext {
  /** REQUIRED: Executing agent identifier */
  agent_id: string;

  /** REQUIRED: Actor classification (HUMAN | SYSTEM | SERVICE) */
  actor_type: ActorType;

  /** REQUIRED: Originating system identifier */
  origin_system_id: string;

  /** REQUIRED if actor_type === "HUMAN", FORBIDDEN otherwise */
  actor_id?: string | null;

  /** Auto-set if not provided */
  origin_ts?: Date;

  /** Best effort, not validated */
  origin_ip?: string;
}
```

---

## 4. Validation Logic (Core Implementation)

### Python Implementation

```python
# Python: aos_sdk/validation.py

from typing import Optional, List
from datetime import datetime, timezone
import logging

from .errors import AttributionError, AttributionErrorCode
from .types import VALID_ACTOR_TYPES
from .attribution import AttributionContext

logger = logging.getLogger("aos_sdk.attribution")


def validate_attribution(
    ctx: AttributionContext,
    *,
    enforcement_mode: str = "hard",  # "shadow" | "soft" | "hard"
    allow_legacy_override: bool = False,
) -> List[AttributionError]:
    """
    Validate attribution context before run creation.

    Args:
        ctx: Attribution context to validate
        enforcement_mode:
            - "shadow": Log violations, don't reject
            - "soft": Reject unless allow_legacy_override=True
            - "hard": Always reject invalid attribution
        allow_legacy_override: Only honored in "soft" mode

    Returns:
        List of validation errors (empty if valid)

    Raises:
        AttributionError: In "hard" mode or "soft" mode without override
    """
    errors: List[AttributionError] = []

    # ─────────────────────────────────────────────────────────────────────────
    # Rule 1: agent_id REQUIRED
    # ─────────────────────────────────────────────────────────────────────────
    if not ctx.agent_id or ctx.agent_id.strip() == "":
        errors.append(AttributionError(
            code=AttributionErrorCode.ATTR_AGENT_MISSING,
            message="agent_id is required and cannot be empty",
            field="agent_id",
        ))

    # Explicitly reject legacy sentinel values
    if ctx.agent_id == "legacy-unknown":
        errors.append(AttributionError(
            code=AttributionErrorCode.ATTR_AGENT_MISSING,
            message="agent_id cannot be 'legacy-unknown' - provide real agent identifier",
            field="agent_id",
        ))

    # ─────────────────────────────────────────────────────────────────────────
    # Rule 2: actor_type REQUIRED and from closed set
    # ─────────────────────────────────────────────────────────────────────────
    if not ctx.actor_type or ctx.actor_type.strip() == "":
        errors.append(AttributionError(
            code=AttributionErrorCode.ATTR_ACTOR_TYPE_MISSING,
            message="actor_type is required (HUMAN | SYSTEM | SERVICE)",
            field="actor_type",
        ))
    elif ctx.actor_type.upper() not in VALID_ACTOR_TYPES:
        errors.append(AttributionError(
            code=AttributionErrorCode.ATTR_ACTOR_TYPE_INVALID,
            message=f"actor_type must be one of: {', '.join(sorted(VALID_ACTOR_TYPES))}",
            field="actor_type",
        ))

    # ─────────────────────────────────────────────────────────────────────────
    # Rule 3: origin_system_id REQUIRED
    # ─────────────────────────────────────────────────────────────────────────
    if not ctx.origin_system_id or ctx.origin_system_id.strip() == "":
        errors.append(AttributionError(
            code=AttributionErrorCode.ATTR_ORIGIN_SYSTEM_MISSING,
            message="origin_system_id is required for accountability",
            field="origin_system_id",
        ))

    # Explicitly reject legacy sentinel values
    if ctx.origin_system_id == "legacy-migration":
        errors.append(AttributionError(
            code=AttributionErrorCode.ATTR_ORIGIN_SYSTEM_MISSING,
            message="origin_system_id cannot be 'legacy-migration' - provide real system identifier",
            field="origin_system_id",
        ))

    # ─────────────────────────────────────────────────────────────────────────
    # Rule 4: actor_id REQUIRED iff actor_type == HUMAN
    # ─────────────────────────────────────────────────────────────────────────
    actor_type_upper = (ctx.actor_type or "").upper()

    if actor_type_upper == "HUMAN":
        if not ctx.actor_id or ctx.actor_id.strip() == "":
            errors.append(AttributionError(
                code=AttributionErrorCode.ATTR_ACTOR_ID_REQUIRED,
                message="actor_id is required when actor_type is HUMAN",
                field="actor_id",
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Rule 5: actor_id MUST be NULL if actor_type != HUMAN
    # ─────────────────────────────────────────────────────────────────────────
    if actor_type_upper in ("SYSTEM", "SERVICE"):
        if ctx.actor_id is not None and ctx.actor_id.strip() != "":
            errors.append(AttributionError(
                code=AttributionErrorCode.ATTR_ACTOR_ID_FORBIDDEN,
                message=f"actor_id must be null when actor_type is {actor_type_upper}",
                field="actor_id",
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Enforcement Decision
    # ─────────────────────────────────────────────────────────────────────────
    if errors:
        _log_violations(ctx, errors, enforcement_mode)

        if enforcement_mode == "shadow":
            # Log only, do not reject
            return errors

        if enforcement_mode == "soft" and allow_legacy_override:
            # Log override usage for audit
            logger.warning(
                "attribution_override_used",
                extra={
                    "agent_id": ctx.agent_id,
                    "origin_system_id": ctx.origin_system_id,
                    "errors": [e.code.value for e in errors],
                }
            )
            return errors

        # Hard fail (or soft fail without override)
        raise errors[0]  # Raise first error

    return []


def _log_violations(
    ctx: AttributionContext,
    errors: List[AttributionError],
    mode: str,
) -> None:
    """Log attribution violations for monitoring."""
    logger.warning(
        "attribution_validation_failed",
        extra={
            "enforcement_mode": mode,
            "agent_id": ctx.agent_id,
            "actor_type": ctx.actor_type,
            "origin_system_id": ctx.origin_system_id,
            "has_actor_id": ctx.actor_id is not None,
            "error_codes": [e.code.value for e in errors],
            "error_count": len(errors),
        }
    )
```

### JavaScript Implementation

```typescript
// JavaScript: aos-sdk/src/validation.ts

import { AttributionError, AttributionErrorCode } from "./errors";
import { AttributionContext, ActorType, VALID_ACTOR_TYPES } from "./types";

export type EnforcementMode = "shadow" | "soft" | "hard";

export interface ValidationOptions {
  enforcementMode?: EnforcementMode;
  allowLegacyOverride?: boolean;
}

export function validateAttribution(
  ctx: AttributionContext,
  options: ValidationOptions = {}
): AttributionError[] {
  const {
    enforcementMode = "hard",
    allowLegacyOverride = false
  } = options;

  const errors: AttributionError[] = [];

  // ─────────────────────────────────────────────────────────────────────────
  // Rule 1: agent_id REQUIRED
  // ─────────────────────────────────────────────────────────────────────────
  if (!ctx.agent_id || ctx.agent_id.trim() === "") {
    errors.push(new AttributionError(
      AttributionErrorCode.ATTR_AGENT_MISSING,
      "agent_id is required and cannot be empty",
      "agent_id"
    ));
  }

  // Explicitly reject legacy sentinel values
  if (ctx.agent_id === "legacy-unknown") {
    errors.push(new AttributionError(
      AttributionErrorCode.ATTR_AGENT_MISSING,
      "agent_id cannot be 'legacy-unknown' - provide real agent identifier",
      "agent_id"
    ));
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Rule 2: actor_type REQUIRED and from closed set
  // ─────────────────────────────────────────────────────────────────────────
  if (!ctx.actor_type || ctx.actor_type.trim() === "") {
    errors.push(new AttributionError(
      AttributionErrorCode.ATTR_ACTOR_TYPE_MISSING,
      "actor_type is required (HUMAN | SYSTEM | SERVICE)",
      "actor_type"
    ));
  } else if (!VALID_ACTOR_TYPES.has(ctx.actor_type.toUpperCase())) {
    errors.push(new AttributionError(
      AttributionErrorCode.ATTR_ACTOR_TYPE_INVALID,
      `actor_type must be one of: ${[...VALID_ACTOR_TYPES].sort().join(", ")}`,
      "actor_type"
    ));
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Rule 3: origin_system_id REQUIRED
  // ─────────────────────────────────────────────────────────────────────────
  if (!ctx.origin_system_id || ctx.origin_system_id.trim() === "") {
    errors.push(new AttributionError(
      AttributionErrorCode.ATTR_ORIGIN_SYSTEM_MISSING,
      "origin_system_id is required for accountability",
      "origin_system_id"
    ));
  }

  // Explicitly reject legacy sentinel values
  if (ctx.origin_system_id === "legacy-migration") {
    errors.push(new AttributionError(
      AttributionErrorCode.ATTR_ORIGIN_SYSTEM_MISSING,
      "origin_system_id cannot be 'legacy-migration' - provide real system identifier",
      "origin_system_id"
    ));
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Rule 4: actor_id REQUIRED iff actor_type == HUMAN
  // ─────────────────────────────────────────────────────────────────────────
  const actorTypeUpper = (ctx.actor_type || "").toUpperCase();

  if (actorTypeUpper === "HUMAN") {
    if (!ctx.actor_id || ctx.actor_id.trim() === "") {
      errors.push(new AttributionError(
        AttributionErrorCode.ATTR_ACTOR_ID_REQUIRED,
        "actor_id is required when actor_type is HUMAN",
        "actor_id"
      ));
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Rule 5: actor_id MUST be NULL if actor_type != HUMAN
  // ─────────────────────────────────────────────────────────────────────────
  if (actorTypeUpper === "SYSTEM" || actorTypeUpper === "SERVICE") {
    if (ctx.actor_id != null && ctx.actor_id.trim() !== "") {
      errors.push(new AttributionError(
        AttributionErrorCode.ATTR_ACTOR_ID_FORBIDDEN,
        `actor_id must be null when actor_type is ${actorTypeUpper}`,
        "actor_id"
      ));
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Enforcement Decision
  // ─────────────────────────────────────────────────────────────────────────
  if (errors.length > 0) {
    logViolations(ctx, errors, enforcementMode);

    if (enforcementMode === "shadow") {
      // Log only, do not reject
      return errors;
    }

    if (enforcementMode === "soft" && allowLegacyOverride) {
      // Log override usage for audit
      console.warn("[aos-sdk] attribution_override_used", {
        agent_id: ctx.agent_id,
        origin_system_id: ctx.origin_system_id,
        errors: errors.map(e => e.code),
      });
      return errors;
    }

    // Hard fail (or soft fail without override)
    throw errors[0];
  }

  return [];
}

function logViolations(
  ctx: AttributionContext,
  errors: AttributionError[],
  mode: EnforcementMode
): void {
  console.warn("[aos-sdk] attribution_validation_failed", {
    enforcement_mode: mode,
    agent_id: ctx.agent_id,
    actor_type: ctx.actor_type,
    origin_system_id: ctx.origin_system_id,
    has_actor_id: ctx.actor_id != null,
    error_codes: errors.map(e => e.code),
    error_count: errors.length,
  });
}
```

---

## 5. Integration Point (Run Creation)

### Python SDK Integration

```python
# Python: aos_sdk/client.py

from typing import Optional
from datetime import datetime, timezone
import os

from .attribution import AttributionContext
from .validation import validate_attribution
from .types import ActorType


class AOSClient:
    """AOS SDK Client with attribution enforcement."""

    def __init__(
        self,
        api_key: str,
        *,
        enforcement_mode: Optional[str] = None,
    ):
        self.api_key = api_key

        # Determine enforcement mode from environment or parameter
        self._enforcement_mode = enforcement_mode or os.getenv(
            "AOS_ATTRIBUTION_ENFORCEMENT",
            "hard"  # Default to hard enforcement
        )

        self._allow_legacy_override = os.getenv(
            "AOS_ALLOW_ATTRIBUTION_LEGACY",
            "false"
        ).lower() == "true"

    def create_run(
        self,
        goal: str,
        *,
        agent_id: str,
        actor_type: str,
        origin_system_id: str,
        actor_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Create a new run with required attribution.

        Args:
            goal: The run's objective
            agent_id: REQUIRED - Executing agent identifier
            actor_type: REQUIRED - HUMAN | SYSTEM | SERVICE
            origin_system_id: REQUIRED - System that initiated this run
            actor_id: REQUIRED if actor_type == HUMAN
            **kwargs: Additional run parameters

        Returns:
            Created run object

        Raises:
            AttributionError: If attribution validation fails
        """
        # Build attribution context
        ctx = AttributionContext(
            agent_id=agent_id,
            actor_type=actor_type,
            origin_system_id=origin_system_id,
            actor_id=actor_id,
            origin_ts=datetime.now(timezone.utc),
        )

        # Validate BEFORE any network call
        validate_attribution(
            ctx,
            enforcement_mode=self._enforcement_mode,
            allow_legacy_override=self._allow_legacy_override,
        )

        # Build request payload
        payload = {
            "goal": goal,
            "agent_id": agent_id,
            "actor_type": actor_type.upper(),
            "origin_system_id": origin_system_id,
            "actor_id": actor_id,
            **kwargs,
        }

        # Make API call
        return self._post("/api/v1/runs", payload)

    # Convenience methods for common actor types

    def create_system_run(
        self,
        goal: str,
        *,
        agent_id: str,
        origin_system_id: str,
        **kwargs,
    ) -> dict:
        """Create a SYSTEM-initiated run (automation, cron, scheduler)."""
        return self.create_run(
            goal=goal,
            agent_id=agent_id,
            actor_type="SYSTEM",
            origin_system_id=origin_system_id,
            actor_id=None,  # Explicitly null for SYSTEM
            **kwargs,
        )

    def create_human_run(
        self,
        goal: str,
        *,
        agent_id: str,
        actor_id: str,  # REQUIRED for human runs
        origin_system_id: str,
        **kwargs,
    ) -> dict:
        """Create a HUMAN-initiated run (requires actor_id)."""
        return self.create_run(
            goal=goal,
            agent_id=agent_id,
            actor_type="HUMAN",
            origin_system_id=origin_system_id,
            actor_id=actor_id,
            **kwargs,
        )

    def create_service_run(
        self,
        goal: str,
        *,
        agent_id: str,
        origin_system_id: str,
        **kwargs,
    ) -> dict:
        """Create a SERVICE-initiated run (service-to-service)."""
        return self.create_run(
            goal=goal,
            agent_id=agent_id,
            actor_type="SERVICE",
            origin_system_id=origin_system_id,
            actor_id=None,  # Explicitly null for SERVICE
            **kwargs,
        )

    def _post(self, path: str, payload: dict) -> dict:
        """Make authenticated POST request."""
        # Implementation details...
        pass
```

---

## 6. Usage Examples

### Python

```python
from aos_sdk import AOSClient

client = AOSClient(api_key="...")

# SYSTEM run (automation)
run = client.create_system_run(
    goal="Process daily reports",
    agent_id="agent-report-processor",
    origin_system_id="cron-scheduler-001",
)

# HUMAN run (user action)
run = client.create_human_run(
    goal="Analyze customer data",
    agent_id="agent-data-analyst",
    actor_id="user_12345",
    origin_system_id="customer-console",
)

# SERVICE run (internal API)
run = client.create_service_run(
    goal="Validate payment",
    agent_id="agent-payment-validator",
    origin_system_id="payment-service-v2",
)
```

### JavaScript

```typescript
import { AOSClient } from "aos-sdk";

const client = new AOSClient({ apiKey: "..." });

// SYSTEM run
const run = await client.createSystemRun({
  goal: "Process daily reports",
  agentId: "agent-report-processor",
  originSystemId: "cron-scheduler-001",
});

// HUMAN run
const run = await client.createHumanRun({
  goal: "Analyze customer data",
  agentId: "agent-data-analyst",
  actorId: "user_12345",
  originSystemId: "customer-console",
});
```

---

## 7. Environment Variables

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `AOS_ATTRIBUTION_ENFORCEMENT` | `shadow`, `soft`, `hard` | `hard` | Enforcement mode |
| `AOS_ALLOW_ATTRIBUTION_LEGACY` | `true`, `false` | `false` | Override in soft mode |

---

## 8. Backend Safeguards (Defense-in-Depth)

Even if SDK validation is bypassed, the database enforces attribution at the constraint level.

### Database CHECK Constraints

| Constraint | Rule | Migration |
|------------|------|-----------|
| `chk_runs_actor_type_valid` | actor_type IN ('HUMAN', 'SYSTEM', 'SERVICE') | 105 |
| `chk_runs_actor_id_human_required` | actor_id NOT NULL when actor_type = HUMAN | 105 |
| `chk_runs_actor_id_nonhuman_null` | actor_id IS NULL when actor_type != HUMAN | 105 |

### Database Triggers (Legacy Sentinel Rejection)

| Trigger | Rejects | Migration |
|---------|---------|-----------|
| `trg_runs_agent_id_not_legacy` | `agent_id = 'legacy-unknown'` | 105 |
| `trg_runs_origin_system_not_legacy` | `origin_system_id = 'legacy-migration'` | 105 |

### Verification Status

All 11 constraint tests passed (2026-01-18):
- 3 valid attribution patterns accepted
- 8 invalid patterns correctly rejected

See `docs/architecture/ATTRIBUTION_ARCHITECTURE.md` for full test matrix.

---

## 9. Testing Checklist

Before releasing SDK with enforcement:

- [x] All error codes produce correct messages
- [x] Shadow mode logs but doesn't reject
- [x] Soft mode respects override flag
- [x] Hard mode always rejects invalid attribution
- [x] Legacy sentinel values are rejected
- [x] HUMAN requires actor_id
- [x] SYSTEM/SERVICE reject actor_id
- [x] Invalid actor_type produces correct error
- [x] Validation happens before network call
- [x] Database constraints verified (11/11 tests)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | Contract specification |
| `RUN_VALIDATION_RULES.md` | R1-R8 invariants |
| `ATTRIBUTION_FAILURE_MODE_MATRIX.md` | Blast radius |
| `SDK_ATTRIBUTION_ALERTS.md` | Monitoring thresholds |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Added backend safeguards section, marked testing checklist complete | Governance |
| 2026-01-18 | Initial creation | Governance |
