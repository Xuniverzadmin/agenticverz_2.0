# Frontend API Audience Map

**Status:** NORMATIVE
**Effective:** 2026-01-06
**Reference:** PIN-319 (Frontend Realignment), R2-1

---

## Purpose

This document classifies each frontend API client by its intended audience.
Import boundary checks (R2-2) enforce these classifications.

---

## Audience Definitions

| Audience | Description | Allowed Consumers |
|----------|-------------|-------------------|
| `customer` | Customer-facing APIs | `products/ai-console/**` |
| `founder` | Founder/operator APIs | `fops/**` |
| `shared` | Infrastructure used by both | Any frontend code |

---

## API Client Classification

### Shared (Infrastructure)

Used by both customer and founder consoles.

| File | Purpose | Notes |
|------|---------|-------|
| `client.ts` | Base axios client | Core infrastructure |
| `auth.ts` | Authentication | Login, token management |
| `health.ts` | Health checks | System status |
| `runtime.ts` | Runtime capabilities | Agent capabilities |
| `traces.ts` | Execution traces | Trace viewing |

### Customer Only

Must NOT be imported by founder code (but may be).

| File | Purpose | Notes |
|------|---------|-------|
| `guard.ts` | Budget/incident guard | Customer console core |
| `credits.ts` | Billing/credits | Customer billing |
| `agents.ts` | Agent management | Customer agents |
| `jobs.ts` | Job management | Customer jobs |
| `messages.ts` | Message history | Customer messages |
| `preflight/customer.ts` | Customer preflight | Customer onboarding |

### Founder Only

Must NOT be imported by customer code.

| File | Purpose | Notes |
|------|---------|-------|
| `ops.ts` | Ops console | System health, customers |
| `killswitch.ts` | Emergency controls | System killswitches |
| `recovery.ts` | Recovery system | Incident recovery |
| `replay.ts` | Replay system | Incident replay |
| `scenarios.ts` | Scenario builder | Test scenarios |
| `integration.ts` | Integration loops | M25 integration |
| `sba.ts` | SBA inspector | Agent inspection |
| `explorer.ts` | Founder explorer | Cross-tenant data |
| `timeline.ts` | Founder timeline | Event timeline |
| `worker.ts` | Worker console | Worker management |
| `operator.ts` | Operator functions | Operator actions |
| `failures.ts` | Failure patterns | Pattern catalog |
| `preflight/founder.ts` | Founder preflight | Founder onboarding |

### Classification Pending

Require analysis to determine correct audience.

| File | Current Usage | Recommended |
|------|---------------|-------------|
| `blackboard.ts` | Unknown | Likely shared |
| `costsim.ts` | Cost simulation | Likely shared |
| `memory.ts` | Memory management | Likely shared |
| `metrics.ts` | Metrics display | Likely shared |

---

## Annotation Format

Each API client file should include an audience annotation in its header:

```typescript
/**
 * @audience founder
 *
 * Description of API client...
 */
```

Valid values: `customer`, `founder`, `shared`

---

## Enforcement

### CI Check (R2-2)

The import boundary checker validates:

1. `products/ai-console/**` files cannot import `@audience founder` clients
2. Violations fail the build

### Manual Review

- PRs changing audience classification require review
- New API clients require audience classification

---

## Adding New API Clients

1. Determine audience based on consumer (who will import this?)
2. Add `@audience` annotation to file header
3. Update this document
4. CI will enforce import boundaries

---

## References

- PIN-319: Frontend Realignment
- `website/app-shell/APP_SHELL_SCOPE.md`
- `scripts/ui-hygiene-check.cjs` (import boundary checks)
