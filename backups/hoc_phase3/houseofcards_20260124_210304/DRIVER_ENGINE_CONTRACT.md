# Driver/Engine Interface Contract

**Status:** LOCKED
**Effective:** 2026-01-23
**Reference:** PIN-468 (Phase 2 Step 2 - L4/L6 Segregation)
**Parent Document:** `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md` (Canonical Layer Architecture)

> **Note:** This contract implements the L5/L6 boundary rules from HOC Layer Topology V1.2.
> For full layer model, see `/docs/architecture/HOC_LAYER_TOPOLOGY_V1.md`.

---

## Purpose

This contract defines the **immutable boundary** between L4 Engines and L6 Drivers.
All SPLIT operations must conform exactly to this specification.

---

## First Principles

| Layer | Role | Question Answered |
|-------|------|-------------------|
| **L4 Engine** | Decide *what* should happen | "Should this integration be enabled?" |
| **L6 Driver** | Perform *effects* only | "Write this status to the database" |

**Invariant:** Decisions ≠ Effects. A file doing both is structurally invalid.

---

## 1. Engine Contract (L4)

### Purpose
Engines decide *what* should happen based on domain rules.

### MUST

- Accept domain inputs (ids, enums, intent objects)
- Call drivers explicitly via injected dependency
- Return domain results (schemas, dataclasses, enums)
- Be testable with a mocked driver
- Contain all business logic (validation, policy, thresholds)

### MUST NOT

- Import `sqlalchemy`, `sqlmodel`, or `Session` (except under `TYPE_CHECKING`)
- Import `app.models.*` ORM classes at runtime
- Construct SQL queries
- Contain transaction management (`commit`, `rollback`, `begin`)
- Reference table names or column names
- Know *how* data is stored

### File Header Template

```python
# Layer: L4 — Domain Engine
# AUDIENCE: {CUSTOMER|FOUNDER|INTERNAL}
# Product: {product-name}
# Temporal:
#   Trigger: {api|worker|scheduler}
#   Execution: {sync|async}
# Role: {single-line description}
# Callers: {who calls this}
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md
```

### Signature Pattern

```python
from typing import TYPE_CHECKING

from app.houseofcards.{domain}/drivers.{name}_driver import {Name}Driver

if TYPE_CHECKING:
    from sqlmodel import Session

class {Name}Engine:
    """
    L4 engine for {domain} decisions.

    Decides: {what decisions this engine makes}
    Delegates: All persistence to {Name}Driver
    """

    def __init__(self, driver: {Name}Driver):
        self._driver = driver

    async def evaluate_{action}(
        self,
        tenant_id: str,
        input: {Input}Schema,
    ) -> {Output}Result:
        """
        Decide {what}.

        Business logic:
        - {rule 1}
        - {rule 2}
        """
        # Decision logic here
        if self._should_allow(input):
            await self._driver.persist_{effect}(...)
            return {Output}Result(allowed=True)
        return {Output}Result(allowed=False, reason="...")
```

### Engine Test Pattern

```python
def test_engine_decides_correctly():
    # Mock the driver
    mock_driver = Mock(spec={Name}Driver)
    mock_driver.fetch_data.return_value = [...]

    engine = {Name}Engine(driver=mock_driver)
    result = await engine.evaluate_{action}(tenant_id="t1", input=...)

    # Assert decision logic
    assert result.allowed is True
    mock_driver.persist_{effect}.assert_called_once()
```

---

## 2. Driver Contract (L6)

### Purpose
Drivers perform database effects. They are policy-blind data access layers.

### MUST

- Accept primitive parameters (str, int, UUID, dataclass)
- Perform DB I/O (queries, inserts, updates, deletes)
- Return raw facts (rows, counts, DTOs, None)
- Be stateless (no caching of decisions)
- Use explicit session management

### MUST NOT

- Contain conditionals based on business rules:
  - `if severity > ...`
  - `if policy.allows(...)`
  - `if threshold exceeded`
  - `if status == "active"`
- Know "why" data is being accessed
- Import engines or other domain modules
- Make decisions about data validity
- Contain retry logic or orchestration

### File Header Template

```python
# Layer: L6 — Driver
# AUDIENCE: {CUSTOMER|FOUNDER|INTERNAL}
# Product: {product-name}
# Temporal:
#   Trigger: {engine-call}
#   Execution: {sync|async}
# Role: Data access for {domain}
# Callers: {Name}Engine (L4)
# Allowed Imports: sqlalchemy, sqlmodel, app.models
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md
```

### Signature Pattern

