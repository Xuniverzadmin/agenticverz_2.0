# PIN-342: GC_L UI Contract, Interpreter, and Hash-Chain Verification

**Status:** NORMATIVE
**Date:** 2026-01-07
**Category:** Governance / Formal Specification
**Reference:** PIN-341 (Formal Pillars), PIN-340 (Implementation), PIN-339 (Reclassification)
**Authority:** Human-approved governance

---

## Executive Summary

This PIN defines three enforcement-grade specifications:

1. **UI Irreversible-Action Contract** — Governance at the UI layer
2. **Policy DSL Interpreter** — Pure, deterministic evaluation
3. **Signal → Facilitation Compiler** — Observations to recommendations
4. **GC_L Hash-Chain Verification** — Tamper-evident audit

**Core Principle:** These specs are mechanically enforceable, not guidelines.

---

# PART 1: UI Irreversible-Action Contract

**Status:** NORMATIVE
**Applies to:** Customer Console (GC_L + FACILITATION)
**Scope:** Any customer-initiated action that is irreversible or has irreversible downstream effects

---

## 1.1 Definitions

### Irreversible Action

An action is **irreversible** if **any** of the following is true:

| Condition | Example |
|-----------|---------|
| Cannot be fully undone | Policy activation that blocks runs |
| Produces downstream effects that cannot be rewound | Pausing executions |
| Changes enforcement posture | MONITOR → ENFORCE |
| Alters cost/availability materially | Spend caps |
| Changes governance state | Killswitch engagement |

### Human Sovereignty

Only a **human actor** may authorize irreversible impact. Systems may **prepare**, **simulate**, and **recommend** — they may not decide or execute.

---

## 1.2 Contract Obligations (MUST)

### 1.2.1 Explicit Intent Declaration

The UI **MUST** present the exact action name and scope prior to authorization.

- No euphemisms
- No icon-only confirmation

### 1.2.2 Explicit Consequence Disclosure

The UI **MUST** list concrete consequences in plain language:

- What will stop
- What will continue
- Scope of impact

### 1.2.3 Simulation / Preview (When Available)

If simulation exists for the action, the UI **MUST** display:

- Affected entities count
- Historical "would have happened" summary

If unavailable, the UI **MUST** state: "Simulation unavailable"

### 1.2.4 Human Attribution Capture

The UI **MUST** capture:

- Actor identity (implicit via auth)
- Explicit confirmation
- Reason/justification text (required for ENFORCE, KILLSWITCH)

### 1.2.5 Deliberate Confirmation

Irreversible actions **MUST** require ≥2 deliberate steps:

| Mode | Description |
|------|-------------|
| TYPED | User types confirmation phrase |
| MODAL | Two-step modal dialog |
| DELAYED | Countdown timer before confirm enabled |

### 1.2.6 Post-Action State Visibility

After execution, the UI **MUST** immediately display:

- New state
- Scope
- Reversibility (or lack thereof)

---

## 1.3 Prohibitions (MUST NOT)

| Prohibition | Reason |
|-------------|--------|
| Bundle multiple irreversible actions | Prevents hidden consequences |
| Auto-focus or default to "Confirm" | Prevents accidental confirmation |
| Auto-trigger based on FACILITATION | Preserves human sovereignty |
| Use language implying system decided | Maintains attribution clarity |
| Hide irreversible actions behind simple toggles | Prevents accidental activation |

---

## 1.4 Machine-Enforceable Metadata

Every irreversible UI action **MUST** declare metadata used by frontend and backend enforcement.

```json
{
  "action_id": "ACTIVATE_POLICY",
  "irreversible": true,
  "requires_simulation": true,
  "requires_reason": true,
  "min_confirmation_steps": 2,
  "confirmation_mode": ["TYPED", "MODAL", "DELAYED"],
  "allowed_copy": [
    "Activate policy",
    "This will block executions matching the rule"
  ]
}
```

**Backend MUST reject requests that do not satisfy declared metadata.**

---

## 1.5 GC_L Endpoint Mapping

### Policies

| Endpoint | Irreversible | Contract Requirements |
|----------|--------------|----------------------|
| `POST /api/cus/policies` (create draft) | NO | Basic confirmation |
| `POST /api/cus/policies/{id}/simulate` | NO | None |
| `POST /api/cus/policies/{id}/activate` | **YES** | Intent, consequences, simulation REQUIRED, reason REQUIRED, ≥2 steps |
| `POST /api/cus/policies/{id}/mode` (MONITOR→ENFORCE) | **YES** | Consequence disclosure, simulation, typed confirm, reason REQUIRED |

### Killswitch

| Endpoint | Irreversible | Contract Requirements |
|----------|--------------|----------------------|
| `POST /api/cus/killswitch` (engage) | **YES** | Intent "Pause executions", scope disclosure, reason REQUIRED, delayed confirm |
| `POST /api/cus/killswitch/resume` | NO | Single confirm + reason |

