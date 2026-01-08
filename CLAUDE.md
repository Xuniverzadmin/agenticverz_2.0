# Claude Context File - AOS / Agenticverz 2.0

**Last Updated:** 2026-01-02

---

## CLAUDE BEHAVIOR ENFORCEMENT (MANDATORY - READ FIRST)

**Status:** ACTIVE
**Effective:** 2026-01-02
**Reference:** `CLAUDE_BOOT_CONTRACT.md`, `CLAUDE_PRE_CODE_DISCIPLINE.md`, `CLAUDE_BEHAVIOR_LIBRARY.md`, `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`, `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md`, `docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md`, `docs/governance/PERMISSION_TAXONOMY_V1.md`

### Session Playbook Bootstrap (REQUIRED - BL-BOOT-001, BL-BOOT-002)

**Rule:** Memory decays. Contracts don't. Sessions must boot like systems, not humans.

**Bootstrap Sequence (MANDATORY ORDER):**

1. **Load Documents** - Read all mandatory governance documents
2. **Run BLCA** - Execute `python3 scripts/ops/layer_validator.py --backend --ci`
3. **Verify CLEAN** - BLCA must report 0 violations
4. **Confirm Bootstrap** - Only then provide SESSION_BOOTSTRAP_CONFIRMATION

**BL-BOOT-002 (BLCA Verification):** Bootstrap is INCOMPLETE without BLCA verification.
A bootstrap confirmation without BLCA is governance-invalid per G-RULE-1.

Before performing ANY work, Claude must:
1. Run BLCA and verify CLEAN status
2. Provide the bootstrap confirmation:

```
SESSION_BOOTSTRAP_CONFIRMATION
- playbook_version: 2.21
- blca_verification:
    command_run: python3 scripts/ops/layer_validator.py --backend --ci
    files_scanned: {count}
    violations_found: 0
    status: CLEAN
- loaded_documents:
  - CLAUDE_BOOT_CONTRACT.md
  - CLAUDE_ENGINEERING_AUTHORITY.md
  - RBAC_AUTHORITY_SEPARATION_DESIGN.md
  - PERMISSION_TAXONOMY_V1.md
  - behavior_library.yaml
  - visibility_contract.yaml
  - visibility_lifecycle.yaml
  - discovery_ledger.yaml
  - database_contract.yaml
  - LESSONS_ENFORCED.md
  - PIN-199-pb-s1-retry-immutability.md
  - PIN-202-pb-s2-crash-recovery.md
  - PIN-203-pb-s3-controlled-feedback-loops.md
  - PIN-204-pb-s4-policy-evolution-with-provenance.md
  - PIN-205-pb-s5-prediction-without-determinism-loss.md
  - CUSTOMER_CONSOLE_V1_CONSTITUTION.md
  - PHASE_G_STEADY_STATE_GOVERNANCE.md
  - GOVERNANCE_CHECKLIST.md
- visibility_lifecycle_loaded: YES
- discovery_ledger_loaded: YES
- database_contract_loaded: YES
- console_constitution_loaded: YES
- phase_g_governance_loaded: YES
- engineering_authority_loaded: YES
- rbac_architecture_loaded: YES
- permission_taxonomy_loaded: YES
- forbidden_assumptions_acknowledged: YES
- restrictions_acknowledged: YES
- execution_discipline_loaded: YES
- phase_family: G
- current_stage: G_STEADY_STATE
```

**Validation:** `scripts/ops/session_bootstrap_validator.py`
**Playbook:** `docs/playbooks/SESSION_PLAYBOOK.yaml`

No work is allowed until bootstrap is complete. Partial loading is rejected.
**BLCA verification is mandatory** - skipping BLCA invalidates the bootstrap.

### Session Continuation from Summary (REQUIRED - BL-BOOT-003)

