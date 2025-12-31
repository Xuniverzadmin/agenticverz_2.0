# Console Slice Mapping

**Reference:** PIN-240 (Seven-Layer Codebase Mental Model)
**Created:** 2025-12-29
**Status:** Active

## Overview

This document maps each console product as a "layer slice" through the seven-layer architecture. A product owns only L1 + L2 + L3 layers. Everything below (L4-L7) is shared platform infrastructure.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCT SLICES                                  │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│     AI Console      │     Ops Console     │       Product Builder           │
│   (Customer View)   │   (Founder View)    │     (Configuration View)        │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│  L1 — Product Experience                                                     │
│  L2 — Product APIs                                                           │
│  L3 — Boundary Adapters                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                           SHARED PLATFORM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  L4 — Domain Engines (System Truth)                                          │
│  L5 — Execution & Workers                                                    │
│  L6 — Platform Substrate                                                     │
│  L7 — Ops & Scripts                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. AI Console (Customer Product)

**Purpose:** Customer-facing AI safety dashboard
**URL Pattern:** `/guard/*`
**Question Answered:** "Is my AI safe right now?"

### L1 — Product Experience

| File Path | Domain | Description |
|-----------|--------|-------------|
| `website/aos-console/console/src/products/ai-console/app/AIConsoleApp.tsx` | Root | Product routing, providers, layout |
| `website/aos-console/console/src/products/ai-console/app/AIConsoleLayout.tsx` | Root | Navigation and shell |
| `website/aos-console/console/src/products/ai-console/pages/overview/OverviewPage.tsx` | Overview | "Is the system okay?" status board |
| `website/aos-console/console/src/products/ai-console/pages/activity/ActivityPage.tsx` | Activity | "What ran / is running?" |
| `website/aos-console/console/src/products/ai-console/pages/incidents/IncidentsPage.tsx` | Incidents | "What went wrong?" |
| `website/aos-console/console/src/products/ai-console/pages/incidents/IncidentDetailPage.tsx` | Incidents | Individual incident detail (O3) |
| `website/aos-console/console/src/products/ai-console/pages/policies/PoliciesPage.tsx` | Policies | "How is behavior defined?" |
| `website/aos-console/console/src/products/ai-console/pages/logs/LogsPage.tsx` | Logs | "What is the raw truth?" |
| `website/aos-console/console/src/products/ai-console/integrations/IntegrationsPage.tsx` | Integrations | Connected services & webhooks |
| `website/aos-console/console/src/products/ai-console/integrations/KeysPage.tsx` | Integrations | API key management |
| `website/aos-console/console/src/products/ai-console/account/SettingsPage.tsx` | Account | Configuration |
| `website/aos-console/console/src/products/ai-console/account/AccountPage.tsx` | Account | Organization & team |
| `website/aos-console/console/src/products/ai-console/account/SupportPage.tsx` | Account | Help & support |

### L2a — Console APIs (AI Console scoped)

| File Path | Description |
|-----------|-------------|
| `backend/app/api/guard.py` | Guard status, freeze/thaw, snapshots |
| `backend/app/api/customer_visibility.py` | Customer-safe filtered views |
| `backend/app/api/onboarding.py` | Customer onboarding flow |
| `backend/app/api/predictions.py` | AI prediction display for customers |

### L3 — Boundary Adapters

| File Path | Description |
|-----------|-------------|
| `backend/app/services/certificate.py` | Compliance certificate generation |
| `backend/app/services/evidence_report.py` | Incident evidence packaging |
| `backend/app/services/email_verification.py` | Email verification adapter |
| `backend/app/services/prediction.py` | Prediction formatting for display |
| `backend/app/services/policy_proposal.py` | Policy proposal adapter |

### NOT Owned by AI Console

These are **shared platform** (L4+) and must NOT have `product: ai-console`:

- `backend/app/api/v1_killswitch.py` — System-wide kill switch (L6 platform, uses tier-gating)
- `backend/app/services/pattern_detection.py` — Domain engine (L4)
- `backend/app/services/recovery_matcher.py` — Domain engine (L4)
- `backend/app/services/recovery_rule_engine.py` — Domain engine (L4)
- `backend/app/services/cost_anomaly_detector.py` — Domain engine (L4)

---

## 2. Ops Console (Founder Product)

**Purpose:** Internal operational visibility and control
**URL Pattern:** `/ops/*`
**Question Answered:** "What's happening across all tenants?"

