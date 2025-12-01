# NOVA / AOS Project Notes

> **Project**: agenticverz2.0
> **Codename**: NOVA (New Optimal Virtual Assistant)
> **Architecture**: AOS (Agent Operating System)
> **Phase**: MVA (Minimal Viable Agent)
> **Created**: 2025-11-30

---

## 1. Architecture Decisions (Locked)

### Core Stack
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Runtime | Python 3.11 + FastAPI | Async-first, LLM ecosystem compatibility |
| Database | PostgreSQL 15 | Reliable, future pgvector support |
| Container | Docker Compose | Simple local dev, production-ready |
| Auth | API Key (X-AOS-Key header) | Minimal viable, JWT later in Phase 2 |

### NOT in MVA (Explicitly Deferred)
- Redis (no caching layer yet)
- NATS/Kafka (no event bus yet)
- Vector DB (pgvector later, no Weaviate/Qdrant)
- LLM integration (planner is a stub)
- Containerized skill sandbox (skills run in-process)
- CRDT/edge sync
- Identity Core / Vault

---

## 2. Data Model Design Notes

### Agent
```
id: UUID (primary key)
name: string
status: enum [active, paused, stopped]
created_at: timestamp
updated_at: timestamp
```
**Note**: `status` field added for lifecycle management. Phase 1 will add `stop_agent`, `pause_agent` endpoints.

### Memory
```
id: UUID
agent_id: UUID (indexed)
memory_type: enum [skill_result, user_input, system, context]
text: string
meta: JSON string (nullable)
created_at: timestamp
```
**Note**: `memory_type` added for future filtering/categorization. Vector embeddings will be added when we swap to pgvector.

### Provenance
```
id: UUID (also serves as run_id)
agent_id: UUID (indexed)
goal: string
status: enum [pending, running, completed, failed, partial]
plan_json: string
tool_calls_json: string
error_message: string (nullable)
created_at: timestamp
completed_at: timestamp (nullable)
```
**Note**: `status` and `error_message` added for failure tracking. `completed_at` separate from `created_at` for duration calculation.

---

## 3. API Design Notes

### Endpoints Implemented (v0.2.0)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | No | Health check with DB validation |
| GET | /version | No | Version info |
| POST | /agents | Yes | Create agent |
| GET | /agents/{id} | Yes | Get agent |
| POST | /agents/{id}/goals | Yes | Submit goal (returns 202 + run_id) |
| GET | /agents/{id}/runs | Yes | List runs for agent |
| GET | /agents/{id}/runs/{run_id} | Yes | Get run status and results |
| GET | /agents/{id}/recall | Yes | Query memory |
| GET | /agents/{id}/provenance | Yes | List provenance records |
| GET | /agents/{id}/provenance/{prov_id} | Yes | Get specific provenance |

### Endpoints TODO (Phase 1)
- `DELETE /agents/{id}` - Delete agent
- `PATCH /agents/{id}` - Update agent (name, status)
- `POST /agents/{id}/stop` - Stop running goal
- `GET /agents` - List all agents (paginated)
- `DELETE /agents/{id}/memory/{memory_id}` - Delete specific memory

### API Conventions
- All timestamps returned as ISO 8601 strings
- All IDs are UUIDs
- Errors return `{"detail": "message"}`
- Request tracing via `X-Request-ID` response header

---

## 4. Skill System Design

### Current: In-Process Skills
Skills run directly in the FastAPI process. Simple but not isolated.

```python
async def run_http_skill(params: Dict) -> Dict:
    # Makes HTTP call, returns result
```

### Future: Sandboxed Skills (Phase 2+)
Two-tier model:
1. **Hot skills**: Pre-warmed worker pool, <500ms latency
2. **Cold skills**: On-demand container spin-up, 1-3s latency

Skill manifest (future):
```yaml
skill_id: http_call
version: 1.0.0
capabilities: [network_egress]
auth_type: none
input_schema: {...}
output_schema: {...}
side_effects: idempotent
```

---

## 5. Course Corrections for GPT

