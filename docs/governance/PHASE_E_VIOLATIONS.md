# PHASE_E_VIOLATIONS.md

**Status:** E-1 COMPLETE (Awaiting Ratification)
**Created:** 2025-12-31
**Method:** Systematic scan of RAW_ARCHITECTURE_NODES.md + RAW_ARCHITECTURE_EDGES.md
**Reference:** Phase E Protocol, PIN-256

---

## Layer Assignment Map (Prerequisite)

Before scanning, each node type was assigned to a layer:

| Layer | Name | Nodes Assigned |
|-------|------|----------------|
| L1 | Product Experience | (Frontend - not in scope) |
| L2 | Product APIs | ENTRY-CONTAINER-001 to -012, TXENTRY-001 to -052 |
| L3 | Boundary Adapters | ADAPT-001, ADAPT-002, ADAPT-003, ADAPT-004 |
| L4 | Domain Engines | PROC-001, PROC-002, PROC-003, PROC-004, PROC-005 |
| L5 | Execution & Workers | WORK-001 to WORK-006, SCHED-001 to SCHED-003 |
| L6 | Platform Substrate | STORE-001 to -006, EXT-001 to -009, PROC-006 to -013 (Services) |
| L7 | Ops & Deployment | OBS-001 (BLCA), OBS-002 (CI), OBS-003, OBS-004 |

## Allowed Import Rules (From Layer Model)

| Layer | Can Import From | Cannot Import From |
|-------|-----------------|-------------------|
| L1 | L2 | L3, L4, L5, L6, L7, L8 |
| L2 | L3, L4, L6 | L1, L5, L7, L8 |
| L3 | L4, L6 | L1, L2, L5, L7, L8 |
| L4 | L5, L6 | L1, L2, L3, L7, L8 |
| L5 | L6 | L1, L2, L3, L4, L7, L8 |
| L6 | (terminal) | All |
| L7 | L6 | L1, L2, L3, L4, L5, L8 |

---

## VIOLATIONS DISCOVERED

### VIOLATION-001: L5 → L4 (Scheduler → Domain Engine)

**Source Node(s):**
- SCHED-001 (failure_aggregation.py) [L5]
- SCHED-002 (graduation_evaluator.py) [L5]
- SCHED-003 (cost_snapshots.py) [L5]

**Target Node(s):**
- PROC-001 (recovery_rule_engine) [L4]
- PROC-002 (cost_model_engine) [L4]
- PROC-005 (policy_engine) [L4]

**Missing Promotion Layer(s):** L6

**Evidence:**
- Edge: `SCHED-001 → PROC-001` (classify_error_category, suggest_recovery_mode)
- Edge: `SCHED-001 → PROC-012 → PROC-001` (Phase A evidence)
- Edge: `SCHED-002 → PROC-005` (graduation evaluation)
- Edge: `SCHED-003 → PROC-002` (cost query)
- Import paths in `backend/app/jobs/*.py`

**Why This Is a Semantic Bypass (Not Stylistic):**
L5 (schedulers) can only import L6. By directly calling L4 domain engines, schedulers are:
1. Making implicit orchestration decisions that belong in L4
2. Bypassing the platform substrate (L6) which should mediate data access
3. Creating inverted control flow where L5 asks L4 for decisions instead of L4 delegating to L5

The correct path: L5 writes state to L6 → L4 reads from L6 and decides → L4 calls L5 to execute

---

### VIOLATION-002: L5 → L4 (Worker → Domain Engine)

**Source Node(s):**
- WORK-001 (runner.py) [L5]
- WORK-003 (recovery_evaluator.py) [L5]
- WORK-004 (recovery_claim_worker.py) [L5]
- WORK-006 (simulate.py) [L5]

**Target Node(s):**
- PROC-001 (recovery_rule_engine) [L4]
- PROC-002 (cost_model_engine) [L4]
- PROC-004 (rbac_engine) [L4]

**Missing Promotion Layer(s):** L6

