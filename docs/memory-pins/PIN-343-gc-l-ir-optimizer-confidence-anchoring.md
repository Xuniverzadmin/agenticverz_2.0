# PIN-343: GC_L IR Optimizer, Signal Confidence, Chain Anchoring

**Status:** SPECIFICATION
**Date:** 2026-01-07
**Category:** Governance / Runtime Optimization
**Reference:** PIN-342 (Interpreter), PIN-341 (Formal Pillars), PIN-340 (Implementation)
**Authority:** Human-specified, governance-safe

---

## Executive Summary

This PIN defines three runtime optimization specifications:

1. **Policy DSL → IR Optimizer** — Faster, safer evaluation with identical semantics
2. **Signal Confidence Calibration & Decay** — Prevents over-confidence drift and alert fatigue
3. **GC_L Chain Anchoring** — Externally provable audit via daily root hash export

**Core Principle:** Deterministic, auditable, governance-safe. No cleverness, no shortcuts.

---

# PART 1: Policy DSL → Bytecode / IR Optimizer

## 1.1 Design Goals (Hard)

| Goal | Enforcement |
|------|-------------|
| Preserve exact DSL semantics | Semantic equivalence test |
| No new expressive power | IR instruction set is closed |
| Deterministic output | Same AST → same IR |
| Pure transformation | AST → IR is side-effect free |
| Optimizable and cacheable | IR hash enables caching |
| Verifiable against source DSL | Round-trip comparison |

---

## 1.2 Intermediate Representation (IR)

### IR Instruction Set (Minimal, Closed)

| Instruction | Operands | Description |
|-------------|----------|-------------|
| `LOAD_METRIC` | `<metric_name>` | Load metric value onto stack |
| `LOAD_CONST` | `<value>` | Load constant onto stack |
| `COMPARE` | `<op>` | Compare top two stack values (`>`, `>=`, `<`, `<=`, `==`, `!=`) |
| `EXISTS` | `<metric_name>` | Push boolean: does metric exist? |
| `AND` | - | Logical AND of top two stack values |
| `OR` | - | Logical OR of top two stack values |
| `EMIT_WARN` | `<message>` | Record warning action |
| `EMIT_BLOCK` | - | Record block action |
| `EMIT_REQUIRE_APPROVAL` | - | Record approval requirement |
| `END` | - | Terminate evaluation |

**Forbidden Instructions (Never Added):**
- `JUMP` / `BRANCH`
- `CALL` / `INVOKE`
- `LOOP` / `ITERATE`
- `LOAD_EXTERNAL`
- `MUTATE`

---

## 1.3 AST → IR Compilation

### Example DSL

```
policy CostSpikeGuard
version 1
scope PROJECT
mode ENFORCE

when cost_per_hour > 200 AND error_rate > 0.1
then warn "Cost spike" block
```

### Compiled IR

```
; Policy: CostSpikeGuard v1
; Mode: ENFORCE
; Scope: PROJECT

LOAD_METRIC cost_per_hour
LOAD_CONST 200
COMPARE >
LOAD_METRIC error_rate
LOAD_CONST 0.1
COMPARE >
AND
EMIT_WARN "Cost spike"
EMIT_BLOCK
END
```

---

## 1.4 Compilation Algorithm

```typescript
interface IRInstruction {
  op: string;
  operand?: string | number | boolean;
}

function compileToIR(ast: PolicyAST, mode: "MONITOR" | "ENFORCE"): IRInstruction[] {
  const ir: IRInstruction[] = [];

  // Compile condition
  compileCondition(ast.when, ir);

  // Compile actions (with mode filtering)
  for (const action of ast.then) {
    if (action.type === "BLOCK" && mode !== "ENFORCE") {
      continue; // Dead action elimination
    }
    compileAction(action, ir);
  }

  ir.push({ op: "END" });
  return ir;
}

function compileCondition(cond: Condition, ir: IRInstruction[]): void {
  switch (cond.type) {
    case "predicate":
      ir.push({ op: "LOAD_METRIC", operand: cond.metric });
      ir.push({ op: "LOAD_CONST", operand: cond.value });
      ir.push({ op: "COMPARE", operand: cond.comparator });
      break;
    case "exists":
      ir.push({ op: "EXISTS", operand: cond.metric });
      break;
    case "compound":
      compileCondition(cond.left, ir);
      compileCondition(cond.right, ir);
      ir.push({ op: cond.op }); // AND or OR
      break;
  }
}

function compileAction(action: Action, ir: IRInstruction[]): void {
  switch (action.type) {
    case "WARN":
      ir.push({ op: "EMIT_WARN", operand: action.message });
      break;
    case "BLOCK":
      ir.push({ op: "EMIT_BLOCK" });
      break;
    case "REQUIRE_APPROVAL":
      ir.push({ op: "EMIT_REQUIRE_APPROVAL" });
      break;
  }
}
```

