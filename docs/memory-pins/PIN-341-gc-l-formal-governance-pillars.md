# PIN-341: GC_L Formal Governance Pillars (DSL, Signals, Audit)

**Status:** AUTHORITATIVE
**Date:** 2026-01-07
**Category:** Governance / Formal Specification
**Reference:** PIN-340 (Implementation Specification), PIN-339 (Capability Reclassification)
**Authority:** Human-specified, formally bounded

---

## Executive Summary

This PIN defines the **three missing governance pillars** for GC_L:

1. **Policy DSL** — Formal grammar, non-Turing-complete by design
2. **FACILITATION Signal Catalog** — Canonical observations, not conclusions
3. **GC_L Audit & Replay Format** — Immutable, defensible history

**Core Principle:** These specs are meant to be **compiled, validated, replayed, and audited** — not interpreted loosely.

---

## 1. Policy DSL — Formal Grammar

### 1.1 Design Constraints (Hard)

| Constraint | Enforcement |
|------------|-------------|
| No loops | Reject at parse time |
| No functions | Reject at parse time |
| No recursion | Reject at parse time |
| No side effects | Reject at parse time |
| No execution primitives | Reject at parse time |
| No external calls | Reject at parse time |

**Rationale:** The DSL is **declarative, deterministic, and non-Turing-complete** by design. This ensures policies can be statically analyzed, validated, and never produce unbounded behavior.

---

### 1.2 Policy DSL Grammar (EBNF)

```ebnf
Policy          ::= Metadata Clause+

Metadata        ::= "policy" Identifier
                    "version" Integer
                    "scope" Scope
                    "mode" Mode

Scope           ::= "ORG" | "PROJECT"

Mode            ::= "MONITOR" | "ENFORCE"

Clause          ::= WhenClause ThenClause

WhenClause      ::= "when" Condition

Condition       ::= Predicate
                  | Condition LogicalOp Condition

LogicalOp       ::= "AND" | "OR"

Predicate       ::= Metric Comparator Value
                  | "exists" "(" Metric ")"

Comparator      ::= ">" | ">=" | "<" | "<=" | "==" | "!="

Value           ::= Number | String | Boolean | Duration

ThenClause      ::= "then" Action+

Action          ::= WarnAction
                  | BlockAction
                  | RequireApprovalAction

WarnAction      ::= "warn" String

BlockAction     ::= "block"

RequireApprovalAction ::= "require_approval"
```

---

### 1.3 Token Definitions

```ebnf
Identifier      ::= [a-zA-Z_][a-zA-Z0-9_]*
Integer         ::= [0-9]+
Number          ::= [0-9]+ ("." [0-9]+)?
String          ::= '"' [^"]* '"'
Boolean         ::= "true" | "false"
Duration        ::= Number ("s" | "m" | "h" | "d")
Metric          ::= Identifier ("." Identifier)*
```

---

### 1.4 Semantic Rules (Non-Negotiable)

| Rule | Enforcement | Rationale |
|------|-------------|-----------|
| Multiple `then` actions allowed | YES | Policies may warn AND require approval |
| `block` requires `ENFORCE` mode | YES | MONITOR mode is observation-only |
| `ENFORCE` requires human activation | YES | No auto-enforcement |
| `MONITOR` never blocks | YES | Observation cannot prevent execution |
| Policy evaluation is pure | YES | No side effects during evaluation |
| Policy cannot mutate state | YES | Policies describe, not execute |

---

### 1.5 Mode Semantics

| Mode | Can Warn | Can Block | Can Require Approval | Activation |
|------|----------|-----------|----------------------|------------|
| MONITOR | ✅ | ❌ | ❌ | Automatic after simulation |
| ENFORCE | ✅ | ✅ | ✅ | Human activation required |

---

### 1.6 Canonical Examples

#### Example 1: Cost Spike Guard (MONITOR)

```
policy CostSpikeGuard
version 1
scope PROJECT
mode MONITOR

when cost_per_hour > 200 AND error_rate > 0.1
then warn "Cost spike with elevated error rate"
```

#### Example 2: Budget Enforcement (ENFORCE)