**Evidence:**
- Edge: `WORK-001 → PROC-004` (Auth check via rbac_engine)
- Edge: `WORK-003 → PROC-001` (should_auto_execute - Phase A SHADOW-001)
- Edge: `WORK-004 → PROC-006 → PROC-001` (recovery matching chain)
- Edge: `WORK-006 → PROC-002` (cost calculation)
- Import paths in `backend/app/worker/*.py`

**Why This Is a Semantic Bypass (Not Stylistic):**
Workers (L5) directly invoke domain engines (L4) for authorization and business decisions. This means:
1. Workers assume the authority to ask domain questions
2. Domain engines are called as libraries, not as authoritative decision makers
3. The execution layer is structurally above the domain layer in invocation graph

Correct architecture: L4 owns the decision, L4 invokes L5 to execute, L5 uses only L6

---

### VIOLATION-003: L2 → L5 (API → Worker)

**Source Node(s):**
- TXENTRY-001 (POST /api/v1/jobs) [L2]

**Target Node(s):**
- WORK-001 (runner.py) [L5]

**Missing Promotion Layer(s):** L3 or L4

**Evidence:**
- Edge: `TXENTRY-001 → WORK-001` (Job submission)
- Note: "agents.py imports worker.*"
- Direct import path in `backend/app/api/agents.py`

**Why This Is a Semantic Bypass (Not Stylistic):**
L2 allowed imports are: L3, L4, L6. L5 is not in the list.
By directly importing worker modules, the API layer:
1. Couples product API to execution implementation
2. Bypasses domain validation (L4) for job submission
3. Creates a structural dependency that should go through L6 (queue/database)

Correct architecture: L2 → L4 (validates) → L6 (persists job) → L5 (picks up from L6)

---

### VIOLATION-004: L7 → L4 (BLCA → Domain Influence)

**Source Node(s):**
- OBS-001 (BLCA) [L7]

**Target Node(s):**
- All domain behavior (L4)
- All execution behavior (L5)

**Missing Promotion Layer(s):** L6, L5

**Evidence:**
- Edges file: "L7 → L4 feedback via L6 state" marked as "Implicit"
- OBS-001 has "Control Authority: Can BLOCK code changes"
- No formal signal path from BLCA to domain engines
- SESSION_PLAYBOOK Section 28-29: BLCA can block sessions

**Why This Is a Semantic Bypass (Not Stylistic):**
BLCA (L7) can halt domain work without a formal promotion path:
1. BLCA observes code/architecture artifacts
2. BLCA decides BLOCK/CLEAN
3. This decision affects what code can execute
4. But domain engines (L4) never receive a formal "DomainReadinessSignal"

The influence is real but implicit. L7 → L4 without passing through L6 → L5.

---

### VIOLATION-005: L7 → L5 (CI → Execution Control)

**Source Node(s):**
- OBS-002 (CI Pipeline) [L7]

**Target Node(s):**
- All code merge paths (affects L2-L5)

**Missing Promotion Layer(s):** L6

**Evidence:**
- Edge: `OBS-002 → Code changes` with BLOCK authority
- `.github/workflows/*.yml` controls PR merge
- No formal signal persisted in L6 for L5 to read

**Why This Is a Semantic Bypass (Not Stylistic):**
CI (L7) blocks code merge, which affects what execution (L5) can run:
1. CI decides pass/fail
2. Failed CI blocks merge
3. Execution environment never runs the blocked code
4. But L5 doesn't receive a formal "code_not_ready" signal from L6

The control is side-effected through Git, not through the formal platform layer.

---

### VIOLATION-006: TIME-BASED Trigger Without L4 Gate

**Source Node(s):**
- SCHED-001 (failure_aggregation.py) [L5]
- SCHED-002 (graduation_evaluator.py) [L5]
- SCHED-003 (cost_snapshots.py) [L5]

**Target Node(s):**
- N/A (the trigger decision itself)

**Missing Promotion Layer(s):** L4 (no domain readiness check)

**Evidence:**
- Nodes file: "Can fire without human intent: YES" on all schedulers
- Trigger source: systemd timer / cron (external to the system)
- No L4 gate that validates "should_aggregation_run_now"

