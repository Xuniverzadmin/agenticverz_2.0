# AOS Test Handbook

**Version:** 1.0
**Last Updated:** 2025-12-13

---

## Overview

This handbook covers testing procedures for the AOS (Agentic Operating System) platform, including the console UI, backend API, and SDK integrations.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Access to AOS API (local or production)
- API key for authentication

### Environment Setup
```bash
# Set environment variables
export AOS_API_BASE=http://localhost:8000
export AOS_API_KEY=your-api-key

# Install test dependencies
pip install requests aiohttp pytest
```

---

## Test Suite Overview

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Smoke Tests | `tests/aos-test-suite/smoke_test.py` | Verify all endpoints respond correctly |
| Load Tests | `tests/aos-test-suite/load_test.py` | Measure performance under load |
| Agent Simulation | `tests/aos-test-suite/agent_simulation_test.py` | Test agent workflows |
| Skill Evaluation | `tests/aos-test-suite/skill_evaluation.py` | Validate skill availability |
| Config Validation | `scripts/deploy/verify_config.py` | Check deployment configs |

---

## Running Tests

### 1. Smoke Tests
```bash
cd /root/agenticverz2.0
AOS_API_BASE=http://localhost:8000 AOS_API_KEY=test \
  python3 tests/aos-test-suite/smoke_test.py
```

Expected output:
- 10 tests covering health, capabilities, simulation, recovery
- Pass rate target: 100% (80% minimum acceptable)

### 2. Load Tests
```bash
# Run all load tests
python3 tests/aos-test-suite/load_test.py --test all

# Run specific test
python3 tests/aos-test-suite/load_test.py --test health --concurrency 20 --requests 200

# Mixed workload
python3 tests/aos-test-suite/load_test.py --test mixed --duration 60
```

Performance targets:
- Health endpoint: >1000 RPS, <50ms P95
- Capabilities: >500 RPS, <100ms P95
- Simulate: >100 RPS, <500ms P95

### 3. Agent Simulation
```bash
# Basic simulation
python3 tests/aos-test-suite/agent_simulation_test.py --agents 10 --workflows 100

# Stress test
python3 tests/aos-test-suite/agent_simulation_test.py --stress --stress-duration 60
```

### 4. Skill Evaluation
```bash
python3 tests/aos-test-suite/skill_evaluation.py
```

Reports saved to: `/tmp/skill_evaluation_report.json`

---

## API Endpoints Reference

### Health Endpoints
| Endpoint | Method | Expected Response |
|----------|--------|-------------------|
| `/health` | GET | `{"status": "healthy", "timestamp": "...", "version": "..."}` |
| `/healthz` | GET | `{"status": "ok"}` |

### Runtime Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/runtime/capabilities` | GET | List skills, budget, rate limits |
| `/api/v1/runtime/simulate` | POST | Simulate execution plan |
| `/api/v1/runtime/query` | POST | Query execution state |

### Simulate Request Format
```json
{
  "plan": [
    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
    {"skill": "json_transform", "params": {"jq": ".data"}},
    {"skill": "llm_invoke", "params": {"prompt": "Analyze this data"}}
  ],
  "budget_cents": 1000
}
```

### Simulate Response Format
```json
{
  "feasible": true,
  "estimated_cost_cents": 5,
  "estimated_duration_ms": 2500,
  "step_estimates": [
    {"skill_id": "http_call", "estimated_cost_cents": 0, "estimated_latency_ms": 500},
    {"skill_id": "json_transform", "estimated_cost_cents": 0, "estimated_latency_ms": 10},
    {"skill_id": "llm_invoke", "estimated_cost_cents": 5, "estimated_latency_ms": 2000}
  ],
  "budget_remaining_cents": 995,
  "budget_sufficient": true,
  "risks": []
}
```

---

## Console UI Testing

### Starting Development Server
```bash
cd /root/agenticverz2.0/website/aos-console/console
npm install
npm run dev  # Starts on http://localhost:5173
```

### Testing Login Flow
1. Navigate to `http://localhost:5173/login`
2. Enter API key (e.g., `test` for development)
3. Click "Connect"
4. Should redirect to Dashboard

### Page Tests

| Page | URL | Key Features to Test |
|------|-----|---------------------|
| Dashboard | `/` | Stats cards, recent activity |
| Agents | `/agents` | Agent list, create agent |
| Jobs | `/jobs` | Job list, simulation |
| Blackboard | `/blackboard` | Shared state entries |
| Credits | `/credits` | Balance, transactions |
| Metrics | `/metrics` | Performance charts |

### Console Test Checklist
- [ ] Login with valid API key
- [ ] Login with invalid API key (should show error)
- [ ] Dashboard loads stats
- [ ] Navigation between pages
- [ ] Logout functionality
- [ ] Dark/light theme toggle
- [ ] Responsive layout on mobile

---

## Common Test Scenarios

### Scenario 1: New Agent Workflow
1. Create agent via POST `/api/v1/agents`
2. Verify agent appears in list
3. Simulate a job for the agent
4. Execute the job
5. Check job status and results

### Scenario 2: Budget Enforcement
1. Set budget_cents to 10
2. Create plan with 100 LLM calls (5¢ each = 500¢)
3. Simulate should return `budget_sufficient: false`

### Scenario 3: Skill Availability
1. GET `/api/v1/runtime/capabilities`
2. Verify all expected skills listed
3. Check rate_limit_remaining > 0
4. Verify cost estimates reasonable

### Scenario 4: Error Recovery
1. Simulate a plan with invalid skill
2. Verify error returned with details
3. Check recovery candidates endpoint
4. Verify failure patterns recorded

---

## Interpreting Test Results

### Success Criteria
- Smoke tests: 100% pass
- Load tests: <5% error rate
- Agent simulation: >95% success rate
- Skill evaluation: All skills available

### Common Failures

| Error | Cause | Resolution |
|-------|-------|------------|
| Connection refused | Backend not running | `docker compose up -d` |
| 401 Unauthorized | Invalid API key | Check AOS_API_KEY |
| 403 Forbidden | RBAC permission denied | Verify role permissions |
| 422 Validation Error | Invalid request format | Check request payload |
| 500 Internal Error | Backend exception | Check backend logs |

---

## Continuous Integration

### GitHub Actions Example
```yaml
name: AOS Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker compose up -d
      - name: Run smoke tests
        run: |
          export AOS_API_BASE=http://localhost:8000
          export AOS_API_KEY=test
          python3 tests/aos-test-suite/smoke_test.py
      - name: Run load tests
        run: python3 tests/aos-test-suite/load_test.py --test health --requests 50
```

---

## Reporting Issues

When reporting test failures:
1. Include full command used
2. Include complete error output
3. Include environment details (OS, Python version)
4. Include relevant logs (`docker compose logs backend`)
5. Tag with `[TEST]` prefix in issue title