---

## 1.5 IR Optimization Passes

### Pass 1: Constant Folding

Evaluate static expressions at compile time.

```typescript
// Before optimization
LOAD_CONST 100
LOAD_CONST 2
COMPARE >   // Always true

// After optimization
LOAD_CONST true
```

**Reject always-false policies early** — they waste evaluation time.

### Pass 2: Dead Action Elimination

Remove unreachable or invalid actions.

```typescript
function eliminateDeadActions(ir: IRInstruction[], mode: string): IRInstruction[] {
  return ir.filter(inst => {
    // EMIT_BLOCK only valid in ENFORCE mode
    if (inst.op === "EMIT_BLOCK" && mode !== "ENFORCE") {
      return false;
    }
    return true;
  });
}
```

### Pass 3: Metric De-duplication

Collapse repeated metric loads.

```typescript
// Before optimization
LOAD_METRIC cost_per_hour
LOAD_CONST 100
COMPARE >
LOAD_METRIC cost_per_hour  // Duplicate
LOAD_CONST 200
COMPARE <

// After optimization (with caching)
LOAD_METRIC cost_per_hour  // Load once, cache
LOAD_CONST 100
COMPARE >
LOAD_CACHED 0              // Reference cached value
LOAD_CONST 200
COMPARE <
```

---

## 1.6 Compiled Policy Output

```typescript
interface CompiledPolicy {
  policy_id: string;
  version: number;
  scope: "ORG" | "PROJECT";
  mode: "MONITOR" | "ENFORCE";
  ir: IRInstruction[];
  required_metrics: string[];
  ir_hash: string;  // SHA256 of canonical IR
  source_hash: string;  // SHA256 of original DSL
  compiled_at: string;  // RFC3339
}
```

The `ir_hash` is referenced in:
- Simulation results
- Audit logs
- Replay evidence

---

## 1.7 IR Execution (Stack Machine)

```typescript
interface EvaluationResult {
  matched: boolean;
  actions: Array<{ type: string; message?: string }>;
}

function executeIR(
  ir: IRInstruction[],
  metrics: Record<string, any>
): EvaluationResult {
  const stack: any[] = [];
  const actions: any[] = [];

  for (const inst of ir) {
    switch (inst.op) {
      case "LOAD_METRIC":
        stack.push(metrics[inst.operand as string]);
        break;
      case "LOAD_CONST":
        stack.push(inst.operand);
        break;
      case "COMPARE":
        const b = stack.pop();
        const a = stack.pop();
        stack.push(compare(a, inst.operand as string, b));
        break;
      case "EXISTS":
        stack.push(inst.operand as string in metrics);
        break;
      case "AND":
        stack.push(stack.pop() && stack.pop());
        break;
      case "OR":
        stack.push(stack.pop() || stack.pop());
        break;
      case "EMIT_WARN":
        if (stack[stack.length - 1]) {
          actions.push({ type: "WARN", message: inst.operand });
        }
        break;
      case "EMIT_BLOCK":
        if (stack[stack.length - 1]) {
          actions.push({ type: "BLOCK" });
        }
        break;
      case "EMIT_REQUIRE_APPROVAL":
        if (stack[stack.length - 1]) {
          actions.push({ type: "REQUIRE_APPROVAL" });
        }
        break;
      case "END":
        return { matched: stack[stack.length - 1] ?? false, actions };
    }
  }
  return { matched: false, actions: [] };
}

function compare(a: any, op: string, b: any): boolean {
  switch (op) {
    case ">": return a > b;
    case ">=": return a >= b;
    case "<": return a < b;
    case "<=": return a <= b;
    case "==": return a === b;
    case "!=": return a !== b;
    default: return false;
  }
}
```

---

## 1.8 Guarantees

| Property | Mechanism |
|----------|-----------|
| Semantic equivalence | Two policies with identical meaning → identical IR hash |
| Bounded execution | No loops, fixed instruction count |
| Portability | IR is language-agnostic (JS, Rust, Go, Python) |
| Cacheable | IR hash enables evaluation result caching |
| Verifiable | Source hash links IR to original DSL |

---

# PART 2: Signal Confidence Calibration & Decay

## 2.1 Problem Statement