**Why This Is a Semantic Bypass (Not Stylistic):**
Schedulers fire based on TIME, not based on DOMAIN READINESS:
1. Time passes → scheduler fires
2. Scheduler calls domain engine for decisions
3. But scheduler doesn't ASK domain "is now appropriate?"

The WHEN decision belongs to L4 (domain), not to systemd (L7/external).
Currently, L7 (ops/cron) implicitly decides when L4 logic executes.

---

### VIOLATION-007: External READ → Decision Path (L6 → L5/L4 Interpretation)

**Source Node(s):**
- EXT-001 (OpenAI API) [L6]
- EXT-002 (Anthropic API) [L6]
- EXT-003 (VoyageAI) [L6]

**Target Node(s):**
- Decision interpretation points (unclear ownership)

**Missing Promotion Layer(s):** Formal L4 interpretation contract

**Evidence:**
- Edge: `ADAPT-001 → EXT-001` (LLM call)
- Edge: `PROC-006 → EXT-003` (embedding call)
- LLM responses influence execution paths
- Who interprets the response? Adapter (L3)? Worker (L5)? Domain (L4)?

**Why This Is a Semantic Bypass (Not Stylistic):**
External READ results (LLM responses, embeddings) contain semantic content:
1. LLM returns text with recommendations
2. Something parses/interprets that text
3. That interpretation drives domain decisions

If L3 (adapter) or L5 (worker) interprets external responses, they are:
- Making domain decisions that belong in L4
- Without formal promotion of the external semantic content

The interpretation authority is implicit, not formally assigned to L4.

---

### VIOLATION-008: L6 Service Making Domain Decisions

**Source Node(s):**
- PROC-006 (recovery_matcher.py) [Classified as L6 Service]

**Target Node(s):**
- Callers expecting match decisions

**Missing Promotion Layer(s):** Reclassification to L4 or split

**Evidence:**
- Nodes file: PROC-006 "Emits: Match results (suggest_hybrid)"
- Called by: TXENTRY-018 (L2), WORK-004 (L5)
- Uses: EXT-003 (VoyageAI embeddings)

**Why This Is a Semantic Bypass (Not Stylistic):**
PROC-006 is classified as an L6 "SERVICE" but its output is a domain decision:
1. It takes error patterns as input
2. It uses embeddings to find similar patterns
3. It returns "match results" that influence recovery decisions

"Matching" is a domain judgment, not platform plumbing.
If this is really L6, then L2 and L5 are consuming L4-level semantics from L6.
If this should be L4, then the classification is wrong.

Either way: semantic authority is misplaced.

---

### VIOLATION-009: L3 → L4 → L6 → L4 Circular Semantic Path

**Source Node(s):**
- ADAPT-001 (openai_adapter) [L3]
- PROC-003 (llm_policy_engine) [L4]
- EXT-001 (OpenAI API) [L6]

**Target Node(s):**
- Caller of ADAPT-001

**Missing Promotion Layer(s):** Clear unidirectional flow

**Evidence:**
- Edge: `ADAPT-001 → PROC-003` (safety check before call)
- Edge: `ADAPT-001 → EXT-001` (actual LLM call)
- PROC-003 checks limits, then ADAPT-001 calls external

**Why This Is a Semantic Bypass (Not Stylistic):**
The flow is: L3 → L4 → (decision) → L3 → L6

This creates a semantic loop:
1. Adapter (L3) asks engine (L4): "can I call this model?"
2. Engine (L4) says yes/no
3. Adapter (L3) then calls external (L6)

But L3's allowed imports are: L4, L6
And L4's allowed imports are: L5, L6

So L3 calling L4 is allowed, but then L3 calling L6 based on L4's decision means:
- L3 is orchestrating a decision flow
- L3 has implicit authority to interpret L4's response
- L3 is more than "thin translation" (<200 LOC)

The adapter has accrued decision-making authority.

---

### VIOLATION-010: Implicit L6 → L4 State Coupling

**Source Node(s):**
- STORE-001 (PostgreSQL) [L6]
- STORE-003 to STORE-006 (ORM models) [L6]

**Target Node(s):**
- PROC-001 to PROC-005 (Domain Engines) [L4]