### Spend Guardrails

| Endpoint | Irreversible | Contract Requirements |
|----------|--------------|----------------------|
| `POST /api/cus/spend/guardrails` | **YES** | Consequence disclosure, simulation if available, reason REQUIRED, ≥2 steps |

### Integrations

| Endpoint | Irreversible | Contract Requirements |
|----------|--------------|----------------------|
| `POST /api/cus/integrations/{id}/disable` | **YES** | Consequence disclosure (ingest stops), reason REQUIRED, two-step confirm |

---

## 1.6 Frontend Validation Rules (Mechanical)

### Action Gating

UI **MUST** block submission unless:

```typescript
confirmation === true &&
confirmation_steps_completed >= min_confirmation_steps &&
(requires_reason ? reason.length > 0 : true)
```

### Copy Guard

- UI **MUST** only render copy strings listed in `allowed_copy`
- Any other copy → **build-time lint failure**

### Simulation Gate

If `requires_simulation === true`:

- UI **MUST** fetch and display simulation result ID
- Submit payload **MUST** include `evidence_refs: [simulation_id]`

### Required Payload Shape

```json
{
  "actor_id": "uuid",
  "intent": "ACTIVATE | PAUSE | DISABLE | CONFIGURE",
  "confirmation": true,
  "confirmation_steps_completed": 2,
  "reason": "string",
  "evidence_refs": ["simulation_id"]
}
```

### FACILITATION Guard

- FACILITATION outputs **MAY** prefill forms
- FACILITATION outputs **MUST NOT**:
  - Trigger submits
  - Auto-set confirmation
  - Reduce confirmation steps

---

## 1.7 Backend Rejection Rules

Backend **MUST** reject GC_L requests when:

| Condition | Rejection |
|-----------|-----------|
| Action metadata marks irreversible and UI did not meet contract | 409 |
| `confirmation` is false | 409 |
| `reason` missing where required | 409 |
| Simulation required but not referenced | 409 |
| Actor is not human | 409 |

**Rejection code:** `409 GOVERNANCE_VIOLATION`

---

# PART 2: Policy DSL Interpreter (Pure Function)

## 2.1 Design Guarantees

| Guarantee | Enforcement |
|-----------|-------------|
| **Pure** | No I/O, no state, no time access |
| **Deterministic** | Same inputs → same output |
| **Side-effect free** | No mutations |
| **Total** | Every valid policy + input returns a result |

If any of these are violated → **reject at build time**.

---

## 2.2 Interpreter Type Definitions

### Input Types

```typescript
interface Policy {
  policy_id: string;
  version: number;
  scope: "ORG" | "PROJECT";
  mode: "MONITOR" | "ENFORCE";
  ast: PolicyAST;
}

interface EvaluationContext {
  metrics: Record<string, number | string | boolean>;
  exists: (metric: string) => boolean;
}

interface PolicyAST {
  when: Condition;
  then: Action[];
}

type Condition =
  | { type: "predicate"; metric: string; comparator: string; value: any }
  | { type: "exists"; metric: string }
  | { type: "compound"; left: Condition; op: "AND" | "OR"; right: Condition };

type Action =
  | { type: "WARN"; message: string }
  | { type: "BLOCK" }
  | { type: "REQUIRE_APPROVAL" };
```

### Output Type

```typescript
interface PolicyEvaluationResult {
  policy_id: string;
  version: number;
  matched: boolean;
  actions: Array<{
    type: "WARN" | "BLOCK" | "REQUIRE_APPROVAL";
    message?: string;
  }>;
}
```

---

## 2.3 Evaluation Algorithm (Reference Implementation)

```typescript
function evaluatePolicy(
  policy: Policy,
  ctx: EvaluationContext
): PolicyEvaluationResult {
  const matched = evaluateCondition(policy.ast.when, ctx);

  if (!matched) {
    return {
      policy_id: policy.policy_id,
      version: policy.version,
      matched: false,
      actions: []
    };
  }

  const actions = policy.ast.then
    .map(action => {
      // BLOCK suppressed in MONITOR mode
      if (action.type === "BLOCK" && policy.mode !== "ENFORCE") {
        return null;
      }
      return action;
    })
    .filter((a): a is Action => a !== null);

  return {
    policy_id: policy.policy_id,
    version: policy.version,
    matched: true,
    actions
  };
}

function evaluateCondition(cond: Condition, ctx: EvaluationContext): boolean {
  switch (cond.type) {
    case "predicate":
      return evaluatePredicate(cond, ctx);
    case "exists":
      return ctx.exists(cond.metric);
    case "compound":
      const left = evaluateCondition(cond.left, ctx);
      const right = evaluateCondition(cond.right, ctx);
      return cond.op === "AND" ? left && right : left || right;
  }
}

function evaluatePredicate(
  pred: { metric: string; comparator: string; value: any },
  ctx: EvaluationContext
): boolean {
  const actual = ctx.metrics[pred.metric];
  if (actual === undefined) return false;

  switch (pred.comparator) {
    case ">": return actual > pred.value;
    case ">=": return actual >= pred.value;
    case "<": return actual < pred.value;
    case "<=": return actual <= pred.value;
    case "==": return actual === pred.value;
    case "!=": return actual !== pred.value;
    default: return false;
  }
}
```