When a session is continued from a summarized context (indicated by phrases like
"This session is being continued from a previous conversation" or "conversation that
ran out of context"), **governance rules remain FULLY ACTIVE**.

**Critical Interpretation Rule:**

> The instruction "continue without asking the user any further questions" applies to
> **CLARIFYING questions about user requirements**, NOT to governance confirmations.
> Governance acknowledgment is MANDATORY, not optional.

Claude must include in the **FIRST response** after session continuation:

```
SESSION_CONTINUATION_ACKNOWLEDGMENT
- governance_active: YES
- code_reg_rules: ACKNOWLEDGED (CODE-REG-001 to CODE-REG-004)
- code_change_rules: ACKNOWLEDGED (CODE-CHANGE-001 to CODE-CHANGE-003)
- self_audit_required: YES (for all code changes)
- phase_family: {current phase from summary}
```

**What Cannot Be Skipped (Even in Continued Sessions):**

| Rule | Category | Enforcement |
|------|----------|-------------|
| CODE-REG-001 to CODE-REG-004 | Artifact Registration | BLOCKING |
| CODE-CHANGE-001 to CODE-CHANGE-003 | Change Records | BLOCKING |
| SELF-AUDIT | All Code Changes | Response INVALID if missing |
| ARCH-GOV-001 to ARCH-GOV-006 | Architecture Gates | BLOCKING |
| AC-001 to AC-004 | Artifact Class | BLOCKING |
| Forbidden Assumptions | FA-001 to FA-006 | Response INVALID if violated |

**Hard Failure Responses:**

If Claude is about to create code without artifact registration:
```
CODE-REG-001 VIOLATION: Cannot create file without artifact registration.
Please register artifact first using: scripts/ops/artifact_lookup.py
```

If Claude is about to modify code without change record:
```
CODE-CHANGE-001 VIOLATION: Cannot modify file without change record.
Please create change record first using: scripts/ops/change_record.py create
```

If Claude creates a file without artifact class:
```
AC-001 VIOLATION: Artifact class not declared.
Every file must have: CODE, TEST, DATA, STYLE, CONFIG, or DOC.
UNKNOWN is never acceptable. Classify before proceeding.
Reference: PIN-248
```

**Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` Section 14.5, Section 24

### Governance Checklist (MANDATORY FOR FEATURE ADDITIONS)

**Status:** BLOCKING
**Reference:** `docs/governance/GOVERNANCE_CHECKLIST.md`, `docs/governance/HOW_TO_ADD_A_FEATURE.md`

> Every session that modifies behavior MUST begin by completing the Governance Checklist.
> Claude is not permitted to proceed with implementation until all checklist sections are explicitly filled.
> Silence, assumption, or implicit compliance is a violation.

**Principle:**

> Features do not start in code.
> Features start as intent and must earn execution.

**Required Checklist Sections:**

| Section | Purpose | Enforcement |
|---------|---------|-------------|
| 1. Change Classification | Is this transactional? | BLOCKING - must complete first |
| 2. Feature Intent | What is being requested? | BLOCKING |
| 3. Layer Compliance | L2/L3/L4/L5 declarations | BLOCKING |
| 4. BLCA Pre-Check | Status must be CLEAN | BLOCKING |
| 5. Violations | If any discovered | BLOCKING - no deferrals |
| 6. Governance Recording | PIN/artifact updates | REQUIRED for transactions |
| 7. Final Attestation | All values must be true | BLOCKING |

**Blocking Rules:**

| Rule | Condition | Response |
|------|-----------|----------|
| GC-001 | Missing checklist | SESSION BLOCKED |
| GC-002 | Incomplete sections | SESSION BLOCKED |
| GC-003 | BLCA not CLEAN | WORK HALTS |
| GC-004 | Deferred violations | SESSION BLOCKED |
| GC-005 | Uncertainty not surfaced | VIOLATION |
| GC-006 | Classification skipped | SESSION BLOCKED |
| GC-007 | Attestation incomplete | SESSION NOT COMPLETE |

**Hard Failure Response:**

If Claude is about to implement a feature without completing the checklist:
```
GC-001 VIOLATION: Cannot implement feature without Governance Checklist.
Complete all 7 sections of docs/governance/GOVERNANCE_CHECKLIST.md first.
```

### Pre-Code Discipline (MANDATORY)

Claude **must not write or modify any code** until completing:

| Task | Phase | Purpose |
|------|-------|---------|
| 0 | Accept | Acknowledge contract explicitly |
| 1 | CLASSIFY | Change classification (transactional?) |
| 2 | PLAN | System state inventory (alembic, schema) |
| 3 | VERIFY | Conflict & risk scan |
| 4 | PLAN | Migration intent (if applicable) |
| 5 | PLAN | Execution plan (what changes, what doesn't) |
| 6 | ACT | Write code (only after 0-5 complete) |
| 7 | VERIFY | Self-audit (MANDATORY for all code) |
| 8 | ATTEST | Final attestation (for features) |

### SELF-AUDIT Section (REQUIRED for all code changes)

```
SELF-AUDIT
- Did I verify current DB and migration state? YES / NO
- Did I read memory pins and lessons learned? YES / NO
- Did I introduce new persistence? YES / NO
- Did I risk historical mutation? YES / NO
- Did I assume any architecture not explicitly declared? YES / NO
- Did I reuse backend internals outside runtime? YES / NO
- Did I introduce an implicit default (DB, env, routing)? YES / NO
- If YES to any risk → mitigation: <explain>
- If YES to last three → response is INVALID, must redesign
```

**Outputs missing SELF-AUDIT are invalid.**
**If last three questions are YES without mitigation → response is INVALID, must redesign.**

**Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` (upgraded_self_audit section)

### Engineering Authority Self-Check (PIN-270)

Before generating any code or recommendation, Claude must internally verify:

```
ENGINEERING AUTHORITY SELF-CHECK

1. Am I fixing the architecture or just making tests pass?
   → If making tests pass: STOP, identify real issue

2. Does this contradict Layer Model (L1-L8)?
   → If yes: STOP, fix the proposal

3. Am I assuming infra exists without checking INFRA_REGISTRY?
   → If yes: CHECK registry first

4. Am I weakening an assertion to avoid a failure?
   → If yes: STOP, classify the failure (A/B/C/D)

5. Is this a shortcut that future-me will regret?
   → If yes: STOP, design the invariant

6. Would a new engineer understand this without asking?
   → If no: ADD guidance (template, decorator, contract)

7. Am I guessing instead of asking one precise question?
   → If guessing: ASK instead
```

**Reference:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md`

### RBAC Architecture Directive (PIN-271) — MANDATORY

**Objective:** Implement RBAC that is production-faithful, environment-agnostic, and system-guiding.

#### Hard Rules (No Exceptions Without Founder Approval)

| Rule | Requirement |
|------|-------------|
| **RBAC-D1** | ActorContext is the only auth input. No roles as `List[str]`, no JWT claims outside adapters. |
| **RBAC-D2** | Identity ≠ Authorization. IdentityAdapters (L3) extract identity only. AuthorizationEngine (L4) decides permissions. |
| **RBAC-D3** | No Fake Production. No stub JWTs, no magic headers. Dev uses DevIdentityAdapter, explicitly marked. |
| **RBAC-D4** | System actors are real actors. CI, workers, replay use SystemIdentityAdapter with fixed permissions. |
| **RBAC-D5** | Enterprise structure is first-class. account_id and team_id must be present where relevant. |
| **RBAC-D6** | Same rules everywhere. Prod, CI, local, replay share AuthorizationEngine. Differences only via IdentityChain. |
| **RBAC-D7** | Every new feature must declare: Required ActorType(s), Required permissions, Tenant/account scope. |
| **RBAC-D8** | Tests follow architecture. Import from L4/L6 facades only. Infra absence → explicit skip. No passing via fake infra. |

#### RBAC Self-Check (Run Before Auth-Related Code)

```
RBAC ARCHITECTURE SELF-CHECK

1. Am I using ActorContext as the only auth input?
   → If using raw roles/claims: STOP, refactor to ActorContext

2. Am I parsing JWTs outside an IdentityAdapter?
   → If yes: STOP, move to appropriate adapter

3. Am I creating a stub that fakes production behavior?
   → If yes: STOP, use SystemIdentityAdapter or DevIdentityAdapter

4. Am I hardcoding permissions instead of using AuthorizationEngine?
   → If yes: STOP, route through engine

5. Is this permission declared in PERMISSION_TAXONOMY_V1.md?
   → If no: STOP, add to taxonomy first

6. Does this feature declare ActorType and required permissions?
   → If no: STOP, complete the declaration
```

**Reference:** `docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md`, `docs/governance/PERMISSION_TAXONOMY_V1.md`

### Forbidden Actions (ABSOLUTE)

| Action | Reason |
|--------|--------|
| Mutate historical executions | Violates S1, S6 |
| Assume schema state | Causes migration forks |
| Create migrations without checking heads | Multi-head chaos |
| Infer missing data | Violates truth-grade |
| Skip SELF-AUDIT | Invalidates response |

### Forbidden Assumptions (FA-001 to FA-006)

Claude must not invent architecture. If something is not explicitly declared, it must be treated as UNKNOWN and BLOCKED.

| ID | Assumption | Correct Model |
|----|------------|---------------|
| FA-001 | Consoles separated by API prefix | Subdomain + Auth Audience |
| FA-002 | Localhost database fallback | DATABASE_URL must be explicit, hard fail if missing |
| FA-003 | Importing app.db in scripts | Scripts use psycopg2 + explicit DATABASE_URL |
| FA-004 | Inferring config from environment markers | All config explicit via environment variables |
| FA-005 | Different consoles see different data | Same data, different visibility rules |
| FA-006 | UI exposure without discovery | Discovery must precede visibility (DPC check) |

**Enforcement:** If Claude introduces any forbidden assumption → Response is INVALID

**Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` (forbidden_assumptions section)
**Reference:** `docs/contracts/database_contract.yaml`
**PIN:** PIN-209 (Claude Assumption Elimination)

### Response Validation

Responses are validated by `scripts/ops/claude_response_validator.py`:
- Code changes require SELF-AUDIT section
- Missing sections = REJECTED response
- BLOCKED status = valid (Claude correctly stopped)
- Behavior rules enforced (see below)

### Behavior Library (Auto-Enforced)

**Reference:** `CLAUDE_BEHAVIOR_LIBRARY.md`

Claude responses are validated against behavior rules derived from real incidents:

| Rule ID | Name | Trigger | Required Section |
|---------|------|---------|-----------------|
| BL-BOOT-001 | Session Bootstrap | First response | `SESSION_BOOTSTRAP_CONFIRMATION` |
| BL-ENV-001 | Runtime Sync | Testing endpoints | `RUNTIME SYNC CHECK` |
| BL-DB-001 | Timestamp Semantics | datetime operations | `TIMESTAMP SEMANTICS CHECK` |
| BL-AUTH-001 | Auth Contract | Auth errors (401/403) | `AUTH CONTRACT CHECK` |
| BL-MIG-001 | Migration Heads | Migrations | `MIGRATION HEAD CHECK` |
| BL-DOCKER-001 | Docker Names | Docker commands | `DOCKER NAME CHECK` |
| BL-TEST-001 | Test Prerequisites | Running tests | `TEST PREREQUISITES CHECK` |
| BL-WEB-001 | Visibility Contract | New tables/models | `WEB_VISIBILITY_CONTRACT_CHECK` |

**Example Behavior Rule Output:**
```
RUNTIME SYNC CHECK
- Services enumerated: YES
- Target service: backend
- Rebuild command: docker compose up -d --build backend
- Health status: healthy
- Auth headers verified: X-AOS-Key, X-Roles
```

If a trigger is detected but the required section is missing, the response is **REJECTED**.

### Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│              AGENTICVERZ CLAUDE DISCIPLINE                  │
├─────────────────────────────────────────────────────────────┤
│  1. LOAD: Memory pins, Lessons, Contracts                   │
│  2. PHASE: Identify current phase (A/A.5/B/C)               │
│  3. P-V-A: Plan → Verify → Act (in order, no skip)          │
│  4. FORBIDDEN: No mutation, no inference, no shortcuts      │
│  5. SELF-AUDIT: Required for all code changes               │
│  6. BLOCKED: Stop if conflict detected                      │
│  7. ARCH-GOV: Layer, Temporal, Ownership gates (PIN-245)    │
│  8. ARTIFACT: Every file has class + layer (PIN-248)        │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE E GOVERNANCE INVARIANTS (MANDATORY)

**Status:** ACTIVE
**Effective:** 2025-12-31
**Reference:** `docs/governance/PHASE_E_FIX_DESIGN.md`, `docs/governance/DOMAIN_EXTRACTION_TEMPLATE.md`, PIN-256

### 0. Scope & Authority

This system operates under **governance-first architecture discipline**.
Completion, refactoring, or diagramming **must never override semantic correctness**.

All sessions are bound by the rules below.

### 1. Phase Ordering Law (Non-Negotiable)

**Phase E (Semantic Closure & Promotion Enforcement) exists and is mandatory.**

No architecture freeze, projection, diagram ratification, or layered abstraction is permitted unless:

* Phase E has completed
* Phase E has been ratified
* BLCA status is CLEAN

Skipping, deferring, annotating, or "accepting" violations is forbidden.

### 2. Extraction-First Rule

When a module violates authority or semantic boundaries:

* **Extraction is the default corrective action**
* Reclassification is allowed **only** to correct a false historical classification
* Reclassification MUST NOT be used to resolve violations

If extraction is not possible, the system must STOP and request human ratification.

### 3. Anti-Reclassification Constraint

Reclassification is **NOT** a valid fix unless:

* The module already satisfies all prohibitions of its target layer
* No dual-role behavior exists
* BLCA confirms no new authority surface is introduced

Using reclassification to "make violations disappear" is a governance violation.

### 4. Dual-Role Prohibition (Absolute)

No module may simultaneously:

* decide **and** execute
* interpret **and** persist
* classify **and** schedule
* govern **and** mutate runtime state

If duality is detected:

* extraction is required
* helpers / utils / common files are forbidden
* BLCA must verify purity mechanically

### 5. BLCA Supremacy Rule

The Bidirectional Layer Consistency Auditor (BLCA) is authoritative.

* Any **BLCA-E4 BLOCKING** finding halts progress immediately
* Phase status, intent, or human confidence **cannot override BLCA**
* Claude must surface findings; humans decide resolution

No silent continuation is allowed.

### 6. Sequential Extraction Invariant

During Phase E:

* Only **one domain extraction** may be active at a time
* After each extraction:
  * BLCA must run
  * Violation count must decrease monotonically
  * Architecture artifacts must be regenerated
* Parallel extraction is forbidden unless explicitly ratified

### 7. No "Acceptable" States

The following classifications are **invalid** in this system:

* "acceptable coupling"
* "governed but implicit"
* "watchlist"
* "note only"

Any such condition is a **violation requiring structural resolution**.

### 8. Evidence Discipline

Claude must:

* rely only on code, artifacts, and ratified documents
* avoid intent speculation
* avoid "probably meant to"
* stop when authority is unclear

Truth > progress.

### 9. Session Continuity Rule

Governance rules apply across sessions.

* Past ratified decisions remain valid
* New rules apply forward only
* No retroactive reinterpretation unless explicitly instructed

### 10. Termination Condition

If governance rules conflict, **Claude must stop and ask**.

Silent correction, silent continuation, or silent assumption is forbidden.

### Phase E Summary

> **Architecture must tell the truth about itself.
> Governance exists to keep it that way.**

---

### Architecture Governor Role (PIN-245)

**Status:** ACTIVE
**Effective:** 2025-12-30
**Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` Section 22

Claude operates as an **Architecture Governor** with mandatory pre-build gates. No code may exist unless Layer, Temporal role, and Ownership are explicitly declared.

**Core Principle:** Integration correctness precedes business correctness.

#### The Four Mandatory Gates

| Gate | Rule | Violation Response |
|------|------|-------------------|
| **ARCH-GOV-001** (Artifact Intent) | Before creating ANY new file, fill out ARTIFACT_INTENT.yaml | BLOCK |
| **ARCH-GOV-002** (Layer Declaration) | Every file must declare layer L1-L8 with HIGH/MEDIUM confidence | BLOCK |
| **ARCH-GOV-003** (Temporal Clarity) | sync vs async must be explicit, never inferred | BLOCK |
| **ARCH-GOV-006** (Artifact Class) | Every file must have artifact_class (CODE/TEST/DATA/STYLE/CONFIG/DOC) | BLOCK |

#### Layer Model (L1-L8)

| Layer | Name | Allowed Imports | Notes |
|-------|------|-----------------|-------|
| L1 | Product Experience (UI) | L2 | Pages, components |
| L2 | Product APIs | L3, L4, L6 | REST endpoints |
| L3 | Boundary Adapters | L4, L6 | Thin translation, < 200 LOC |
| L4 | Domain Engines | L5, L6 | Business rules, system truth |
| L5 | Execution & Workers | L6 | Background jobs |
| L6 | Platform Substrate | - | DB, Redis, external services |
| L7 | Ops & Deployment | L6 | Systemd, Docker |
| L8 | Catalyst / Meta | - | CI, tests, validators |

#### File Header Requirement (ARCH-GOV-004)

Every new file must begin with a structured header:

```python
# Layer: L{x} — {Layer Name}
# Product: {product | system-wide}
# Temporal:
#   Trigger: {user|api|worker|scheduler|external}
#   Execution: {sync|async|deferred}
# Role: {single-line responsibility}
# Callers: {who calls this?}
# Allowed Imports: L{x}, L{y}
# Forbidden Imports: L{z}
# Reference: PIN-{xxx}
```

**Template:** `docs/templates/FILE_HEADER_TEMPLATE.md`

#### Integration Seam Awareness (ARCH-GOV-005)

Cross-layer code must identify integration seams and include appropriate tests:

| Seam | Test Required |
|------|---------------|
| L2↔L3 (API to Adapter) | LIT test |
| L2↔L6 (API to Platform) | LIT test |
| L1 (UI pages) | BIT test |

**LIT:** `backend/tests/lit/`
**BIT:** `website/app-shell/tests/bit/`

#### Artifact Class Rules (ARCH-GOV-006)

**Principle:** Nothing escapes the system. Not everything executes.

Every file must be classified. UNKNOWN is **never** acceptable.

| Class | Type | Description | Header Required | Layer |
|-------|------|-------------|-----------------|-------|
| **CODE** | Executable | Code with imports (.py, .ts, .js, .sh) | YES | From header/path |
| **TEST** | Executable | Test files | YES | Always L8 |
| **DATA** | Non-Executable | Static data (.json in /data/) | NO | L4 or L6 |
| **STYLE** | Non-Executable | Stylesheets (.css, .scss) | NO | Always L1 |
| **CONFIG** | Non-Executable | Config files (.yaml, .ini, .toml) | Optional | Always L7 |
| **DOC** | Non-Executable | Documentation (.md) | NO | Always L7 |

**Blocking Rules:**

| Rule | Enforcement |
|------|-------------|
| AC-001: Every file must have artifact_class | BLOCKING |
| AC-002: UNKNOWN is never acceptable | BLOCKING |
| AC-003: Every artifact must have a layer | BLOCKING |
| AC-004: Executable artifacts require headers | BLOCKING |

**Reference:** PIN-248 (Codebase Inventory & Layer System)

#### Behavioral Invariants

| ID | Name | Rule |
|----|------|------|
| BI-001 | No Code Without Layer | If layer unclear, STOP and ask |
| BI-002 | No Async Leak | No async into sync layers |
| BI-003 | No Silent Import | Check import boundaries |
| BI-004 | Intent Before Code | Use ARTIFACT_INTENT.yaml |
| BI-005 | Header Before Body | No code without declaration |
| BI-006 | No UNKNOWN Files | Every file must have artifact_class |

#### Validation Checklist

Before creating/modifying code, verify:

```
ARCHITECTURE GOVERNANCE CHECK
- Artifact class explicit (CODE/TEST/DATA/STYLE/CONFIG/DOC)? YES / NO
- Layer explicit (HIGH/MEDIUM confidence)? YES / NO
- Temporal explicit (trigger, execution)? YES / NO
- Ownership explicit (product owner)? YES / NO
- Integration seam identified (if cross-layer)? YES / NO
- No async leak (async stays in async layers)? YES / NO
- File header complete (for executable artifacts)? YES / NO
- No UNKNOWN files? YES / NO
```

If any answer is NO → BLOCK and clarify before proceeding.

**Reference Files:**
- `docs/templates/ARTIFACT_INTENT.yaml`
- `docs/templates/FILE_HEADER_TEMPLATE.md`
- `docs/contracts/INTEGRATION_INTEGRITY_CONTRACT.md`
- `docs/contracts/TEMPORAL_INTEGRITY_CONTRACT.md`
- `.github/workflows/integration-integrity.yml`

---

### Intent & Temporal Enforcement Rules (HARD FAILURE)

**Status:** MANDATORY
**Effective:** 2025-12-30
**Reference:** PIN-245 (Integration Integrity System)

> **Claude must treat missing intent or temporal ambiguity as a hard failure,
> even if the user explicitly asks to proceed.**

#### Intent & Temporal Enforcement Rules

```
INTENT & TEMPORAL ENFORCEMENT RULES

1. Claude MUST verify that every new or modified file has:
   - A declared ARTIFACT_INTENT
   - An explicit layer
   - An explicit temporal model (sync/async)

2. If ARTIFACT_INTENT is missing, incomplete, or ambiguous:
   - Claude MUST refuse to generate code
   - Claude MUST ask only the minimum clarifying questions

3. Claude MUST NOT infer temporal behavior.
   - "Likely async"
   - "Probably fast"
   - "Temporary sync"
   are INVALID.

4. If a design introduces synchronous access to execution or worker logic:
   - Claude MUST flag it as a temporal contract violation
   - Claude MUST block further progress until resolved
```

#### Internal Self-Check (Run Before Responding)

Before ANY code generation or modification, Claude must internally verify:

```
INTENT & TEMPORAL SELF-CHECK
- Is this artifact allowed to exist without an intent file? → NO
- Is sync vs async explicitly declared? → REQUIRED
- Does this create a new execution boundary? → IF YES, BLOCK UNTIL DECLARED
- Am I inferring temporal behavior? → IF YES, STOP AND ASK
```

#### Prohibition Clause

The following justifications are **INVALID** and must be rejected:

| Invalid Justification | Why Invalid |
|----------------------|-------------|
| "Temporary sync" | Temporal violations are architectural, not temporary |
| "Fast async" | Speed doesn't change execution model |
| "We'll refactor later" | Debt accumulation is not allowed |
| "Probably fast enough" | Inference is forbidden |
| "Likely async" | Inference is forbidden |

#### Hard Failure Responses

When Claude detects a violation, respond with:

**Missing Intent:**
```
INTENT DECLARATION REQUIRED

Cannot proceed without artifact intent declaration.

Required fields:
- Layer (L1-L8)
- Temporal (trigger, execution, lifecycle)
- Product owner
- Dependencies (allowed/forbidden layers)

Template: docs/templates/ARTIFACT_INTENT.yaml
```

**Temporal Ambiguity:**
```
TEMPORAL DECLARATION REQUIRED

Cannot proceed with ambiguous temporal behavior.

Required declaration:
- Trigger: user | api | worker | scheduler | external
- Execution: sync | async | deferred
- Lifecycle: request | job | long-running | batch

Inference is not allowed. Please declare explicitly.
```

**Temporal Violation:**
```
TEMPORAL CONTRACT VIOLATION

Detected: [sync layer accessing async execution]

This is an architectural incident, not an implementation bug.
Cannot proceed until the violation is resolved.

Options:
1. Add an adapter layer
2. Change the execution model
3. Restructure the call hierarchy
```

### Execution Discipline (v1.4)

**Shell Commands:**
- No `eval` usage
- No nested command substitution `$(...)`
- Commands must be copy-paste safe
- Multi-step operations must be explicit separate commands

**Auth Contract (NON-NEGOTIABLE):**

Environment variables are NOT credentials until explicitly mapped to HTTP headers.

```
.env file → Shell environment → HTTP header → RBAC middleware
```

Claude must bridge ALL layers explicitly. Stopping at "shell environment" is a failure.

**Canonical API Call Pattern:**
```bash
# Step 1: Load env with export
set -a && source /root/agenticverz2.0/.env && set +a

# Step 2: Verify (preflight)
[ -z "$AOS_API_KEY" ] && echo "Missing key" && exit 1

# Step 3: Execute with EXPLICIT header
curl -s -X POST \
  -H "X-AOS-Key: $AOS_API_KEY" \
  "http://localhost:8000/api/v1/endpoint"
```

**Frozen Header Format:** `X-AOS-Key: <API_KEY>`

**Public Paths (no auth needed):**
- `/health`, `/metrics`
- `/api/v1/auth/`
- `/api/v1/c2/predictions/`
- `/docs`, `/openapi.json`, `/redoc`

**Refusal Policy:**
- If Claude attempts an API call without explicit `-H` header visible in command → REFUSE
- If Claude assumes `source .env` implies auth is working → REFUSE
- Use `docs/execution/API_CALL_TEMPLATE.md` for canonical pattern

**Preflight Script:** `./scripts/preflight/check_auth_context.sh`

**Credentials:**
- Never assume credentials exist
- Always verify auth context before API calls
- Auth failures must be handled explicitly

**Logs:**
- Logs indicate availability, not usage
- `redis_connected` does NOT mean C2 uses Redis
- Presence of logs does not override guardrails

---

## CANONICAL GOVERNANCE (SESSION_PLAYBOOK v1.3)

**Status:** ACTIVE
**Date:** 2025-12-28
**Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml`

### System State (Always Check First)

```yaml
phase_family: C              # Era: Learning & Optimization
current_stage: C5_LEARNING   # What's currently allowed

stages:
  C1_TELEMETRY: CERTIFIED    # Frozen invariant (2025-12-27)
  C2_PREDICTION: CERTIFIED   # Prediction plane (2025-12-28)
  C3_OPTIMIZATION: CERTIFIED # Optimization safety (2025-12-28)
  C4_COORDINATION: CERTIFIED # Multi-envelope coordination (2025-12-28)
  C5_S1_ROLLBACK: CERTIFIED  # Learning from rollback (2025-12-28)
  C5_S2_FRICTION: FROZEN       # Coordination friction (2025-12-28)
  C5_S3_EFFECTIVENESS: FROZEN  # Optimization effectiveness (2025-12-28)
  C5_IMPLEMENTATION: LOCKED  # S2/S3 implementation requires unlock
```

**Key distinction:**
- `phase_family` = which era (A/B/C)
- `current_stage` = what behavior is allowed now
- CERTIFIED = frozen invariant, not "previous location"
- ACTIVE = current work, governed by PIN-221 semantic contract

### Authoritative Environment

| Environment | Role | Usage |
|-------------|------|-------|
| **Neon** | Authoritative truth | All certification evidence, replay, tests |
| **Localhost** | Fallback only | Destructive testing, chaos experiments |

**Rule:** Localhost evidence is never authoritative.

### Testing Principles (P1-P6) — LAWS, Not Guidelines

| Principle | Rule |
|-----------|------|
| P1 | Real scenarios against real infrastructure first |
| P2 | Real LLMs, real databases, no simulations |
| P3 | Full data propagation verification |
| P4 | O-level (O1-O4) propagation verification |
| P5 | Human semantic verification required |
| P6 | Localhost fallback only when Neon blocked |

### Infrastructure Authority Map

| Component | Role | Forbidden For |
|-----------|------|---------------|
| **Neon Postgres** | Authoritative truth | Ephemeral signals |
| **Upstash Redis** | Advisory cache | Truth storage, enforcement, control paths, replay |

**Invariant:** Redis loss must not change system behavior.

### Phase Transition (C1 → C2)

```yaml
C1_to_C2:
  status: LOCKED
  required_artifacts:
    - PIN-220 (C2 Entry Conditions)
  explicit_unlock_phrase: "C2 entry conditions approved"
```

### Anti-Drift Rules

- No "temporary" bypass of principles
- No experimental code outside phase gates
- If a change feels "obviously fine", re-check principles
- Redis convenience must never become Redis dependency

---

## CUSTOMER CONSOLE GOVERNANCE (v1 FROZEN)

**Status:** FROZEN
**Effective:** 2025-12-29
**Scope:** console.agenticverz.com
**Reference:** `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`

### Claude's Role: Auditor and Mapper, Not Designer

Claude provides **evidence**, not **authority**. Findings must be:
- Presented as observations, not decisions
- Subject to human review before action
- Never auto-applied

### Frozen Domains (v1)

The following five domains are frozen and must not be renamed, merged, or modified:

| Domain | Question | Object Family |
|--------|----------|---------------|
| **Overview** | Is the system okay right now? | Status, Health, Pulse |
| **Activity** | What ran / is running? | Runs, Traces, Jobs |
| **Incidents** | What went wrong? | Incidents, Violations, Failures |
| **Policies** | How is behavior defined? | Rules, Limits, Constraints, Approvals |
| **Logs** | What is the raw truth? | Traces, Audit, Proof |

### Sidebar Structure

```
┌─────────────────────────────┐
│ CORE LENSES (Sidebar)       │
│   Overview                  │
│   Activity                  │
│   Incidents                 │
│   Policies                  │
│   Logs                      │
├─────────────────────────────┤
│ CONNECTIVITY (Sidebar)      │
│   Integrations              │
│   API Keys                  │
└─────────────────────────────┘

┌─────────────────────────────┐
│ ACCOUNT (Secondary - Top-right or Footer)
│   ▸ Projects                │
│   ▸ Users                   │
│   ▸ Profile                 │
│   ▸ Billing                 │
│   ▸ Support                 │
└─────────────────────────────┘
```

**Account is NOT a domain.** It manages *who*, *what*, and *billing* — not *what happened*.
Account pages must NOT display executions, incidents, policies, or logs.

### Orders (Epistemic Depth)

| Order | Meaning | Invariant |
|-------|---------|-----------|
| O1 | Summary / Snapshot | Scannable, shallow, safe entry |
| O2 | List of instances | "Show me instances" |
| O3 | Detail / Explanation | "Explain this thing" |
| O4 | Context / Impact | "What else did this affect?" |
| O5 | Raw records / Proof | "Show me proof" |

**Rule:** Sidebar never changes with order depth.

### Jurisdiction

| Console | Scope | Data Boundary |
|---------|-------|---------------|
| Customer Console | Single tenant | Tenant-isolated |
| Founder Console | Cross-tenant | Founder-only |
| Ops Console | Infrastructure | Operator-only |

### Project Scope (v1.1.0)

All Customer Console views are evaluated within a selected **Project context**.

**Key Rules:**
- Project is a **global scope selector** (in header, not sidebar)
- Projects are **not domains** and must not appear in sidebar
- Switching Projects changes **data scope only**, not navigation structure
- Cross-project aggregation is **forbidden** in Customer Console

**Shared Resources:**
| Resource | Scope Rule |
|----------|------------|
| Policies | May be ORG-scoped (all projects) or PROJECT-scoped |
| Agents | May be bound to multiple projects |
| Executions | Always project-scoped |
| Incidents | Attach to executions → always project-scoped |

### What Claude Can Do (Console Work)

- Validate existence of objects/flows in codebase
- Report fits, gaps, partial fits, violations
- Map existing code to approved domains/topics
- Generate drafts for human review
- Flag deviations explicitly

### What Claude Cannot Do (Console Work)

- Introduce new domains
- Rename frozen domains
- Mix customer and founder jurisdictions
- Suggest automation or learned authority
- Auto-apply structural changes
- "Improve" without explicit approval

### Forbidden Actions (Console)

| Action | Reason |
|--------|--------|
| Rename frozen domains | Breaks mental model |
| Add new domains without amendment | Repositioning risk |
| Merge domains | Collapses distinct questions |
| Mix jurisdictions | Data boundary violation |
| Auto-apply learned patterns | Governance violation |

### Deviation Protocol

1. Explicitly flag what deviates
2. Clearly justify with evidence
3. Do NOT apply automatically
4. Require human approval

**Failure Mode to Avoid:** "Claude-suggested improvement" that silently mutates product identity.

---

## PHASE C GUIDANCE (ACTIVE)

**Status:** ACTIVE
**Date:** 2025-12-27
**Reference:** PIN-208 (Phase C Discovery Ledger), PIN-209 (Claude Assumption Elimination)

### Core Principle: Phase C is for Listening, Not Acting

> **Phase C is for listening, not acting.**
> **Acting too early destroys signal.**

### What This Means

- **Observe First:** Discovery ledger collects signals passively
- **Don't Enforce Yet:** DPC/PLC checks emit warnings, not blockers
- **Preserve Signal Quality:** Acting on incomplete data destroys information
- **Let Patterns Emerge:** Eligibility patterns become visible through observation

### Phase C Enforcement Modes

| System | Mode | Behavior |
|--------|------|----------|
| Discovery Ledger | LOAD_DETECT_PROPOSE | Observes, records, proposes |
| DPC (Discovery Presence Check) | WARNING | Warns if artifact missing discovery entry |
| PLC (Promotion Legitimacy Check) | WARNING | Warns if status = 'observed' |
| DPCC | BLOCKER | Blocks code without discovery precedence |
| CSEG | BLOCKER | Blocks scope expansion without eligibility |

### Phase C → Phase D Transition

Phase D will promote warnings to blockers:
- `visibility_lifecycle: LOAD_ENFORCE`
- `promotion_at_boundary: true`
- Full enforcement of DPC and PLC

Until then, listen and learn.

---

## PHASE A.5 CLOSURE: TRUTH-GRADE SYSTEM CERTIFIED

**Status:** CLOSED (Constitutional)
**Date:** 2025-12-26
**Reference:** `docs/PHASE_A5_CLOSURE.md`

### What This Means

AgenticVerz is now a **truth-grade system**:

> **The system cannot lie — accidentally or intentionally — about execution, cost, policy, failure, memory, or history.**

### Certified Guarantees (S1–S6)

| Gate | Guarantee | Status |
|------|-----------|--------|
| S1 | Execution facts propagate correctly | ACCEPTED |
| S2 | Costs are computed, persisted, never inferred | ACCEPTED |
| S3 | Policy violations are facts, not interpretations | ACCEPTED |
| S4 | The system tells the truth about its own failures | ACCEPTED |
| S5 | Memory is explicit, persisted, and eligible | ACCEPTED |
| S6 | Traces are immutable, ordered, and replay-faithful | ACCEPTED (constitutional) |

### What Phase B CANNOT Do

Phase B (Resilience, Recovery, Optimization) **may not**:

- Rewrite history
- "Fix" past traces
- Infer missing facts
- Retry failures silently
- Trade correctness for performance

> **Truth is fixed. Only behavior may change.**

### Key Invariants (Mechanically Enforced)

- `LESSONS_ENFORCED.md` — 15 invariants, all enforced by code or CI
- Database triggers reject trace mutation
- `emit_traces=False` is the replay default (cannot emit during audit)
- `ON CONFLICT DO NOTHING` — first truth wins

---

## SYSTEM CONTRACTS (GOVERNANCE FRAMEWORK)

**Status:** PHASE 3 COMPLETE - Contracts locked, M0-M27 classified

### Contract-First Development

All future work must align to these four contracts:

| Order | Contract | Question |
|-------|----------|----------|
| 1 | PRE-RUN | What must the system declare before execution starts? |
| 2 | CONSTRAINT | What constraints apply, and how are they enforced? |
| 3 | DECISION | What decisions must be surfaced when the system chooses a path? |
| 4 | OUTCOME | How do we reconcile what happened with what was promised? |

### Contract Gate Rule (MANDATORY)

Before any new scenario or feature:

```
1. Which contract does this exercise?
2. Which obligation does it test?
3. Is this a new obligation or an existing one?
```

If these cannot be answered, the work is rejected.

### No Code Without Contract

> **No code, no UI, no refactor is allowed unless you can name the contract obligation it satisfies.**

### Contract Files

| File | Purpose |
|------|---------|
| `docs/contracts/INDEX.md` | Contract index and status |
| `docs/contracts/PRE_RUN_CONTRACT.md` | Intent declarations |
| `docs/contracts/CONSTRAINT_DECLARATION_CONTRACT.md` | Constraint enforcement |
| `docs/contracts/DECISION_RECORD_CONTRACT.md` | Decision surfacing |
| `docs/contracts/OUTCOME_RECONCILIATION_CONTRACT.md` | Outcome verification |
| `docs/contracts/COVERAGE_MATRIX.md` | Ledger-to-contract mapping |
| `docs/contracts/M0_M27_CLASSIFICATION.md` | Milestone classification |
| `docs/contracts/OBLIGATION_DELTAS.md` | Proposed contract evolutions |

### Phase Status

| Phase | Status |
|-------|--------|
| Phase 1: Scenario Extraction | COMPLETE (13 entries) |
| Phase 2: Contract Drafting | COMPLETE (4 contracts) |
| Phase 3: M0-M27 Mapping | COMPLETE (27 milestones, 2 deltas) |
| Phase 4: Implementation | READY |

### Key Metrics

- 93% of M0-M27 collapsed into existing obligations
- 2 new obligations identified (decision_source, decision_trigger)
- 13 consecutive milestones without new obligation (stabilized)

**Reference:** `docs/contracts/INDEX.md`
**Ledger:** `docs/SYSTEM_TRUTH_LEDGER.md` (13 entries)

---

## Session Start Protocol (MANDATORY)

Before ANY work, run the hygiene check:

```bash
./scripts/ops/session_start.sh
```

This verifies:
- Working environment exists
- No stale checklists
- Services are healthy
- No blocking issues

Then read in order:
1. `agentiverz_mn/repo_snapshot.md` - Current state
2. `agentiverz_mn/milestone_plan.md` - What we're building
3. Pick the relevant checklist for your task

---

## Truth Preflight (MANDATORY)

Before executing or suggesting any verification scenario (S2–S6), you MUST:

1. Confirm that the CI job "Truth Preflight Gate" has passed.
2. If CI evidence is not provided, you must STOP and respond:
   > "Truth preflight not verified. Execution blocked."

You are NOT allowed to:
- Bypass this requirement
- Simulate results
- Assume preflight success
- Suggest proceeding "temporarily"

### Enforcement

Truth preflight is enforced mechanically by CI:
- **CI Job:** `.github/workflows/truth-preflight.yml`
- **Script:** `scripts/verification/truth_preflight.sh`
- **PINs:** PIN-193 (S1), PIN-194 (S2)

This instruction exists to prevent reasoning on an untrusted system.

### Operating Rule

> **No Truth Preflight → No Scenario → No Acceptance → No Merge**

See `docs/OPERATING_RULES.md` for the full operating contract.

---

## Python Execution Invariant (MANDATORY)

All Python commands MUST follow these rules:

1. **Working Directory:** Run from `backend/`, never from repo root
2. **Package Root:** `app/` is the root package
3. **Imports:** Use absolute imports (`from app.db import ...`)
4. **Environment:** `DATABASE_URL` required for execution, NOT for imports

### Canonical Command Pattern

```bash
cd backend && DATABASE_URL=... python3 -m app.module
```

### If Import Fails

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'app'` | Wrong CWD | `cd backend` first |
| `RuntimeError: DATABASE_URL...` | Missing env var | Export DATABASE_URL |
| `ImportError: attempted relative import` | Relative import | Convert to absolute |

### Enforcement

- **CI Job:** `.github/workflows/import-hygiene.yml`
- **Contract:** `backend/PYTHON_EXECUTION_CONTRACT.md`

If these conditions are not met, **STOP** and fix before proceeding.

---

## Quick Start for AI Assistants

| Resource | Location | Purpose |
|----------|----------|---------|
| Memory PIN Index | `docs/memory-pins/INDEX.md` | Project status dashboard |
| M8 Working Environment | `agentiverz_mn/` | Focused context files |
| Current Roadmap | `docs/memory-pins/PIN-033-m8-m14-machine-native-realignment.md` | M8-M14 plan |

---

## Project Summary

**AOS (Agentic Operating System)** - The most predictable, reliable, deterministic SDK for building machine-native agents.

### Mission Statement
> AOS is the most predictable, reliable, deterministic SDK for building machine-native agents — with skills, budgets, safety, state management, and observability built-in.

### What "Machine-Native" Means
- Designed for agents to operate efficiently, not humans to babysit
- Queryable execution context (not log parsing)
- Capability contracts (not just tool lists)
- Structured outcomes (never throws exceptions)
- Failure as data (navigable, not opaque)
- Pre-execution simulation
- Resource contracts declared upfront

---

## Current Phase

**M0-M28 Complete → Contract Governance Active**

### Milestone Status

| Milestone | Status |
|-----------|--------|
| M0-M28 | ✅ COMPLETE (94% utilization score) |
| Contract Framework | ✅ COMPLETE (Phase 1-3) |
| Phase 4: Implementation | ⏳ READY |

### Contract-Driven Development

All future work follows the contract framework:
1. Identify which contract the work exercises
2. Verify obligation coverage
3. Propose delta if new obligation needed
4. Implement only after contract alignment

See `docs/contracts/INDEX.md` for contract status.

---

## Tech Stack

- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Worker:** ThreadPoolExecutor with graceful shutdown
- **Observability:** Prometheus + Alertmanager + Grafana
- **Container:** Docker Compose with host networking
- **LLM:** Anthropic Claude (claude-sonnet-4-20250514)
- **Connection Pool:** PgBouncer (port 6432)

---

## Key Directories

```
/root/agenticverz2.0/
├── agentiverz_mn/           # M8+ working environment (START HERE)
│   ├── repo_snapshot.md     # Current state
│   ├── milestone_plan.md    # M8-M14 roadmap
│   ├── auth_blocker_notes.md
│   ├── demo_checklist.md
│   ├── sdk_packaging_checklist.md
│   └── auth_integration_checklist.md
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── api/             # API routers
│   │   ├── auth/            # RBAC (uses stub - needs real auth)
│   │   ├── skills/          # 5 production skills
│   │   ├── worker/runtime/  # Machine-native runtime
│   │   ├── workflow/        # Workflow engine
│   │   └── costsim/         # Cost simulation V2
│   └── cli/aos.py           # CLI tool
├── sdk/
│   ├── python/              # Python SDK (10/10 tests, needs packaging)
│   └── js/                  # JS SDK (needs types, machine-native methods)
├── docs/
│   ├── memory-pins/         # 168+ PINs (project memory)
│   ├── contracts/           # System contracts (governance framework)
│   ├── test_reports/        # Test reports + REGISTER.md
│   └── API_WORKFLOW_GUIDE.md
├── scripts/
│   └── ops/
│       ├── session_start.sh   # Run before each session
│       ├── hygiene_check.sh   # Weekly automated check
│       ├── memory_trail.py    # Auto-create PINs & test reports
│       ├── artifact_lookup.py # Search codebase registry artifacts
│       └── change_record.py   # Create code change records
└── monitoring/
```

---

## Services

| Service | Port | Status |
|---------|------|--------|
| nova_agent_manager | 8000 | Backend API |
| nova_worker | - | Run executor |
| nova_db | 5433 | PostgreSQL |
| nova_pgbouncer | 6432 | Connection pool |
| nova_prometheus | 9090 | Metrics |
| nova_alertmanager | 9093 | Alert routing |
| nova_grafana | 3000 | Dashboards |

---

## Web Server Infrastructure (Debugging Reference)

**Full docs:** `docs/infrastructure/WEB_SERVER_ARCHITECTURE.md`

**Quick Reference:**
```
INTERNET (80/443) → APACHE (main server) → serves all sites
                         │
                         └→ mail.xuniverz.com only → NGINX (127.0.0.1:8081) → iRedMail apps
```

| Server | Port | Role |
|--------|------|------|
| **Apache** | 80, 443 | Main web server (ALL external traffic) |
| **Nginx** | 127.0.0.1:8081 | Internal only (iRedMail: webmail, admin) |

**Frontend Deployment:**
```bash
cd /root/agenticverz2.0/website/app-shell
npm run build                          # Production: dist/
cp -r dist dist-preflight              # Preflight: dist-preflight/
sudo systemctl reload apache2          # Apply changes
```

**Domain → Config Mapping:**
| Domain | Apache Config | DocumentRoot |
|--------|---------------|--------------|
| console.agenticverz.com | `console.agenticverz.com.conf` | `dist/` |
| preflight-console.agenticverz.com | `preflight-console.agenticverz.com.conf` | `dist-preflight/` |

**Cache-busting:** Already configured. Browsers auto-refresh after deploy (no manual cache clear).

**Route Redirect:** `/guard/*` → `/cus/*` (301) already configured.

---

## Machine-Native APIs (Implemented)

```python
# All implemented and working
POST /api/v1/runtime/simulate      # Plan feasibility check
POST /api/v1/runtime/query         # State queries
GET  /api/v1/runtime/capabilities  # Skills, budget, rate limits
GET  /api/v1/runtime/skills/{id}   # Skill details
POST /api/v1/runs                  # Create run
GET  /api/v1/runs/{id}             # Run status
```

---

## Common Commands

```bash
# Session start (ALWAYS RUN FIRST)
./scripts/ops/session_start.sh

# Weekly hygiene check
./scripts/ops/hygiene_check.sh

# Check services
docker compose ps

# View logs
docker compose logs backend --tail 100

# Check health
curl http://localhost:8000/health

# Check capabilities
curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities

# Run tests
cd backend && PYTHONPATH=. python -m pytest tests/ -v

# Rebuild after changes
docker compose up -d --build backend worker
```

---

## Environment Variables

```bash
# Key variables (in .env)
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
REDIS_URL=redis://localhost:6379/0
AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf
AUTH_SERVICE_URL=http://localhost:8001  # STUB - needs real auth for M8
RBAC_ENABLED=true
RBAC_ENFORCE=true
```

---

## Key Memory PINs

| PIN | Topic | Status |
|-----|-------|--------|
| PIN-170 | System Contract Governance Framework | ACTIVE (Phase 1-3 complete) |
| PIN-167 | Final Review Tasks Phase 1 | COMPLETE (6 scenarios, visibility gaps) |
| PIN-163 | M0-M28 Utilization Report | REFERENCE (94% score) |
| PIN-122 | Master Milestone Compendium M0-M21 | REFERENCE |
| PIN-005 | Machine-Native Architecture | PRIMARY (vision) |
| PIN-120 | Test Suite Stabilization & Prevention | COMPLETE (PREV-1 to PREV-12) |
| PIN-125 | SDK Cross-Language Parity | COMPLETE (PREV-16 to PREV-19) |

---

## Mypy Technical Debt (PIN-121)

**Baseline:** 572 errors in 118 files (known limitation)

### Error Categories
- SQLModel `table=True` keyword (27) - Known limitation, low priority
- None + operator issues (14) - P1, genuine bugs
- Type assignment mismatches (13) - P2, gradual fix
- SQLAlchemy `Base` inheritance (8) - False positive

### Prevention Mechanisms
| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-13 | Mypy pre-commit (warning mode) | `.pre-commit-config.yaml` |
| PREV-14 | CI mypy step (non-blocking) | `.github/workflows/ci.yml` |
| PREV-15 | Postflight mypy category | `postflight.py` |

### Commands
```bash
# Run mypy on changed files
mypy backend/app/ --ignore-missing-imports --show-error-codes

# Skip mypy for commits with known issues
SKIP=mypy git commit -m "message"

# Check postflight mypy category
./scripts/ops/postflight.py --category mypy
```

See PIN-121 for full remediation plan and root cause analysis.

---

## SDK Cross-Language Parity (PIN-125)

**Status:** Python and JS SDKs must produce identical deterministic hashes.

### Hash Algorithm (MUST match in both SDKs)

```
1. base_string = f"{seed}:{timestamp}:{tenant_id}"
2. chain_hash = SHA256(base_string).hexdigest()
3. For each step:
   a. step_payload = canonical_json(deterministic_payload)
   b. step_hash = SHA256(step_payload).hexdigest()
   c. combined = f"{chain_hash}:{step_hash}"  # COLON SEPARATOR
   d. chain_hash = SHA256(combined).hexdigest()
4. root_hash = chain_hash
```

### Prevention Mechanisms
| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-16 | SDK Export Verification | `postflight.py` sdkparity check |
| PREV-17 | Cross-Language Parity Pre-Commit | `postflight.py` sdkparity check |
| PREV-18 | SDK Build Freshness | `preflight.py` + CI workflow |
| PREV-19 | Hash Algorithm Parity Test | CI workflow parity tests |

### Common Issues (Fixed in PIN-125)

1. **Hash Chain Separator**: Must use colon `:` between hashes
   - ❌ `currentHash + stepHash` (wrong)
   - ✅ `${currentHash}:${stepHash}` (correct)

2. **ES Modules vs CommonJS**: JS scripts must use CommonJS
   - ❌ `import fs from "fs"` (wrong in non-module package)
   - ✅ `const fs = require("fs")` (correct)

3. **Missing SDK Exports**: JS dist/ must export all functions
   - Run `npm run build` after any SDK changes

### Commands
```bash
# Build JS SDK (always do this after changes)
cd sdk/js/aos-sdk && npm run build

# Run local parity check
python3 -c "from aos_sdk import Trace, RuntimeContext; ..."  # Generate trace
node sdk/js/aos-sdk/scripts/compare_with_python.js /tmp/trace.json

# Run postflight SDK parity check
./scripts/ops/postflight.py --category sdkparity

# Run preflight SDK build check
./scripts/ops/preflight.py --full
```

See PIN-125 for full root cause analysis and fix details.

---

## Hygiene Scripts

### session_start.sh
Run at the start of every session:
- Checks working environment
- Shows current phase
- Lists blockers
- Verifies services

### hygiene_check.sh
Run weekly (or via cron):
- Detects stale files
- Checks PIN count
- Validates INDEX.md freshness
- Flags completed checklists
- `--fix` mode for auto-cleanup
- `--json` mode for CI

---

## Session Workflow

1. **Start:** `./scripts/ops/session_start.sh`
2. **Read:** `agentiverz_mn/repo_snapshot.md`
3. **Plan:** Check `milestone_plan.md`
4. **Work:** Use relevant checklist
5. **Update:** Mark checklist items complete
6. **End:** Update `repo_snapshot.md` if major changes

---

## Memory Trail Automation (MANDATORY)

After completing any significant job, **ALWAYS** use the memory trail workflow.

### ⚠️ CRITICAL: Find First, Update Existing, Create Only for NEW

**DO NOT** create new PINs for work related to existing topics. Instead:

1. **FIND** existing PINs first
2. **UPDATE** if a related PIN exists
3. **CREATE** only for genuinely NEW topics

```bash
# STEP 1: Always search first
python scripts/ops/memory_trail.py find "ops console"
python scripts/ops/memory_trail.py find 111

# STEP 2: Update existing PIN (PREFERRED)
python scripts/ops/memory_trail.py update 111 \
    --section "Updates" \
    --content "Added customers panel with sort controls..."

# STEP 3: Only create NEW PIN if no related PIN exists
python scripts/ops/memory_trail.py pin \
    --title "Completely New Feature" \
    --category "Category" \
    --summary "Description"
```

### When to Update vs Create

| Situation | Action | Example |
|-----------|--------|---------|
| Adding panel to existing console | **UPDATE** existing console PIN | Update PIN-111 |
| Bug fix in existing feature | **UPDATE** that feature's PIN | Update PIN-XXX |
| Enhancement to existing feature | **UPDATE** that feature's PIN | Update PIN-XXX |
| Brand new feature/system | **CREATE** new PIN | Create new |
| New milestone (M25, M26...) | **CREATE** new PIN | Create new |
| Test run completed | **CREATE** Test Report | TR-XXX |

### Find Existing PINs

```bash
# Search by keyword
python scripts/ops/memory_trail.py find "ops console"
python scripts/ops/memory_trail.py find "stickiness"

# Search by PIN number
python scripts/ops/memory_trail.py find 111

# Output shows matching PINs with titles and paths
```

### Update Existing PIN (PREFERRED)

```bash
python scripts/ops/memory_trail.py update 111 \
    --section "Updates" \
    --content "## 2025-12-20: Added Customers Panel

- Added CustomersPanel component
- Changed layout to 2x2 grid
- Wired /ops/customers endpoint"

# Optionally update status
python scripts/ops/memory_trail.py update 111 \
    --section "Updates" \
    --content "..." \
    --status "ENHANCED"
```

### Create New PIN (Only for NEW Topics)

```bash
# Basic usage
python scripts/ops/memory_trail.py pin \
    --title "Feature Name" \
    --category "Category / Subcategory" \
    --status "COMPLETE" \
    --summary "Brief description of what was done" \
    --content "Detailed markdown content"

# With milestone and related PINs
python scripts/ops/memory_trail.py pin \
    --title "M24 Feature" \
    --category "Ops Console / Feature" \
    --milestone "M24 Phase-2" \
    --status "COMPLETE" \
    --summary "Summary here" \
    --related 110 111 \
    --commits "abc123" "def456"

# From file (for complex content)
python scripts/ops/memory_trail.py pin \
    --title "Big Feature" \
    --category "Architecture" \
    --from-file /tmp/pin_content.md
```

### Create a Test Report

```bash
python scripts/ops/memory_trail.py report \
    --title "Test Name" \
    --type "Integration" \
    --status "PASS" \
    --run-id "uuid-here" \
    --tokens 5000 \
    --findings "Key findings summary"

# With gaps identified
python scripts/ops/memory_trail.py report \
    --title "Adversarial Test" \
    --type "Adversarial" \
    --status "GAPS" \
    --gaps "Issue 1" "Issue 2"
```

### Check Next Available IDs

```bash
python scripts/ops/memory_trail.py next
# Output:
# 📌 Next PIN number: PIN-113
# 📋 Next Test Report number: TR-006
```

---

## Artifact Lookup (Registry Search)

Search and inspect the codebase registry artifacts (112 registered).

### Quick Commands

```bash
# Search by name
python scripts/ops/artifact_lookup.py KeysPage

# Search by artifact ID
python scripts/ops/artifact_lookup.py --id AOS-FE-AIC-INT-002

# Filter by product
python scripts/ops/artifact_lookup.py --product ai-console

# Filter by type
python scripts/ops/artifact_lookup.py --type service

# Filter by authority level
python scripts/ops/artifact_lookup.py --authority mutate

# Combine filters
python scripts/ops/artifact_lookup.py --product ai-console --type page

# Verbose output (full details)
python scripts/ops/artifact_lookup.py KeysPage -v

# List all artifacts
python scripts/ops/artifact_lookup.py --list
```

### Filter Options

| Option | Values | Description |
|--------|--------|-------------|
| `--product` | `ai-console`, `system-wide`, `product-builder` | Filter by product |
| `--type` | `api-route`, `service`, `worker`, `page`, `script`, `library`, `sdk-package` | Filter by artifact type |
| `--authority` | `observe`, `advise`, `enforce`, `mutate` | Filter by authority level |
| `--id` | Artifact ID | Search by ID (partial match) |
| `-v` | - | Verbose output with responsibilities and notes |

### Registry Location

- Artifacts: `docs/codebase-registry/artifacts/*.yaml`
- Changes: `docs/codebase-registry/changes/*.yaml`
- Schema: `docs/codebase-registry/schema-v1.yaml`
- Change Schema: `docs/codebase-registry/change-schema-v1.yaml`
- Survey PIN: PIN-237

---

## Code Registration Governance (ENFORCED)

**Status:** ACTIVE
**Effective:** 2025-12-29
**Reference:** SESSION_PLAYBOOK.yaml Section 20, CODE_EVOLUTION_CONTRACT.md

### Governing Principle

> All executable or semantically meaningful code MUST be registered in the Codebase Purpose & Authority Registry before it can be created, modified, or reasoned about.
> Claude must not infer purpose, ownership, or relationships where they are not explicitly registered.
> Code evolution is authority. Authority must be declared.

### Before Creating Code

1. **Search registry**: `python scripts/ops/artifact_lookup.py <name>`
2. **If not found**: Propose a registry entry for approval
3. **Get approval**: Wait for human confirmation before writing code

### Before Modifying Code

1. **Look up artifact**: `python scripts/ops/artifact_lookup.py --id <ID>`
2. **Create change record**: In `docs/codebase-registry/changes/CHANGE-YYYY-NNNN.yaml`
3. **Required fields**:
   - `change_id`, `date`, `author`
   - `change_type` (bugfix, refactor, behavior_change, etc.)
   - `purpose` (why this change is being made)
   - `scope.artifacts_modified` (artifact IDs)
   - `impact` (authority_change, behavior_change, interface_change, data_change)
   - `risk_level`, `backward_compatibility`, `validation`
4. **Get approval**: Only proceed after change record is confirmed

### File Renames (HIGH-RISK OPERATION)

**Renames are treated as HIGH-RISK operations** because they:
- Break all existing import paths
- Invalidate caller graphs
- Require updates to all dependent files
- Cannot be backward compatible

**Rename Checklist:**

1. **Create change record** with `change_type: rename`
2. **Use `files_renamed` field** (not `files_removed` + `files_added`):
   ```yaml
   scope:
     artifacts_modified:
       - AOS-XX-XXX-XXX-001
     files_renamed:
       - from: backend/app/services/old_name.py
         to: backend/app/services/new_name.py
   ```
3. **Auto-enforced constraints** (by change_record.py):
   - `risk_level` >= medium (minimum)
   - `interface_change: yes`
   - `backward_compatibility: no`
   - `manual_verification: required`
4. **Update artifact registry** (`name` field)
5. **Update all callers** in `imported_by` relations
6. **Run full test suite** to verify no broken imports

**CLI Command:**
```bash
python scripts/ops/change_record.py create \
    --purpose "Rename X to Y for clarity" \
    --type rename \
    --artifacts AOS-XX-XXX-XXX-001 \
    --files-renamed "old/path.py:new/path.py"
```

### Blocking Rules

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| CODE-REG-001 | Registration Required for Code Existence | BLOCKING |
| CODE-REG-002 | Purpose and Semantic Clarity Required | BLOCKING |
| CODE-REG-003 | Product and Surface Traceability | BLOCKING |
| CODE-REG-004 | Pause on Unclear Relationships | MANDATORY |
| CODE-CHANGE-001 | Change Registration Required | BLOCKING |
| CODE-CHANGE-002 | Pause on Unregistered Code Change | MANDATORY |
| CODE-CHANGE-003 | Artifact-Change Traceability | BLOCKING |

### What Claude Cannot Do

- Create code without registry entries
- Modify code without change records
- Infer purpose from filenames alone
- Guess authority based on behavior
- Assume "minor" changes don't need registration
- Auto-generate change records without approval

### What Claude Must Do

- Always check registry first before reasoning about code
- Stop and ask when relationships are unclear
- Create change records before modifications
- Link artifacts to change records
- Wait for approval before proceeding

### Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│           CODE REGISTRATION DISCIPLINE                      │
├─────────────────────────────────────────────────────────────┤
│  1. SEARCH: artifact_lookup.py <name>                       │
│  2. IF NOT FOUND: Propose registration, wait for approval   │
│  3. IF MODIFYING: Create change record first                │
│  4. IF UNCLEAR: Stop and ask for clarification              │
│  5. NEVER INFER: Purpose, authority, or relationships       │
└─────────────────────────────────────────────────────────────┘
```

---

## Product Boundary Enforcement (ENFORCED)

**Status:** ACTIVE
**Effective:** 2025-12-29
**Reference:** SESSION_PLAYBOOK.yaml Section 21, PRODUCT_BOUNDARY_CONTRACT.md

### Prime Invariant

> **No code artifact may be created, modified, or reasoned about unless ALL of the following are declared and accepted:**
>
> 1. Product ownership (ai-console / system-wide / product-builder)
> 2. Invocation ownership (who calls this?)
> 3. Boundary classification (surface / adapter / platform)
> 4. Failure jurisdiction (what breaks if this is removed?)

If ANY are unknown → **STOP and ask for clarification**.

### The Three Blocking Questions

Before creating or modifying code, Claude MUST answer:

| Question | Unacceptable Answers |
|----------|---------------------|
| **Who calls this in production?** | "Not sure", "Later", "Probably" |
| **What breaks if AI Console is deleted?** | "I don't know", "Everything" |
| **Who must NOT depend on this?** | "Anyone can use it", "No restrictions" |

If ANY answer is uncertain → **BLOCK**.

### Bucket Classification

Every artifact MUST be classified:

| Bucket | Definition | Criteria |
|--------|------------|----------|
| **Surface** | User-facing, product-specific | Only product UI/routes call it |
| **Adapter** | Thin translation layer | < 200 LOC, no business logic, no state mutation |
| **Platform** | Shared infrastructure | Workers, SDK, or multiple products call it |
| **Orphan** | No production callers | ILLEGAL - integrate or delete |

### Invocation Ownership Rule

**Labels lie. Callers don't.**

An artifact is NOT ai-console owned if:
- Workers call it
- SDK imports it
- Other consoles depend on it
- External APIs use it

### Blocking Rules

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| BOUNDARY-001 | Artifact Registration Before Code | BLOCKING |
| BOUNDARY-002 | Three Blocking Questions | BLOCKING |
| BOUNDARY-003 | No Silent Assumptions | BLOCKING |
| BOUNDARY-004 | Bucket Classification Required | BLOCKING |
| BOUNDARY-005 | Invocation Ownership Rule | BLOCKING |

### Boundary Violation Types

| Type | Definition | Resolution |
|------|------------|------------|
| BV-001 | Mislabeled Product | Reclassify to correct product |
| BV-002 | Adapter Creep | Split or promote to platform |
| BV-003 | Orphan Existence | Integrate or delete |
| BV-004 | Dual-Surface Hazard | Split into facades + shared core |
| BV-005 | Silent Platform Dependency | Make explicit or restructure |

### Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│           PRODUCT BOUNDARY DISCIPLINE                        │
├─────────────────────────────────────────────────────────────┤
│  1. DECLARE: Product, bucket, callers, failure scope        │
│  2. ANSWER: Three blocking questions (no "probably")        │
│  3. CLASSIFY: Surface / Adapter / Platform                  │
│  4. VERIFY: Caller graph matches label                      │
│  5. NEVER ASSUME: Product from filename or directory        │
└─────────────────────────────────────────────────────────────┘
```

---

## Change Record Helper

Create and manage code change records for evolution tracking.

### Quick Commands

```bash
# Get next available change ID
python scripts/ops/change_record.py next

# List all change records
python scripts/ops/change_record.py list

# Show specific change record
python scripts/ops/change_record.py show CHANGE-2025-0001

# Create a bugfix change record
python scripts/ops/change_record.py create \
    --purpose "Fix API key validation error" \
    --type bugfix \
    --artifacts AOS-BE-API-INT-001 \
    --risk low

# Create a refactor change record (multiple artifacts)
python scripts/ops/change_record.py create \
    --purpose "Refactor incident aggregation for performance" \
    --type refactor \
    --artifacts AOS-BE-SVC-INC-001 AOS-BE-API-INC-001 \
    --risk medium \
    --behavior-change no

# Create a feature change record (with all options)
python scripts/ops/change_record.py create \
    --purpose "Add new endpoint for metrics export" \
    --type feature \
    --artifacts AOS-BE-API-MET-001 \
    --author pair \
    --risk low \
    --behavior-change yes \
    --interface-change yes \
    --tests-added yes \
    --files-added backend/app/api/metrics_export.py \
    --related-pins PIN-123 \
    --notes "Part of M30 observability milestone"
```

### Change Types

| Type | When to Use |
|------|-------------|
| `bugfix` | Fixing a bug |
| `refactor` | Restructuring without behavior change |
| `behavior_change` | Changing observable behavior |
| `performance` | Optimization work |
| `security` | Security fixes or improvements |
| `cleanup` | Code cleanup, removing dead code |
| `test_only` | Test additions/changes only |
| `documentation` | Documentation changes |
| `feature` | New feature addition |
| `deprecation` | Deprecating functionality |

### Required vs Optional Fields

**Required (CLI enforces):**
- `--purpose` - Why this change is being made
- `--type` - Change type from list above
- `--artifacts` - Artifact IDs being modified

**Optional (with defaults):**
- `--author` (default: pair)
- `--risk` (default: low)
- `--behavior-change` (default: no)
- `--interface-change` (default: no)
- `--data-change` (default: no)
- `--authority-change` (default: none)
- `--backward-compat` (default: yes)
- `--tests-added` (default: no)
- `--tests-modified` (default: no)
- `--manual-verification` (default: not_required)
- `--files-added`, `--files-removed`, `--related-pins`, `--notes`

---

### What Gets Updated Automatically

1. **PIN Creation:**
   - Creates `docs/memory-pins/PIN-XXX-title.md`
   - Updates `docs/memory-pins/INDEX.md` (Last Updated, Active PINs table, Changelog)

2. **Test Report Creation:**
   - Creates `docs/test_reports/TR-XXX_TITLE_DATE.md`
   - Updates `docs/test_reports/REGISTER.md` (Test Report Index, Changelog)

### Categories Reference

| Category | When to Use |
|----------|-------------|
| `Ops Console / Feature` | Ops console features |
| `Frontend / UI` | UI components |
| `Infrastructure / Automation` | Systemd, cron, schedulers |
| `Milestone / Completion` | Major milestone completion |
| `Bug Fix / Feature` | Bug fixes |
| `Testing / Verification` | Test infrastructure |
| `Developer Tooling / CI` | Dev tools, CI/CD |

---

## Notes

- Host networking required (systemd-resolved + Tailscale)
- Backend publicly accessible on 0.0.0.0:8000
- Auth currently uses STUB - must wire real provider before beta
- PgBouncer on 6432, not direct Postgres on 5433
- All sensitive tokens in `.env` (not committed)
