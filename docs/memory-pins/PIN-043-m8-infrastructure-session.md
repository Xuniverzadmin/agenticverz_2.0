# PIN-043: M8 Infrastructure Session - Docker Network & Rate Limiting

**Status:** COMPLETE
**Created:** 2025-12-06
**Category:** Infrastructure / Operations

---

## Session Summary

This session addressed critical infrastructure issues blocking M8 production readiness:

1. **Docker Container Network Failure** - Containers couldn't reach external internet
2. **Rate Limiting Verification** - Confirmed middleware working in production
3. **nftables Persistence** - Prepared for reboot validation

---

## Issue 1: Docker Container Network Failure

### Symptoms
- `docker build` hanging on `pip install` / `apt-get update`
- Containers couldn't ping external IPs (100% packet loss to 8.8.8.8)
- Host internet working fine
- Initially appeared to be DNS/BuildKit issue

### Root Cause
**nftables `inet filter forward` chain had `policy drop` with no rules allowing Docker traffic.**

```nft
table inet filter {
    chain forward {
        type filter hook forward priority filter; policy drop;
        # NO DOCKER RULES - all container traffic dropped!
    }
}
```

### Fix Applied

Added Docker forwarding rules to `/etc/nftables.conf`:

```nft
chain forward {
    type filter hook forward priority filter; policy drop;

    # Allow Docker container traffic
    iifname "docker0" accept
    iifname "br-*" accept
    oifname "docker0" accept
    oifname "br-*" accept
}
```

### Verification
```bash
# Test container network
docker run --rm alpine ping -c 2 8.8.8.8
# Result: 2 packets transmitted, 2 received, 0% packet loss

# Test Docker build with pip
docker build --no-cache -t test-dns -f - . <<'EOF'
FROM python:3.11-slim
RUN pip install requests
EOF
# Result: Completed in ~9 seconds
```

### Repair Script Created
`/root/scripts/fix-nft-docker.sh` - Run when Docker containers lose internet access

---

## Issue 2: Rate Limiting Verification

### Configuration Confirmed
- `RATE_LIMIT_FAIL_OPEN` environment variable already implemented (line 68)
- Tiers: free (60/min), dev (300/min), pro (1200/min), enterprise (6000/min), unlimited

### Test Results
```
aos_rate_limit_allowed_total{tier="free"} = 60   (exactly at limit)
aos_rate_limit_blocked_total{tier="free"} = 11  (excess blocked)
aos_rate_limit_redis_connected = 1              (Redis healthy)
aos_rate_limit_redis_errors_total = 0           (no errors)
```

### Rate-Limited Endpoints
- `POST /api/v1/runtime/simulate` - rate_limit_dependency wired
- `POST /api/v1/runtime/replay/{run_id}` - rate_limit_dependency wired

### Integration Tests
9/9 rate-limit tests passing:
- `test_tier_limits_configured`
- `test_extract_tier_from_user`
- `test_check_rate_limit_allowed`
- `test_check_rate_limit_blocked`
- `test_check_rate_limit_redis_error_fail_open`
- `test_check_rate_limit_redis_error_fail_closed`
- `test_metrics_registered`
- `test_tier_limits_in_gauge`
- `test_live_redis_rate_limit`

---

## Issue 3: Container Code Verification

### Concern
Initial analysis suggested containers might have outdated code (Dec 4 vs Dec 6).

### Resolution
**Files are identical** - timestamp difference was timezone (container UTC 17:xx, local CET 18:xx).

Verified by diff:
```bash
diff <(docker exec nova_agent_manager cat /app/app/middleware/rate_limit.py) backend/app/middleware/rate_limit.py
# No output - files identical

diff <(docker exec nova_agent_manager cat /app/app/api/traces.py) backend/app/api/traces.py
# No output - files identical
```

Both backend and worker containers have latest code.

---

## Artifacts Created

### Scripts
| Script | Purpose |
|--------|---------|
| `/root/scripts/fix-nft-docker.sh` | Fix nftables blocking Docker traffic |
| `/root/scripts/repair-claude-cli.sh` | Repair broken Node.js/Claude CLI |
| `/root/scripts/post-reboot-verify.sh` | Post-reboot system health check |

### Documentation
| Document | Purpose |
|----------|---------|
| `docs/STAGING_READINESS.md` | M9 entrance checklist |
| `docs/DEPLOYMENT_GATE_POLICY.md` | PR gating rules for determinism |

### GitHub Workflow
| Workflow | Purpose |
|----------|---------|
| `.github/workflows/e2e-parity-check.yml` | E2E + cross-language parity + k6 SLO |

### Pre-Reboot Snapshot
Location: `/root/reboot-test-20251206/`
- `nftables.rules.pre` - nftables rules before reboot
- `docker-compose-ps.json` - Docker container state
- `docker-images.pre.txt` - Docker images list
- `repo-commit.txt` - Git commit hash
- `metrics.pre.txt` - Prometheus metrics snapshot

---

## Pending: nftables Reboot Validation

### Purpose
Confirm nftables rules persist across system reboot.

### Procedure
1. Pre-reboot snapshot saved to `/root/reboot-test-20251206/`
2. Run `sudo reboot`
3. After reconnect, run `/root/scripts/post-reboot-verify.sh`
4. Script validates:
   - nftables Docker rules present
   - Docker containers running
   - Container internet connectivity
   - API health endpoint
   - Redis connection
   - Database connectivity
   - Prometheus metrics

### Rollback (if needed)
```bash
# Restore previous nft rules
sudo cp /root/reboot-test-20251206/nftables.rules.pre /etc/nftables.conf
sudo nft -f /etc/nftables.conf

# Or run repair script
/root/scripts/fix-nft-docker.sh
```

---

## M8 Status After This Session

| Component | Status |
|-----------|--------|
| Docker networking | FIXED |
| Rate limiting | VERIFIED (60 allowed, 11 blocked) |
| Redis connectivity | HEALTHY (connected=1, errors=0) |
| Container code | CURRENT (identical to repo) |
| nftables persistence | PENDING reboot test |

---

## Next Steps

1. Execute reboot test with `post-reboot-verify.sh`
2. Run `e2e-parity-check.yml` workflow against staging
3. Complete staging readiness checklist items
4. Proceed to M9 when all gates pass

---

## Related PINs

- PIN-039: M8 Implementation Progress
- PIN-040: Rate Limit Middleware
- PIN-041: Mismatch Tracking System
- PIN-042: Alert & Observability Tooling
