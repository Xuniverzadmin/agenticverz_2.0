# PIN-245: Integration Integrity System

**Status:** ACTIVE
**Created:** 2025-12-30
**Category:** Architecture / Testing / CI Enforcement
**Related:** PIN-240 (Seven-Layer Model), PIN-242 (Baseline Freeze), PIN-244 (L3 Adapter Contract)

---

## Purpose

Eliminate integration errors before they reach manual browser checks. This PIN establishes:

1. **Layer Integration Tests (LIT)** — Test seams between layers
2. **Browser Integration Tests (BIT)** — Catch console errors on page load
3. **CI enforcement** — Hard build failures on integration errors

---

## Problem Statement

Current state:
- Unit tests exist and pass
- Layer validators exist and pass
- Real failures appear **post-build** in browser consoles
- These are **integration errors**, not business logic errors

Root cause:
- Layer boundaries are defined but not **integration-tested**
- Browser console errors are not captured in CI
- Integration wiring failures slip through

---

## Integration Seam Definitions

### Layer Integration Boundaries (Seams)

| Seam | Description | Direction | Test Strategy |
|------|-------------|-----------|---------------|
| L1 ↔ L2 | Frontend ↔ Product APIs | Bidirectional | BIT + API shape tests |
| L2 ↔ L3 | API ↔ Boundary Adapters | L2 → L3 | LIT response shape |
| L3 ↔ L4 | Adapter ↔ Domain Engines | L3 → L4 | LIT domain contracts |
| L4 ↔ L5 | Domain ↔ Execution/Workers | L4 → L5 | LIT async invocation |
| L2 ↔ L6 | API ↔ Platform Services | L2 → L6 | LIT auth/persistence |

### What Integration Tests Validate

| Property | Validated | NOT Validated |
|----------|-----------|---------------|
| Response shape | ✅ | Business correctness |
| Null safety | ✅ | Data accuracy |
| Timing assumptions | ✅ | Performance |
| Auth wiring | ✅ | Access policy logic |
| Error format | ✅ | Error messages |

---

## Layer Integration Tests (LIT)

### Test Category Definition

```python
# pytest marker for LIT tests
@pytest.mark.lit  # Layer Integration Test
@pytest.mark.lit_l2_l3  # Specific seam
```

### LIT Characteristics

1. **Uses real code paths** — No mocks for layer boundaries
2. **Stubs async execution** — Where needed for speed
3. **Validates contracts** — Response shapes, not business logic
4. **Fast execution** — < 30 seconds per seam

### LIT File Structure

```
backend/tests/
└── lit/                          # Layer Integration Tests
    ├── __init__.py
    ├── conftest.py               # LIT fixtures
    ├── test_l2_l3_api_adapter.py # L2 ↔ L3 seam
    ├── test_l3_l4_adapter_domain.py
    ├── test_l4_l5_domain_worker.py
    └── test_l2_l6_api_platform.py
```

### LIT Contract

Each LIT test must:
1. Call a real layer boundary
2. Assert response shape (schema validation)
3. Assert null safety (no unexpected None)
4. Assert timing (async returns handle, sync returns value)

Each LIT test must NOT:
1. Assert business logic correctness
2. Assert data accuracy
3. Require database state
4. Depend on external services

---

## Browser Integration Tests (BIT)

### Purpose

Detect browser-console-level integration failures on **every L1 page**.

### What BIT Does

For each page:
1. Load page in headless browser
2. Capture:
   - `console.error`
   - Unhandled promise rejections
   - Network 4xx/5xx (except allowlist)
3. **NO clicks, NO flows, NO content assertions**

### Failure Rule (HARD)

> If ANY console error appears → BUILD FAILS

### BIT File Structure

```
website/aos-console/console/
└── tests/
    └── bit/                      # Browser Integration Tests
        ├── playwright.config.ts
        ├── bit.spec.ts           # All page load tests
        └── allowlist.yaml        # Whitelisted errors
```

### BIT Page Registry

All L1 pages must be registered:

```yaml
# bit/page-registry.yaml
pages:
  - path: /
    name: Overview
    auth_required: true
  - path: /activity
    name: Activity
    auth_required: true
  - path: /incidents
    name: Incidents
    auth_required: true
  - path: /policies
    name: Policies
    auth_required: true
  - path: /logs
    name: Logs
    auth_required: true
  - path: /integrations
    name: Integrations
    auth_required: true
  - path: /keys
    name: API Keys
    auth_required: true
  # Ops Console
  - path: /ops
    name: Ops Console
    auth_required: true
    role: founder
```

---

## CI Pipeline Integration

### Test Execution Order

```
1. Static architecture validators (existing)
2. Unit tests (existing)
3. Layer Integration Tests (LIT) ← NEW
4. Browser Integration Tests (BIT) ← NEW
5. Smoke tests (existing)
6. E2E tests (existing)
```

### CI Job Definitions

#### LIT Job

```yaml
lit-tests:
  runs-on: ubuntu-latest
  needs: [unit-tests]
  steps:
    - uses: actions/checkout@v4
    - name: Run Layer Integration Tests
      run: |
        cd backend
        PYTHONPATH=. pytest tests/lit -v -m lit --tb=short
```

#### BIT Job

```yaml
bit-tests:
  runs-on: ubuntu-latest
  needs: [lit-tests]
  steps:
    - uses: actions/checkout@v4
    - name: Install Playwright
      run: |
        cd website/aos-console/console
        npm ci
        npx playwright install --with-deps chromium
    - name: Start backend
      run: |
        cd backend
        nohup python -m uvicorn app.main:app --port 8000 &
        # Wait for health
    - name: Run Browser Integration Tests
      run: |
        cd website/aos-console/console
        npm run build
        npx playwright test tests/bit --project=chromium
```

