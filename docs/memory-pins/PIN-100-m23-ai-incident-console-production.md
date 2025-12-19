# PIN-100: M23 AI Incident Console - Production Ready

**Status:** ACTIVE
**Created:** 2025-12-19
**Author:** Claude Opus 4.5
**Depends On:** PIN-095 (Strategy), PIN-096 (M22 KillSwitch), PIN-098 (M22.1 UI)
**Milestone:** M23

---

## Executive Summary

M23 transforms the AI Incident Console from demo-ready to **production-ready**. All gaps identified in PIN-095 are filled. No localhost. No mocks. All tests live against real infrastructure.

**Goal:** A paying customer can sign up, integrate, investigate an incident, and export evidence - all in production.

---

## ⛔ Phase 0: Hard Lock - What's OUT

Before any work begins, these are **explicitly out of scope for M23**:

| OUT | Reason |
|-----|--------|
| New agent abstractions | We're selling the console, not reinventing agents |
| LangChain evangelism | Wrong audience - we're B2B SaaS, not framework users |
| "AI governance platform" branding | Too abstract - we're selling incident investigation |
| Multi-cloud fantasies | Focus on Neon + Upstash + Vault - no new infra |
| New skills development | M11 skills are sufficient for this phase |
| Complex pricing tiers | One price, one product - simplify sales |

**Rule:** If it's not in the 7 objectives below, it doesn't exist for M23.

---

## Current State (Post-M22.1)

| Component | Status | Gap |
|-----------|--------|-----|
| Backend MOATs (M4-M20) | ✅ 100% | None |
| Kill Switch MVP | ✅ 100% | None |
| OpenAI Proxy | ✅ 90% | Missing `user_id` field |
| Guard Console | ⚠️ 80% | Missing search UI, export |
| Operator Console | ⚠️ 90% | Missing PDF export |
| Decision Timeline | ⚠️ 60% | Needs enhancement |
| Evidence Layer | ❌ 20% | Certificates, SOC2 missing |
| Live Tests | ❌ 0% | All tests use mocks |

**Overall: 77% → Target: 100%**

---

## M23 Objectives

### Objective 1: Complete Search & Discovery

**Problem:** Can't search incidents by customer/time/content
**Solution:** Full search UI with backend indexing

#### 1.1 Backend: Decision Search API

```python
# NEW: POST /api/v1/incidents/search
@router.post("/search", response_model=IncidentSearchResponse)
async def search_incidents(
    query: str,                    # Free text search
    user_id: Optional[str],        # Customer ID filter
    tenant_id: str,                # Required
    time_from: Optional[datetime], # Start time
    time_to: Optional[datetime],   # End time
    severity: Optional[str],       # critical/high/medium/low
    policy: Optional[str],         # Policy that triggered
    limit: int = 50,
    offset: int = 0
):
    """
    Search incidents with full-text and filters.
    Uses M9 Failure Catalog + proxy_calls index.
    """
```

#### 1.2 Frontend: Search Component

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 Search incidents...                        [Filters ▼]      │
├─────────────────────────────────────────────────────────────────┤
│  Filters:                                                       │
│  [User ID: ________] [From: ____] [To: ____] [Severity: All ▼] │
│                                                                 │
│  Results (23 matches)                          [Export Results] │
│  ───────────────────────────────────────────────────────────── │
│  ⚠️ Dec 19, 14:23 │ user_8372 │ "Contract auto-renew..."      │
│  🔴 Dec 19, 14:20 │ user_1234 │ "Payment failed..."           │
│  ✓  Dec 19, 14:18 │ user_5678 │ "Order confirmed..."          │
└─────────────────────────────────────────────────────────────────┘
```

**Files:**
- `backend/app/api/incidents.py` - New search endpoint
- `console/src/pages/guard/incidents/SearchBar.tsx` - Search UI
- `console/src/pages/guard/incidents/FilterPanel.tsx` - Filters

---

### Objective 2: User ID Tracking

**Problem:** Proxy calls don't track end-user ID
**Solution:** Add `user_id` to request schema

#### 2.1 Proxy Request Enhancement

```python
# MODIFY: v1_proxy.py
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    # NEW FIELDS
    user_id: Optional[str] = None      # End-user identifier
    session_id: Optional[str] = None   # Conversation session
    metadata: Optional[Dict] = None    # Custom context
