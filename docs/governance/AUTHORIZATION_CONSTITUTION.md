# Authorization Constitution

**Status:** RATIFIED
**Effective:** 2026-01-11
**Authority:** Founder
**Amendments:** Require explicit founder approval

---

## Preamble

This constitution establishes the permanent governance framework for authorization in the AOS system. Authorization controls WHO may do WHAT with HOW MUCH data. These rules are not guidelines — they are structural invariants that the system enforces mechanically.

**Why this exists:**

> Authorization drift killed trust silently.
> Gateway said yes, middleware said no.
> Claude guessed access levels.
> 403 errors appeared without explanation.
> Security became folklore, not fact.

This constitution makes authorization:
- **Declared** — rules exist in schema, not code
- **Mechanical** — enforcement is automatic, not discretionary
- **Observable** — violations are visible, not silent
- **Accountable** — every decision traces to a rule

---

## Article I: Core Principles

### Principle 1: Authorization is Declared, Not Inferred

> Rules MUST be declared in schema.
> Code may mirror rules temporarily, but MUST NOT invent them.
> Missing rules = BLOCKED, not guessed.

**Rationale:** Inference creates drift. Declaration creates accountability.

### Principle 2: Schema is the Single Source of Truth

> `RBAC_RULES.yaml` is the canonical authority for access rules.
> All enforcement code derives from this schema.
> No component may maintain independent access lists.

**Rationale:** Dual authority sources caused the 403 incidents we eliminated.

### Principle 3: Fail Closed, Not Open

> If a rule is missing, access is DENIED.
> If schema loading fails, access is DENIED.
> If enforcement is uncertain, access is DENIED.

**Rationale:** Security failures must be obvious, not silent.

### Principle 4: Route Access ≠ Data Access

> Reaching an endpoint does not grant unlimited query rights.
> RBAC controls WHO may touch WHAT.
> Query Authority controls HOW MUCH they may see.
> Both layers must be declared, both must be enforced.

**Rationale:** A user may reach `/api/v1/incidents/` but still be constrained to 100 rows, 7 days, no synthetic data.

### Principle 5: Production is More Restrictive Than Preflight

> Production constraints MUST be a subset of preflight constraints.
> If preflight allows X, production may allow X or less.
> If preflight denies X, production MUST deny X.

**Rationale:** Preflight is for testing. Production is for trust.

---

## Article II: Authority Layers

Authorization operates through distinct, non-overlapping layers:

| Layer | Question | Schema Location |
|-------|----------|-----------------|
| **RBAC** | WHO may touch WHAT? | `RBAC_RULES.yaml` rules |
| **Query Authority** | HOW MUCH may they see? | `query_authority` per rule |
| **SDSR** | Does the system actually behave that way? | Scenario verification |
| **UI** | What should the user be allowed to try? | Projection |

### Layer Separation Invariant

> Each layer does ONE job.
> Layers may not assume the behavior of other layers.
> Cross-layer enforcement requires explicit wiring.

---

## Article III: Access Tiers

All endpoints MUST be classified into exactly one tier:

| Tier | Description | Auth Required | Declaration |
|------|-------------|---------------|-------------|
| `PUBLIC` | Unauthenticated access | No | Explicit, rare, justified |
| `SESSION` | Authenticated user session | Yes | Default for user-facing |
| `PRIVILEGED` | Specific permission required | Yes + permissions | Must declare permissions |
| `SYSTEM` | Engine/SDSR/control-plane only | Yes + system | Preflight-only or internal |

### Tier Assignment Rules

1. **PUBLIC is exceptional** — requires justification and PIN reference
2. **SESSION is default** — any user-facing endpoint without special needs
3. **PRIVILEGED requires declaration** — must specify `required_permissions` or `required_roles`
4. **SYSTEM is internal** — never exposed to customer console

---

## Article IV: Query Authority Constraints

Every data-reading endpoint MUST declare query authority:

