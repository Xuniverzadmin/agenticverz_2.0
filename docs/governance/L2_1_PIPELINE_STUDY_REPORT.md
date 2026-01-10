# L2.1 Intent Ingestion Pipeline Study Report

**Date:** 2026-01-10
**Status:** DISCOVERY COMPLETE
**Purpose:** Study before action — understand existing pipeline before proposing fixes

---

## Step 1: Locate Intent Ingestion

### 1.1 Intent Declaration Format

**Finding:** Intents are declared in **CSV format**, NOT YAML.

| Artifact | Location | Role |
|----------|----------|------|
| Source of Truth | `design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv` | Human-editable intent declarations |

**CSV Columns (22 total):**
```
Domain, Subdomain, Topic, Topic ID, Panel ID, Panel Name, Order,
Ranking Dimension, Nav Required, Filtering, Selection Mode, Read,
Download, Write, Write Action, Activate, Activate Action, Action Layer,
Confirmation Required, Control Set (Explicit), Visible by Default,
Replay, Notes
```

### 1.2 YAML Files Identified

| File | Purpose | Role in Pipeline |
|------|---------|------------------|
| `l2_1/journeys/canonical_journeys.yaml` | Journey definitions for capability testing | NOT part of intent pipeline |
| `backend/scripts/sdsr/scenarios/*.yaml` | SDSR E2E scenario definitions | Consumers of projection, not sources |

**Finding:** No YAML-based intent ingestion exists. The CSV is the sole source of truth.

### 1.3 Python Ingestion Scripts

| Script | Location | Input | Output |
|--------|----------|-------|--------|
| `l2_pipeline.py` | `scripts/tools/` | CSV + capabilities CSV | XLSX (versioned) |
| `l2_cap_expander.py` | `scripts/tools/` | CSV files | Expanded XLSX |
| `l2_raw_intent_parser.py` | `scripts/tools/` | XLSX | `ui_intent_ir_raw.json` |
| `intent_normalizer.py` | `scripts/tools/` | raw JSON | `ui_intent_ir_normalized.json` |
| `surface_to_slot_resolver.py` | `scripts/tools/` | normalized JSON | `ui_intent_ir_slotted.json` |
| `intent_compiler.py` | `scripts/tools/` | slotted JSON | `ui_intent_ir_compiled.json` |
| `ui_projection_builder.py` | `scripts/tools/` | compiled JSON | `ui_projection_lock.json` |

### 1.4 Intent Row Creation/Update/Versioning

**Creation:** Manual edit of `L2_1_UI_INTENT_SUPERTABLE.csv`

**Versioning:** Handled via manifest system:
- Location: `design/l2_1/supertable/l2_supertable_manifest.json`
- Current approved version: **v4**
- Versions are CANDIDATE → APPROVED → SUPERSEDED

**Update Process:**
1. Edit CSV
2. Run `python3 scripts/tools/l2_pipeline.py generate vN`
3. Run `python3 scripts/tools/l2_pipeline.py promote vN` (requires human approval)

---

## Step 2: Full Pipeline Map

### 2.1 Pipeline Chain (Verified)

```
L2_1_UI_INTENT_SUPERTABLE.csv  (SOURCE OF TRUTH - edit here)
        │
        ▼
l2_pipeline.py generate vN
        │ (merges with capability_intelligence_all_domains.csv)
        ▼
l2_supertable_vN_cap_expanded.xlsx  (versioned artifact)
        │
        ▼
run_l2_pipeline.sh
   │
   ├─[1]─► l2_raw_intent_parser.py
   │             ▼
   │       ui_intent_ir_raw.json
   │
   ├─[2]─► intent_normalizer.py
   │             ▼
   │       ui_intent_ir_normalized.json
   │
   ├─[2A]► surface_to_slot_resolver.py (PIN-365)
   │             ▼
   │       ui_intent_ir_slotted.json
   │
   ├─[3]─► intent_compiler.py
   │             ▼
   │       ui_intent_ir_compiled.json
   │
   └─[4]─► ui_projection_builder.py
                 ▼
           ui_projection_lock.json  (FROZEN OUTPUT)
                 │
                 ▼
           Copy to website/app-shell/public/projection/
                 │
                 ▼
           PanelContentRegistry.tsx  (UI renderer bindings)
```

