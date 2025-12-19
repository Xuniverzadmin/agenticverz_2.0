# PIN-101: Website Cluster Restructure - From Product-Selling to Capability-Mapping

**Status:** ACTIVE
**Created:** 2025-12-19
**Author:** Claude Opus 4.5
**Depends On:** PIN-095 (AI Incident Console Strategy), PIN-100 (M23 Production)
**Category:** Frontend / Landing Page / UX / Strategy

---

## Executive Summary

The current agenticverz.com landing page conflates two audiences (buyers and investors) and two products (AOS SDK for developers + Build Your App for non-coders). This creates friction, unclear positioning, and buyer hesitation.

This PIN defines the **cluster-based homepage restructure** - transforming from product-selling to **capability-mapping** that lets visitors self-select their entry path.

**Goal:** A homepage where a visitor can understand what we do in <10 seconds and find their path without being sold to prematurely.

---

## Current State Analysis

### What the Page Currently Sells

| Product | Target | CTA |
|---------|--------|-----|
| AOS SDK | Developers building agent infrastructure | "Get Started" |
| Build Your App | Non-coders who want AI without code | "Build your app" |

**Problem:** Two products, two buyers, one homepage - creates cognitive overload.

### Issues Identified

| Issue | Evidence | Impact |
|-------|----------|--------|
| **Two products, two audiences** | AOS (SDK) vs Build Your App (no-code) | Visitors don't know which they are |
| **Investor language on buyer page** | "Moat" tables, VC terminology | Buyers don't care about defensibility |
| **CTA mismatch** | "Build Your App" before explaining what it is | High bounce, low conversion |
| **Manifesto lines** | "Machine-native", philosophical statements | Interesting but premature for new visitors |
| **Abstract feature cards** | "Predictable", "Reliable", "Deterministic" | No concrete benefits visible |

### What Works (KEEP)

| Element | Why It Works |
|---------|--------------|
| Preview-before-execute concept | Differentiator, builds trust |
| 3-step flow clarity | Easy to understand |
| Headline tone | Confident without being arrogant |

---

## Target State: Cluster-Based Homepage

### Information Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HEADER                                          │
│  [Logo]  Products▼  Use Cases  Docs  Pricing  [Request Demo]                │
│          └─ Dropdown: Incident Console | Build Your App | API               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               HERO                                           │
│  "AI decisions happen fast. Yours should too."                              │
│                                                                              │
│  We help teams investigate, govern, and prevent AI failures                 │
│  — before they become support tickets.                                      │
│                                                                              │
│  [See How It Works]  ← Neutral CTA, not asking for commitment yet           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAPABILITY CLUSTERS (4 columns)                          │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│ 🔴 Incident &   │ 📋 Governance & │ 💰 Risk, Cost & │ ⚡ Automation &       │
│    Failure      │    Policy       │    Exposure     │    Remediation        │
│    Management   │    Evaluation   │                 │                       │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ • Incident      │ • Policy        │ • Severity      │ • Safeguard           │
│   Console       │   Evaluation    │   Scoring       │   Suggestions         │
│ • Evidence      │ • Coverage      │ • Cost          │ • Incident-to-Fix     │
│   Export        │   Analysis      │   Attribution   │   Workflows           │
│ • Deterministic │ • Counterfactual│ • Audit Trails  │ • Runtime Controls    │
│   Replay        │   Prevention    │                 │                       │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ [Learn More →]  │ [Learn More →]  │ [Learn More →]  │ [Learn More →]        │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HOW IT FITS INTO YOUR STACK                              │
│  (Thin horizontal flow diagram)                                              │
│                                                                              │
│  [Your LLM] → [AOS Proxy] → [Policy Evaluation] → [Decision] → [Audit Log] │
│                                                                              │
│  "Drop-in proxy between your app and any LLM provider"                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WHO THIS IS FOR                                     │
├────────────────────────────────────┬────────────────────────────────────────┤
│ ✓ Good Fit                         │ ✗ Not For You                          │
├────────────────────────────────────┼────────────────────────────────────────┤
│ • Teams with AI in prod that need  │ • Teams still prototyping              │
│   audit trails                     │ • Hobby projects                       │
│ • Products needing SOC2/compliance │ • Single LLM, no policy needs          │
│ • Support teams debugging AI       │ • "Move fast, break things" mindset    │
│   responses                        │                                        │
└────────────────────────────────────┴────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROOF OF SERIOUSNESS                                  │
│                                                                              │
│  [Deterministic Replay Demo]        [Evidence Export Sample]                │
│                                                                              │
│  "See exactly what happened"        "Export incident report (PDF)"          │
│                                                                              │
│  • No magic, just facts             • SOC2 compatible evidence              │
│  • Full decision trace              • Timestamped, immutable                │
│  • Before/after comparison          • Exportable artifacts                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTRY PATHS (Decision Router)                      │
│                                                                              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │ Explore Incident│  │   Read Docs     │  │ Request Demo    │             │
│   │     Tools       │  │                 │  │                 │             │
│   │                 │  │                 │  │                 │             │
│   │ Interactive tour│  │ API reference,  │  │ Talk to sales,  │             │
│   │ of the console  │  │ integration     │  │ see live        │             │
│   │                 │  │ guides          │  │ environment     │             │
│   │   [Try Now →]   │  │   [Go →]        │  │   [Schedule →]  │             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               FOOTER                                         │
│  Products: Incident Console | Build Your App | API                          │
│  Resources: Docs | Blog | Changelog | Status                                │
│  Company: About | Contact | Terms | Privacy                                 │
│  © 2025 Agenticverz                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What to DELETE

