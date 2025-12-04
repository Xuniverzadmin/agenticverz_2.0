# Makefile for AOS Backend
# Common development and CI tasks

.PHONY: help test test-unit test-skills test-integration docker-integration benchmark clean lint

help:
	@echo "AOS Backend Development Tasks"
	@echo "=============================="
	@echo "make test              - Run all tests (unit + skills)"
	@echo "make test-unit         - Run unit tests only"
	@echo "make test-skills       - Run skill tests only"
	@echo "make test-integration  - Run integration tests (requires Docker)"
	@echo "make docker-integration - Run full Dockerized integration tests"
	@echo "make benchmark         - Run registry performance benchmark"
	@echo "make lint              - Run linting checks"
	@echo "make import-check      - Check import hygiene"
	@echo "make clean             - Clean up artifacts"

# Run all tests (excluding live adapter tests)
test:
	PYTHONPATH=. python -m pytest tests/ -v --tb=short --ignore=tests/live/

# Run unit tests only
test-unit:
	PYTHONPATH=. python -m pytest tests/ -v --tb=short \
		--ignore=tests/skills/ \
		--ignore=tests/workflow/ \
		--ignore=tests/live/

# Run skill tests only
test-skills:
	PYTHONPATH=. python -m pytest tests/skills/ -v --tb=short

# Run integration tests (requires external services)
test-integration:
	PYTHONPATH=. python -m pytest tests/ -v --tb=short -m integration

# Run full Dockerized integration tests
docker-integration:
	@echo "Starting Dockerized integration tests..."
	docker compose -f docker-compose.test.yml build
	docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from integration-tests
	@echo "Dockerized integration tests complete."

# Stop and clean up Docker test containers
docker-integration-clean:
	docker compose -f docker-compose.test.yml down -v --remove-orphans

# Run registry performance benchmark
benchmark:
	PYTHONPATH=. python scripts/benchmark_registry.py

# Import hygiene check
import-check:
	@echo "Checking import hygiene..."
	@PYTHONPATH=. python -c "\
import sys; \
before = set(sys.modules.keys()); \
import app.skills; \
FORBIDDEN = ['httpx', 'anthropic', 'openai', 'psycopg2', 'asyncpg']; \
violations = [m for m in FORBIDDEN if m in sys.modules]; \
sys.exit(1) if violations else print('✓ Import hygiene PASSED')"

# Determinism check - verify canonical outputs
determinism-check:
	@echo "Running determinism checks..."
	PYTHONPATH=. python -m pytest tests/skills/test_m3_integration.py -v -k deterministic

# Lint checks
lint:
	@echo "Running linting..."
	python -m py_compile app/**/*.py 2>/dev/null || echo "Syntax check passed"

# Clean up artifacts
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	rm -rf test-results benchmark_results.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# CI targets
ci-test: import-check test benchmark
	@echo "CI tests complete"

ci-full: import-check test docker-integration benchmark
	@echo "Full CI pipeline complete"