| Constraint | Purpose | Default |
|------------|---------|---------|
| `include_synthetic` | Synthetic/test data visible | `false` |
| `include_deleted` | Soft-deleted records visible | `false` |
| `include_internal` | Internal/system records visible | `false` |
| `max_rows` | Maximum rows per request | `100` |
| `max_time_range_days` | Maximum time range | `7` |
| `aggregation` | Aggregation level (NONE/BASIC/FULL) | `NONE` |
| `export_allowed` | Bulk export permitted | `false` |

### Aggregation Hierarchy

```
NONE < BASIC < FULL
```

Production aggregation level MUST be ≤ preflight aggregation level.

### Promotion Safety

Before promoting preflight rules to production:

| Constraint | Rule |
|------------|------|
| `include_synthetic` | MUST be `false` in production |
| `max_rows` | prod ≤ preflight |
| `max_time_range_days` | prod ≤ preflight |
| `aggregation` | prod ≤ preflight |

Violation = promotion blocked.

---

## Article V: Hard Invariants

These invariants are mechanically enforced. Violation is a system failure.

### INV-001: No Silent Auth Bypass

> Every request either matches a declared rule or is DENIED.
> There is no "default allow" path.

**Enforcement:** `strict=True` in `resolve_rbac_rule()`

### INV-002: No Inferred Access

> Claude MUST NOT classify endpoints by inference.
> Access levels come from schema, not reasoning.

**Enforcement:** Claude guardrail in SESSION_PLAYBOOK.yaml

### INV-003: No Undocumented Public Endpoint

> Every PUBLIC path has a rule with:
> - `rule_id`
> - `pin` reference
> - `description`
> - Explicit `allow_console` and `allow_environment`

**Enforcement:** CI guard `check_rbac_alignment.py`

### INV-004: No Expired Rules in Production

> Temporary rules have `expires` dates.
> Expired rules are CI failures, not warnings.

**Enforcement:** Expiry check in CI guard

### INV-005: No Schema-Code Drift

> Code-level PUBLIC_PATHS must match schema PUBLIC_PATHS.
> Discrepancies are logged and eventually blocking.

**Enforcement:** Shadow comparison logging (Phase 2A), hard block (Phase 2B)

### INV-006: No Cross-Environment Leakage

> Preflight rules do not apply to production.
> Production rules do not apply to preflight.
> Environment is explicit in every rule.

**Enforcement:** `allow_environment` field in schema

---

## Article VI: Forbidden Actions

The following actions are unconditionally forbidden:

| Action | Reason |
|--------|--------|
| Adding to PUBLIC_PATHS without schema update | Creates drift |
| Removing schema rules without removing code | Creates orphan enforcement |
| Guessing access tier from endpoint name | Inference is forbidden |
| Hardcoding bypass for "temporary" needs | Temporary becomes permanent |
| Weakening production constraints below preflight | Violates promotion safety |
| Catching and ignoring `RBACSchemaViolation` | Governance violation |
| Using `strict=False` in new code | Legacy mode only |

---

## Article VII: Required Behaviors

The following behaviors are unconditionally required:

### For Developers

1. **Read RBAC_RULES.yaml before modifying auth** — understand current rules
2. **Add new rules to schema first** — code follows schema
3. **Run CI guard before committing** — `python3 scripts/ci/check_rbac_alignment.py`
4. **Reference PINs in temporary rules** — accountability

### For Claude

1. **RBAC-001:** MUST NOT classify endpoints by inference
2. **RBAC-002:** MUST NOT modify PUBLIC_PATHS without schema update
3. **RBAC-003:** All decisions reference RBAC_RULES.yaml
4. **RBAC-004:** If no rule exists, report "RBAC RULE MISSING"

### For CI

1. Validate schema loads without error
2. Validate all PUBLIC paths have corresponding schema rules
3. Validate no temporary rules are expired
4. Validate production rules are subset of preflight

---

## Article VIII: Decision Ladders

### Adding a New Endpoint

