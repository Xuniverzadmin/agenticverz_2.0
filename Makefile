.PHONY: up down logs rebuild shell clean test help lint-fix lint-check

# Default API key for development
export AOS_API_KEY ?= nova-dev-key-change-me

help:
	@echo "NOVA Agent Manager - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Services:"
	@echo "  make up       - Build and start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - Tail logs from all services"
	@echo "  make rebuild  - Force rebuild and restart"
	@echo "  make shell    - Open shell in backend container"
	@echo "  make clean    - Stop and remove all containers, volumes"
	@echo "  make test     - Run curl test suite"
	@echo ""
	@echo "Code Quality (Governance-Safe Commit Mode):"
	@echo "  make lint-fix   - Auto-fix lint errors and format code"
	@echo "  make lint-check - Check lint errors without fixing"
	@echo ""
	@echo "Governance-Safe Workflow:"
	@echo "  1. Write code"
	@echo "  2. make lint-fix    (explicit mutation)"
	@echo "  3. git add <files>  (stage changes)"
	@echo "  4. git commit       (check-only hooks verify)"
	@echo ""
	@echo "Environment Variables:"
	@echo "  AOS_API_KEY   - API key for authentication (default: nova-dev-key-change-me)"

up:
	@echo "Starting NOVA Agent Manager..."
	docker compose up --build -d
	@echo ""
	@echo "Services started. API available at http://localhost:8000"
	@echo "API Key: $(AOS_API_KEY)"
	@echo ""
	@echo "Run 'make logs' to view logs"
	@echo "Run 'make test' to run test suite"

down:
	@echo "Stopping NOVA Agent Manager..."
	docker compose down

logs:
	docker compose logs -f

rebuild:
	@echo "Rebuilding NOVA Agent Manager..."
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	@echo "Rebuild complete."

shell:
	docker compose exec backend /bin/bash

clean:
	@echo "Cleaning up all containers and volumes..."
	docker compose down -v --remove-orphans
	@echo "Cleanup complete."

# =============================================================================
# CODE QUALITY (Governance-Safe Commit Mode - PIN-290)
# =============================================================================
# Non-Mutating Tooling Invariant:
# - Pre-commit hooks are CHECK-ONLY (no auto-fix)
# - All mutation happens EXPLICITLY via lint-fix
# - This prevents stash conflicts during constitutional commits
#
# Reference: PIN-290 (Non-Mutating Tooling Invariant)

lint-fix:
	@echo "Running lint auto-fix (explicit mutation)..."
	@echo "============================================="
	@echo ""
	@echo "[1/4] Fixing trailing whitespace..."
	@find backend sdk scripts -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.sh" 2>/dev/null | xargs -I{} sed -i 's/[[:blank:]]*$$//' {} 2>/dev/null || true
	@echo "[2/4] Fixing EOF newlines..."
	@find backend sdk scripts -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.sh" 2>/dev/null | while read f; do if [ -f "$$f" ] && [ -s "$$f" ]; then sed -i -e '$$a\' "$$f" 2>/dev/null || true; fi; done
	@echo "[3/4] Fixing lint errors..."
	ruff check . --fix || true
	@echo "[4/4] Formatting code..."
	ruff format .
	@echo ""
	@echo "Done. Now stage changes with: git add <files>"

lint-check:
	@echo "Running lint check (no auto-fix)..."
	@echo "===================================="
	ruff check .
	ruff format --check .

# =============================================================================
# TESTING
# =============================================================================

test:
	@echo "Running NOVA API Test Suite"
	@echo "============================"
	@echo ""
	@echo "1. Health Check..."
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@echo "2. Creating Agent..."
	@AGENT_RESPONSE=$$(curl -s -X POST "http://localhost:8000/agents" \
		-H "Content-Type: application/json" \
		-H "X-AOS-Key: $(AOS_API_KEY)" \
		-d '{"name":"nova-test-agent"}'); \
	echo "$$AGENT_RESPONSE" | python3 -m json.tool; \
	AGENT_ID=$$(echo "$$AGENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['agent_id'])"); \
	echo ""; \
	echo "3. Posting Goal (agent: $$AGENT_ID)..."; \
	GOAL_RESPONSE=$$(curl -s -X POST "http://localhost:8000/agents/$$AGENT_ID/goals" \
		-H "Content-Type: application/json" \
		-H "X-AOS-Key: $(AOS_API_KEY)" \
		-d '{"goal":"fetch github zen wisdom"}'); \
	echo "$$GOAL_RESPONSE" | python3 -m json.tool; \
	echo ""; \
	echo "4. Recalling Memory..."; \
	curl -s "http://localhost:8000/agents/$$AGENT_ID/recall?query=wisdom&k=5" \
		-H "X-AOS-Key: $(AOS_API_KEY)" | python3 -m json.tool; \
	echo ""; \
	echo "5. Getting Provenance..."; \
	curl -s "http://localhost:8000/agents/$$AGENT_ID/provenance?limit=5" \
		-H "X-AOS-Key: $(AOS_API_KEY)" | python3 -m json.tool; \
	echo ""; \
	echo "============================"
	@echo "Test suite complete!"