### 2.2 Expected Chain vs Actual Chain

| Expected (from user) | Actual |
|----------------------|--------|
| intent.yaml | **CSV** (L2_1_UI_INTENT_SUPERTABLE.csv) |
| python ingestion script | l2_pipeline.py → l2_raw_intent_parser.py |
| L2.1 SuperTable | XLSX (l2_supertable_vN_cap_expanded.xlsx) |
| slot registry | surface_to_slot_resolver.py |
| capability binding | l2_cap_expander.py (merges capabilities) |
| projection builder | ui_projection_builder.py |
| UI renderer | PanelContentRegistry.tsx |

**The chain is CSV-driven, not YAML-driven.**

---

## Step 3: Inventory of Existing Policy-Related Intents

### 3.1 Policy Domain Structure in CSV

| Subdomain | Topic | Panel IDs | Count |
|-----------|-------|-----------|-------|
| ACTIVE_POLICIES | BUDGET_POLICIES | POL-AP-BP-O1, O2, O3 | 3 |
| ACTIVE_POLICIES | RATE_LIMITS | POL-AP-RL-O1, O2, O3 | 3 |
| ACTIVE_POLICIES | APPROVAL_RULES | POL-AP-AR-O1, O2, O3, O4 | 4 |
| POLICY_AUDIT | POLICY_CHANGES | POL-PA-PC-O1, O2, O3, O4, O5 | 5 |
| PROPOSALS | PENDING_PROPOSALS | POL-PR-PP-O1, O2 | 2 |

**Total Policy Panels in CSV:** 17

### 3.2 Policy-Related Topics NOT in CSV

| Topic | Panel Pattern | Status |
|-------|---------------|--------|
| **POLICY_RULES** | POL-RU-* | **NOT EXISTS** |
| **ENFORCEMENT** | POL-EN-* | **NOT EXISTS** |
| **PREVENTION_RECORDS** | POL-PV-* | **NOT EXISTS** |

### 3.3 Search Results

| Search Term | CSV Matches | Projection Matches |
|-------------|-------------|-------------------|
| `policy_rule` | 0 | 0 |
| `POLICY_RULE` | 0 | 0 |
| `enforcement` | 0 | 0 |
| `prevention` | 0 | 0 |
| `POL-RU` | 0 | 0 |
| `ACTIVE_RULES` | 0 | 0 |

**Finding:** No intent for `policy_rules`, `enforcement`, or `prevention_records` has ever been declared.

### 3.4 Related Decision Ledger Review

File: `design/l2_1/supertable/PHASE_2_1_DECISION_LEDGER.md`

**No mention of:**
- Policy rules
- Enforcement
- Prevention records

**Decision ledger focused on:**
- Control proposals (ACTIVATE_TOGGLE, ADD_NOTE, SEARCH, etc.)
- Column proposals (danger_level, requires_interpreter)

---

## Step 4: Precise Explanation of UI Gap

### 4.1 The Gap

**POL-RU-O2 is referenced in SDSR-E2E-004.yaml but:**

| Check | Result |
|-------|--------|
| Intent YAML never existed? | N/A — system uses CSV, not YAML |
| CSV row exists? | **NO** — no POLICY_RULES topic in CSV |
| YAML exists but never ingested? | N/A — wrong model |
| Ingestion exists but slot/binding missing? | **NO** — source is missing |
| Projection intentionally omitted? | **NO** — never declared |

### 4.2 Root Cause

```
POL-RU-O2 was INVENTED by the scenario author (SDSR-E2E-004.yaml)
without a corresponding intent declaration in the source CSV.

The scenario YAML is a CONSUMER of projections, not a SOURCE.
The scenario violated the L2.1 contract by assuming a panel exists.
```

### 4.3 Evidence Trail

