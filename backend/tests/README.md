# AOS Test Suite

## Overview

This directory contains all tests for the AOS (Agentic Operating System) backend.

## Test Categories

| Category | Directory/File | Dependencies | Description |
|----------|---------------|--------------|-------------|
| **Unit** | `tests/schemas/` | None | Schema validation, no external deps |
| **Unit** | `tests/unit/` | None | Pure logic tests |
| **Integration** | `tests/test_integration.py` | Redis, PostgreSQL | Service integration |
| **E2E** | `tests/test_phase4_e2e.py` | Full stack | End-to-end flows |
| **Security** | `tests/test_phase5_security.py` | Full stack | Security validation |
| **Worker** | `tests/test_worker_pool.py` | None | Worker pool logic |

## Running Tests

### All Tests (requires services)

```bash
# From backend directory
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=app --cov-report=html
```

### Unit Tests Only (no dependencies)

```bash
python -m pytest tests/schemas/ tests/unit/ -v
```

### Integration Tests (requires Redis + PostgreSQL)

```bash
# Start services first
docker compose up -d db redis

# Run integration tests
python -m pytest tests/test_integration.py -v
```

### By Marker

```bash
# Unit tests
python -m pytest -m unit -v

# Security tests
python -m pytest -m security -v

# Slow tests excluded
python -m pytest -m "not slow" -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://nova:novapass@localhost:5433/nova_aos` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `AOS_API_KEY` | `test-key-for-testing` | API authentication |
| `ENFORCE_TENANCY` | `false` | Tenant isolation |
| `API_BASE_URL` | `http://localhost:8000` | API base URL |

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and config
├── README.md                # This file
├── schemas/
│   ├── __init__.py
│   └── test_m0_schemas.py   # M0 schema validation
├── unit/                    # Pure unit tests (future)
├── test_integration.py      # Integration tests
├── test_phase4_e2e.py       # E2E tests
├── test_phase5_security.py  # Security tests
└── test_worker_pool.py      # Worker tests
```

## Writing Tests

### Unit Test Example

```python
import pytest
from app.schemas.skill import SkillMetadata

@pytest.mark.unit
def test_skill_metadata_validation():
    """Skill metadata validates correctly."""
    metadata = SkillMetadata(
        skill_id="test_skill",
        version="1.0.0",
        name="Test Skill"
    )
    assert metadata.skill_id == "test_skill"
```

### Integration Test Example

```python
import pytest
import httpx

@pytest.mark.integration
def test_health_endpoint(api_base_url):
    """Health endpoint returns 200."""
    response = httpx.get(f"{api_base_url}/health", timeout=10.0)
    assert response.status_code == 200
```

### Determinism Test Example

```python
import pytest

@pytest.mark.determinism
def test_retry_decision_deterministic():
    """Same inputs produce same retry decision."""
    from app.utils.retry import should_retry

    results = [
        should_retry("ERR_HTTP_503", attempt=2, max_retries=3)
        for _ in range(100)
    ]
    assert all(r == results[0] for r in results)
```

## CI Integration

Tests run automatically via GitHub Actions:

- **Unit tests**: Every commit
- **Schema validation**: Every commit
- **Integration tests**: Every PR (with mocked services)
- **E2E tests**: Nightly/release

See `.github/workflows/ci.yml` for configuration.

## Coverage Requirements

| Category | Minimum Coverage |
|----------|-----------------|
| Schemas | 90% |
| Core runtime | 80% |
| Skills | 70% |
| Overall | 75% |

## Fixtures

Common fixtures are defined in `conftest.py`:

- `api_base_url` - Base URL for API tests
- `api_key` - API authentication key
- `auth_headers` - Headers with API key
- `sample_agent_profile` - Sample agent profile
- `sample_skill_metadata` - Sample skill metadata
- `sample_structured_outcome` - Sample outcome

## Troubleshooting

### Tests timing out

Increase httpx timeout:

```python
response = httpx.get(url, timeout=30.0)
```

### Database connection errors

Ensure PostgreSQL is running:

```bash
docker compose up -d db
pg_isready -h localhost -p 5433 -U nova
```

### Redis connection errors

Ensure Redis is running:

```bash
docker compose up -d redis
redis-cli ping
```
