# Demo Checklist (M8)

**Goal:** New user can install + run examples in <10 minutes
**Status:** ✅ **COMPLETE (2025-12-06)**

---

## Summary

All demos implemented and working:

| Demo | Location | Status |
|------|----------|--------|
| BTC → Slack | `examples/btc_price_slack/` | ✅ Complete |
| JSON Transform | `examples/json_transform/` | ✅ Complete |
| HTTP Retry | `examples/http_retry/` | ✅ Complete |

---

## Demo Scenarios (COMPLETE)

### 1. BTC Price → Slack Notification

**Location:** `examples/btc_price_slack/`

**Files:**
- ✅ `demo.py` - Main Python script
- ✅ `run.sh` - Shell wrapper
- ✅ `README.md` - Documentation

**Features:**
- ✅ Simulate before execute
- ✅ Budget constraint checking
- ✅ Retry on failure
- ✅ Slack webhook integration
- ✅ Works with env vars only

---

### 2. JSON Transform Demo

**Location:** `examples/json_transform/`

**Files:**
- ✅ `demo.py` - Main Python script
- ✅ `run.sh` - Shell wrapper
- ✅ `README.md` - Documentation

**Features:**
- ✅ Pure deterministic transform
- ✅ Simulate before execute
- ✅ Determinism verification (--check-determinism)
- ✅ Structured outcomes

---

### 3. HTTP Retry Demo

**Location:** `examples/http_retry/`

**Files:**
- ✅ `demo.py` - Main Python script
- ✅ `run.sh` - Shell wrapper
- ✅ `README.md` - Documentation

**Features:**
- ✅ Failure → retry → fallback flow
- ✅ Structured error outcomes
- ✅ Failure catalog matching (--catalog)
- ✅ Risk annotation in simulation

---

## Documentation (COMPLETE)

### Root README

**Location:** `/root/agenticverz2.0/README.md`

- ✅ Installation (pip, npm)
- ✅ Quick start (5 commands)
- ✅ Link to demos
- ✅ Link to docs
- ✅ Architecture summary

### Quickstart

**Location:** `docs/QUICKSTART.md`

- ✅ Prerequisites
- ✅ Step-by-step (7 steps)
- ✅ <10 minutes flow
- ✅ Troubleshooting section

### Auth Setup

**Location:** `docs/AUTH_SETUP.md`

- ✅ API key auth
- ✅ OIDC token auth
- ✅ Keycloak token acquisition
- ✅ Role mappings

### Demos Index

**Location:** `docs/DEMOS.md`

- ✅ All demos listed
- ✅ Prerequisites per demo
- ✅ Run instructions
- ✅ Troubleshooting

---

## Screencast

**Status:** PENDING (nice-to-have)

Script ready in original checklist. Can be recorded with:
- YouTube: @AgenticverzAdmin
- Loom: Agenticverz-AOS workspace

---

## Acceptance Criteria

| Criteria | Status |
|----------|--------|
| `pip install aos-sdk` works | ✅ |
| `aos version` returns 0.1.0 | ✅ |
| `examples/btc_price_slack/run.sh` exists | ✅ |
| `examples/json_transform/run.sh` exists | ✅ |
| `examples/http_retry/run.sh` exists | ✅ |
| Root README with install + quickstart | ✅ |
| docs/QUICKSTART.md complete | ✅ |
| docs/AUTH_SETUP.md complete | ✅ |
| docs/DEMOS.md complete | ✅ |
| Each demo has README | ✅ |
| Screencast recorded | ⏳ (nice-to-have) |

---

## Verification

```bash
# SDK installed
aos version
# Output: aos-sdk 0.1.0

# Examples exist
ls examples/
# Output: README.md btc_price_slack http_retry json_transform

# Docs exist
ls docs/*.md
# Output: AUTH_SETUP.md DEMOS.md QUICKSTART.md ...
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-06 | Created 3 demo directories with demo.py, run.sh, README.md |
| 2025-12-06 | Created root README.md |
| 2025-12-06 | Created docs/QUICKSTART.md |
| 2025-12-06 | Created docs/AUTH_SETUP.md |
| 2025-12-06 | Created docs/DEMOS.md |
| 2025-12-06 | Created examples/README.md |
| 2025-12-06 | Verified aos CLI works |
| 2025-12-06 | Marked checklist COMPLETE |