```python
from typing import List, Optional
from sqlalchemy import select, and_
from sqlmodel import Session

from app.models.{domain} import {Model}

class {Name}Driver:
    """
    L6 driver for {domain} data access.

    Pure persistence - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    async def fetch_{entities}(
        self,
        tenant_id: str,
        limit: int = 50,
    ) -> List[{Entity}Row]:
        """Fetch {entities} for tenant."""
        stmt = select({Model}).where({Model}.tenant_id == tenant_id).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_row(r) for r in result.scalars()]

    async def persist_{effect}(
        self,
        entity_id: str,
        status: str,
    ) -> None:
        """Persist {effect}."""
        stmt = update({Model}).where({Model}.id == entity_id).values(status=status)
        await self._session.execute(stmt)
        await self._session.commit()

    def _to_row(self, model: {Model}) -> {Entity}Row:
        """Convert ORM model to DTO."""
        return {Entity}Row(
            id=model.id,
            name=model.name,
            # ... pure field mapping, no logic
        )
```

### Driver DTO Pattern

```python
@dataclass(frozen=True)
class {Entity}Row:
    """
    Immutable data transfer object.

    Represents raw database row - no business interpretation.
    """
    id: str
    tenant_id: str
    name: str
    status: str
    created_at: datetime
```

---

## 3. Naming Rules (LOCKED)

| Pattern | Status | Use Case |
|---------|--------|----------|
| `*_service.py` | ❌ BANNED | Never use |
| `*_engine.py` | ✅ Required | L4 decision logic |
| `*_driver.py` | ✅ Required | L6 data access |
| `*_adapter.py` | ✅ Allowed | L3 boundary translation |
| `*_facade.py` | ✅ Allowed | L2 API composition |

**One role per file. No hybrids.**

---

## 4. SPLIT Execution Checklist

### Before Split

- [ ] Read entire source file
- [ ] Classify each function: **DECISION** or **PERSISTENCE**
- [ ] Count: N decision functions, M persistence functions
- [ ] Identify shared state/dependencies

### During Split

- [ ] Create `{name}_driver.py` first (all persistence)
- [ ] Move **all** DB code in one pass
- [ ] Create `{name}_engine.py` (all decisions)
- [ ] Engine receives driver via `__init__`
- [ ] Update imports in engine to use driver

### After Split

- [ ] Engine imports compile with `sqlalchemy` removed from env
- [ ] Driver contains zero business keywords: `severity`, `threshold`, `policy`, `enforce`, `validate`, `check`
- [ ] Tests run with driver mocked
- [ ] No leftover DB signals in engine (`grep -E "select\(|session\." engine.py` → empty)

### Rollback Trigger

If ANY item fails:
1. Delete new files
2. Restore original
3. Re-analyze classification
4. Re-split with corrected boundaries

---

## 5. Forbidden Patterns (Hard Block)

### In Engines

```python
# ❌ FORBIDDEN - Direct DB access
from sqlmodel import Session
result = session.exec(select(Model))

# ❌ FORBIDDEN - ORM import
from app.models.tenant import Tenant

# ❌ FORBIDDEN - Query construction
stmt = select(func.count(Model.id))
```

### In Drivers

```python
# ❌ FORBIDDEN - Business logic
if severity > self.THRESHOLD:
    return None

# ❌ FORBIDDEN - Policy check
if not policy.allows_action(user):
    raise Forbidden()

# ❌ FORBIDDEN - Validation
if not is_valid_email(email):
    return Error("invalid")

# ❌ FORBIDDEN - Cross-domain import
from app.houseofcards.policies.engines import PolicyEngine
```

---

## 6. CI Enforcement (Mandatory)

### Engine Guard

```bash
# Fail if engines import DB libs
grep -rE "^from (sqlalchemy|sqlmodel)|^import (sqlalchemy|sqlmodel)" \
  backend/app/houseofcards/*/engines/*.py \
  --include="*_engine.py" && exit 1
```

### Driver Guard

```bash
# Fail if drivers contain business logic keywords
grep -rE "if.*(severity|threshold|policy|enforce|validate|budget|limit)" \
  backend/app/houseofcards/*/drivers/*.py \
  --include="*_driver.py" && exit 1
```

### Naming Guard

```bash
# Fail on new *_service.py in houseofcards
find backend/app/houseofcards -name "*_service.py" -newer /tmp/baseline && exit 1
```

---

## 7. Reference Implementation

After this contract is locked, `cus_integration_service.py` will be split as the reference:

- **Source:** `cus_integration_service.py` (36 persistence, 9 decisions)
- **Output:** `cus_integration_engine.py` + `cus_integration_driver.py`
- **Pattern:** All 21 remaining files follow this exact template

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-23 | Contract created and locked |
