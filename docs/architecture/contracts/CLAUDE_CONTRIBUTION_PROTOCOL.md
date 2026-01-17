# CLAUDE-SAFE CONTRIBUTION PROTOCOL

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All Claude-assisted code contributions
**Reference:** Design Fix Contracts

---

## Prime Directive

> **Claude mirrors structure. Architecture must be structured to be mirrored correctly.**

This protocol defines how Claude (and LLMs) should interact with the codebase to produce correct, contract-compliant code.

---

## 1. The Problem This Solves

When architecture is silent, Claude fills gaps with:
- Reasonable-sounding names (that don't match conventions)
- Plausible parent revisions (that don't exist)
- Intuitive field mappings (that violate layer boundaries)
- Common patterns (that aren't this codebase's patterns)

**Solution:** Make the correct path the obvious path.

---

## 2. Pre-Contribution Checklist

Before writing ANY code, Claude must verify:

```
CLAUDE CONTRIBUTION PRE-CHECK

1. Contract Identification
   □ Which contract(s) does this code touch?
   □ Have I read the relevant contract(s)?

2. Pattern Discovery
   □ Is there existing code that does something similar?
   □ What patterns does the existing code follow?

3. Naming Verification
   □ What naming convention applies? (see NAMING.md)
   □ Am I using runtime names or API names?

4. Layer Verification
   □ What layer is this code in? (L1-L8)
   □ What can this layer import?
   □ What must this layer NOT import?

5. Wiring Verification
   □ If adding a router: Is registry.py updated?
   □ If adding a migration: Is MIGRATION_CONTRACT header present?
   □ If adding an endpoint: Is there an adapter?
```

---

## 3. Domain-Specific Protocols

### 3.1 Adding a New Migration

**Protocol:**

1. **Find the current head:**
   ```bash
   cd backend && alembic heads
   ```

2. **Copy the EXACT revision ID** (do not paraphrase)

3. **Create migration with header:**
   ```python
   # MIGRATION_CONTRACT:
   #   domain: {domain}
   #   parent: {EXACT_HEAD_FROM_STEP_1}
   #   creates_tables: {tables} | none
   #   modifies_tables: {tables} | none
   #   irreversible: false
   #   requires_backfill: false

   """
   {NNN} — {Description}
   ...
   """

   revision = "{NNN}_{snake_case_description}"
   down_revision = "{EXACT_HEAD_FROM_STEP_1}"  # MUST MATCH CONTRACT
   ```

4. **Verify before commit:**
   ```bash
   python scripts/preflight/check_alembic_parent.py {revision_id}
   ```

**Anti-Pattern:** Guessing the parent revision from memory or filename patterns.

---

### 3.2 Adding a New API Endpoint

**Protocol:**

1. **Create the router file** with proper header:
   ```python
   # Layer: L2 — Product APIs
   # Product: {product}
   # Role: {description}
   # Reference: PIN-XXX
   ```

2. **Create or update the adapter** in `app/api/_adapters/{domain}.py`

3. **Register in registry.py:**
   ```python
   from app.api.{domain}.{action} import router as {domain}_{action}_router

   def register(app):
       # ... existing routers
       app.include_router({domain}_{action}_router, prefix="/api/v1")
   ```

4. **Do NOT modify main.py** (registry handles it)

5. **Verify:**
   ```bash
   python scripts/preflight/check_router_registry.py
   ```

**Anti-Pattern:** Adding router imports directly to main.py.

---

### 3.3 Adding a New Schema

**Protocol:**

1. **Determine if runtime or API schema:**
   - Runtime (L4): Goes in `app/schemas/{domain}/`
   - API (L2): Goes in the endpoint file or `app/api/{domain}/`

2. **For runtime schemas, use semantic names:**
   ```python
   # CORRECT
   class HeadroomInfo(BaseModel):
       tokens: int
       runs: int
       cost_cents: int

   # WRONG
   class HeadroomInfo(BaseModel):
       tokens_remaining: int  # Context belongs in API
   ```

3. **For API responses, use adapters:**
   ```python
   # In app/api/_adapters/{domain}.py
   def adapt_headroom(headroom: HeadroomInfo) -> dict:
       return {
           "tokens_remaining": headroom.tokens,
           "runs_remaining": headroom.runs,
       }
   ```

4. **Verify:**
   ```bash
   python scripts/preflight/check_naming_contract.py
   ```

**Anti-Pattern:** Adding `_remaining`, `_current`, `_total` suffixes to runtime schemas.

---

### 3.4 Adding Auth-Protected Endpoints

**Protocol:**

1. **Do NOT add auth dependencies to endpoints.** Gateway handles it.

2. **Access auth context via:**
   ```python
   from app.auth.gateway_middleware import get_auth_context

   @router.post("/endpoint")
   async def my_endpoint(request: Request, ...):
       ctx = get_auth_context(request)
       tenant_id = ctx.tenant_id
   ```

3. **Add tenant state check if mutating:**
   ```python
   from app.services.tenant_state_gate import require_tenant_ready

   tenant = await get_tenant(session, ctx.tenant_id)
   require_tenant_ready(tenant)
   ```

4. **Return structured errors with state info:**
   ```python
   raise HTTPException(
       status_code=403,
       detail={
           "error": "tenant_not_ready",
           "state": tenant.onboarding_state,
           "required_state": 4,
       }
   )
   ```

**Anti-Pattern:** Adding `Depends(get_jwt_auth())` to endpoint signatures.

---

## 4. Contract Discovery Commands

When unsure which contract applies, use these commands:

```bash
# Find existing patterns for a domain
grep -rn "class.*BaseModel" backend/app/schemas/{domain}/

# Find how existing routers are wired
grep -rn "include_router" backend/app/api/registry.py

# Find adapter patterns
ls backend/app/api/_adapters/

# Find migration patterns
head -30 backend/alembic/versions/$(ls backend/alembic/versions/ | tail -1)

# Check current migration head
cd backend && alembic heads
```

---

## 5. Error Recovery Protocol

When Claude produces code that violates a contract:

### Step 1: Identify the Contract

```
Which contract was violated?
  □ NAMING.md (field names)
  □ MIGRATIONS.md (revision lineage)
  □ RUNTIME_VS_API.md (layer boundaries)
  □ AUTH_STATE.md (auth/state checks)
  □ ROUTER_WIRING.md (router registration)
```

### Step 2: Read the Contract

```bash
cat docs/architecture/contracts/{CONTRACT}.md
```

### Step 3: Find Correct Pattern

```bash
# Find existing code that does this correctly
grep -rn "{pattern}" backend/app/
```

### Step 4: Fix and Verify

```bash
# Run the relevant check
python scripts/preflight/check_{contract}.py
```

---

## 6. Structural Cues for Claude

These structural patterns help Claude produce correct code:

### 6.1 File Headers as Contracts

Every file starts with a header that declares its constraints:
```python
# Layer: L2 — Product APIs
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
```

**Claude behavior:** Copy this header pattern. It declares what's allowed.

### 6.2 Registry as Single Source

`app/api/registry.py` is the only file that imports routers and calls `include_router`.

**Claude behavior:** Never add router imports elsewhere. Always modify registry.py.

### 6.3 Adapters as Translation Layer

`app/api/_adapters/` contains all runtime-to-API translations.

**Claude behavior:** Create adapter functions for new domains. Never access runtime fields directly in endpoints.

### 6.4 Migration Contract Header

Every migration starts with `MIGRATION_CONTRACT:` block.

**Claude behavior:** Copy the header format. Fill in values from actual verification (not memory).

---

## 7. Conversation Patterns

### When Starting a New Task

```
Before I start, let me verify:
1. Which contracts apply to this task?
2. Are there existing patterns I should follow?
3. What preflight checks will this code need to pass?
```

### When Uncertain About Naming

```
I see two possible naming patterns:
- Runtime style: `tokens` (semantic, no context)
- API style: `tokens_remaining` (client context)

This code is in {layer}, so I should use {style}.
```

### When Adding Code to a New Domain

```
This domain doesn't have:
- [ ] Adapter file in _adapters/
- [ ] Entry in registry.py
- [ ] Schema file in schemas/

I'll create these following the patterns from {existing_domain}.
```

---

## 8. Anti-Patterns to Avoid

| Anti-Pattern | Why It Happens | Correct Pattern |
|--------------|----------------|-----------------|
| Guessing revision IDs | Names look similar | Run `alembic heads` |
| Direct runtime access in API | Shorter code | Use adapter functions |
| Router imports in main.py | Seems logical | Use registry.py |
| Context suffixes in schemas | Client-friendly | Adapters add context |
| Auth dependencies on endpoints | Common pattern | Gateway handles auth |
| State assumptions | Implicit behavior | Explicit state gates |

---

## 9. Verification Before Response

Before providing code, Claude should internally verify:

```
CLAUDE CONTRIBUTION VERIFICATION

□ Did I read the relevant contract(s)?
□ Did I find existing code that does something similar?
□ Did I follow the existing pattern exactly?
□ Would this code pass the preflight checks?
□ Are all layer boundaries respected?
□ Is the naming consistent with the contract?
```

If any answer is uncertain: **Ask, don't guess.**

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│           CLAUDE CONTRIBUTION QUICK GUIDE                   │
├─────────────────────────────────────────────────────────────┤
│  Before coding:                                             │
│    1. Identify applicable contract(s)                       │
│    2. Find existing pattern                                 │
│    3. Verify naming convention                              │
│                                                             │
│  When uncertain:                                            │
│    - Ask, don't guess                                       │
│    - Run discovery commands                                 │
│    - Read the contract                                      │
│                                                             │
│  After coding:                                              │
│    - Run preflight checks                                   │
│    - Verify layer boundaries                                │
│    - Confirm registry/adapter updates                       │
│                                                             │
│  Key files to know:                                         │
│    - app/api/registry.py (router wiring)                    │
│    - app/api/_adapters/ (response transformation)           │
│    - alembic/versions/ (migration lineage)                  │
│    - docs/architecture/contracts/ (the rules)               │
└─────────────────────────────────────────────────────────────┘
```
