# PIN-183: AgenticVerz Runtime v1 - Feature Freeze

**Status:** LOCKED
**Category:** Architecture / Runtime / Feature Freeze
**Created:** 2025-12-26
**Milestone:** Runtime v1 Declaration
**Related PINs:** PIN-182, PIN-181, PIN-180, PIN-179

---

## Declaration

**AgenticVerz Runtime v1 is hereby declared FEATURE FROZEN.**

From this point forward:
- No new primitives
- No new contracts
- No console reshuffling
- Only observation, learning, and bug fixes

---

## What Is Frozen

| Component | Status | Modification Allowed |
|-----------|--------|---------------------|
| Three-plane architecture | FROZEN | None |
| Console structure | FROZEN | Bug fixes only |
| Navigation hierarchy | FROZEN | None |
| Customer surface area | FROZEN | None |
| Founder/Customer separation | FROZEN | None |
| Contract obligations | FROZEN | None |
| API schemas | FROZEN | Bug fixes only |

---

## Three-Plane Architecture (Canonical)

```
Founder / PrefOps  →  /ops           →  Truth, diagnosis
Founder / Control  →  /founder/*     →  Authority, reversibility
Customer           →  /guard         →  Product outcomes
```

**Rules:**
- No fourth plane
- No permission blur
- No "convenience" exceptions
- No cross-plane leakage

---

## Domain Architecture (Authoritative)

### Separated Preflight Model

> **Preflight is not a plane. It's an environment.**
> Environments inherit the blast radius of whatever they touch.
> Shared preflight = delayed incident.

### Final Domain Map

| Domain | Plane | Stage | Audience | Purpose |
|--------|-------|-------|----------|---------|
| `preflight-fops.agenticverz.com` | Founder Ops | Preflight | Founder only | System truth verification |
| `fops.agenticverz.com` | Founder Ops | Production | Founder | Operate & govern system |
| `preflight-console.agenticverz.com` | Customer Experience | Preflight | Founder/Dev/QA (INTERNAL) | Verify customer experience before exposure |
| `console.agenticverz.com` | Customer Experience | Production | Customers | Consume the product |

### Visual Architecture

```
FOUNDER OPS PLANE
────────────────────────────────────────────────────
preflight-fops.agenticverz.com   → Is the system sane?
        │
        │ promote (verify system truth)
        ▼
fops.agenticverz.com             → Run the system


CUSTOMER EXPERIENCE PLANE
────────────────────────────────────────────────────
preflight-console.agenticverz.com → What will users see?
        │                           (INTERNAL ONLY)
        │ promote (verify UX before exposure)
        ▼
console.agenticverz.com           → What users actually see
```

---

## Founder Preflight (preflight-fops.agenticverz.com)

### Purpose
- Verify infra data presence
- Verify cost pipelines
- Verify incident tables
- Verify recovery state
- Validate before promoting to fops.agenticverz.com

### Rules
- Founder-only auth
- Read-only
- Full system visibility
- Zero customer UI reuse
- Explicit banner: "FOUNDER PREFLIGHT"

### Schema: FounderPreflightDTO

```typescript
interface FounderPreflightDTO {
  // Identity
  plane: 'founder';
  environment: 'preflight';
  timestamp: string;

  // Infra Health
  infra: {
    database: { status: 'ok' | 'degraded' | 'down'; latency_ms: number };
    redis: { status: 'ok' | 'degraded' | 'down'; latency_ms: number };
    worker: { status: 'ok' | 'degraded' | 'down'; active_count: number };
    prometheus: { status: 'ok' | 'degraded' | 'down' };
  };

  // Cost Pipeline
  cost_pipeline: {
    last_aggregation: string;
    pending_records: number;
    total_tracked_cents: number;
  };

  // Incident State
  incidents: {
    open_count: number;
    last_24h_count: number;
    severity_breakdown: { critical: number; high: number; medium: number; low: number };
  };

  // Recovery State
  recovery: {
    frozen_tenants: number;
    frozen_keys: number;
    active_guardrails: number;
  };

  // System Truth
  system: {
    version: string;
    deployed_at: string;
    feature_flags: Record<string, boolean>;
  };
}
```

---

## Customer Experience Preflight (preflight-console.agenticverz.com)

### Purpose
**Verify customer experience before exposure.**

This is NOT for customers. It is a shadow environment for founders/developers
to see exactly what customers would see before shipping.

Like iOS TestFlight - internal validation of the customer-facing surface.

