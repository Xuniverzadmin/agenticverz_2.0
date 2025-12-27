# PIN-201: Enhanced Behavior Library System

**Status:** COMPLETE
**Created:** 2025-12-27
**Category:** Governance / Claude Discipline
**Milestone:** Phase B.1

---

## Summary

Implemented machine-enforced behavior library system that converts incidents into executable rules. Includes YAML/JSON schema, enhanced validator with library loading, incident classifier, and scaffold generator.

---

## Problem Statement

Claude operates as a stateless LLM that cannot "remember" lessons between sessions. Previous incidents (runtime drift, auth mismatch, timezone errors) were repeated because:

1. Rules existed only as prose documentation
2. Enforcement relied on human vigilance
3. No machine-readable trigger → check → evidence chain

**Goal:** Convert incidents into machine-enforced behavior that cannot be bypassed.

---

## Solution: Behavior Library v1

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   BEHAVIOR LIBRARY SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   docs/behavior/                                                 │
│   ├── behavior_library.yaml    (Authoritative, human-readable)  │
│   └── behavior_library.json    (Machine-friendly)               │
│                                                                  │
│   scripts/ops/                                                   │
│   └── claude_response_validator.py                               │
│       ├── load_behavior_library()   - Loads rules from JSON     │
│       ├── evaluate_behavior_rules() - Checks triggers/sections  │
│       ├── classify_incident()       - Tags incident class       │
│       └── scaffold_rule()           - Suggests rule template    │
│                                                                  │
│   CLAUDE_BOOT_CONTRACT.md                                        │
│   └── Boot Step 1.3: Load Behavior Library, comply with rules   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Rule Schema

```yaml
- id: BL-XXX-NNN
  name: Rule Name
  severity: BLOCKER | ERROR | WARN
  class: incident_class

  triggers:
    any_of:
      - keyword: "pattern to match"
      - file_glob: "path/pattern"

  requires:
    sections:
      - SECTION_NAME
    fields:
      - field_name

  evidence:
    required_fields:
      - field_1
      - field_2

  message_on_fail: "Error message on violation"
```

### Active Rules (v1)

| ID | Name | Class | Severity |
|----|------|-------|----------|
| BL-ENV-001 | Runtime Sync Before Test | environment_drift | BLOCKER |
| BL-AUTH-001 | Auth Contract Enumeration | auth_mismatch | BLOCKER |
| BL-TIME-001 | Timestamp Semantics | timezone_mismatch | BLOCKER |
| BL-DEPLOY-001 | Service Name Verification | service_name_mismatch | ERROR |
| BL-MIG-001 | Migration Head Verification | migration_fork | BLOCKER |
| BL-TEST-001 | Test Execution Prerequisites | test_prerequisites | BLOCKER |

---

## Implementation

### 1. Behavior Library Files

**YAML (authoritative):** `docs/behavior/behavior_library.yaml`
- Human-readable format
- Contains section templates
- Full documentation

**JSON (machine-friendly):** `docs/behavior/behavior_library.json`
- Loaded by validator
- Parsed directly

### 2. Enhanced Validator

**File:** `scripts/ops/claude_response_validator.py`

New functions:
```python
def load_behavior_library(library_path: Optional[str] = None) -> Dict
    """Load rules from JSON file."""

def evaluate_behavior_rules(response_text: str, rules: List) -> List[RuleFinding]
    """Evaluate all rules against response text."""

def classify_incident(log_text: str) -> set
    """Classify incident from log/error text."""

def scaffold_rule(tag: str) -> Optional[str]
    """Return rule ID template for incident tag."""
```

### 3. Incident Classification

Automatically classifies incidents:

| Tag | Keywords | Rule |
|-----|----------|------|
| ENV_DRIFT | docker, health, container, stale | BL-ENV-001 |
| AUTH_MISMATCH | forbidden, rbac, 401, 403 | BL-AUTH-001 |
| TIME_SEMANTICS | timezone, timestamp, naive, aware | BL-TIME-001 |
| MIGRATION_FORK | alembic, migration, heads | BL-MIG-001 |

### 4. Boot Contract Update

Added to `CLAUDE_BOOT_CONTRACT.md`:
- Section 1.3: Behavior Library load
- Rule table with triggers and required sections
- Enforcement policy

---

## Usage

### Validate Response

```bash
# Validate with library
python scripts/ops/claude_response_validator.py response.md --library docs/behavior/behavior_library.json

# From stdin
echo "curl http://localhost:8000/health" | python scripts/ops/claude_response_validator.py --stdin --lenient
```

### Classify Incident

```bash
# Classify error log
echo "Error: 403 Forbidden. RBAC denied" | python scripts/ops/claude_response_validator.py --stdin --classify --json
```

Output:
```json
{
  "tags": ["AUTH_MISMATCH"],
  "suggested_rules": ["BL-AUTH-001"]
}
```

### Add New Rule

1. Classify incident: `--classify` mode
2. Get scaffold: `scaffold_rule(tag)`
3. Fill in triggers/evidence
4. Add to `behavior_library.yaml`
5. Regenerate JSON

---

## Enforcement Policy

| Severity | Behavior |
|----------|----------|
| BLOCKER | Response rejected automatically |
| ERROR | Response rejected, must fix |
| WARN | Response allowed, annotated |

---

## Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `docs/behavior/behavior_library.yaml` | Created | Authoritative rule definitions |
| `docs/behavior/behavior_library.json` | Created | Machine-readable rules |
| `scripts/ops/claude_response_validator.py` | Enhanced | Library loading, rule evaluation |
| `CLAUDE_BOOT_CONTRACT.md` | Modified | Added Behavior Library section |

---

## What This Buys

| Before | After |
|--------|-------|
| Repeated incidents | Impossible (machine-blocked) |
| Debug time post-hoc | Front-loaded verification |
| AI errors at runtime | Blocked before execution |
| Human enforcement | Machine enforcement |

---

## Validation

Test with trigger but no section:
```
$ echo 'curl localhost:8000' | python validator.py --stdin --lenient
Status: ❌ INVALID
lib:BL-ENV-001: BL-ENV-001 VIOLATION: Runtime sync missing
```

Test with section present:
```
$ echo 'curl localhost:8000
RUNTIME SYNC CHECK
- Services enumerated: YES
- Target service: backend
- Health status: healthy' | python validator.py --stdin --lenient
Status: ✅ VALID
lib:BL-ENV-001: Section and evidence present
```

---

## Related PINs

- [PIN-199](PIN-199-pb-s1-retry-creates-new-execution---implementation.md) - PB-S1 Retry Immutability
- [PIN-200](PIN-200-claude-behavior-enforcement-system.md) - Claude Behavior Enforcement System
