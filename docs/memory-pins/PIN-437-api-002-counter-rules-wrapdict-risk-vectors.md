# PIN-437: API-002 Counter-Rules: wrap_dict Risk Vectors

**Status:** 📋 ENFORCED
**Created:** 2026-01-17
**Category:** Governance / Counter-Rules

---

## Summary

Documents risk vectors identified during API-002 remediation to prevent future misuse of wrap_dict pattern

---

## Details

## Risk Vectors Identified

During API-002 (Response Envelope) remediation, two risk vectors were identified that could lead to future violations while technically passing the guardrail check.

---

## RISK-001: 'Just wrap it' Mentality

### Problem
Future developers may copy-paste the pattern:
```python
return wrap_dict(some_object)
```

This passes API-002 check but violates domain integrity if `some_object` is:
- A raw ORM/SQLModel entity
- An internal domain object
- A partial computation result

### Counter-Rule (API-002-CR-001)
> `wrap_dict()` must ONLY receive:
> 1. `model_dump()` output from Pydantic models
> 2. Fully constructed response dictionaries
>
> **Never** internal domain objects, ORM entities, or partial results.

### Valid Examples
```python
# ✅ CORRECT
return wrap_dict(result.model_dump())
return wrap_dict({'key': 'value', 'count': 42})

# ❌ VIOLATION
return wrap_dict(orm_entity)
return wrap_dict(domain_service.get_internal_state())
```

---

## RISK-002: Ad-hoc Total Computation

### Problem
Pattern used during remediation:
```python
return wrap_dict({'items': [...], 'total': len(results)})
```

This is correct **today** for non-paginated endpoints, but becomes a lie when:
- Pagination is later added (`total ≠ len(current_page)`)
- Results are pre-filtered (`total` reflects filtered, not actual)
- DB-level counts diverge from in-memory counts

### Counter-Rule (API-002-CR-002)
> The `{'items': [...], 'total': len(results)}` pattern is valid ONLY for:
> - Non-paginated endpoints
> - Endpoints where `results` represents the **complete** dataset
>
> For paginated endpoints, `total` MUST come from a separate `COUNT(*)` query.

### Valid Examples
```python
# ✅ CORRECT - Non-paginated endpoint
results = service.get_all_items()
return wrap_dict({'items': [r.model_dump() for r in results], 'total': len(results)})

# ✅ CORRECT - Paginated endpoint
items = service.get_page(offset, limit)
total = service.count_total()  # Separate COUNT(*) query
return wrap_dict({'items': [i.model_dump() for i in items], 'total': total})

# ❌ VIOLATION - Paginated but using len()
items = service.get_page(offset, limit)
return wrap_dict({'items': items, 'total': len(items)})  # LIES about total
```

---

## Enforcement

1. **Code Review Gate**: Any PR using `wrap_dict` must verify counter-rules
2. **Docstring Warning**: Added to `wrap_dict()` function in `app/schemas/response.py`
3. **Governance Doc**: Added to `docs/architecture/GOVERNANCE_GUARDRAILS.md` under API-002

## Related
- API-002: Response Envelope Consistency
- `scripts/ci/check_response_envelopes.py`
- `backend/app/schemas/response.py`