```
1. Is endpoint in RBAC_RULES.yaml?
   └─ No → STOP. Add rule to schema first.
   └─ Yes → Continue.

2. What access tier?
   └─ PUBLIC → Requires justification + PIN reference
   └─ SESSION → Default, proceed
   └─ PRIVILEGED → Declare required_permissions
   └─ SYSTEM → Preflight-only, internal use

3. Does it read data?
   └─ Yes → Declare query_authority
   └─ No → Skip query_authority

4. Is it temporary?
   └─ Yes → Add expires date
   └─ No → Proceed
```

### Modifying Access Level

```
1. Find existing rule in RBAC_RULES.yaml
   └─ Not found → This is a new rule, use "Adding" ladder

2. Is this a tier change?
   └─ Relaxing (e.g., SESSION → PUBLIC) → Requires founder approval
   └─ Tightening (e.g., PUBLIC → SESSION) → Standard process

3. Update schema

4. Run CI guard

5. Update any mirroring code (if still in Phase 2A)
```

### Handling Missing Rule

```
1. Claude encounters endpoint not in schema

2. STOP. Do not guess.

3. Report:
   "RBAC RULE MISSING: No rule covers {method} {path}
    for console={console}, env={environment}.
    Add rule to design/auth/RBAC_RULES.yaml (PIN-391)"

4. Propose rule structure for approval

5. Wait for human decision
```

---

## Article IX: Enforcement Mechanisms

| Mechanism | Location | Mode |
|-----------|----------|------|
| Schema Loader | `rbac_rules_loader.py` | Runtime |
| CI Guard | `check_rbac_alignment.py` | Pre-merge |
| Claude Guardrail | SESSION_PLAYBOOK.yaml Section 26 | Session |
| Shadow Logging | Middleware | Observation |
| Exception on Missing | `RBACSchemaViolation` | Runtime |

### Enforcement Phases

| Phase | Behavior |
|-------|----------|
| Phase 2A (CURRENT) | Schema-driven, fallbacks exist, discrepancies logged |
| Phase 2B (FUTURE) | Fallbacks removed, schema-only enforcement |
| Phase 3 (FUTURE) | Full unification, no legacy code paths |

---

## Article X: Amendment Process

This constitution may only be amended by:

1. **Explicit founder approval** — not implicit, not delegated
2. **Written amendment** — added to this document with date
3. **PIN reference** — every amendment references a PIN

### Amendment Format

```markdown
## Amendment {N}: {Title}

**Date:** YYYY-MM-DD
**PIN:** PIN-XXX
**Approved by:** Founder

{Description of change}
```

### What Cannot Be Amended

The following are permanent and cannot be amended:

- Principle 1 (Authorization is Declared)
- Principle 3 (Fail Closed)
- INV-001 (No Silent Auth Bypass)
- INV-002 (No Inferred Access)

These are constitutional bedrock.

---

## Article XI: Canonical Artifacts

| Artifact | Location | Authority |
|----------|----------|-----------|
| RBAC Schema | `design/auth/RBAC_RULES.yaml` | Single source of truth |
| Loader | `backend/app/auth/rbac_rules_loader.py` | Runtime API |
| Query Authority | `backend/app/auth/query_authority.py` | Enforcement helpers |
| CI Guard | `scripts/ci/check_rbac_alignment.py` | Alignment validation |
| Claude Guardrail | `docs/playbooks/SESSION_PLAYBOOK.yaml` | Section 26 |
| PIN-391 | `docs/memory-pins/PIN-391-*` | RBAC Unification |
| PIN-392 | `docs/memory-pins/PIN-392-*` | Query Authority |
| This Constitution | `docs/governance/AUTHORIZATION_CONSTITUTION.md` | Governance |

---

## Signature

This constitution is ratified and effective as of the date above.

> Authorization is declared, not inferred.
> Code may mirror rules temporarily, but must not invent them.
> Drift is now visible, measurable, and attributable.
> Trust is earned, not assumed.

---

## Amendments

*No amendments yet.*
