# Claude Epistemic Safety Rules

**Status:** MANDATORY
**Effective:** 2026-01-11
**Reference:** PIN-389, SDSR System Contract, AURORA_L2

---

## Prime Directive

> **Schema is law.**
> If a schema exists, I MUST load it, reason from it, and constrain outputs to it.
> If a schema is missing, ambiguous, or not provided, I MUST stop and ask for it.
> Guessing, extrapolation, or pattern-based invention is forbidden.

---

## Why This Exists

Claude failed earlier **not because it lacked intelligence**, but because:

- It treated schema as *documentation*, not *authority*
- It inferred intent from filenames and patterns
- It "helpfully" filled gaps instead of refusing to proceed

The fix is **not** "be more careful" —
the fix is **procedural refusal unless schema is loaded and validated**.

---

## Mental Model (Internalize This)

> *"I behave like a compiler, not a co-designer."*

This reframes all interactions:
- Compilers don't guess missing tokens
- Compilers don't rename fields "for clarity"
- Compilers halt on invalid input
- Compilers produce deterministic output

---

## Mandatory Operating Protocol

Claude MUST follow these steps **in order**, every time.

### Step 0 — Declare Scope

Claude must explicitly state:
- Which file(s) it is operating on
- Which schema(s) govern those files

**If it cannot name the schema → STOP**

```
SCOPE DECLARATION
- Operating on: <file_path>
- Governing schema: <schema_name>
- Schema location: <schema_path>
```

---

### Step 1 — Load Schema (Not Optional)

Claude must do one of the following:
- Quote the schema fields it is using
- Or explicitly say: "Schema not provided — cannot proceed"

**Example (correct):**
```
Using `SDSR_OBSERVATION_SCHEMA.json`
Required fields: scenario_id, status, observed_at, capabilities_observed[]
```

**Example (forbidden):**
```
"Typically an observation would include…"
```

---

### Step 2 — Validate Before Writing

Before generating **any** output, Claude must self-check:

| Check | Question |
|-------|----------|
| Required fields | Are all required fields present? |
| Field names | Are field names exact (no synonyms)? |
| Enum values | Are enum values valid per schema? |
| Responsibilities | Is this layer allowed to write this? |

**If any check fails → refuse output**

---

### Step 3 — Write Output (Zero Creativity)

When emitting files:
- Only schema-defined fields allowed
- No inferred fields
- No renamed fields
- No "extra helpful metadata"

Claude treats schemas like **compiler headers**, not suggestions.

---

### Step 4 — Post-Write Assertion

Claude must end with a verification block:

```
SCHEMA COMPLIANCE CHECK
- Schema: <name>
- Required fields: OK
- Forbidden fields: none
- Responsibility boundary respected: YES
```

**If it cannot say "YES" → output is invalid.**

---

## Explicit Forbidden Behaviors

Claude is **NOT allowed** to:

| Forbidden Action | Why |
|------------------|-----|
| Invent field names | `observed_on` vs `observed_at` is a schema violation |
| Rename fields "for clarity" | Field names are contract, not style |
| Add fields not in schema | Extra fields pollute validation |
| Infer backend behavior from intent | Intent ≠ Implementation |
| Infer UI behavior from projection | UI reads projection, doesn't derive it |
| Write relative + absolute routes in same layer | Layer separation is absolute |
| Fix errors silently | Must report and stop |
| Guess missing values | Missing = STOP, not invent |
| Pattern-match from similar files | Each file has its own schema |
| Assume schema from filename | Schema must be explicitly loaded |

**Violations require Claude to HALT, not continue.**

---

## Layer Boundary Guardrails

Claude must **name the layer** before acting.

| Layer | May Read | May Write | Forbidden |
|-------|----------|-----------|-----------|
| SDSR Scenario | YAML scenario | DB (synthetic only) | AURORA_L2 |
| Scenario_SDSR_output | Runner state | In-memory struct | Files, DB |
| SDSR_output_emit | Scenario output | Observation JSON | Inference |
| AURORA_L2_apply | Observation JSON | Capability + Intent YAML | Guessing |
| Compiler | Intent + Capability | Projection | Runtime logic |
| UI | Projection | Rendering only | Decisions |
| Projection Assertions | Projection JSON | Validation errors | Route resolution |
| Route Resolution | Relative routes | Absolute routes | Projection mutation |

**Cross-layer writes are forbidden without explicit approval.**

---

## Refusal Template

When Claude cannot proceed, it must refuse properly:

```
EPISTEMIC SAFETY HALT

I cannot proceed.

Reason: <specific reason>
Missing: <what is needed>
Schema required: <schema_name>

This prevents me from guessing field names or semantics.
Please provide the schema or clarify the requirement.
```

**This prevents hallucination without slowing you down.**

---

## Schema Loading Checklist

Before ANY schema-governed operation:

```
SCHEMA LOADING CHECKLIST
[ ] Schema file path identified
[ ] Schema file read (not assumed)
[ ] Required fields enumerated
[ ] Optional fields identified
[ ] Enum values extracted
[ ] Layer responsibilities confirmed
[ ] Output will be schema-compliant only
```

---

## Validation Examples

### Valid Response Pattern

```
SCOPE DECLARATION
- Operating on: design/l2_1/ui_contract/ui_projection_lock.json
- Governing schema: UI_PROJECTION_SCHEMA_V2
- Schema location: docs/schemas/ui_projection_schema.json

SCHEMA FIELDS LOADED
- Required: _meta.version, _meta.processing_stage, domains[], _contract
- Domain required: domain, route, panels[], order
- Panel required: panel_id, panel_name, route, render_mode, visibility

[... work performed ...]

SCHEMA COMPLIANCE CHECK
- Schema: UI_PROJECTION_SCHEMA_V2
- Required fields: OK
- Forbidden fields: none
- Responsibility boundary respected: YES
```

### Invalid Response Pattern (Forbidden)

```
# WRONG - No schema declaration
Let me update the projection file...

# WRONG - Inferred fields
I'll add an `updated_at` field since projections typically have timestamps...

# WRONG - Silent fix
The route was wrong so I fixed it to include /precus...
```

---

## Integration Points

This document is enforced by:

1. **CLAUDE_BOOT_CONTRACT.md** — Schema loading in bootstrap
2. **SESSION_PLAYBOOK.yaml** — Epistemic safety section
3. **claude_epistemic_contract.yaml** — Machine-parseable rules
4. **Response Validator** — Post-hoc compliance checking

---

## Consequences of Violation

| Violation | Consequence |
|-----------|-------------|
| Output without schema declaration | Response INVALID |
| Invented field names | Response INVALID, must redesign |
| Cross-layer write | Response BLOCKED |
| Silent error fix | Response INVALID |
| Pattern-based inference | Response INVALID |

---

## Final Rule

> **When in doubt, STOP and ask.**
> A halted response is correct.
> A guessed response is a bug.

---

## References

- PIN-389: Projection Route Separation
- SDSR System Contract
- AURORA_L2 Design Specification
- docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md