```

#### 2.2 Database Schema

```sql
-- MODIFY: proxy_calls table
ALTER TABLE proxy_calls ADD COLUMN user_id TEXT;
ALTER TABLE proxy_calls ADD COLUMN session_id TEXT;
ALTER TABLE proxy_calls ADD COLUMN metadata JSONB;

-- Index for search
CREATE INDEX idx_proxy_calls_user_id ON proxy_calls(user_id);
CREATE INDEX idx_proxy_calls_user_tenant ON proxy_calls(tenant_id, user_id);
```

**Files:**
- `backend/app/api/v1_proxy.py` - Add fields
- `backend/app/models/killswitch.py` - Update ProxyCall model
- `backend/alembic/versions/038_m23_user_tracking.py` - Migration

---

### Objective 3: Decision Timeline Component

**Problem:** Incident detail doesn't show step-by-step trace
**Solution:** Interactive timeline with policy evaluation

#### 3.1 Timeline API

```python
# NEW: GET /api/v1/incidents/{id}/timeline
@router.get("/{incident_id}/timeline", response_model=TimelineResponse)
async def get_incident_timeline(incident_id: str, tenant_id: str):
    """
    Returns chronological events for an incident:
    - Input received
    - Context retrieved
    - Policy evaluations (each policy)
    - LLM call
    - Output generated
    - Root cause (if any)
    """
    return {
        "incident_id": incident_id,
        "events": [
            {"time": "...", "type": "input", "data": {...}},
            {"time": "...", "type": "context", "data": {...}},
            {"time": "...", "type": "policy", "policy": "SAFETY", "result": "PASS"},
            {"time": "...", "type": "policy", "policy": "CONTENT_ACCURACY", "result": "WARN", "reason": "..."},
            {"time": "...", "type": "output", "data": {...}},
            {"time": "...", "type": "root_cause", "analysis": "..."}
        ]
    }
```

#### 3.2 Timeline Component

```
┌─────────────────────────────────────────────────────────────────┐
│  DECISION TIMELINE                                   dec_a8f3c2 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ●───────●───────●───────●───────●───────●                     │
│  │       │       │       │       │       │                     │
│  INPUT   CONTEXT POLICY  POLICY  LLM     OUTPUT                │
│          ✓       ✓       ⚠️      ✓       ⚠️                    │
│                                                                 │
│  ▼ [23:47:12.001] INPUT RECEIVED                               │
│    User: "Is my contract auto-renewed?"                        │
│    Channel: chat │ Session: sess_abc123                        │
│                                                                 │
│  ▼ [23:47:12.010] CONTEXT RETRIEVED                            │
│    • contract_status: "active"                                 │
│    • auto_renew: null ⚠️ MISSING                               │
│                                                                 │
│  ▼ [23:47:12.050] POLICY: SAFETY                               │
│    Result: ✓ PASS                                              │
│                                                                 │
│  ▼ [23:47:12.055] POLICY: CONTENT_ACCURACY                     │
│    Result: ⚠️ WARNING                                          │
│    Reason: Missing data for definitive answer                  │
│    Should have: Triggered uncertainty response                 │
│    Actually did: Made assertion                                │
│    🔴 ROOT CAUSE IDENTIFIED                                    │
│                                                                 │
│  ▼ [23:47:12.847] OUTPUT                                       │
│    "Yes, your contract is set to auto-renew..."               │
│    Tokens: 47 │ Cost: $0.0023 │ Latency: 837ms                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Files:**
- `backend/app/api/incidents.py` - Timeline endpoint
- `console/src/pages/guard/incidents/Timeline.tsx` - Timeline component
- `console/src/pages/guard/incidents/TimelineEvent.tsx` - Event cards