### L1 — Product Experience

| File Path | Domain | Description |
|-----------|--------|-------------|
| `website/aos-console/console/src/products/ops-console/app/OpsConsoleApp.tsx` | Root | Product routing, providers |
| `website/aos-console/console/src/products/ops-console/pages/dashboard/DashboardPage.tsx` | Dashboard | System-wide metrics |
| `website/aos-console/console/src/products/ops-console/pages/tenants/TenantsPage.tsx` | Tenants | Multi-tenant overview |
| `website/aos-console/console/src/products/ops-console/pages/decisions/DecisionsPage.tsx` | Decisions | Decision timeline viewer |
| `website/aos-console/console/src/products/ops-console/pages/killswitches/KillswitchesPage.tsx` | Killswitches | Global kill switch control |
| `website/aos-console/console/src/products/ops-console/pages/recovery/RecoveryPage.tsx` | Recovery | CARE recovery dashboard |

### L2a — Console APIs (Ops Console scoped)

| File Path | Description |
|-----------|-------------|
| `backend/app/api/ops/dashboard.py` | Ops dashboard metrics |
| `backend/app/api/ops/tenants.py` | Tenant management |
| `backend/app/api/ops/decisions.py` | Decision timeline queries |
| `backend/app/api/ops/recovery.py` | Recovery operations |

### L3 — Boundary Adapters

| File Path | Description |
|-----------|-------------|
| `backend/app/services/ops/tenant_adapter.py` | Multi-tenant data formatting |
| `backend/app/services/ops/decision_formatter.py` | Decision timeline formatting |

---

## 3. Product Builder (Configuration Product)

**Purpose:** Product configuration and AI behavior definition
**URL Pattern:** `/builder/*` or `/products/*`
**Question Answered:** "How should AI behave for this product?"

### L1 — Product Experience

| File Path | Domain | Description |
|-----------|--------|-------------|
| `website/aos-console/console/src/products/product-builder/app/ProductBuilderApp.tsx` | Root | Product routing, providers |
| `website/aos-console/console/src/products/product-builder/pages/products/ProductsPage.tsx` | Products | Product listing |
| `website/aos-console/console/src/products/product-builder/pages/policies/PolicyEditorPage.tsx` | Policies | Policy rule editor |
| `website/aos-console/console/src/products/product-builder/pages/templates/TemplatesPage.tsx` | Templates | Policy templates library |
| `website/aos-console/console/src/products/product-builder/pages/testing/PolicyTesterPage.tsx` | Testing | Policy simulation/testing |

### L2a — Console APIs (Product Builder scoped)

| File Path | Description |
|-----------|-------------|
| `backend/app/api/builder/products.py` | Product CRUD |
| `backend/app/api/builder/policies.py` | Policy definition API |
| `backend/app/api/builder/templates.py` | Template library API |
| `backend/app/api/builder/simulate.py` | Policy simulation API |

### L3 — Boundary Adapters

| File Path | Description |
|-----------|-------------|
| `backend/app/services/builder/policy_compiler.py` | Policy compilation adapter |
| `backend/app/services/builder/template_renderer.py` | Template rendering |

---

## Shared Platform (L4-L7)

These layers are **NEVER** product-owned. They serve all products equally.

### L4 — Domain Engines

| File Path | Domain | Description |
|-----------|--------|-------------|
| `backend/app/services/pattern_detection.py` | CARE | Incident pattern detection |
| `backend/app/services/recovery_matcher.py` | CARE | Recovery action matching |
| `backend/app/services/recovery_rule_engine.py` | CARE | Recovery rule processing |
| `backend/app/services/cost_anomaly_detector.py` | Cost | Cost anomaly detection |
| `backend/app/domain/decision_engine.py` | Decisions | Core decision logic |
| `backend/app/domain/policy_engine.py` | Policies | Policy evaluation engine |

### L5 — Execution & Workers

| File Path | Description |
|-----------|-------------|
| `backend/app/worker/` | All worker implementations |
| `backend/app/workflow/` | All workflow definitions |

### L6 — Platform Substrate

| File Path | Description |
|-----------|-------------|
| `backend/app/auth/` | Authentication infrastructure |
| `backend/app/db/` | Database layer |
| `backend/app/models/` | Data models |
| `backend/app/services/event_emitter.py` | Event infrastructure |
| `backend/app/api/v1_killswitch.py` | System-wide kill switch |
| `website/aos-console/console/src/components/` | Shared UI components |
| `website/aos-console/console/src/lib/` | Shared utilities |