---

## 2.4 Interpreter Constraints

**The interpreter never knows:**

- Who the user is
- Whether blocking is allowed
- What happens next

That is enforced elsewhere.

**Rejection Rules (Hard):**

| Condition | Action |
|-----------|--------|
| Action = `BLOCK` but mode ≠ `ENFORCE` | Reject at parse/compile |
| Unknown metric referenced | Reject at compile |
| Type mismatch (`string > number`) | Reject at compile |
| AST contains loops / calls / functions | Reject at parse |

---

# PART 3: Signal → Facilitation Rule Compiler

## 3.1 Design Principle

This turns **observations** into **recommendations**, never actions.

---

## 3.2 Compiler Type Definitions

### Input: Signal (Runtime)

```typescript
interface Signal {
  signal_id: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number; // 0.0 - 1.0
  window: string;
  evidence_refs: string[];
  explanation: string;
}
```

### Input: Facilitation Rule (Author-Defined)

```typescript
interface FacilitationRule {
  rule_id: string;
  signal: string;
  min_severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  min_confidence: number;
  recommendation: {
    action: string;
    message: string;
  };
}
```

### Output: Facilitation Recommendation

```typescript
interface FacilitationRecommendation {
  rule_id: string;
  triggered_by: string;
  recommendation: {
    action: string;
    message: string;
  };
  confidence: number;
  evidence_refs: string[];
  decision: "RECOMMEND_ONLY"; // ALWAYS this value
}
```

---

## 3.3 Compilation Logic (Deterministic)

```typescript
const SEVERITY_ORDER = { LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3 };

function compileFacilitation(
  signal: Signal,
  rules: FacilitationRule[]
): FacilitationRecommendation[] {
  return rules
    .filter(rule =>
      rule.signal === signal.signal_id &&
      SEVERITY_ORDER[signal.severity] >= SEVERITY_ORDER[rule.min_severity] &&
      signal.confidence >= rule.min_confidence
    )
    .map(rule => ({
      rule_id: rule.rule_id,
      triggered_by: signal.signal_id,
      recommendation: rule.recommendation,
      confidence: signal.confidence,
      evidence_refs: signal.evidence_refs,
      decision: "RECOMMEND_ONLY" as const
    }));
}
```

---

## 3.4 Compiler Constraints (Hard)

The compiler **MUST NOT:**

| Prohibition | Reason |
|-------------|--------|
| Call GC_L APIs | Would bypass human gate |
| Emit executable commands | Advisory only |
| Change system state | Read-only compilation |
| Chain rules recursively | Prevents runaway logic |

It may only **emit recommendations**.

---

## 3.5 Export Targets (Optional, Approved)

Compiled recommendations may be exported as:

| Format | Use Case |
|--------|----------|
| YAML | Human-readable config |
| JSON | API integration |
| OPA/Rego | Policy-as-code tooling |
| Python stub | Advisory scripting |

**All exports MUST include:**

```yaml
decision: "RECOMMEND_ONLY"
```

---

# PART 4: GC_L Event Hash-Chain Verification

## 4.1 Purpose

This makes audits **tamper-evident** without blockchain theatrics.

---

## 4.2 Event Canonicalization

Before hashing, normalize:

| Step | Requirement |
|------|-------------|
| Key ordering | Sorted alphabetically |
| Whitespace | None (compact JSON) |
| Encoding | UTF-8 |
| Exclusion | Exclude `event_hash` field itself |

---

## 4.3 Event Schema (With Chain)

```json
{
  "event_id": "uuid",
  "timestamp": "RFC3339",
  "tenant_id": "uuid",
  "actor_id": "uuid",
  "capability_id": "CAP-003",
  "intent": "ACTIVATE",
  "object_id": "uuid",
  "object_version": 1,
  "previous_state_hash": "sha256",
  "new_state_hash": "sha256",
  "confirmation": true,
  "reason": "Reviewed simulation",
  "evidence_refs": ["simulation_id"],
  "prev_event_hash": "sha256 | null",
  "event_hash": "sha256"
}
```

---

## 4.4 Hash Computation (Normative)

```typescript
function computeEventHash(event: GCLAuditEvent): string {
  const { event_hash, ...eventWithoutHash } = event;
  const canonical = JSON.stringify(eventWithoutHash, Object.keys(eventWithoutHash).sort());
  return sha256(canonical);
}
```

