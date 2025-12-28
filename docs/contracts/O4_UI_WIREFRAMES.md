# O4 UI Wireframes (Implementation-Grade)

**Status:** FROZEN
**Date:** 2025-12-28
**Reference:** O4_UI_ACCEPTANCE_CRITERIA.md v2

---

## Purpose

These wireframes are **structurally aligned**, not visually identical.
Build directly against these layouts.

---

## A. CUSTOMER O4 — `console.agenticverz.com`

**Route:** `/insights/predictions`

```
┌───────────────────────────────────────────────────────────┐
│ Insights                                                   │
│ Advisory Predictions                                      │
│ Informational only • Does not affect system behavior      │
├───────────────────────────────────────────────────────────┤
│ Filters: [ All ] [ Incident Risk ] [ Spend Spike ] [ PD ]│
├───────────────────────────────────────────────────────────┤
│ ○ Incident Risk (Advisory)                                │
│   Observed pattern may indicate elevated incident risk.  │
│   Confidence: 82%        Expires in 24 min                │
│                                                           │
│ ○ Spend Spike (Advisory)                                  │
│   Recent spend pattern may indicate a spike.              │
│   Confidence: 71%        Expires in 18 min                │
│                                                           │
│ ○ Policy Drift (Advisory)                                 │
│   Observed similarity to past policy patterns.            │
│   Confidence: 65%        Expires in 12 min                │
├───────────────────────────────────────────────────────────┤
│ No advisory predictions available.   [empty state]       │
└───────────────────────────────────────────────────────────┘
```

### Key Elements

| Element | Content | Notes |
|---------|---------|-------|
| Page Title | "Insights" | Not "Alerts" or "Warnings" |
| Subtitle | "Advisory Predictions" | Redundant advisory cue |
| Helper Text | "Informational only • Does not affect system behavior" | Required |
| Filters | Type-based, client-side | No "severity" filter |
| Card Header | "{Type} (Advisory)" | Badge required |
| Card Body | Advisory sentence | From copy blocks |
| Card Footer | Confidence + Expiry | Small text, neutral |
| Empty State | "No advisory predictions available." | Exact text required |

---

## B. FOPS O4 — `fops.agenticverz.com`

**Route:** `/oversight/predictions`

```
┌───────────────────────────────────────────────────────────┐
│ Oversight • Advisory Predictions                          │
├───────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐   │
│ │ ⚠ Advisory Signals Only                             │   │
│ │ These do not trigger, justify, or recommend actions.│   │
│ │ Use for situational awareness only.                 │   │
│ └─────────────────────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────┤
│ Filters: [ All Tenants ] [ Incident ] [ Spend ] [ Policy ]│
├───────────────────────────────────────────────────────────┤
│ Tenant: ACME-PROD                                         │
│ ○ Policy Drift (Advisory)                                 │
│   Observed similarity to past policy enforcement patterns │
│   Confidence: 74%        Expires in 22 min                │
│                                                           │
│ Tenant: BETA-LAB                                          │
│ ○ Spend Spike (Advisory)                                  │
│   Observed spend pattern may indicate spike.              │
│   Confidence: 69%        Expires in 15 min                │
├───────────────────────────────────────────────────────────┤
│ No advisory predictions available.   [empty state]       │
└───────────────────────────────────────────────────────────┘
```

### Key Elements

| Element | Content | Notes |
|---------|---------|-------|
| Page Title | "Oversight • Advisory Predictions" | Combined header |
| Containment Banner | 3-line disclaimer | **CANNOT BE DISMISSED** |
| Banner Icon | ⚠ (info, not warning) | Neutral, not urgent |
| Filters | Tenant + Type filters | Client-side only |
| Tenant Label | "Tenant: {name}" | Context, not target |
| Card Header | "{Type} (Advisory)" | Badge required |
| Card Body | Advisory sentence | From copy blocks |
| Card Footer | Confidence + Expiry | Small text, neutral |
| Empty State | "No advisory predictions available." | Exact text required |

---

## C. LAYOUT COMPARISON

| Element | Customer O4 | FOPS O4 |
|---------|-------------|---------|
| Route | `/insights/predictions` | `/oversight/predictions` |
| Containment Banner | ❌ None | ✅ Required |
| Tenant Visibility | ❌ Hidden | ✅ Visible |
| Cross-Tenant | ❌ No | ✅ Yes |
| Filters | Type only | Tenant + Type |
| Card Structure | Same | Same |
| Empty State | Same | Same |

---

## D. COMPONENT SPECIFICATIONS

### Prediction Card (Shared)

```
┌─────────────────────────────────────────────────────────┐
│ ○ {Prediction Type} (Advisory)                          │
│   {Advisory sentence from copy blocks}                  │
│   Confidence: {N}%        Expires in {M} min            │
└─────────────────────────────────────────────────────────┘
```

**Styling:**
- Circle indicator: Neutral gray, not colored
- "(Advisory)" badge: Light gray background
- Confidence: Small text, no emphasis
- Expiry: Small text, neutral

### Containment Banner (FOPS Only)

```
┌─────────────────────────────────────────────────────────┐
│ ⚠ Advisory Signals Only                                 │
│ These do not trigger, justify, or recommend actions.    │
│ Use for situational awareness only.                     │
└─────────────────────────────────────────────────────────┘
```

**Styling:**
- Background: Light gray or light blue
- Border: 1px solid neutral
- Icon: Info icon, not warning
- Font: Normal weight, not bold
- **FIXED POSITION**: Cannot scroll away
- **NON-DISMISSABLE**: No X button

### Filter Bar

```
[ All ] [ Incident Risk ] [ Spend Spike ] [ Policy Drift ]
```

**Customer:** Type filters only
**FOPS:** Add tenant dropdown:
```
[ All Tenants ▾ ] [ All ] [ Incident ] [ Spend ] [ Policy ]
```

### Empty State

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│            No advisory predictions available.           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Styling:**
- Centered text
- Neutral gray color
- No icons (no checkmark, no "all clear" imagery)

---

## E. FORBIDDEN UI PATTERNS

| Pattern | Reason | Alternative |
|---------|--------|-------------|
| Red/amber cards | Implies urgency | Gray/blue neutral |
| Bold confidence | Implies importance | Small, normal weight |
| Severity badges | Implies ranking | "(Advisory)" only |
| Action buttons | Implies enforcement | None |
| Sorting by confidence | Implies priority | Chronological default |
| "All clear" empty state | Implies safety | Neutral "none available" |
| Collapsible banner (FOPS) | Loses containment | Fixed, non-dismissable |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| O4_UI_ACCEPTANCE_CRITERIA.md | Acceptance rules |
| O4_UI_COPY_BLOCKS.md | Pre-approved language |
| O4_ADVISORY_UI_CONTRACT.md | Contract |