| Element | File | Reason |
|---------|------|--------|
| Moat tables | `App.jsx` | Investor language, not buyer |
| "AOS" primary branding | Throughout | Too abstract for landing page |
| Manifesto lines | Hero section | Save for /about or /philosophy |
| Abstract feature cards | Features section | Replace with capability clusters |
| "Build App" as primary CTA | Header | Should be a product, not main CTA |
| Philosophy/vision statements | Hero | Move to dedicated page |

---

## What to KEEP

| Element | Location | Reason |
|---------|----------|--------|
| Preview-before-execute | Keep as capability | Key differentiator |
| 3-step flow clarity | How it works | Easy comprehension |
| Headline tone | Hero | Confident, not arrogant |
| Demo booking option | Footer/Entry paths | Keep but don't lead with it |

---

## CTA Strategy

### Current (Bad)
```
[Build your app] ← What does this even mean?
[Get Started] ← Start what?
```

### Target (Good)
```
Hero: [See How It Works] ← Low commitment, learn first
Clusters: [Learn More →] ← Context-specific exploration
Entry Paths: [Try Now] [Read Docs] [Schedule Demo] ← Equal weight, self-select
```

**Rule:** No premature commitment. Let visitors explore before asking for signup.

---

## Page-Specific Deep Links

### /incident-console (Deep Page)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AI INCIDENT CONSOLE                                     │
│                                                                              │
│  When AI goes wrong, you need answers - not guesses.                        │
│                                                                              │
│  The AI Incident Console gives you:                                         │
│  • Full decision trace (inputs → policies → outputs)                        │
│  • Search across all incidents by user, time, severity                      │
│  • Deterministic replay ("what would have happened if...")                  │
│  • Evidence export for compliance/legal                                     │
│                                                                              │
│  [See Live Demo]  [Read Docs]  [Request Access]                             │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  FEATURES                                                                    │
│  ├── Decision Timeline (step-by-step trace)                                 │
│  ├── Policy Evaluation (which rules triggered)                              │
│  ├── Counterfactual Analysis (what-if scenarios)                            │
│  ├── Evidence Export (PDF/JSON for audit)                                   │
│  └── Search & Filter (find incidents fast)                                  │
│                                                                              │
│  INTEGRATION                                                                 │
│  "One line change: point your OpenAI client at our proxy"                   │
│  └── [Integration Guide →]                                                  │
│                                                                              │
│  PRICING                                                                     │
│  Starts at $X/mo for Y calls. [See Pricing →]                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Files

### Homepage (`landing/src/App.jsx`)

**Changes:**
1. Replace hero with problem-domain statement
2. Replace feature cards with 4 capability clusters
3. Add "How it fits" integration diagram
4. Add "Who this is for" inclusion/exclusion section
5. Replace CTAs with entry paths (3 equal options)
6. Remove moat tables, investor language

### New Pages

| Page | Route | Purpose |
|------|-------|---------|
| Incident Console | `/incident-console` | Deep dive on M22/M23 product |
| Build Your App | `/build` | Existing page, moved from primary |
| Docs | `/docs` | API reference, guides |
| Pricing | `/pricing` | Clear tier structure |

### Components to Create

| Component | File | Purpose |
|-----------|------|---------|
| CapabilityCluster | `components/CapabilityCluster.jsx` | Reusable cluster card |
| EntryPaths | `components/EntryPaths.jsx` | 3-column CTA section |
| FitSection | `components/FitSection.jsx` | Who this is for/not for |
| IntegrationFlow | `components/IntegrationFlow.jsx` | Horizontal stack diagram |

---

## Stress Tests for New Design

1. **10-second test**: Can a first-time visitor understand what we do in <10 seconds?
   - Current: No (AOS, machine-native, etc.)
   - Target: Yes ("investigate, govern, prevent AI failures")

2. **"What do I click?" test**: Is there one obvious path for each visitor type?
   - Current: No (Build app? Get started? Docs?)
   - Target: Yes (3 equal entry paths based on intent)

3. **Investor vs Buyer test**: Would a buyer be confused by VC language?
   - Current: Yes (moat tables)
   - Target: No (removed)

4. **Mobile scroll test**: Does the IA work on mobile?
   - Current: Untested
   - Target: Clusters stack vertically, CTAs remain prominent

---

## Rollout Plan

### Phase 1: Content Surgery (1 day)
- [ ] Remove moat tables
- [ ] Remove abstract feature cards
- [ ] Update hero copy
- [ ] Add capability clusters
- [ ] Add entry paths section

### Phase 2: Deep Pages (1 day)
- [ ] Create `/incident-console` page
- [ ] Link from cluster "Incident Management"
- [ ] Ensure existing `/build` still works

### Phase 3: Navigation Update (0.5 day)
- [ ] Update header nav
- [ ] Add Products dropdown
- [ ] Update footer links

### Phase 4: Testing (0.5 day)
- [ ] Mobile responsive check
- [ ] Link integrity check
- [ ] Screenshot comparison

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to first meaningful action | Unknown | <15 seconds |
| Bounce rate on hero | Unknown | <40% |
| CTA clarity score (user testing) | Unknown | >8/10 |
| Mobile usability | Unknown | No horizontal scroll |

---

## References

- PIN-095: AI Incident Console Strategy (GTM positioning)
- PIN-100: M23 Production (what we're actually selling)
- PIN-094: Build Your App Landing Page (existing no-code page)
