# How M25 Works (Internal Reference)

**Author:** Claude (for future you)
**Date:** 2025-12-23
**Status:** FROZEN

---

## One Sentence

**Every incident can become a prevention, without manual runtime intervention.**

---

## The Loop

```
Incident → Pattern → Recovery → Policy → Prevention
    ↑                                         |
    └─────────────────────────────────────────┘
```

1. **Incident occurs** (user request triggers guardrail)
2. **Pattern extracted** (signature: model, category, severity, error type)
3. **Recovery generated** (suggested fix + evidence)
4. **Policy created** (rule to block similar future requests)
5. **Prevention triggered** (next matching request blocked *before* incident)

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/integrations/events.py` | Event definitions (FROZEN) |
| `backend/app/integrations/prevention_contract.py` | Prevention validation rules (FROZEN) |
| `scripts/ops/m25_graduation_delta.py` | Graduation metrics |
| `backend/app/integrations/dispatcher.py` | Event routing |
| `backend/app/integrations/L3_adapters.py` | Stage-to-stage connectors |

---

## The Prevention Contract (PIN-136)

A prevention record is ONLY valid when:

1. Policy mode is `active` (not shadow, not pending)
2. No incident was created (blocked *before* INSERT)
3. Signature confidence ≥ 0.6
4. tenant_id present
5. pattern_id present
6. policy_id present

Any violation = `PreventionContractViolation` exception.

---

## Graduation Gates

| Gate | Status | Meaning |
|------|--------|---------|
| 1. Prevention | ✅ | Real prevention record exists in prod |
| 2. Rollback | ✅ | Pattern 015 deletion doesn't break loop |
| 3. Timeline | ⏳ | UI shows incident→prevention chain (needs console) |

**2/3 = ROLLBACK_SAFE** (current state)
**3/3 = PRODUCTION_COMPLETE**

---

## What's Frozen

These files have `M25_FROZEN` headers and CI guards:

- `events.py` - Loop event schema
- `m25_graduation_delta.py` - Graduation logic
- `prevention_contract.py` - Prevention validation

To modify: Add `M25_REOPEN` to commit message (invalidates graduation evidence).

---

## Evidence Location

Canonical artifacts at `/evidence/m25/`:
- `policy_activation_*.json` - Active policy proof
- `prevention_*.json` - Prevention record proof
- `graduation_delta_*.json` - Gate status snapshot

**Rule:** Never regenerate. If you need new evidence, create new artifacts.

---

## What M25 Doesn't Do

- No cost tracking (that's M26/M27)
- No unified console (that's M28)
- No quality scoring (that's M29)
- No trust badges (that's M30)

---

## How to Test

```bash
# Run the graduation delta script
python scripts/ops/m25_graduation_delta.py --json

# Check for prevention records
psql $DATABASE_URL -c "SELECT * FROM prevention_records LIMIT 5"

# Check active policies
psql $DATABASE_URL -c "SELECT * FROM policy_rules WHERE mode = 'active'"
```

---

## If Something Breaks

1. Check if frozen files were modified (`git log --oneline -5 backend/app/integrations/`)
2. Check if prevention contract is being violated (look for `PreventionContractViolation` in logs)
3. Check if dispatcher is routing events (look for `IntegrationEvent` in redis)
4. Check if policies are being created (check `policy_rules` table)

---

*"The loop either works or it fails loudly. There is no silent degradation."*