```
policy BudgetEnforcement
version 1
scope ORG
mode ENFORCE

when monthly_spend >= budget_limit
then block
     warn "Monthly budget exhausted"
```

#### Example 3: Safety Threshold (ENFORCE)

```
policy SafetyThreshold
version 2
scope PROJECT
mode ENFORCE

when safety_score < 0.5 OR exists(anomaly_flag)
then require_approval
     warn "Safety threshold breach requires review"
```

---

### 1.7 Static Validation Errors

| Invalid Construct | Error Code | Reason |
|-------------------|------------|--------|
| `then execute` | DSL-E001 | Execution primitive forbidden |
| `while condition` | DSL-E002 | Control flow forbidden |
| `call webhook(url)` | DSL-E003 | Side effect forbidden |
| `function foo()` | DSL-E004 | Function definition forbidden |
| Missing `version` | DSL-E005 | Lineage tracking required |
| Missing `mode` | DSL-E006 | Execution semantics required |
| `block` in MONITOR mode | DSL-E007 | MONITOR cannot block |
| Recursive reference | DSL-E008 | Recursion forbidden |

---

### 1.8 AST Node Types

```python
@dataclass
class PolicyAST:
    name: str
    version: int
    scope: Literal["ORG", "PROJECT"]
    mode: Literal["MONITOR", "ENFORCE"]
    clauses: list[Clause]

@dataclass
class Clause:
    when: Condition
    then: list[Action]

@dataclass
class Condition:
    left: Predicate | Condition
    op: Literal["AND", "OR"] | None
    right: Condition | None

@dataclass
class Predicate:
    metric: str
    comparator: str
    value: Any

@dataclass
class ExistsPredicate:
    metric: str

@dataclass
class WarnAction:
    message: str

@dataclass
class BlockAction:
    pass

@dataclass
class RequireApprovalAction:
    pass
```

---

## 2. FACILITATION Signal Catalog (Canonical v1)

### 2.1 Core Principle

**Signals are observations, not conclusions.**

No signal may contain:
- "decision"
- "verdict"
- "action taken"

Signals are **inputs** to facilitation, nothing more.

---

### 2.2 Signal Taxonomy

#### A. Execution Signals

| Signal ID | Description | Severity Range | Typical Window |
|-----------|-------------|----------------|----------------|
| EXEC_ERROR_RATE_SPIKE | Error rate exceeds baseline by threshold | MEDIUM-HIGH | 5m-15m |
| EXEC_TIMEOUT_SURGE | Timeout frequency increased significantly | MEDIUM-HIGH | 5m-30m |
| EXEC_RETRY_STORM | Retry count exceeds normal patterns | HIGH | 1m-5m |
| EXEC_FAILURE_CLUSTER | Correlated failures across executions | HIGH | 5m-15m |
| EXEC_LATENCY_DEGRADATION | P99 latency exceeds SLA threshold | MEDIUM | 5m-15m |
| EXEC_THROUGHPUT_DROP | Execution rate below expected | LOW-MEDIUM | 15m-1h |

#### B. Cost & Utilization Signals

| Signal ID | Description | Severity Range | Typical Window |
|-----------|-------------|----------------|----------------|
| COST_RATE_SPIKE | Spend velocity exceeds baseline | MEDIUM-HIGH | 5m-1h |
| COST_BUDGET_RISK | Approaching budget limit (>80%) | MEDIUM | 1h-24h |
| COST_BUDGET_BREACH | Budget limit exceeded | HIGH | Instant |
| UTIL_IDLE_WASTE | Resources allocated but unused | LOW | 1h-24h |
| UTIL_OVERCOMMIT | Resource saturation detected | HIGH | 5m-15m |
| UTIL_QUOTA_PRESSURE | Approaching rate limits | MEDIUM | 5m-15m |

#### C. Policy Signals

| Signal ID | Description | Severity Range | Typical Window |
|-----------|-------------|----------------|----------------|
| POLICY_FREQUENT_WARN | Policy warning frequency elevated | LOW-MEDIUM | 1h-24h |
| POLICY_BLOCK_RATE | High percentage of blocked executions | MEDIUM-HIGH | 1h |
| POLICY_CONFLICT | Conflicting policies detected | MEDIUM | Instant |
| POLICY_DORMANT | Policy never triggered (staleness) | LOW | 7d-30d |
| POLICY_CASCADE | Multiple policies triggered together | MEDIUM | 5m |