### Things GPT Got Right
1. ✅ Unified ASL for MVA (don't split MemoryStore/GraphStore/EventStore yet)
2. ✅ Event bus for multi-agent (NATS, not Kafka for simplicity)
3. ✅ Two-tier skill latency model (hot/cold)
4. ✅ Minimal JWT in Phase 0 (we used API key, acceptable)

### Things to Clarify/Correct

#### 5.1 Planner Fallback Strategy
**GPT said**: "How should Planner handle LLM provider outages?"
**Decision**: For MVA, planner is a stub. When we add LLM:
- Primary: Anthropic Claude
- Fallback: OpenAI GPT-4
- Last resort: Queue goals with exponential backoff (not rule-based fallback)

#### 5.2 Agent-to-Agent Communication
**GPT said**: "Direct RPC or event bus?"
**Decision**:
- Phase 1: No agent-to-agent (single agent only)
- Phase 2: Event bus (NATS) for async coordination
- Phase 3: Direct gRPC for tight coupling (rare cases only)

#### 5.3 Rollback Semantics
**GPT said**: "Should skills declare compensating actions?"
**Decision**:
- MVA: No rollback, provenance only (audit trail)
- Phase 2: Skills declare `reversible: true/false`
- Phase 3: Saga pattern for multi-skill transactions (only if needed)

#### 5.4 Identity Timeline
**GPT said**: "Minimal identity in Phase 0?"
**Decision**: API key is sufficient for MVA. Full Identity Core (JWT + refresh tokens + agent identity) in Phase 2 before multi-tenant.

#### 5.5 pgvector Migration Trigger
**GPT asked**: "At what scale migrate from pgvector to dedicated vector DB?"
**Decision**:
- <100K memories: pgvector is fine
- 100K-1M: Evaluate Qdrant (simpler than Weaviate)
- >1M: Mandatory migration to Qdrant/Milvus
- Make vector store a pluggable adapter from start

---

## 6. Implementation Checklist

### MVA (Current Phase)
- [x] Docker Compose with Postgres + healthcheck
- [x] FastAPI backend with structured logging
- [x] API key authentication
- [x] Agent CRUD (create, get)
- [x] Goal submission with stub planner
- [x] HTTP skill (GitHub Zen)
- [x] Memory storage and recall
- [x] Provenance logging
- [x] Makefile for local ops
- [x] Request ID tracing
- [x] CORS middleware

### Phase 1 (Next)
- [ ] Real LLM planner (Anthropic Claude)
- [ ] 3+ real skills (calendar, email, http_call)
- [ ] Agent lifecycle (stop, pause)
- [ ] NATS event bus
- [ ] Replay harness
- [ ] Basic CLI SDK

### Phase 2
- [ ] JWT authentication
- [ ] Identity Core
- [ ] Containerized skill sandbox
- [ ] Multi-tenant sharding
- [ ] pgvector integration

---

## 7. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | - | PostgreSQL connection string |
| AOS_API_KEY | Yes | - | API authentication key |
| HOST | No | 0.0.0.0 | Server bind host |
| PORT | No | 8000 | Server bind port |

---

## 8. Testing Strategy

### MVA Testing
```bash
# Run full test suite
make test

# Or manually
./test_api.sh
```

### Test Coverage Goals
- MVA: Manual curl tests (current)
- Phase 1: pytest with 80% coverage
- Phase 2: Integration tests with testcontainers

---

## 9. Deployment Notes

### Docker DNS Workaround

**Problem**: Docker containers on this VPS fail to resolve external DNS (e.g., `api.github.com`) even with `dns: [8.8.8.8, 1.1.1.1]` in compose and `/etc/docker/daemon.json`.

**Root Cause**: This VPS runs systemd-resolved + Tailscale. Docker's embedded DNS resolver (127.0.0.11) uses the host's stub resolver (127.0.0.53) which works on the host but doesn't properly forward for Docker's bridge network. The embedded DNS shows `ExtServers: [8.8.8.8 1.1.1.1]` in resolv.conf but fails to actually forward.

**Solution Applied**: Use `network_mode: host` for the backend container.

```yaml
backend:
  image: nova_agent_manager
  network_mode: host  # Uses host's DNS directly
  environment:
    DATABASE_URL: postgresql://nova:novapass@localhost:5433/nova_aos  # Note: localhost:5433
```

**Trade-offs**:
- ✅ DNS works correctly
- ✅ No port forwarding issues
- ⚠️ Container shares host network namespace (mitigated by running as non-root user)
- ⚠️ Port 8000 must be free on host

**Mitigations Applied**:
- Container runs as non-root user `nova`
- Postgres bound to localhost only (`127.0.0.1:5433`)
- Application uses minimal privileges

**Alternative for other environments**: If `network_mode: host` is not desired:
1. On systems without systemd-resolved/Tailscale, bridge networking with `dns:` should work
2. Or configure Docker to bypass systemd-resolved entirely

### Local Development
```bash
cd /root/agenticverz2.0
make up       # Start services
make logs     # View logs
make test     # Run tests
make down     # Stop services
```

### Production Checklist
- [ ] Change `AOS_API_KEY` from default
- [ ] Restrict CORS origins
- [ ] Add rate limiting (nginx or FastAPI middleware)
- [ ] Set up log aggregation
- [ ] Configure Postgres backups
- [ ] Add health check monitoring

---

## 10. Open Questions (For Future Discussion)

1. **Goal Priority Queue**: Should goals have priority levels? How to handle goal preemption?

2. **Memory Retention Policy**: How long to keep memories? Auto-summarization for old memories?

3. **Skill Marketplace Model**: Revenue share percentage? Certification requirements?

4. **NOVA vs Enterprise AOS**: Feature parity or separate codebases?

5. **Edge Sync Conflict Resolution**: Last-write-wins or semantic merge?

---

## 11. File Structure

```
agenticverz2.0/
├── docker-compose.yml      # Service orchestration
├── Makefile                # Development commands
├── test_api.sh             # Curl test suite
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── PROJECT_NOTES.md        # This file
└── backend/
    ├── Dockerfile          # Container build
    ├── requirements.txt    # Python dependencies
    └── app/
        ├── __init__.py
        ├── main.py         # FastAPI app + routes
        ├── db.py           # SQLModel models
        ├── auth.py         # API key auth
        ├── logging_config.py   # JSON logging
        └── skill_http.py   # HTTP skill
```

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-11-30 | Initial MVA scaffold |
| 0.2.0 | 2025-11-30 | Phase 2: Async runs, resilient HTTP skill, polling endpoints |

### v0.2.0 Details
- **Async execution**: POST /goals returns 202 Accepted with run_id
- **Run tracking**: New `/runs` and `/runs/{run_id}` endpoints for polling
- **Resilient HTTP skill**: 5s timeout, 3 retries with exponential backoff
- **Improved healthcheck**: Validates DB connection and API key config
- **DNS fix**: network_mode: host for reliable external connectivity

---

*Last updated: 2025-11-30*