Without calibration:
- Signals drift toward over-confidence
- Alert fatigue from stale/noisy signals
- No learning from human feedback

---

## 2.2 Confidence Model

Each signal has **three confidence components**:

| Component | Source | Range |
|-----------|--------|-------|
| `raw_confidence` | Detector output | 0.0 - 1.0 |
| `historical_accuracy` | Human feedback over time | 0.0 - 1.0 |
| `temporal_decay` | Recency weighting | 0.0 - 1.0 |

---

## 2.3 Calibrated Confidence Formula

```
calibrated_confidence = raw_confidence × historical_accuracy × temporal_decay
```

Clamped to `[0.0, 1.0]`.

### Example

```
raw_confidence = 0.85
historical_accuracy = 0.72  (72% useful historically)
temporal_decay = 0.90       (signal is 10 minutes old)

calibrated_confidence = 0.85 × 0.72 × 0.90 = 0.55
```

---

## 2.4 Historical Accuracy Update

After a **human action** or **policy outcome**, update accuracy:

```
accuracy_new = (accuracy_old × N + outcome_score) / (N + 1)
```

Where:
- `N` = number of previous outcomes
- `outcome_score = 1.0` if signal was useful
- `outcome_score = 0.0` if signal was noise

**Critical Rule:** Only **human-attributed outcomes** update accuracy. System actions do not count.

### Implementation

```typescript
interface AccuracyRecord {
  signal_type: string;
  tenant_id: string;
  total_outcomes: number;
  accuracy: number;
  last_updated: string;
}

function updateAccuracy(
  record: AccuracyRecord,
  outcome_useful: boolean
): AccuracyRecord {
  const score = outcome_useful ? 1.0 : 0.0;
  const newAccuracy = (record.accuracy * record.total_outcomes + score) / (record.total_outcomes + 1);

  return {
    ...record,
    total_outcomes: record.total_outcomes + 1,
    accuracy: newAccuracy,
    last_updated: new Date().toISOString()
  };
}
```

---

## 2.5 Temporal Decay Function

Use exponential decay:

```
temporal_decay = e^(-λ × age_in_minutes)
```

### Decay Rate Constants (λ)

| Signal Category | λ Value | Half-life |
|-----------------|---------|-----------|
| Execution errors | 0.15 | ~5 minutes |
| Cost signals | 0.05 | ~14 minutes |
| Policy drift | 0.01 | ~69 minutes |
| Safety signals | 0.10 | ~7 minutes |

### Implementation

```typescript
function computeTemporalDecay(
  signalTimestamp: Date,
  currentTime: Date,
  lambda: number
): number {
  const ageMinutes = (currentTime.getTime() - signalTimestamp.getTime()) / 60000;
  return Math.exp(-lambda * ageMinutes);
}
```

Old signals naturally lose influence.

---

## 2.6 Severity Adjustment

Final severity may be downgraded based on calibrated confidence:

| Calibrated Confidence | Severity Action |
|-----------------------|-----------------|
| ≥ 0.6 | Keep original severity |
| 0.4 - 0.6 | Downgrade one level |
| 0.2 - 0.4 | Downgrade to LOW |
| < 0.2 | Suppress signal entirely |

### Implementation

```typescript
function adjustSeverity(
  originalSeverity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  calibratedConfidence: number
): "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "SUPPRESSED" {
  if (calibratedConfidence < 0.2) return "SUPPRESSED";
  if (calibratedConfidence < 0.4) return "LOW";
  if (calibratedConfidence < 0.6) {
    const levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
    const idx = levels.indexOf(originalSeverity);
    return levels[Math.max(0, idx - 1)] as any;
  }
  return originalSeverity;
}
```

---

## 2.7 Auditability

Every confidence update emits an audit record:

```json
{
  "event_type": "CONFIDENCE_UPDATE",
  "signal_id": "COST_RATE_SPIKE",
  "tenant_id": "uuid",
  "old_confidence": 0.82,
  "new_confidence": 0.61,
  "components": {
    "raw": 0.85,
    "historical_accuracy": 0.72,
    "temporal_decay": 0.90
  },
  "reason": "Temporal decay + low recent usefulness",
  "timestamp": "RFC3339"
}
```

**No silent tuning.** All confidence changes are observable.

---

## 2.8 Database Schema

