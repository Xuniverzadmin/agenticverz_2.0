# STOP: Read Before Editing RBAC Rules

**Authority:** PIN-391 (RBAC Unification)
**Status:** LOCKED
**Enforcement:** BLOCKING

---

## This File Is a Gate

If you are Claude (or any AI assistant), you **MUST** read and acknowledge this file before modifying any RBAC rules.

If you are a human, you **SHOULD** read this before editing `RBAC_RULES.yaml`.

---

## The Invariant

> **Authorization is declared, not inferred.**
> Code may mirror rules temporarily, but must not invent them.

---

## Before Any RBAC Change, Answer These Questions

### 1. Is this endpoint already in RBAC_RULES.yaml?

```bash
grep -n "path_prefix:" design/auth/RBAC_RULES.yaml | grep "<your-path>"
```

- **Yes** → Modify the existing rule
- **No** → You must add a new rule (continue to question 2)

### 2. What is the correct access tier?

| Tier | When to Use |
|------|-------------|
| `PUBLIC` | Extremely rare. Health checks, docs, auth endpoints only. |
| `SESSION` | User must be authenticated. Most endpoints. |
| `PRIVILEGED` | User must have specific permissions. Write operations. |
| `SYSTEM` | Engine/SDSR/control-plane only. Never user-accessible. |

**Default:** `SESSION` (authenticated required)
**Never guess:** If unsure, ask.

### 3. Is this a temporary rule?

Temporary rules exist for preflight validation or phased rollouts.

If temporary:
- Set `temporary: true`
- Set `expires:` to a date (e.g., `"2026-03-01"`)
- Add a `pin:` reference

### 4. Which consoles can access this?

| Console | Who Uses It |
|---------|-------------|
| `customer` | End users via console.agenticverz.com |
| `founder` | Founders via founder console |

Most endpoints: `[customer, founder]`
Some endpoints: `[founder]` only

### 5. Which environments?

| Environment | When |
|-------------|------|
| `preflight` | Testing/staging |
| `production` | Live production |

Most endpoints: `[preflight, production]`
Some temporary rules: `[preflight]` only

---

## Forbidden Actions

| Action | Why Forbidden |
|--------|---------------|
| Adding to `PUBLIC_PATHS` without schema rule | Creates drift |
| Classifying endpoint by inference | Must be declared |
| Making endpoint PUBLIC "for convenience" | Security risk |
| Modifying schema without CI check | Alignment violation |

---

## After Making Changes

1. **Run the loader validation:**
   ```bash
   python3 backend/app/auth/rbac_rules_loader.py
   ```

2. **Run the CI alignment guard:**
   ```bash
   python3 scripts/ci/check_rbac_alignment.py --verbose
   ```

3. **If adding to PUBLIC_PATHS (temporary mirror):**
   - Add comment with `# PIN-391` reference
   - Add comment with expiry date
   - Update schema first, then mirror

---

## Claude Guardrail Checklist

Before modifying RBAC, Claude must confirm:

- [ ] I have read design/auth/RBAC_READ_BEFORE_EDITING.md
- [ ] I know which rule I am modifying (or adding)
- [ ] I have not inferred the access tier from behavior
- [ ] I have checked if this is a temporary rule
- [ ] I will run the CI guard after changes

If ANY checkbox is unchecked → STOP and ask for clarification.

---

## Quick Reference

```yaml
# Minimal rule template
- rule_id: YOUR_RULE_ID
  path_prefix: /api/v1/your-endpoint/
  methods: [GET]
  access_tier: SESSION
  allow_console: [customer, founder]
  allow_environment: [preflight, production]
  description: "What this endpoint does."

# Temporary rule template
- rule_id: YOUR_RULE_ID_PREFLIGHT
  pin: PIN-XXX
  path_prefix: /api/v1/your-endpoint/
  methods: [GET]
  access_tier: PUBLIC
  allow_console: [customer]
  allow_environment: [preflight]
  temporary: true
  expires: "2026-03-01"
  description: >
    TEMPORARY - explain why and when to remove.
```

---

## Reference

- **Canonical Schema:** `design/auth/RBAC_RULES.yaml`
- **Loader:** `backend/app/auth/rbac_rules_loader.py`
- **CI Guard:** `scripts/ci/check_rbac_alignment.py`
- **PIN:** PIN-391 (RBAC Unification)
