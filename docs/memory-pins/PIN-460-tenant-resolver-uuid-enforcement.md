# PIN-460: Tenant Resolver UUID Enforcement

**Status:** COMPLETE
**Created:** 2026-01-21
**Category:** Auth / Infrastructure

---

## Summary

Centralized tenant resolution to enforce valid UUID tenant identifiers. Created `tenant_resolver.py` as the single authority for extracting tenant_id from requests. All services now receive validated UUIDs, never strings.

---

## Details

### Problem Statement

The system had inconsistent tenant_id handling:
- Some code paths accepted string identifiers like `'demo-tenant'` or `'sdsr-tenant-e2e-004'`
- Services were parsing tenant_id from various sources with different validation
- Database queries failed due to UUID vs VARCHAR type mismatches

### Solution: Single Authority Pattern

Created `backend/app/auth/tenant_resolver.py` as the canonical source for tenant identity:

```python
def resolve_tenant_id(request: Request) -> UUID:
    """
    Single authority for tenant resolution.

    Returns: UUID (always valid)
    Raises: HTTPException 400 if tenant_id is invalid or missing
    """
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Returns UUID, never str | Forces callers to handle types correctly |
| Raises HTTP 400 on invalid | Fail fast, no silent fallbacks |
| Single resolution point | No duplicate parsing logic |
| Never infers or guesses | Tenant identity must be explicit |

### Files Modified

**Created:**
- `backend/app/auth/tenant_resolver.py` - Single authority for tenant resolution

**Modified:**
- `backend/app/api/aos_cus_integrations.py` - Uses `resolve_tenant_id()` for all endpoints
- `backend/app/services/cus_integration_service.py` - Converts UUID to str for VARCHAR columns
- `backend/app/models/cus_models.py` - Changed enum fields to str type for DB compatibility

### Type Handling Pattern

Services receive UUID from resolver, convert to str for VARCHAR column comparisons:

```python
# In service methods
tenant_id: UUID  # Received from resolver

# In queries (VARCHAR column)
CusIntegration.tenant_id == str(tenant_id)
```

### Migration Strategy

1. Created `scripts/migrations/fix_demo_tenant_uuid.sql` for data cleanup
2. Created `backend/alembic/versions/c8213cda2be4_add_uuid_constraint_to_tenant_id.py` for schema enforcement
3. Migration adds CHECK constraints enforcing UUID format on tenant_id columns

### Canonical Demo Tenant

| Environment | Tenant UUID |
|-------------|-------------|
| LOCAL | `11111111-1111-1111-1111-111111111101` |
| NEON TEST | `22222222-2222-2222-2222-222222222101` |

---

## Exit Criteria

- [x] `tenant_resolver.py` created as single authority
- [x] All integration endpoints use `resolve_tenant_id()`
- [x] Service layer handles UUID → str conversion for DB queries
- [x] Data migration script created (`fix_demo_tenant_uuid.sql`)
- [x] Alembic migration created for UUID CHECK constraints
- [x] Demo Tenant 101 documented in `docs/architecture/DEMO_TENANT.md`

---

## Invariants Established

1. **Tenant identity MUST be a valid UUID** — No string identifiers allowed
2. **Services receive UUID** — Never parse tenant_id themselves
3. **Resolution is explicit** — No inference, no fallbacks, no guessing
4. **Fail closed** — Invalid tenant_id → HTTP 400, not silent degradation

---

## Related Files

- `backend/app/auth/tenant_resolver.py` — Single authority
- `docs/architecture/DEMO_TENANT.md` — Demo tenant documentation
- `scripts/migrations/fix_demo_tenant_uuid.sql` — Data cleanup
- `backend/alembic/versions/c8213cda2be4_add_uuid_constraint_to_tenant_id.py` — Schema enforcement

---

## Reference

- Contract: `docs/architecture/ENVIRONMENT_CONTRACT.md` (Three-plane auth model)
- Pattern: Single Authority Resolution (no dual parsing)