#### D. Integration Signals

| Signal ID | Description | Severity Range | Typical Window |
|-----------|-------------|----------------|----------------|
| INTEG_FAILURE_LOOP | Repeated integration failures | HIGH | 5m-15m |
| INTEG_LATENCY_DRIFT | External service latency degradation | MEDIUM | 15m-1h |
| INTEG_AUTH_ERROR | Credential or auth failures | HIGH | Instant |
| INTEG_TIMEOUT_PATTERN | External timeouts increasing | MEDIUM | 15m |
| INTEG_RATE_LIMIT_HIT | External rate limit encountered | MEDIUM | 5m |

#### E. Safety Signals

| Signal ID | Description | Severity Range | Typical Window |
|-----------|-------------|----------------|----------------|
| SAFETY_ANOMALOUS_BEHAVIOR | Execution pattern deviates from norm | HIGH | 5m-15m |
| SAFETY_THRESHOLD_BREACH | Safety limit exceeded | HIGH | Instant |
| SAFETY_KILLSWITCH_RECOMMENDED | Aggregate risk exceeds tolerance | CRITICAL | 5m |
| SAFETY_DRIFT_DETECTED | Behavior drift from baseline | MEDIUM | 1h-24h |

---

### 2.3 Signal Contract Schema

```json
{
  "signal_id": "string (from catalog)",
  "signal_category": "EXEC | COST | POLICY | INTEG | SAFETY",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": 0.0 - 1.0,
  "timestamp": "RFC3339",
  "window": "duration (e.g., 5m, 1h)",
  "tenant_id": "uuid",
  "project_id": "uuid | null",
  "evidence_refs": ["uuid array - exec_id, metric_id, etc."],
  "explanation": "string - human-readable description",
  "baseline": {
    "value": "number | null",
    "window": "duration"
  },
  "current": {
    "value": "number",
    "threshold": "number"
  }
}
```

---

### 2.4 Signal Immutability Rules

| Rule | Enforcement |
|------|-------------|
| Signals are append-only | No UPDATE on signal records |
| Signals cannot be deleted | Soft-delete only with retention |
| Signals reference evidence | Must include `evidence_refs` |
| Signals have monotonic IDs | UUID v7 or timestamp-ordered |

---

### 2.5 Signal → Facilitation Mapping

Signals feed into FACILITATION rules. The mapping is explicit:

```yaml
facilitation_rule:
  id: FAC-COST-001
  trigger_signals:
    - COST_RATE_SPIKE
    - COST_BUDGET_RISK
  condition:
    any_signal_severity: ">= MEDIUM"
  recommendation:
    message: "Cost pressure detected"
    suggested_action: "REVIEW_SPEND_GUARDS"
    confidence_boost: 0.1
```

---

## 3. GC_L Audit & Replay Format

### 3.1 Core Principle

Every GC_L interaction emits **exactly one immutable audit record**.

This is what makes the system **defensible**.

---

### 3.2 GC_L Audit Event Schema

```json
{
  "event_id": "uuid",
  "timestamp": "RFC3339",
  "tenant_id": "uuid",
  "project_id": "uuid | null",
  "actor_id": "uuid",
  "actor_type": "HUMAN | SYSTEM_FACILITATION",
  "capability_id": "CAP-XXX",
  "intent": "CONFIGURE | ACTIVATE | PAUSE | DISABLE | SIMULATE",
  "object_type": "POLICY | INTEGRATION | SPEND_GUARD | KILLSWITCH | PREFERENCE",
  "object_id": "uuid",
  "object_version": "integer",
  "previous_state_hash": "sha256 | null (for creates)",
  "new_state_hash": "sha256",
  "confirmation": true,
  "reason": "string",
  "evidence_refs": {
    "simulation_ids": ["uuid array"],
    "signal_ids": ["uuid array"],
    "policy_ids": ["uuid array"]
  },
  "metadata": {
    "client_ip": "string | null",
    "user_agent": "string | null",
    "session_id": "uuid | null"
  }
}
```