---

### Objective 4: Export Package (PDF/JSON/SOC2)

**Problem:** Can't export evidence for legal/compliance
**Solution:** Multi-format export system

#### 4.1 Export API

```python
# NEW: POST /api/v1/incidents/{id}/export
@router.post("/{incident_id}/export", response_model=ExportResponse)
async def export_incident(
    incident_id: str,
    tenant_id: str,
    format: ExportFormat,  # pdf, json, soc2, legal_discovery
    include: ExportIncludes = ExportIncludes()
):
    """
    Generate export package for incident.

    Formats:
    - pdf: Human-readable report
    - json: Machine-readable evidence pack
    - soc2: SOC2 audit format
    - legal_discovery: Legal discovery format

    Includes (optional):
    - full_trace: Complete decision trace
    - policy_log: All policy evaluations
    - replay_cert: Replay verification certificate
    - root_cause: Root cause analysis
    - raw_io: Raw model inputs/outputs
    """
```

#### 4.2 PDF Template

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ╔═══════════════════════════════════════════════════════════╗ │
│  ║           AI INCIDENT INVESTIGATION REPORT                 ║ │
│  ╚═══════════════════════════════════════════════════════════╝ │
│                                                                 │
│  INCIDENT ID: dec_a8f3c2                                       │
│  DATE: December 19, 2025 23:47:12 UTC                          │
│  TENANT: Acme Corp (tenant_acme_001)                           │
│  USER: cust_8372                                               │
│                                                                 │
│  ─────────────────────────────────────────────────────────────│
│  EXECUTIVE SUMMARY                                             │
│  ─────────────────────────────────────────────────────────────│
│                                                                 │
│  An AI-generated response made an inaccurate assertion about  │
│  contract auto-renewal status when the underlying data was    │
│  missing. The CONTENT_ACCURACY policy flagged this but did    │
│  not block the response.                                       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────│
│  ROOT CAUSE                                                    │
│  ─────────────────────────────────────────────────────────────│
│                                                                 │
│  Policy enforcement gap: CONTENT_ACCURACY policy was set to   │
│  WARN mode instead of BLOCK mode for assertions with missing  │
│  data.                                                         │
│                                                                 │
│  ─────────────────────────────────────────────────────────────│
│  REMEDIATION                                                   │
│  ─────────────────────────────────────────────────────────────│
│                                                                 │
│  1. Policy updated to BLOCK assertions with null data         │
│  2. Response template updated to express uncertainty          │
│  3. Replay verification confirmed fix effectiveness           │
│                                                                 │
│  ─────────────────────────────────────────────────────────────│
│  EVIDENCE CERTIFICATE                                          │
│  ─────────────────────────────────────────────────────────────│
│                                                                 │
│  This incident has been cryptographically verified:           │
│  • Original Hash: sha256:e3b0c44298fc1c14...                  │
│  • Replay Hash: sha256:e3b0c44298fc1c14...                    │
│  • Match: EXACT (100% deterministic)                          │
│  • Verified At: December 19, 2025 23:52:01 UTC                │
│                                                                 │
│  [QR Code for verification]                                    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────│
│  FULL DECISION TRACE                                           │
│  ─────────────────────────────────────────────────────────────│
│                                                                 │
│  [Timeline details...]                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Files:**
- `backend/app/services/export_service.py` - Export generation
- `backend/app/services/pdf_generator.py` - PDF generation (WeasyPrint)
- `backend/app/templates/incident_report.html` - PDF template
- `console/src/pages/guard/incidents/ExportModal.tsx` - Export UI

---

### Objective 5: Evidence Certificates

**Problem:** Can't cryptographically prove determinism
**Solution:** Signed verification certificates

#### 5.1 Certificate Schema

