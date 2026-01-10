# AURORA_L2 Default Projection Rules for UNREVIEWED Intents

**Status:** ACTIVE
**Reference:** design/l2_1/AURORA_L2.md

---

## Governance Principle

> **UNREVIEWED intents may be normalized ONLY in the projection layer. They may never be edited silently upstream.**

All rules below are:
- **Deterministic** (same input → same output)
- **Reversible** (reviewed intents can override)
- **Overridable** (future review changes behavior)

---

## Default Rules

### 1. Expansion Mode Normalization

| Order Level | Default Expansion Mode | Rationale |
|-------------|------------------------|-----------|
| O1 (Summary) | INLINE | Summaries should be visible immediately |
| O2 (List) | INLINE | Lists are primary navigation |
| O3 (Detail) | CONTEXTUAL | Details appear in side panel |
| O4 (Context) | OVERLAY | Context shown in modal |
| O5 (Proof) | NAVIGATE | Proof requires full page |

**Rule:** If UNREVIEWED intent has different expansion mode, normalize to default and emit warning.

---

### 2. Control Binding Verification

Controls are classified into three categories:

#### Known Bound Controls (Fully Functional)

```
FILTER, SORT, SELECT_SINGLE, SELECT_MULTI, DOWNLOAD, NAVIGATE, APPROVE, REJECT
```

These controls have verified backend implementations and are enabled by default.

#### Action Controls Requiring Verification

```
ACKNOWLEDGE, RESOLVE, ACTIVATE, DEACTIVATE, UPDATE_THRESHOLD, UPDATE_LIMIT, UPDATE_RULE, ADD_NOTE
```

For UNREVIEWED intents:
- Show these controls but **disable** them
- Add warning: "Control '{X}' may not be wired (UNREVIEWED)"
- Once intent is REVIEWED, enable the control

#### Unknown Controls

- **Hide** unknown controls entirely
- Log warning for investigation

---

### 3. Control Affordance

| Control Type | Affordance | Display |
|--------------|------------|---------|
| APPROVE, REJECT | `primary` | Prominent button |
| FILTER, SORT, DOWNLOAD, NAVIGATE | `secondary` | Standard control |
| Unverified actions on UNREVIEWED | `disabled` | Grayed out with tooltip |
| Unknown controls | `hidden` | Not rendered |

---

### 4. Visibility Rules

| Condition | Visibility |
|-----------|------------|
| `visible_by_default: true` AND `order_level <= 2` | Visible |
| `nav_required: true` AND `order_level > 2` | Hidden (requires navigation) |
| `order_level >= 4` | Hidden by default (context/proof) |

---

### 5. Topic Collapse Rules

| Condition | Behavior |
|-----------|----------|
| Topic has > 3 panels | Collapse by default |
| Topic has 1-3 panels | Expand by default |
| All panels UNREVIEWED | Add "Migrated" badge |

---

### 6. Visual Weight (Panel Ordering)

Panels within a topic are sorted by visual weight:

```
weight = (5 - order_level) * 10
       + (has_primary_action ? 20 : 0)
       + (visible_by_default ? 15 : 0)
       - (is_unreviewed ? 5 : 0)
```

Higher weight = appears first.

---

### 7. Warning Emission

Warnings are emitted (not suppressed) for:

| Condition | Warning Text |
|-----------|--------------|
| Unbound control on UNREVIEWED | `Control 'X' may not be wired (UNREVIEWED)` |
| Expansion mode normalized | `Expansion mode normalized: X → Y` |
| Unknown control found | `Unknown control 'X' hidden` |

Warnings appear in:
- Browser console (development)
- Projection metadata (production)
- Never in UI to end users

---

## Overriding Rules

Once an intent is REVIEWED:

1. `migration_status` changes to `REVIEWED` or `APPROVED`
2. All projection normalization stops for that intent
3. Intent's declared values are used directly
4. Warnings are cleared

**Process:**
1. Edit intent YAML: `migration_status: REVIEWED`
2. Add `reviewed_by: <name>`
3. Add `reviewed_at: <date>`
4. Re-run compiler
5. Projection builder detects REVIEWED status and skips normalization

---

## Backward Compatibility

The projection builder produces output compatible with:
- `ui_projection_lock.json` (legacy format)
- `PanelContentRegistry.tsx` (existing binding layer)

The `toLegacyFormat()` function converts AURORA_L2 projection to legacy format.

---

## File References

| File | Purpose |
|------|---------|
| `projection_rules.ts` | Rule implementations |
| `projection_builder.ts` | Main builder entry point |
| `design/l2_1/AURORA_L2.md` | Governance |
| `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` | Intent registry |