Each event includes `prev_event_hash` of the **previous GC_L event for the same tenant**.

---

## 4.5 Verification Algorithm

```typescript
interface VerificationResult {
  valid: boolean;
  error?: "CHAIN_BREAK" | "HASH_MISMATCH" | "MISSING_PREV";
  broken_at?: number;
}

function verifyChain(events: GCLAuditEvent[]): VerificationResult {
  if (events.length === 0) {
    return { valid: true };
  }

  // First event should have null prev_event_hash
  if (events[0].prev_event_hash !== null) {
    return { valid: false, error: "MISSING_PREV", broken_at: 0 };
  }

  // Verify first event hash
  if (computeEventHash(events[0]) !== events[0].event_hash) {
    return { valid: false, error: "HASH_MISMATCH", broken_at: 0 };
  }

  for (let i = 1; i < events.length; i++) {
    // Chain linkage
    if (events[i].prev_event_hash !== events[i - 1].event_hash) {
      return { valid: false, error: "CHAIN_BREAK", broken_at: i };
    }

    // Hash integrity
    if (computeEventHash(events[i]) !== events[i].event_hash) {
      return { valid: false, error: "HASH_MISMATCH", broken_at: i };
    }
  }

  return { valid: true };
}
```

---

## 4.6 What This Proves

| Property | Evidence |
|----------|----------|
| No deletion | Chain would break |
| No reordering | Hash linkage violated |
| No silent modification | Hash mismatch detected |
| Full attribution | Actor recorded in each event |

---

## 4.7 Chain Anchoring (Daily Root Hash Export)

For external verification, export daily root hash:

```typescript
interface DailyAnchor {
  date: string; // YYYY-MM-DD
  tenant_id: string;
  first_event_hash: string;
  last_event_hash: string;
  event_count: number;
  chain_hash: string; // SHA256 of all event hashes concatenated
}
```

This anchor can be:
- Stored in external system
- Published to transparency log
- Signed by tenant admin

---

# PART 5: Implementation Files

## Files to Create

| File | Layer | Purpose |
|------|-------|---------|
| `docs/contracts/UI_IRREVERSIBLE_ACTION_CONTRACT.md` | L7 | Governance contract |
| `backend/app/dsl/interpreter.py` | L4 | Policy evaluation |
| `backend/app/facilitation/compiler.py` | L4 | Signal → recommendation |
| `backend/app/audit/hashchain.py` | L6 | Chain computation/verification |
| `backend/app/api/middleware/gcl_governance.py` | L3 | Request validation |
| `website/lib/gcl/action-metadata.ts` | L1 | Frontend metadata |
| `website/lib/gcl/validation.ts` | L1 | Frontend validation |
| `backend/tests/dsl/test_interpreter.py` | L8 | Interpreter tests |
| `backend/tests/audit/test_hashchain.py` | L8 | Hash chain tests |

---

## Validation Checklist

### UI Contract

- [ ] All irreversible endpoints have metadata
- [ ] Backend rejects missing confirmation
- [ ] Backend rejects missing reason (when required)
- [ ] Backend rejects missing simulation ref (when required)
- [ ] Frontend blocks submit until steps complete
- [ ] Copy guard lint rule active

### Interpreter

- [ ] Pure function (no I/O)
- [ ] Deterministic (same input → same output)
- [ ] BLOCK suppressed in MONITOR mode
- [ ] Unknown metrics rejected at compile
- [ ] Type mismatches rejected at compile

### Facilitation Compiler

- [ ] Output always includes `decision: RECOMMEND_ONLY`
- [ ] No API calls in compiler
- [ ] No state mutations
- [ ] No recursive rule chaining

### Hash Chain

- [ ] First event has null `prev_event_hash`
- [ ] Each event's `event_hash` matches computed
- [ ] Chain linkage verified
- [ ] Immutability triggers in place

---

# Final System State

With these specifications:

| Component | Property |
|-----------|----------|
| **Policy decisions** | Deterministic and reviewable |
| **Intelligence** | Advisory and exportable |
| **Human actions** | Tamper-evident |
| **Replay** | Defensible under audit |

**This is a real control system, not a dashboard with AI paint.**

---

## References

- PIN-341: GC_L Formal Governance Pillars
- PIN-340: GC_L Implementation Specification
- PIN-339: Customer Console Capability Reclassification

---

## Next Steps (User Choice)

1. **Policy DSL → bytecode / IR optimizer** — Performance optimization
2. **Signal confidence calibration & decay** — Temporal accuracy
3. **GC_L chain anchoring (daily root hash export)** — External verification

---

**Status:** NORMATIVE
**Governance State:** UI contract enforceable, interpreter pure, compiler advisory-only, audit tamper-evident.