---

### 3.3 Immutability Rules (ABSOLUTE)

| Rule | Implementation |
|------|----------------|
| Append-only | INSERT only, no UPDATE |
| No UPDATE | Constraint or trigger enforced |
| No DELETE | Constraint or trigger enforced |
| ON CONFLICT DO NOTHING | First write wins |
| Hash chain optional but recommended | Link via `previous_state_hash` |

#### Database Enforcement

```sql
CREATE TABLE gcl_audit_log (
  event_id            UUID PRIMARY KEY,
  timestamp           TIMESTAMP NOT NULL DEFAULT NOW(),
  tenant_id           UUID NOT NULL,
  project_id          UUID,
  actor_id            UUID NOT NULL,
  actor_type          TEXT NOT NULL,
  capability_id       TEXT NOT NULL,
  intent              TEXT NOT NULL,
  object_type         TEXT NOT NULL,
  object_id           UUID NOT NULL,
  object_version      INTEGER NOT NULL,
  previous_state_hash TEXT,
  new_state_hash      TEXT NOT NULL,
  confirmation        BOOLEAN NOT NULL DEFAULT true,
  reason              TEXT,
  evidence_refs       JSONB NOT NULL DEFAULT '{}',
  metadata            JSONB NOT NULL DEFAULT '{}'
);

-- Immutability enforcement
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'GCL audit log is immutable - no UPDATE or DELETE allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER gcl_audit_immutable_update
  BEFORE UPDATE ON gcl_audit_log
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

CREATE TRIGGER gcl_audit_immutable_delete
  BEFORE DELETE ON gcl_audit_log
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

-- Indexes for replay queries
CREATE INDEX idx_gcl_audit_tenant_time ON gcl_audit_log(tenant_id, timestamp);
CREATE INDEX idx_gcl_audit_actor ON gcl_audit_log(actor_id, timestamp);
CREATE INDEX idx_gcl_audit_object ON gcl_audit_log(object_type, object_id, timestamp);
CREATE INDEX idx_gcl_audit_capability ON gcl_audit_log(capability_id, timestamp);
```

---

### 3.4 Replay Envelope (READ-ONLY)

Replay **never re-executes**. It reconstructs **intent and context**.

```json
{
  "replay_id": "uuid",
  "requested_by": "uuid",
  "requested_at": "RFC3339",
  "time_range": {
    "start": "RFC3339",
    "end": "RFC3339"
  },
  "filters": {
    "tenant_id": "uuid",
    "project_id": "uuid | null",
    "capability_id": "CAP-XXX | null",
    "actor_id": "uuid | null",
    "object_type": "string | null",
    "object_id": "uuid | null",
    "intent": "string | null"
  },
  "events": [
    { "...audit event..." }
  ],
  "derived_view": {
    "timeline": true,
    "diffs": true,
    "policy_versions": true,
    "signal_context": true
  },
  "summary": {
    "total_events": 47,
    "actors_involved": 3,
    "objects_modified": 12,
    "intents": {
      "CONFIGURE": 23,
      "ACTIVATE": 8,
      "PAUSE": 4,
      "DISABLE": 2,
      "SIMULATE": 10
    }
  }
}
```

---

### 3.5 Replay Query API

```
POST /api/customer/audit/replay
```

**Request:**
```json
{
  "time_range": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-07T23:59:59Z"
  },
  "filters": {
    "capability_id": "CAP-009",
    "intent": "ACTIVATE"
  },
  "derived_view": {
    "timeline": true,
    "diffs": true
  }
}
```

**Response:** Replay envelope as defined above.

---

### 3.6 What Replay Must Answer

| Question | Data Source |
|----------|-------------|
| Who acted? | `actor_id`, `actor_type` |
| What did they see? | `evidence_refs.signal_ids` |
| What signals existed? | Signal catalog join |
| What simulations were reviewed? | `evidence_refs.simulation_ids` |
| What changed? | `previous_state_hash` → `new_state_hash` |
| What did NOT change? | Absence of events for object |
| What was the stated reason? | `reason` field |
| Was confirmation given? | `confirmation` field |