```sql
CREATE TABLE signal_accuracy (
  tenant_id           UUID NOT NULL,
  signal_type         TEXT NOT NULL,
  total_outcomes      INTEGER NOT NULL DEFAULT 0,
  accuracy            NUMERIC NOT NULL DEFAULT 0.5,
  last_updated        TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (tenant_id, signal_type)
);

CREATE TABLE confidence_audit_log (
  event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id           TEXT NOT NULL,
  tenant_id           UUID NOT NULL,
  old_confidence      NUMERIC NOT NULL,
  new_confidence      NUMERIC NOT NULL,
  components          JSONB NOT NULL,
  reason              TEXT NOT NULL,
  timestamp           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_confidence_audit_tenant ON confidence_audit_log(tenant_id, timestamp);
```

---

# PART 3: GC_L Chain Anchoring (Daily Root Hash Export)

## 3.1 Purpose

Make the audit log **externally provable** without blockchain theatrics.

---

## 3.2 Daily Root Hash Computation

For each tenant, once per day (UTC):

1. Collect all GC_L events for the day
2. Verify the internal hash chain
3. Compute a rolling root hash

### Rolling Root Algorithm

```typescript
function computeDailyRoot(events: GCLAuditEvent[]): string {
  if (events.length === 0) {
    return sha256("EMPTY_DAY");
  }

  const concatenated = events
    .map(e => e.event_hash)
    .join("");

  return sha256(concatenated);
}
```

For larger volumes, use Merkle tree:

```typescript
function computeMerkleRoot(hashes: string[]): string {
  if (hashes.length === 0) return sha256("EMPTY");
  if (hashes.length === 1) return hashes[0];

  const nextLevel: string[] = [];
  for (let i = 0; i < hashes.length; i += 2) {
    const left = hashes[i];
    const right = hashes[i + 1] || left; // Duplicate last if odd
    nextLevel.push(sha256(left + right));
  }

  return computeMerkleRoot(nextLevel);
}
```

---

## 3.3 Anchor Record Schema

```json
{
  "anchor_id": "uuid",
  "tenant_id": "uuid",
  "date": "YYYY-MM-DD",
  "event_count": 128,
  "first_event_id": "uuid",
  "last_event_id": "uuid",
  "first_event_hash": "sha256",
  "last_event_hash": "sha256",
  "root_hash": "sha256",
  "algorithm": "ROLLING_SHA256 | MERKLE_SHA256",
  "computed_at": "RFC3339",
  "exported_to": ["S3", "GIT"]
}
```

---

## 3.4 Database Schema

```sql
CREATE TABLE gcl_daily_anchors (
  anchor_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL,
  anchor_date         DATE NOT NULL,
  event_count         INTEGER NOT NULL,
  first_event_id      UUID,
  last_event_id       UUID,
  first_event_hash    TEXT,
  last_event_hash     TEXT,
  root_hash           TEXT NOT NULL,
  algorithm           TEXT NOT NULL,
  computed_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  exported_to         JSONB NOT NULL DEFAULT '[]',

  UNIQUE (tenant_id, anchor_date)
);

-- Immutability enforcement
CREATE OR REPLACE FUNCTION prevent_anchor_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'GCL anchors are immutable - no UPDATE or DELETE allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER gcl_anchor_immutable_update
  BEFORE UPDATE ON gcl_daily_anchors
  FOR EACH ROW EXECUTE FUNCTION prevent_anchor_mutation();

CREATE TRIGGER gcl_anchor_immutable_delete
  BEFORE DELETE ON gcl_daily_anchors
  FOR EACH ROW EXECUTE FUNCTION prevent_anchor_mutation();
```

---

## 3.5 Export Targets

| Target | Description | Implementation |
|--------|-------------|----------------|
| Object Storage | S3/GCS/Azure Blob | Upload JSON anchor file |
| Git Repository | Append-only commits | Commit anchor to repo |
| Transparency Log | Sigstore-style | POST to log endpoint |
| Customer Download | CSV + hash | API endpoint |

**Not Required:**
- Blockchain
- Smart contracts
- Tokens

---

## 3.6 Export Implementation

```typescript
interface AnchorExport {
  format: "JSON" | "CSV";
  target: "S3" | "GCS" | "GIT" | "TRANSPARENCY_LOG" | "CUSTOMER_API";
  path: string;
}

async function exportAnchor(
  anchor: DailyAnchor,
  exports: AnchorExport[]
): Promise<void> {
  for (const exp of exports) {
    switch (exp.target) {
      case "S3":
        await uploadToS3(exp.path, JSON.stringify(anchor));
        break;
      case "GIT":
        await commitToGit(exp.path, anchor);
        break;
      case "TRANSPARENCY_LOG":
        await postToTransparencyLog(anchor);
        break;
      case "CUSTOMER_API":
        // Available via GET /api/customer/audit/anchors/{date}
        break;
    }
  }
}
```

