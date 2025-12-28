# PIN-209: Claude Assumption Elimination

**Status:** FROZEN
**Date:** 2025-12-27
**Category:** Infrastructure / Agent Governance
**Phase:** C

---

## Purpose

Prevent Claude from inventing architecture by making forbidden assumptions explicit and machine-enforced.

**Truth Anchor:**
> LLMs fail where constraints are implicit.
> Make the implicit illegal, and the failures disappear.

---

## Problem Statement

Claude naturally fills missing structure with defaults:
- "Console → API prefix" (wrong: subdomain + auth)
- "Local scripts → localhost DB" (wrong: split-brain)
- "Reuse app.db because it exists" (wrong: coupling)

This is not fixable by "being careful". It is fixable only by making forbidden assumptions explicit and mechanically enforced.

---

## Core Principle

> **Claude must not invent architecture.**
> If something is not explicitly declared, it must be treated as UNKNOWN and BLOCKED.

---

## Solution: Assumption Elimination via Playbook Guards

### 1. Forbidden Assumptions (FA-001 to FA-006)

| ID | Name | Description |
|----|------|-------------|
| FA-001 | api_prefix_based_console_separation | Assuming consoles separated by API prefix |
| FA-002 | localhost_database_fallback | Using localhost as default |
| FA-003 | app_db_import_outside_backend_runtime | Importing app.db in scripts |
| FA-004 | implicit_environment_detection | Inferring config from environment markers |
| FA-005 | data_partitioned_by_console | Assuming consoles see different data |
| FA-006 | visibility_without_discovery | Exposing UI without discovery entry |

**Enforcement:** If Claude introduces any forbidden assumption → Response INVALID

### 2. Negative Design Rules (NDR-001 to NDR-006)

| ID | Rule | Reason |
|----|------|--------|
| NDR-001 | Database must never encode visibility logic | Visibility is declarative |
| NDR-002 | Validators must never import backend modules | Prevents split-brain |
| NDR-003 | Discovery must never mutate execution data | Discovery observes only |
| NDR-004 | Consoles must never be inferred from routes | Subdomain + auth model |
| NDR-005 | Scripts must never have default DB URLs | Prevents split-brain |
| NDR-006 | Historical data must never be mutated | Truth-grade immutability |

### 3. Authority Declaration (Required)

For any system-level change, Claude must declare:

```
AUTHORITY_DECLARATION
- Data truth source: [Neon DB / Local DB / explicit]
- Access control source: [Auth audience / visibility_contract.yaml]
- Visibility source: [visibility_contract.yaml]
- Phase rules source: [SESSION_PLAYBOOK.yaml]
- Database contract: [database_contract.yaml]
```

### 4. Upgraded Self-Audit

```
SELF-AUDIT
- Did I verify current DB and migration state? YES / NO
- Did I read memory pins and lessons learned? YES / NO
- Did I introduce new persistence? YES / NO
- Did I risk historical mutation? YES / NO
- Did I assume any architecture not explicitly declared? YES / NO
- Did I reuse backend internals outside runtime? YES / NO
- Did I introduce an implicit default (DB, env, routing)? YES / NO
- If YES to last three → response is INVALID, must redesign
```

### 5. Database Contract

New contract: `docs/contracts/database_contract.yaml`

Key rules:
- DATABASE_URL must be explicitly set (no fallback)
- Scripts must not import from app.db
- No localhost default
- Same DB for backend and scripts

---

## Files Created/Modified

| File | Change |
|------|--------|
| `docs/contracts/database_contract.yaml` | NEW - DB access rules |
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | Added FA, NDR, authority, self-audit |

---

## Implementation Details

### SESSION_PLAYBOOK.yaml Changes (v1.1)

1. Added `database_contract.yaml` to mandatory_load
2. Added `forbidden_assumptions` section (FA-001 to FA-006)
3. Added `negative_design_rules` section (NDR-001 to NDR-006)
4. Added `authority_declaration` requirement
5. Added `upgraded_self_audit` with self-rejection checks
6. Updated bootstrap confirmation format

### Bootstrap Confirmation (New Fields)

```yaml
- database_contract_loaded: YES
- forbidden_assumptions_acknowledged: YES
```

---

## Why This Works

Prompts fail because:
- They're advisory
- They rely on memory
- They decay over sessions

Playbook + validator works because:
- It blocks execution
- It encodes negative space
- It turns architecture into law

Claude then stops being "creative" in places where creativity is dangerous.

---

## Validation

```bash
# Verify playbook loads correctly
cat docs/playbooks/SESSION_PLAYBOOK.yaml | grep -A 50 "forbidden_assumptions"

# Verify database contract exists
cat docs/contracts/database_contract.yaml

# Verify bootstrap includes new fields
grep "database_contract_loaded" docs/playbooks/SESSION_PLAYBOOK.yaml
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | Playbook with guardrails |
| `docs/contracts/database_contract.yaml` | DB access rules |
| `docs/contracts/visibility_contract.yaml` | Visibility rules |
| PIN-208 | Phase C Discovery Ledger (origin of split-brain fix) |
| PIN-206 | Session Playbook Bootstrap |

---

## Truth Anchors

- "Claude must not invent architecture."
- "If something is not explicitly declared, it must be treated as UNKNOWN."
- "LLMs fail where constraints are implicit."
- "Make the implicit illegal, and the failures disappear."

---

*Created: 2025-12-27*
*Phase: C*
*Reference: Claude Assumption Elimination / Playbook Guards*
