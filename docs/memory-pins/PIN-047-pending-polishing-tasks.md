# PIN-047: Pending Polishing Tasks

**Date:** 2025-12-07
**Status:** PENDING
**Category:** Technical Debt / Polishing
**Priority:** P1-P3 (Non-blocking)

---

## Summary

This PIN tracks pending polishing tasks identified during M8 production hardening sessions. These are non-blocking improvements to be addressed in future sessions.

---

## P1 Tasks (Address Soon)

### Prometheus Alert Reload
| Task | Details |
|------|---------|
| Reload Prometheus | `docker exec prometheus kill -HUP 1` or restart container |
| Verify alerts | Check http://localhost:9093 for new embedding alerts |
| Test alert firing | Use `scripts/ops/inject_synthetic_alert.py` |

**Files affected:** `monitoring/rules/embedding_alerts.yml`

### Move Remaining Secrets to Vault
| Secret | Current Location | Target Vault Path |
|--------|------------------|-------------------|
| GITHUB_TOKEN | `.env` | `agenticverz/external-apis` |
| SLACK_MISMATCH_WEBHOOK | `.env` | `agenticverz/webhooks` |
| POSTHOG_API_KEY | `.env` | `agenticverz/external-apis` |
| RESEND_API_KEY | `.env` | `agenticverz/external-apis` |
| TRIGGER_API_KEY | `.env` | `agenticverz/external-apis` |
| CLOUDFLARE_API_TOKEN | `.env` | `agenticverz/external-apis` |

---

## P2 Tasks (Next Sprint)

### Quota Status API Endpoint
| Task | Details |
|------|---------|
| Create endpoint | `GET /api/v1/embedding/quota` |
| Response fields | `daily_quota`, `current_count`, `remaining`, `exceeded`, `reset_at` |
| Auth | Machine token or admin role |

**Implementation location:** `app/api/v1/memory.py`

### Test Quota Exhaustion
| Scenario | Test |
|----------|------|
| Near limit (80%) | Verify warning alert fires |
| At limit (100%) | Verify requests blocked, fallback to keyword search |
| Post-reset | Verify counter resets at midnight UTC |

### Embedding Cost Monitoring Dashboard
| Panel | Metric |
|-------|--------|
| Daily usage gauge | `aos_embedding_daily_calls` |
| Quota remaining | `EMBEDDING_DAILY_QUOTA - aos_embedding_daily_calls` |
| Error rate | `rate(aos_embedding_errors_total[5m])` |
| Provider latency | `histogram_quantile(0.95, aos_embedding_api_latency_seconds_bucket)` |

---

## P3 Tasks (Future)

### Anthropic Voyage Backup Provider
| Task | Details |
|------|---------|
| Add VOYAGE_API_KEY to Vault | `agenticverz/external-apis` |
| Implement `get_embedding_anthropic()` | Already stubbed in `vector_store.py` |
| Add provider failover | Try OpenAI, fallback to Voyage on error |
| Document in PIN-046 | Update production checklist |

### Embedding Cache Layer
| Task | Details |
|------|---------|
| Cache key | SHA256 hash of text content |
| Cache backend | Redis (Upstash) |
| TTL | 7 days |
| Purpose | Reduce API calls for repeated content |

### Vector Index Optimization
| Task | Details |
|------|---------|
| Review HNSW parameters | m=16, ef_construction=64 (defaults) |
| Benchmark query latency | Target <50ms for 10k vectors |
| Add index stats to metrics | `aos_vector_index_size`, `aos_vector_query_latency_seconds` |

---

## Related PINs

- **PIN-046**: Stub Replacement & pgvector (parent work)
- **PIN-034**: Vault Secrets Management
- **PIN-038**: Upstash Redis Integration
- **PIN-037**: Grafana Cloud Integration

---

## Completion Criteria

- [ ] P1: All alerts verified in Alertmanager
- [ ] P1: All secrets migrated to Vault
- [ ] P2: Quota API endpoint available
- [ ] P2: Cost dashboard in Grafana
- [ ] P3: Backup embedding provider ready
- [ ] P3: Cache layer implemented

---

## Notes

These tasks are intentionally deferred to avoid scope creep during M8 hardening. Address as part of M9+ milestones or dedicated polishing sprints.