| Artifact | POL-RU-O2 Present? |
|----------|-------------------|
| `L2_1_UI_INTENT_SUPERTABLE.csv` | NO |
| `l2_supertable_v4_cap_expanded.xlsx` | NO (implied from CSV) |
| `ui_intent_ir_raw.json` | NO |
| `ui_intent_ir_normalized.json` | NO |
| `ui_intent_ir_slotted.json` | NO |
| `ui_intent_ir_compiled.json` | NO |
| `ui_projection_lock.json` | NO |
| `PanelContentRegistry.tsx` | NO |
| `SDSR-E2E-004.yaml` | **YES** (lines 281, 442) |

**The scenario references a panel_id that never existed anywhere in the pipeline.**

---

## Summary

### What Exists

| Component | Status |
|-----------|--------|
| CSV-based intent source | EXISTS (`L2_1_UI_INTENT_SUPERTABLE.csv`) |
| Pipeline scripts (7) | EXISTS and functional |
| Manifest versioning | EXISTS (currently v4 approved) |
| 17 Policy panels | EXISTS in projection |
| Proposals subdomain | EXISTS (POL-PR-PP-O1, O2) |

### What Is Missing

| Component | Status |
|-----------|--------|
| POLICY_RULES topic in CSV | **MISSING** |
| POL-RU-* panel definitions | **MISSING** |
| ENFORCEMENT topic | **MISSING** |
| PREVENTION_RECORDS topic | **MISSING** |
| YAML-based intent format | **DOES NOT EXIST** (CSV is the format) |

### What Is Ambiguous

| Question | Status |
|----------|--------|
| Should POLICY_RULES be a separate topic or part of ACTIVE_POLICIES? | **UNDECIDED** |
| Should prevention_records have a UI panel? | **UNDECIDED** |
| Should enforcement status be visible? | **UNDECIDED** |
| What Order levels (O1-O5) should POLICY_RULES have? | **UNDECIDED** |

### What Must Be Decided By Humans

1. **Topic Taxonomy:** Should POLICY_RULES be:
   - `POLICIES.ACTIVE_POLICIES.ACTIVE_RULES` (sibling to BUDGET_POLICIES)?
   - `POLICIES.ENFORCEMENT.ACTIVE_RULES` (new subdomain)?
   - `POLICIES.PROPOSALS.ENFORCED_RULES` (under PROPOSALS)?

2. **Order Depth:** What epistemic levels?
   - O1 (summary): "X active rules"
   - O2 (list): List of policy_rules with status
   - O3 (detail): Individual rule detail
   - O4 (context): Related proposals, incidents prevented
   - O5 (proof): Raw policy_rule record

3. **Controls:** What actions on policy_rules?
   - DEACTIVATE? (requires confirmation)
   - EDIT? (modify parameters)
   - VIEW_IMPACT? (show prevented incidents)

4. **Prevention Records:** Should these have a panel?
   - If yes, where in topology?
   - What Order levels?

---

## File References

| Purpose | Path |
|---------|------|
| Intent Source | `design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv` |
| Pipeline Script | `scripts/tools/l2_pipeline.py` |
| Full Pipeline | `scripts/tools/run_l2_pipeline.sh` |
| Manifest | `design/l2_1/supertable/l2_supertable_manifest.json` |
| Raw Parser | `scripts/tools/l2_raw_intent_parser.py` |
| Normalizer | `scripts/tools/intent_normalizer.py` |
| Slot Resolver | `scripts/tools/surface_to_slot_resolver.py` |
| Compiler | `scripts/tools/intent_compiler.py` |
| Projection Builder | `scripts/tools/ui_projection_builder.py` |
| Projection Lock | `design/l2_1/ui_contract/ui_projection_lock.json` |
| Panel Registry | `website/app-shell/src/components/panels/PanelContentRegistry.tsx` |
| Scenario with Gap | `backend/scripts/sdsr/scenarios/SDSR-E2E-004.yaml:281,442` |

---

## Attestation

```
STUDY BEFORE ACTION COMPLETE
- No fixes proposed
- No YAML modified
- No code changes made
- All findings evidence-based with file paths
- Human decisions required before proceeding
```