```python
class EvidenceCertificate(BaseModel):
    """Cryptographically signed proof of replay verification."""

    certificate_id: str           # cert_uuid
    incident_id: str              # Reference to incident

    # Original execution
    original_hash: str            # SHA256 of original output
    original_timestamp: datetime
    original_model: str
    original_policy_version: str

    # Replay execution
    replay_hash: str              # SHA256 of replay output
    replay_timestamp: datetime
    replay_model: str
    replay_policy_version: str

    # Verification
    match_level: str              # EXACT, LOGICAL, SEMANTIC, MISMATCH
    determinism_verified: bool

    # Signature
    signature: str                # HMAC-SHA256 signature
    signed_at: datetime
    signed_by: str                # System identifier

    # Verification URL
    verification_url: str         # URL to verify certificate
```

#### 5.2 Certificate Generation

```python
# NEW: POST /api/v1/incidents/{id}/certificate
@router.post("/{incident_id}/certificate", response_model=EvidenceCertificate)
async def generate_certificate(incident_id: str, tenant_id: str):
    """
    Generate cryptographically signed evidence certificate.

    1. Retrieve original call from proxy_calls
    2. Execute replay
    3. Compare hashes
    4. Sign certificate with HMAC
    5. Store in certificates table
    6. Return downloadable certificate
    """
```

#### 5.3 Certificate Verification

```python
# NEW: GET /api/v1/certificates/{id}/verify
@router.get("/certificates/{certificate_id}/verify")
async def verify_certificate(certificate_id: str):
    """
    Public endpoint to verify certificate authenticity.
    No authentication required - anyone can verify.
    """
```

**Files:**
- `backend/app/models/certificates.py` - Certificate model
- `backend/app/services/certificate_service.py` - Generation/verification
- `backend/alembic/versions/039_m23_certificates.py` - Migration
- `console/src/pages/guard/replay/CertificateView.tsx` - Certificate UI

---

### Objective 6: Remove All Mocks

**Problem:** Tests use mocks, not real infrastructure
**Solution:** Live integration tests

#### 6.1 Mock Inventory (To Remove)

| Mock | Location | Replacement |
|------|----------|-------------|
| `MockOpenAI` | tests/conftest.py | Real OpenAI API |
| `MockRedis` | tests/conftest.py | Upstash Redis |
| `MockDB` | tests/conftest.py | Neon PostgreSQL |
| `MockVault` | tests/conftest.py | HashiCorp Vault |
| `DemoIncidents` | guard.py | Real incident generation |
| `StubAuth` | tenant_auth.py | Real Clerk auth |

#### 6.2 Live Test Configuration

```python
# tests/conftest_live.py
import pytest
from app.core.config import settings

@pytest.fixture(scope="session")
def live_db():
    """Use production Neon database (test schema)."""
    return settings.DATABASE_URL  # Neon pooler

@pytest.fixture(scope="session")
def live_redis():
    """Use Upstash Redis."""
    return settings.REDIS_URL  # Upstash

@pytest.fixture(scope="session")
def live_openai():
    """Use real OpenAI API."""
    return settings.OPENAI_API_KEY  # Real key

@pytest.fixture(scope="session")
def live_vault():
    """Use HashiCorp Vault."""
    return settings.VAULT_ADDR, settings.VAULT_TOKEN
```

#### 6.3 Live Test Suite

```python
# tests/test_m23_live.py
"""
M23 Live Integration Tests
All tests run against production infrastructure.
"""

class TestLiveProxy:
    """Test OpenAI proxy with real API."""

    async def test_chat_completion_real(self, live_openai):
        """Call real OpenAI through proxy."""
        response = await client.post("/v1/chat/completions", json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say 'test'"}],
            "user_id": "test_user_001"
        })
        assert response.status_code == 200
        assert "test" in response.json()["choices"][0]["message"]["content"].lower()

class TestLiveIncidents:
    """Test incident flow with real data."""

    async def test_create_and_search_incident(self, live_db):
        """Create incident, search for it, verify found."""
        # Trigger real policy violation
        # Search for incident
        # Verify timeline
        # Generate certificate
        # Export PDF

class TestLiveReplay:
    """Test replay with real model calls."""

    async def test_deterministic_replay(self, live_openai):
        """Verify replay produces same output."""
        # Make original call
        # Wait
        # Replay
        # Compare hashes
```