---

## 3.7 Verification Flow (External)

To verify audit integrity later:

```typescript
async function verifyAuditIntegrity(
  tenantId: string,
  date: string,
  expectedRootHash: string
): Promise<VerificationResult> {
  // 1. Fetch all events for the day
  const events = await fetchEventsForDay(tenantId, date);

  // 2. Verify internal chain
  const chainResult = verifyChain(events);
  if (!chainResult.valid) {
    return { valid: false, error: "CHAIN_BROKEN", details: chainResult };
  }

  // 3. Recompute daily root
  const computedRoot = computeDailyRoot(events);

  // 4. Compare with anchored root
  if (computedRoot !== expectedRootHash) {
    return { valid: false, error: "ROOT_MISMATCH", computed: computedRoot, expected: expectedRootHash };
  }

  return { valid: true, event_count: events.length };
}
```

**If mismatch → tampering proven.**

---

## 3.8 Operational Rules

| Rule | Enforcement |
|------|-------------|
| Anchoring is **read-only** | No modifications to events |
| No backfilling allowed | Missing days are gaps, not filled |
| Missed day → explicit gap record | Gap record with event_count: 0 |
| Root hashes are immutable | Trigger prevents UPDATE/DELETE |
| Daily computation at UTC midnight + 1h | Cron job |

---

## 3.9 Gap Handling

If a day has no events:

```json
{
  "tenant_id": "uuid",
  "date": "2026-01-05",
  "event_count": 0,
  "root_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "algorithm": "EMPTY_DAY_MARKER",
  "computed_at": "RFC3339"
}
```

The hash `e3b0c44...` is SHA256 of empty string — a known constant.

---

# PART 4: Implementation Files

## Files to Create

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/dsl/ir_compiler.py` | L4 | AST → IR compilation |
| `backend/app/dsl/ir_optimizer.py` | L4 | Optimization passes |
| `backend/app/dsl/ir_executor.py` | L4 | Stack machine execution |
| `backend/app/signals/confidence.py` | L4 | Calibration & decay |
| `backend/app/audit/anchoring.py` | L6 | Daily root computation |
| `backend/app/audit/anchor_export.py` | L3 | Export to targets |
| `backend/alembic/versions/XXX_signal_accuracy.py` | L6 | Migration |
| `backend/alembic/versions/XXX_gcl_anchors.py` | L6 | Migration |
| `backend/tests/dsl/test_ir_compiler.py` | L8 | Compiler tests |
| `backend/tests/dsl/test_ir_executor.py` | L8 | Executor tests |
| `backend/tests/signals/test_confidence.py` | L8 | Calibration tests |
| `backend/tests/audit/test_anchoring.py` | L8 | Anchor tests |

---

## Validation Checklist

### IR Optimizer

- [ ] Same AST → same IR hash
- [ ] BLOCK eliminated in MONITOR mode
- [ ] Constant folding works
- [ ] Metric de-duplication works
- [ ] No loops/jumps in output
- [ ] Bounded execution time

### Confidence Calibration

- [ ] Only human outcomes update accuracy
- [ ] Temporal decay formula correct
- [ ] Severity downgrade at thresholds
- [ ] Suppression below 0.2
- [ ] All updates audited

### Chain Anchoring

- [ ] Daily computation runs reliably
- [ ] Root hash matches recomputation
- [ ] Immutability triggers active
- [ ] Gap records for empty days
- [ ] Exports to configured targets

---

# Final System Capabilities

| Capability | Evidence |
|------------|----------|
| Policies execute in **bounded, optimized IR** | No loops, fixed instruction count |
| Signals self-regulate confidence over time | Decay + accuracy learning |
| Human actions are **cryptographically anchored** | Daily root hash export |
| Audits survive legal and compliance scrutiny | External verification possible |

**This is serious governance infrastructure.**

---

## References

- PIN-342: UI Contract, Interpreter, Hash-Chain
- PIN-341: Formal Governance Pillars
- PIN-340: Implementation Specification
- PIN-339: Capability Reclassification

---

## Next Steps (User Choice)

1. **Policy IR interpreter JIT vs interpreter tradeoffs**
2. **Signal usefulness feedback UX contract**
3. **Cross-tenant anonymized benchmarking (founder-only)**

---

**Status:** SPECIFICATION
**Governance State:** IR deterministic, confidence self-regulating, anchoring externally provable.
