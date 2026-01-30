# hoc_cus_incidents_L6_drivers_postmortem_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/postmortem_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for post-mortem analytics operations (async)

## Intent

**Role:** Data access for post-mortem analytics operations (async)
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** PostMortemEngine (L5)

## Purpose

Post-Mortem Driver (L6)

---

## Functions

### `get_postmortem_driver(session: AsyncSession) -> PostMortemDriver`
- **Async:** No
- **Docstring:** Factory function to get PostMortemDriver instance.
- **Calls:** PostMortemDriver

## Classes

### `PostMortemDriver`
- **Docstring:** L6 driver for post-mortem analytics operations (async).
- **Methods:** __init__, fetch_category_stats, fetch_resolution_methods, fetch_recurrence_data, fetch_resolution_summary, fetch_similar_incidents

## Attributes

- `logger` (line 70)
- `__all__` (line 313)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

PostMortemEngine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_postmortem_driver
      signature: "get_postmortem_driver(session: AsyncSession) -> PostMortemDriver"
  classes:
    - name: PostMortemDriver
      methods: [fetch_category_stats, fetch_resolution_methods, fetch_recurrence_data, fetch_resolution_summary, fetch_similar_incidents]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