**Files:**
- `backend/tests/conftest_live.py` - Live fixtures
- `backend/tests/test_m23_live.py` - Live test suite
- `backend/tests/test_m23_proxy_live.py` - Proxy tests
- `backend/tests/test_m23_incidents_live.py` - Incident tests
- `backend/tests/test_m23_export_live.py` - Export tests

---

### Objective 7: Production Deployment

**Problem:** Not deployed to production URLs
**Solution:** Full production deployment

#### 7.1 Production URLs

| Service | URL | Status |
|---------|-----|--------|
| API | `api.agenticverz.com` | ✅ Active |
| Guard Console | `console.agenticverz.com/guard` | ⏳ Deploy |
| Operator Console | `ops.agenticverz.com` | ⏳ Deploy |
| Certificate Verify | `verify.agenticverz.com` | ⏳ Create |

#### 7.2 Environment Configuration

```bash
# Production environment (.env.production)
DATABASE_URL=postgresql://neondb_owner:***@ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://default:***@apn1-picked-skink-35210.upstash.io:6379
OPENAI_API_KEY=sk-proj-***
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=hvs.***
AOS_OPERATOR_TOKEN=***
CLERK_SECRET_KEY=sk_live_***
```

#### 7.3 CI/CD Pipeline

```yaml
# .github/workflows/m23-deploy.yml
name: M23 Production Deploy

on:
  push:
    branches: [main]
    paths:
      - 'backend/app/api/incidents.py'
      - 'backend/app/services/export_service.py'
      - 'website/aos-console/**'

jobs:
  test-live:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Live Tests
        env:
          DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pytest tests/test_m23_live.py -v

  deploy:
    needs: test-live
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Backend
        run: ./scripts/ops/deploy_backend.sh
      - name: Deploy Console
        run: ./scripts/ops/deploy_website.sh
```

---

## File Manifest

### New Files (M23)

```
backend/
├── alembic/versions/
│   ├── 038_m23_user_tracking.py        # user_id, session_id columns
│   └── 039_m23_certificates.py         # certificates table
├── app/
│   ├── api/
│   │   └── incidents.py                # Search, timeline, export endpoints
│   ├── models/
│   │   └── certificates.py             # EvidenceCertificate model
│   ├── services/
│   │   ├── export_service.py           # Export orchestration
│   │   ├── pdf_generator.py            # PDF generation
│   │   └── certificate_service.py      # Certificate signing
│   └── templates/
│       ├── incident_report.html        # PDF template
│       └── certificate.html            # Certificate template
├── tests/
│   ├── conftest_live.py                # Live test fixtures
│   ├── test_m23_live.py                # Integration tests
│   ├── test_m23_proxy_live.py          # Proxy live tests
│   ├── test_m23_incidents_live.py      # Incident live tests
│   └── test_m23_export_live.py         # Export live tests

website/aos-console/console/src/
├── pages/guard/incidents/
│   ├── SearchBar.tsx                   # Search input
│   ├── FilterPanel.tsx                 # Filter controls
│   ├── Timeline.tsx                    # Decision timeline
│   └── TimelineEvent.tsx               # Timeline event card
├── pages/guard/export/
│   └── ExportModal.tsx                 # Export format selection
└── pages/guard/replay/
    └── CertificateView.tsx             # Certificate display

.github/workflows/
└── m23-deploy.yml                      # CI/CD pipeline
```

### Modified Files

```
backend/app/api/v1_proxy.py             # Add user_id, session_id
backend/app/api/guard.py                # Wire new endpoints
backend/app/models/killswitch.py        # Update ProxyCall model
website/aos-console/console/src/
├── pages/guard/IncidentsPage.tsx       # Add search UI
└── pages/guard/incidents/IncidentDetail.tsx  # Add timeline
```

