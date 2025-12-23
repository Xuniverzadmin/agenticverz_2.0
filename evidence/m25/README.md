# M25 Evidence Artifacts

**Created:** 2025-12-23
**Status:** ROLLBACK_SAFE (2/3 Gates)
**Frozen:** Yes - Never regenerate

---

## The Court Exhibit

These artifacts prove the M25 core invariant:

> **Every incident can become a prevention, without manual runtime intervention.**

---

## Timeline

| Step | Artifact | Timestamp |
|------|----------|-----------|
| 1. Incident created | (via integration loop) | 2025-12-23 |
| 2. Pattern matched | (from failure_patterns) | 2025-12-23 |
| 3. Recovery suggested | (from recovery engine) | 2025-12-23 |
| 4. Policy generated | `pol_eff9bcd477874df3` | 2025-12-23 |
| 5. Policy activated | Mode: SHADOW → ACTIVE | 2025-12-23 |
| 6. Prevention triggered | `prev_ee322953b7764bac` | 2025-12-23 |
| 7. Graduation advanced | ROLLBACK_SAFE (2/3) | 2025-12-23 |

---

## Artifacts

| File | Description |
|------|-------------|
| `policy_activation_pol_eff9bcd477874df3.json` | Active policy with activation audit |
| `prevention_prev_ee322953b7764bac.json` | Real (non-simulated) prevention record |
| `graduation_delta_2025-12-23.json` | Graduation gate status |

---

## Frozen Versions

| Component | Version |
|-----------|---------|
| Loop Mechanics | v1.0.0 |
| Graduation Rules | v1.0.0 |
| Confidence Calculator | CONFIDENCE_V1 |
| Prevention Contract | PIN-136 |

---

## Rules

1. **Never regenerate these artifacts**
2. **Never modify frozen components**
3. **Changes require M25 reopen approval**
4. **Changes invalidate all prior evidence**

---

## Verification

To verify these artifacts are authentic:

```bash
# Check policy exists and is active
psql $DATABASE_URL -c "SELECT id, mode, is_active FROM policy_rules WHERE id = 'pol_eff9bcd477874df3'"

# Check prevention is real (not simulated)
psql $DATABASE_URL -c "SELECT id, is_simulated FROM prevention_records WHERE id = 'prev_ee322953b7764bac'"

# Check graduation status
psql $DATABASE_URL -c "SELECT level, computed_at FROM graduation_history ORDER BY computed_at DESC LIMIT 1"
```

---

## Related Documentation

- PIN-135: M25 Integration Loop Wiring
- PIN-136: M25 Prevention Contract
- PIN-137: M25 Stabilization & Hygiene Freeze
- PIN-140: M25 Complete - ROLLBACK_SAFE