---

### 3.7 What Replay Must NEVER Answer

| Forbidden Question | Reason |
|--------------------|--------|
| What should have happened? | Normative, not descriptive |
| What would the system do now? | Present state, not history |
| Was this the right decision? | Judgment, not fact |
| What would happen if...? | Counterfactual reasoning |

---

### 3.8 Hash Chain Verification (Optional)

For high-assurance environments, implement hash chain:

```python
def compute_event_hash(event: AuditEvent) -> str:
    canonical = json.dumps({
        "event_id": str(event.event_id),
        "timestamp": event.timestamp.isoformat(),
        "actor_id": str(event.actor_id),
        "intent": event.intent,
        "object_id": str(event.object_id),
        "new_state_hash": event.new_state_hash,
        "previous_state_hash": event.previous_state_hash
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()

def verify_chain(events: list[AuditEvent]) -> bool:
    for i, event in enumerate(events[1:], 1):
        expected_prev = compute_event_hash(events[i-1])
        if event.previous_state_hash != expected_prev:
            return False
    return True
```

---

## 4. Trust Boundary Summary (Frozen)

| Layer | Can Observe | Can Recommend | Can Decide | Can Act |
|-------|-------------|---------------|------------|---------|
| Signals | ✅ | ❌ | ❌ | ❌ |
| FACILITATION | ✅ | ✅ | ❌ | ❌ |
| Policy Library | ✅ | ✅ | ❌ | ❌ |
| GC_L APIs | ✅ | ✅ | ❌ | ❌ |
| **Human** | ✅ | ✅ | ✅ | ✅ |

**This table MUST NEVER change.**

---

## 5. Implementation Artifacts

### Files to Create

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/dsl/policy_grammar.py` | L4 | DSL parser and validator |
| `backend/app/dsl/policy_ast.py` | L4 | AST node definitions |
| `backend/app/dsl/policy_evaluator.py` | L4 | Pure evaluation function |
| `backend/app/signals/catalog.py` | L4 | Signal type definitions |
| `backend/app/signals/emitter.py` | L4 | Signal emission service |
| `backend/app/audit/gcl_audit.py` | L6 | Audit log service |
| `backend/app/audit/replay.py` | L4 | Replay query engine |
| `backend/alembic/versions/XXX_gcl_audit_log.py` | L6 | Migration |
| `backend/tests/dsl/test_policy_grammar.py` | L8 | Grammar tests |
| `backend/tests/dsl/test_policy_validation.py` | L8 | Semantic rule tests |
| `backend/tests/audit/test_immutability.py` | L8 | Immutability enforcement |

---

## 6. Validation Checklist

### Policy DSL

- [ ] Parser rejects loops
- [ ] Parser rejects functions
- [ ] Parser rejects external calls
- [ ] `block` rejected in MONITOR mode
- [ ] Version required
- [ ] Scope required
- [ ] Mode required
- [ ] Evaluation is pure (no side effects)

### Signal Catalog

- [ ] All signals have unique IDs
- [ ] All signals have severity range
- [ ] All signals have evidence refs
- [ ] No signal contains "decision" or "action taken"
- [ ] Signals are append-only

### Audit & Replay

- [ ] UPDATE trigger raises exception
- [ ] DELETE trigger raises exception
- [ ] Hash chain verification passes
- [ ] Replay never modifies state
- [ ] All required fields present
- [ ] `confirmation` always true for writes

---

## References

- PIN-340: GC_L Implementation Specification
- PIN-339: Customer Console Capability Reclassification
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md
- AUTHORITY_DECLARATIONS_V1.yaml

---

## Next Steps (User Choice)

1. **Policy DSL interpreter** — Pure function implementation
2. **Signal → Facilitation rule compiler** — Mapping engine
3. **GC_L event hash-chain verification** — Cryptographic audit
4. **UI copy contract** — "recommend" vs "require" language

---

**Status:** AUTHORITATIVE
**Governance State:** Policy logic formally bounded, intelligence observable, control human-attributed, history replayable and defensible.
