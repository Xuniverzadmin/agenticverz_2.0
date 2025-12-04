# Known Warnings

This document tracks known warnings that appear in the test suite or runtime logs.
These are acknowledged and either:
- Cannot be fixed (external dependency)
- Scheduled for future fix
- Intentionally suppressed

---

## Test Suite Warnings

### 1. Pydantic `default_factory` datetime warning

**Warning:**
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal
in a future version. Use timezone-aware objects to represent datetimes in UTC:
datetime.datetime.now(datetime.UTC).
```

**Source:** Pydantic internal `fields.py:510`

**Status:** Cannot fix directly - internal to Pydantic library

**Affected Tests:**
- `tests/test_integration.py::TestCLI::test_cli_create_agent`
- Any test creating Pydantic models with datetime defaults

**Root Cause:**
Pydantic v2's internal `fields.py` uses `datetime.utcnow()` in its `default_factory`
machinery. This is not our code - it's inside the Pydantic library.

**Resolution Plan:**
| Step | Action | Timeline | Owner |
|------|--------|----------|-------|
| 1 | Monitor Pydantic releases for v2.10+ fix | Ongoing | Maintainer |
| 2 | Pin Pydantic version in requirements.txt | Done | - |
| 3 | Suppress warning in pytest config | Done | - |
| 4 | Upgrade when Pydantic releases fix | When available | Sprint task |

**Verification:**
```bash
# Check current Pydantic version
pip show pydantic | grep Version

# Monitor for fix
# https://github.com/pydantic/pydantic/issues (search utcnow)
```

---

### 2. Event Loop Deprecation Warning

**Warning:**
```
DeprecationWarning: There is no current event loop
```

**Source:** Tests using `asyncio.get_event_loop()` pattern

**Status:** ✅ Resolved in most places

**Resolution Applied:**
All instances in our codebase migrated from:
```python
# OLD (deprecated)
loop = asyncio.get_event_loop()
```
to:
```python
# NEW (correct)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(coro())
finally:
    loop.close()
```

**Remaining Instances:**
- External test fixtures (httpx, pytest-asyncio)
- Cannot control - comes from dependencies

**Resolution Plan:**
| Step | Action | Timeline | Owner |
|------|--------|----------|-------|
| 1 | Migrate all internal asyncio calls | ✅ Done | - |
| 2 | Add `asyncio_mode = "auto"` to pytest.ini | ✅ Done | - |
| 3 | Monitor pytest-asyncio updates | Ongoing | Maintainer |

---

## Runtime Warnings

No known runtime warnings at this time.

---

## Suppressed Warnings

The following warnings are intentionally suppressed via pytest configuration:

```python
# pytest.ini or conftest.py
filterwarnings = [
    "ignore::DeprecationWarning:pydantic.*:",
]
```

**Rationale:** These warnings originate from Pydantic internals, not our code.
Suppression prevents noise while we wait for upstream fix.

**Review Cadence:** Monthly check for Pydantic updates that resolve these warnings.

---

## Resolution Timeline

| Warning | Priority | Status | Target | Notes |
|---------|----------|--------|--------|-------|
| Pydantic default_factory | P3 | Waiting | Pydantic v2.10+ | External dependency |
| Event loop deprecation | P2 | ✅ Done | v1.0 | Internal code fixed |

---

## Acceptance Criteria for Closure

A warning can be closed when:

1. **External Dependency Warning:**
   - Upstream fix is released AND
   - We upgrade to fixed version AND
   - Warning no longer appears in test output

2. **Internal Code Warning:**
   - Code is migrated to non-deprecated API AND
   - Tests pass without warning AND
   - No regression in functionality

---

## Audit Log

| Date | Action | Result |
|------|--------|--------|
| 2025-12-01 | Created initial warning tracker | 2 warnings documented |
| 2025-12-01 | Migrated all datetime.utcnow() in our code | Fixed 25+ occurrences |
| 2025-12-01 | Migrated all @validator to @field_validator | Fixed 2 occurrences |
| 2025-12-01 | Fixed asyncio event loop patterns | Fixed 5+ occurrences |
| 2025-12-01 | Added resolution plan | Documented |

---

*Last updated: 2025-12-01*