### What It Validates
- UI correctness (pixel-for-pixel clone of customer console)
- Data quality (using test tenants)
- Copy & surfacing
- Feature completeness
- Performance at UX layer

### Audience
- Founder
- Core engineers
- Internal QA
- **NEVER customers**

### Rules
- VPN / IP allowlist (internal only)
- Founder auth only
- No SEO, no public DNS discovery
- Same routes/components as console.agenticverz.com
- Different data source (ENV-level switch, not UI-level)
- No `if (preflight)` in components
- Customers must NEVER know this exists

### Schema: CustomerPreflightDTO

```typescript
interface CustomerPreflightDTO {
  // Identity
  plane: 'customer';
  environment: 'preflight';
  timestamp: string;
  tenant_id: string;

  // Account Status
  account: {
    status: 'active' | 'suspended' | 'pending';
    plan: string;
    created_at: string;
  };

  // API Keys
  keys: {
    total_count: number;
    active_count: number;
    has_valid_key: boolean;
  };

  // Limits (What applies to you)
  limits: {
    budget_limit_cents: number;
    rate_limit_per_minute: number;
    rate_limit_per_day: number;
    max_cost_per_request_cents: number;
  };

  // Readiness
  readiness: {
    account_configured: boolean;
    api_key_valid: boolean;
    limits_set: boolean;
    ready_to_use: boolean;
  };

  // Recent Activity (Customer's own)
  recent: {
    runs_last_24h: number;
    spend_last_24h_cents: number;
    incidents_last_24h: number;
  };
}
```

---

## Hard Rules (Non-Negotiable)

### Plane Separation
1. **preflight-fops and preflight-console serve different purposes**
   - preflight-fops: System truth verification
   - preflight-console: Customer experience verification
2. **No shared auth tokens between planes**
3. **Different schemas for system vs experience data**

### Customer Experience Preflight (preflight-console)
4. **preflight-console is INTERNAL ONLY**
   - VPN / IP allowlist required
   - Founder auth only
   - No SEO, no public DNS discovery
   - Customers must NEVER know this exists

5. **preflight-console and console share UI code**
   - Same routes, same components, same copy
   - Different data sources (ENV-level switch)
   - **No `if (preflight)` in components**
   - Build-time or deploy-time switch only

6. **Customers never see "preflight" banners**
   - Because they never see preflight at all

### Promotion Rules
7. **Cross-plane promotion is NEVER allowed**
8. **Same-plane promotion only: preflight → production**

If any of these are violated, separation collapses.

---

## Promotion Rules

### Definition
Promotion = Preflight → Production, same plane only.

### Founder Promotion
```
preflight-fops.agenticverz.com → fops.agenticverz.com
```

Checklist:
- [ ] All infra checks pass
- [ ] Cost pipeline healthy
- [ ] No critical incidents open
- [ ] Recovery state understood
- [ ] Founder auth verified

### Customer Promotion
```
preflight-console.agenticverz.com → console.agenticverz.com
```

Checklist:
- [ ] Account configured
- [ ] API key valid
- [ ] Limits set
- [ ] Readiness = true
- [ ] Customer auth verified

### Cross-Plane Promotion
**NEVER ALLOWED.**

---

## What Will NOT Happen

- No dashboards added
- No AI "insights" added
- No automation added
- No "smart" recommendations added
- No customer recovery controls added
- No shared preflight code

Any `if (isFounder) showMore()` patterns are traps and must be deleted.

---

## Next Phase: Founder-Led Beta

With Runtime v1 frozen, the next phase is:

1. **3-7 real users** with real workloads
2. **Watch every failure**
3. **Fix surfacing, not semantics** (UI/docs fixes only)
4. **Bugs are bugs** (not feature requests)
5. **Pricing & positioning** only after validation

---

## Audit Trail

| Time | Action | Result |
|------|--------|--------|
| 2025-12-26 | Phase 5E-4 completed | Customer Essentials done |
| 2025-12-26 | Runtime v1 feature freeze declared | This document |
| 2025-12-26 | Separated preflight architecture defined | Domain map locked |
| 2025-12-26 | FounderPreflightDTO defined | Schema locked |
| 2025-12-26 | CustomerPreflightDTO defined | Schema locked |
| 2025-12-26 | Promotion rules defined | Cross-plane never allowed |

---

## References

- Phase 5E completion: PIN-179, PIN-180, PIN-181, PIN-182
- Three-plane architecture: PIN-182
- Contract framework: PIN-170