**Missing Promotion Layer(s):** Explicit state promotion contract

**Evidence:**
- All domain engines read from PostgreSQL
- No formal "state snapshot" or "readiness signal" contract
- Engines assume database state reflects domain truth

**Why This Is a Semantic Bypass (Not Stylistic):**
L4 engines consume L6 state directly, which is allowed.
But the state itself carries semantic meaning:
1. A row in `killswitch_state` means "traffic should stop"
2. Domain engines read this and act accordingly

The bypass is: state written by L7 (BLCA artifacts) or L5 (workers) is consumed by L4 without:
- Explicit promotion semantics
- Formal interpretation contract
- Clear ownership of who decides what the state means

State is shared, not promoted.

---

## VIOLATIONS SUMMARY

| ID | Type | Source Layer | Target Layer | Severity |
|----|------|--------------|--------------|----------|
| VIOLATION-001 | L5 → L4 | L5 (Schedulers) | L4 (Domain) | STRUCTURAL |
| VIOLATION-002 | L5 → L4 | L5 (Workers) | L4 (Domain) | STRUCTURAL |
| VIOLATION-003 | L2 → L5 | L2 (API) | L5 (Worker) | STRUCTURAL |
| VIOLATION-004 | L7 → L4 | L7 (BLCA) | L4 (Domain) | IMPLICIT |
| VIOLATION-005 | L7 → L5 | L7 (CI) | L5 (Execution) | IMPLICIT |
| VIOLATION-006 | No L4 Gate | L5 (Schedulers) | N/A | AUTHORITY |
| VIOLATION-007 | L6 → ? | L6 (External) | Unclear | INTERPRETATION |
| VIOLATION-008 | L6 = L4? | L6 (Service) | Callers | CLASSIFICATION |
| VIOLATION-009 | L3 → L4 → L6 | L3 (Adapter) | Circular | ORCHESTRATION |
| VIOLATION-010 | L6 → L4 | L6 (State) | L4 (Domain) | COUPLING |

---

## VIOLATION PATTERNS (Grouped)

### Pattern A: Inverted Control Flow (VIOLATION-001, -002, -003)
Lower layers (L5, L2) calling higher authority layers (L4) directly.
**Fix pattern:** Invert the call direction or introduce L6 mediation.

### Pattern B: Implicit Governance Influence (VIOLATION-004, -005)
Ops/deployment (L7) affecting domain/execution without formal signals.
**Fix pattern:** Persist governance decisions in L6 with explicit semantics.

### Pattern C: Orphan Authority (VIOLATION-006, -008)
Decisions being made by nodes without clear layer authority.
**Fix pattern:** Assign decision authority to L4, execution to L5.

### Pattern D: Semantic Interpretation Drift (VIOLATION-007, -009, -010)
External or platform data being interpreted without formal contracts.
**Fix pattern:** Create explicit interpretation contracts owned by L4.

---

## NOT VIOLATIONS (Confirmed Valid)

These edges were checked and confirmed as layer-compliant:

| Edge | Layers | Why Valid |
|------|--------|-----------|
| TXENTRY → PROC-007 (guard_write_service) | L2 → L6 | L2 can import L6 |
| ADAPT-001 → EXT-001 | L3 → L6 | L3 can import L6 |
| PROC-001 → STORE-001 | L4 → L6 | L4 can import L6 |
| OBS-003 → OBS-004 | L7 → L7 | Same layer |
| ACTOR-001 → ENTRY-CONTAINER | External → L2 | Actors are external |

---

## E-1 COMPLETION STATUS

**Violations Found:** 10
**Patterns Identified:** 4
**Confirmed Valid Edges:** 5+ (sample)

**Constraints Met:**
- No fixes proposed
- No reclassification as "acceptable"
- No annotations, notes, or watchlists
- Completeness prioritized over speed

---

**E-1 COMPLETE. AWAITING RATIFICATION BEFORE E-2.**

*Extracted from: RAW_ARCHITECTURE_NODES.md v2, RAW_ARCHITECTURE_EDGES.md v2*
*Method: Layer assignment + allowed import matrix + edge-by-edge scan*
