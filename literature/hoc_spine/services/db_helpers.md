# db_helpers.py

**Path:** `backend/app/hoc/hoc_spine/services/db_helpers.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            db_helpers.py
Lives in:        services/
Role:            Services
Inbound:         services, drivers
Outbound:        none
Transaction:     Flush only (no commit)
Cross-domain:    none
Purpose:         Database helper functions for SQLModel row extraction.
Violations:      none
```

## Purpose

Database helper functions for SQLModel row extraction.

PIN-099: SQLModel Row Extraction Patterns

This module provides helper functions to safely extract values from
SQLModel/SQLAlchemy query results, avoiding common anti-patterns that
cause runtime errors.

Common Issues Prevented:
1. Row objects are truthy even when containing 0/None
2. Row objects don't support direct comparison operators
3. Row objects from .all() are not Python tuples

Usage:
    from app.utils.db_helpers import scalar_or_default, extract_model

    # For scalar queries (COUNT, SUM, AVG, etc.)
    row = session.exec(select(func.count(Model.id))).first()
    count = scalar_or_default(row, default=0)

    # For model queries with potential Row wrapping
    results = session.exec(stmt).all()
    for row in results:
        model = extract_model(row, 'id')

## Import Analysis

**External:**
- `sqlmodel`

## Transaction Boundary

- **Commits:** no
- **Flushes:** yes
- **Rollbacks:** no

## Functions

### `scalar_or_default(row: Optional[Any], default: Any) -> Any`

Extract scalar value from Row or return default.

SQLModel's session.exec(stmt).first() returns a Row object for scalar
queries (like func.count, func.sum). This function safely extracts
the scalar value.

Args:
    row: The Row object from .first(), or None if no results
    default: Value to return if row is None or contains None

Returns:
    The scalar value from row[0], or default if unavailable

Example:
    stmt = select(func.count(Incident.id)).where(...)
    row = session.exec(stmt).first()
    count = scalar_or_default(row, 0)  # Returns int, not Row

### `scalar_or_none(row: Optional[Any]) -> Optional[Any]`

Extract scalar value from Row, returning None if unavailable.

Similar to scalar_or_default but returns None instead of a default.

Args:
    row: The Row object from .first(), or None

Returns:
    The scalar value from row[0], or None

Example:
    stmt = select(func.max(Run.ended_at)).where(...)
    row = session.exec(stmt).first()
    last_time = scalar_or_none(row)  # Returns datetime or None

### `extract_model(row: Any, model_attr: str) -> Any`

Extract model instance from Row or return as-is.

When using session.exec(stmt).all(), results may be:
1. Model instances directly (single model select)
2. Row objects (joins, expressions, order_by with expressions)

This function detects which case and extracts appropriately.

Args:
    row: A result from .all() iteration
    model_attr: An attribute that exists on the model (for detection)

Returns:
    The model instance, extracted from Row if necessary

Example:
    for row in session.exec(select(Incident).order_by(...)).all():
        incident = extract_model(row, 'tenant_id')
        print(incident.title)

### `extract_models(results: List[Any], model_attr: str) -> List[Any]`

Extract model instances from a list of results.

Convenience wrapper around extract_model for processing .all() results.

Args:
    results: List from session.exec(stmt).all()
    model_attr: An attribute that exists on the model

Returns:
    List of extracted model instances

Example:
    results = session.exec(select(Tenant).order_by(...)).all()
    tenants = extract_models(results, 'tenant_id')

### `count_or_zero(row: Optional[Any]) -> int`

Extract count value, guaranteed to return int.

### `sum_or_zero(row: Optional[Any]) -> float`

Extract sum value, guaranteed to return numeric.

### `query_one(session: Any, statement: Any, model_class: Optional[type]) -> Optional[Any]`

Safe single-row query with automatic Row/Model detection.

Handles SQLModel version differences where .first() may return:
- Row tuple (needs [0] extraction)
- Model directly (no extraction needed)

Args:
    session: SQLModel Session
    statement: Select statement
    model_class: Optional model class for isinstance check

Returns:
    Model instance or None

Example:
    user = query_one(session, select(User).where(User.email == email), User)

### `query_all(session: Any, statement: Any, model_class: Optional[type]) -> list`

Safe multi-row query with automatic Row/Model detection.

Handles SQLModel version differences where .all() may return:
- List of Row tuples (needs [0] extraction)
- List of Models directly (no extraction needed)