### L7 — Ops & Scripts

| File Path | Description |
|-----------|-------------|
| `scripts/` | All operational scripts |
| `scripts/ops/layer_validator.py` | Layer violation detector |

---

## Slice Boundary Rules

### What a Product Slice CAN Do

1. **L1 pages** can import from L2 (API clients) and L3 (adapters)
2. **L2 routes** can import from L3, L4, and L6
3. **L3 adapters** can import from L4 and L6
4. Products can define product-specific adapters in L3

### What a Product Slice CANNOT Do

1. **L1 CANNOT** import L4, L5, or L6 directly
2. **L2 CANNOT** import L5 (workers) — this is a common violation!
3. **L4/L5/L6 CANNOT** know about products — they are product-agnostic
4. Products CANNOT share L1 pages (each has its own)
5. Products CANNOT modify shared L4 engines

### Cross-Product Rules

1. If AI Console and Ops Console need the same data, it flows through shared L4
2. If Product Builder configures policies, those policies live in L4 (not L3)
3. L3 adapters can be product-specific (translate L4 for that product's needs)

---

## Validation

Use the layer validator to check for violations:

```bash
# Validate entire codebase
python scripts/ops/layer_validator.py

# Validate backend only
python scripts/ops/layer_validator.py --backend

# CI mode (exit 1 on violations)
python scripts/ops/layer_validator.py --ci
```

### Current Known Violations

As of 2025-12-29, the following architectural violations exist:

| Violation Type | Count | Description |
|----------------|-------|-------------|
| L2 -> L5 | 17 | API routes importing worker code directly |

These need refactoring to route through L4 domain engines or L3 adapters.

---

## Diagram: Product Slice Ownership

```
                    ┌─────────────────────────────────────────────────┐
                    │                   PRODUCTS                       │
                    │  (Each owns their own L1 + L2 + L3 slice)       │
                    ├─────────────┬─────────────┬─────────────────────┤
                    │ AI Console  │ Ops Console │  Product Builder    │
                    │   /guard/*  │   /ops/*    │    /builder/*       │
     ┌──────────────┼─────────────┼─────────────┼─────────────────────┤
     │ L1 Pages     │ OverviewPg  │ DashboardPg │   ProductsPg        │
     │              │ ActivityPg  │ TenantsPg   │   PolicyEditorPg    │
     │              │ IncidentsPg │ DecisionsPg │   TemplatesPg       │
     ├──────────────┼─────────────┼─────────────┼─────────────────────┤
     │ L2 APIs      │ guard.py    │ ops/*.py    │   builder/*.py      │
     │              │ cust_vis.py │             │                     │
     ├──────────────┼─────────────┼─────────────┼─────────────────────┤
     │ L3 Adapters  │ certificate │ tenant_fmt  │   policy_compiler   │
     │              │ evidence_rpt│ decision_fmt│   template_render   │
     └──────────────┴─────────────┴─────────────┴─────────────────────┘
                    │                                                  │
                    │              SHARED PLATFORM                     │
                    │         (No product ownership)                   │
     ┌──────────────┼──────────────────────────────────────────────────┤
     │ L4 Domain    │ pattern_detection, recovery_matcher,            │
     │              │ recovery_rule_engine, cost_anomaly_detector,    │
     │              │ decision_engine, policy_engine                   │
     ├──────────────┼──────────────────────────────────────────────────┤
     │ L5 Workers   │ worker/*, workflow/*                             │
     ├──────────────┼──────────────────────────────────────────────────┤
     │ L6 Platform  │ auth/, db/, models/, event_emitter,             │
     │              │ v1_killswitch, components/, lib/                 │
     ├──────────────┼──────────────────────────────────────────────────┤
     │ L7 Ops       │ scripts/*                                        │
     └──────────────┴──────────────────────────────────────────────────┘
```

---

## Appendix: Layer Header Format

Each file should have a layer header comment at the top:

**Python:**
```python
# Layer: L4 — Domain Engine
# Domain: CARE
# Reference: PIN-240
```

**TypeScript/TSX:**
```typescript
// Layer: L1 — Product Experience (Frontend)
// Product: AI Console
// Domain: Overview
// Reference: PIN-240
```

This enables automated layer detection and validation.