---

## Success Criteria

### 🏆 Phase 4: Business Success (Primary)

These are the **real** success metrics - everything else supports these:

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Companies onboarded | ≥ 5 | Validates product-market fit |
| Real incidents analyzed | ≥ 1 per company | Proves actual value delivery |
| "This saved us" quote | ≥ 1 | Social proof for sales |
| Unprompted payment | ≥ 1 | Someone pays without negotiating price |

**M23 is not done until at least one company pays without being asked for a discount.**

### Functional

- [ ] Search finds incidents by user_id, time, content
- [ ] Timeline shows all policy evaluations step-by-step
- [ ] PDF export generates professional report
- [ ] JSON export is machine-parseable
- [ ] Certificates are cryptographically verifiable
- [ ] All tests pass against live infrastructure

### Performance

- [ ] Search returns in <500ms
- [ ] Timeline loads in <1s
- [ ] PDF generates in <5s
- [ ] Certificate generates in <2s

### Quality

- [ ] Zero mocks in test suite
- [ ] 100% of tests use real APIs
- [ ] All endpoints return production data
- [ ] Documentation complete

---

## Timeline (14-Day Execution Plan)

**Philosophy:** Product-first, sell-first. Build only what we can demo tomorrow.

### Phase 1: Sellable Demo (Days 1-3)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 1 | Demo flow script | Written walkthrough for sales calls |
| Day 2 | Timeline polish | Decision timeline component working |
| Day 3 | Export foundation | Basic PDF export functional |

**Gate:** Can run a 15-minute demo that answers "What happened? Why? Proof?"

### Phase 2: First 5 Users (Days 4-7)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 4-5 | Onboarding | Integration guide, API key flow |
| Day 6-7 | User feedback | Watch 5 companies use it, note friction |

**Gate:** 5 companies integrated, feedback collected

### Phase 3: First Incident (Days 8-11)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 8-9 | Wait for incidents | Monitor for real policy violations |
| Day 10-11 | Investigation support | Help users analyze their first incident |

**Gate:** ≥1 real incident analyzed end-to-end

### Phase 4: First Quote (Days 12-14)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Day 12 | Value capture | Get "this saved us" quote |
| Day 13-14 | Pricing test | Present price, observe reaction |

**Gate:** Someone pays without negotiating

---

## Technical Timeline (Original 6-Week Reference)

For reference, the detailed technical work maps to:

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Search + User ID | Search API, Search UI, user_id in proxy |
| **Week 2** | Timeline | Timeline API, Timeline component |
| **Week 3** | Export | PDF generator, JSON pack, Export UI |
| **Week 4** | Certificates | Certificate service, verification endpoint |
| **Week 5** | Live Tests | Remove all mocks, live test suite |
| **Week 6** | Deploy | Production deployment, documentation |

*Technical work is sequenced based on business milestones, not completed in isolation.*

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API costs during testing | Medium | Use gpt-4o-mini, limit test runs |
| Neon connection limits | Medium | Use connection pooling |
| PDF generation performance | Low | Cache templates, async generation |
| Certificate signing security | High | Use Vault for key management |

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-095 | Strategic direction (this implements it) |
| PIN-096 | M22 KillSwitch (foundation) |
| PIN-098 | M22.1 UI Console (foundation) |
| PIN-066 | External API Keys (credentials) |
| PIN-048 | M9 Failure Catalog (incident data) |
| PIN-004 | M4 Golden Replay (determinism) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-19 | Added Phase 0 "Hard Lock" OUT list - explicit scope boundaries |
| 2025-12-19 | Added Phase 4 business success criteria (5 companies, 1 quote, 1 payment) |
| 2025-12-19 | Updated timeline to 14-day execution plan (product-first approach) |
| 2025-12-19 | Initial M23 specification created |

---

*PIN-100: M23 AI Incident Console - Production Ready*