### Failure Conditions

| Test Type | Failure Condition | Blocking |
|-----------|-------------------|----------|
| LIT | Any assertion failure | ✅ BLOCKS |
| BIT | Any console.error | ✅ BLOCKS |
| BIT | Any unhandled rejection | ✅ BLOCKS |
| BIT | Any 5xx response | ✅ BLOCKS |
| BIT | 4xx not in allowlist | ✅ BLOCKS |

---

## Enforcement Rules

### Pre-Build Gate

Any new L1 or L2 artifact MUST include:
- At least one Layer Integration Test
- If UI: Browser Integration Test coverage

**If missing → BLOCK implementation**

### Allowlist Protocol

Exceptions ONLY via explicit allowlist:

```yaml
# allowlist.yaml
allowed_console_errors:
  - page: /guard/experimental
    pattern: "FeatureFlag: guard_v2 disabled"
    reason: feature_flag_disabled
    expiry: 2025-03-01
    owner: team-platform
```

**No expiry → INVALID**

---

## Integration Integrity Contract

> **A build is invalid if:**
>
> 1. Any browser console error appears on first load
> 2. Any layer seam returns malformed or undocumented data
> 3. Async execution leaks into sync layers

Business correctness is allowed to fail.
**Integration correctness is not.**

---

## Sample Test Implementations

### LIT: L2 ↔ L3 Integration Test

```python
# tests/lit/test_l2_l3_api_adapter.py
"""
Layer Integration Test: L2 (API) ↔ L3 (Adapter)
Tests that API endpoints correctly invoke adapters with proper shapes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.lit
@pytest.mark.lit_l2_l3
class TestL2L3Integration:
    """L2 API to L3 Adapter integration."""

    def setup_method(self):
        self.client = TestClient(app)

    def test_capabilities_response_shape(self):
        """GET /api/v1/runtime/capabilities returns valid shape."""
        response = self.client.get(
            "/api/v1/runtime/capabilities",
            headers={"X-AOS-Key": "test-key"}
        )

        # Integration assertions (NOT business logic)
        assert response.status_code in (200, 401, 403)

        if response.status_code == 200:
            data = response.json()
            # Shape validation
            assert "skills" in data or "error" in data
            assert data is not None
            # No unexpected None in top-level keys
            for key, value in data.items():
                assert value is not None or key in ["optional_field"]

    def test_simulate_endpoint_shape(self):
        """POST /api/v1/runtime/simulate returns SimulationResult shape."""
        response = self.client.post(
            "/api/v1/runtime/simulate",
            headers={"X-AOS-Key": "test-key"},
            json={"plan": {}, "budget_cents": 100}
        )

        assert response.status_code in (200, 400, 401, 403, 422)

        if response.status_code == 200:
            data = response.json()
            # SimulationResult shape
            assert "feasible" in data or "error" in data
```

### BIT: Page Load Test

```typescript
// tests/bit/bit.spec.ts
import { test, expect } from '@playwright/test';
import * as yaml from 'js-yaml';
import * as fs from 'fs';

interface PageDef {
  path: string;
  name: string;
  auth_required: boolean;
  role?: string;
}

interface Allowlist {
  allowed_console_errors: Array<{
    page: string;
    pattern: string;
    reason: string;
    expiry: string;
  }>;
}

const pages: PageDef[] = yaml.load(
  fs.readFileSync('./tests/bit/page-registry.yaml', 'utf8')
) as { pages: PageDef[] }.pages;

const allowlist: Allowlist = yaml.load(
  fs.readFileSync('./tests/bit/allowlist.yaml', 'utf8')
) as Allowlist;

function isAllowed(page: string, message: string): boolean {
  const now = new Date();
  return allowlist.allowed_console_errors.some(entry => {
    if (entry.page !== page) return false;
    if (!message.includes(entry.pattern)) return false;
    if (new Date(entry.expiry) < now) return false;  // Expired
    return true;
  });
}

test.describe('Browser Integration Tests', () => {
  for (const pageDef of pages) {
    test(`${pageDef.name} (${pageDef.path}) loads without console errors`, async ({ page }) => {
      const errors: string[] = [];

      // Capture console errors
      page.on('console', msg => {
        if (msg.type() === 'error') {
          const text = msg.text();
          if (!isAllowed(pageDef.path, text)) {
            errors.push(text);
          }
        }
      });

      // Capture unhandled rejections
      page.on('pageerror', error => {
        if (!isAllowed(pageDef.path, error.message)) {
          errors.push(`UNHANDLED: ${error.message}`);
        }
      });

      // Navigate
      const response = await page.goto(`http://localhost:5173${pageDef.path}`);

      // Check for 5xx errors
      expect(response?.status()).toBeLessThan(500);

      // Wait for initial render
      await page.waitForLoadState('networkidle');

      // Assert no errors
      expect(errors).toEqual([]);
    });
  }
});
```

---

## Validation Questions (MANDATORY)

| Question | Required Answer |
|----------|-----------------|
| Can a frontend page load with broken wiring and still pass CI? | **NO** |
| Can a developer introduce a new API without integration tests? | **NO** |
| Will browser console errors reach users without being caught? | **NO** |

---

## Prohibited Behaviors

- ❌ Converting this into E2E testing
- ❌ Adding retry logic to hide errors
- ❌ Silencing console errors
- ❌ Marking failures as flaky
- ❌ Testing business correctness in LIT/BIT

---

## Success Criteria

The system is complete when:

> Integration failures are **impossible to ship**
> without explicitly bypassing policy via allowlist.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial design and implementation plan |