Args:
    session: SQLModel Session
    statement: Select statement
    model_class: Optional model class for isinstance check

Returns:
    List of model instances

Example:
    users = query_all(session, select(User).where(User.status == 'active'), User)

### `model_to_dict(model: Any, include: Optional[list], exclude: Optional[list]) -> dict`

Convert ORM model to dict to prevent DetachedInstanceError.

Call this BEFORE the session closes to extract values safely.

Args:
    model: ORM model instance
    include: List of attributes to include (None = all)
    exclude: List of attributes to exclude

Returns:
    Dictionary with model values

Example:
    with Session(engine) as session:
        user = session.get(User, user_id)
        user_data = model_to_dict(user, exclude=['password_hash'])
    # user_data is safe to use after session closes
    return user_data

### `models_to_dicts(models: list, include: Optional[list], exclude: Optional[list]) -> list`

Convert list of ORM models to list of dicts.

Args:
    models: List of ORM model instances
    include: List of attributes to include
    exclude: List of attributes to exclude

Returns:
    List of dictionaries

### `safe_get(session: Any, model_class: type, id: Any, to_dict: bool, include: Optional[list], exclude: Optional[list]) -> Any`

Safe session.get() wrapper with optional dict conversion.

Use session.get() for direct ID lookups - it's simpler and always
returns the model directly (not a Row tuple).

Args:
    session: SQLModel Session
    model_class: Model class to query
    id: Primary key value
    to_dict: If True, convert to dict before returning
    include: Attributes to include in dict
    exclude: Attributes to exclude from dict

Returns:
    Model instance, dict, or None

Example:
    # Simple get
    user = safe_get(session, User, user_id)

    # Get as dict (safe after session closes)
    user_data = safe_get(session, User, user_id, to_dict=True)

### `get_or_create(session: Any, model_class: type, defaults: Optional[dict], **kwargs) -> tuple`

Get existing model or create new one.

Similar to Django's get_or_create, but with proper SQLModel handling.

Args:
    session: SQLModel Session
    model_class: Model class
    defaults: Dict of fields to set on creation only
    **kwargs: Fields to filter by

Returns:
    Tuple of (instance, created: bool)

Example:
    user, created = get_or_create(
        session, User,
        defaults={'status': 'active'},
        email='test@example.com'
    )

## Domain Usage

**Callers:** services, drivers

## Export Contract

```yaml
exports:
  functions:
    - name: scalar_or_default
      signature: "scalar_or_default(row: Optional[Any], default: Any) -> Any"
      consumers: ["orchestrator"]
    - name: scalar_or_none
      signature: "scalar_or_none(row: Optional[Any]) -> Optional[Any]"
      consumers: ["orchestrator"]
    - name: extract_model
      signature: "extract_model(row: Any, model_attr: str) -> Any"
      consumers: ["orchestrator"]
    - name: extract_models
      signature: "extract_models(results: List[Any], model_attr: str) -> List[Any]"
      consumers: ["orchestrator"]
    - name: count_or_zero
      signature: "count_or_zero(row: Optional[Any]) -> int"
      consumers: ["orchestrator"]
    - name: sum_or_zero
      signature: "sum_or_zero(row: Optional[Any]) -> float"
      consumers: ["orchestrator"]
    - name: query_one
      signature: "query_one(session: Any, statement: Any, model_class: Optional[type]) -> Optional[Any]"
      consumers: ["orchestrator"]
    - name: query_all
      signature: "query_all(session: Any, statement: Any, model_class: Optional[type]) -> list"
      consumers: ["orchestrator"]
    - name: model_to_dict
      signature: "model_to_dict(model: Any, include: Optional[list], exclude: Optional[list]) -> dict"
      consumers: ["orchestrator"]
    - name: models_to_dicts
      signature: "models_to_dicts(models: list, include: Optional[list], exclude: Optional[list]) -> list"
      consumers: ["orchestrator"]
    - name: safe_get
      signature: "safe_get(session: Any, model_class: type, id: Any, to_dict: bool, include: Optional[list], exclude: Optional[list]) -> Any"
      consumers: ["orchestrator"]
    - name: get_or_create
      signature: "get_or_create(session: Any, model_class: type, defaults: Optional[dict], **kwargs) -> tuple"
      consumers: ["orchestrator"]
  classes: []
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['sqlmodel']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

