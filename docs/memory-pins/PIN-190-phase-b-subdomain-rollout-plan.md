# PIN-190: Phase B Subdomain Rollout Plan

**Status:** DESIGNED (Execute Post-Beta Only)
**Category:** Infrastructure / Migration / Governance
**Created:** 2025-12-26
**Milestone:** Runtime v1 Post-Beta
**Related:** PIN-189 (Phase A Closure), PIN-188 (Beta Signals), PIN-186 (UI Law)
**Trigger:** Beta exit criteria met (PIN-188)

---

## Execution Gate (NON-NEGOTIABLE)

> **This plan executes ONLY when beta exit criteria are met.**

Do NOT execute if:
- Beta is still running
- P0 fails exist
- Scorecards incomplete
- Exit criteria unclear

**The scorecard decides, not the roadmap.**

---

## Pre-Execution Checklist

Before ANY Phase B work:

- [ ] Beta exit criteria met (PIN-188)
- [ ] Zero P0 fails for 7 consecutive days
- [ ] All scorecards collected and synthesized
- [ ] This PIN reviewed and confirmed current
- [ ] Rollback plan tested in preflight

---

## 1. Routing Bias Review (COMPLETED)

### Verdict: No Action Required

| Check | Status |
|-------|--------|
| Navigation bias | ACCEPTABLE |
| Domain semantics | MITIGATED (banner) |
| Navigation law integrity | STRONG |
| Route structure | CLEAR |

**Beta signals remain clean.**

---

## 2. Subdomain Rollout Order (AUTHORITATIVE)

### Wave 1: Customer Plane (Lowest Risk)

```
console.agenticverz.com
```

| Current Route | Target Route | Purpose |
|---------------|--------------|---------|
| `/console/guard/*` | `/guard/*` | Customer dashboard |
| `/console/guard/runs` | `/guard/runs` | Run history |
| `/console/guard/incidents` | `/guard/incidents` | Incidents |
| `/console/guard/keys` | `/guard/keys` | API keys |
| `/console/guard/limits` | `/guard/limits` | Limits |

**Why First:**
- Pure read/consume UI
- No kill-switches
- Lowest blast radius
- Most obvious separation win

**Cookies:** Scoped to `console.agenticverz.com`

---

### Wave 2: Founder Ops Plane

```
fops.agenticverz.com
```

| Current Route | Target Route | Purpose |
|---------------|--------------|---------|
| `/console/ops` | `/ops` | Ops dashboard |
| `/console/founder/controls` | `/founder/controls` | Kill-switch |
| `/console/founder/timeline` | `/founder/timeline` | Decision audit |
| `/console/traces` | `/traces` | Execution traces |

**Requirements:**
- Stronger CSP
- Separate auth audience
- Founder-only access enforcement

---

### Wave 3: Preflight Consoles (Internal Only)

```
preflight-console.agenticverz.com
preflight-fops.agenticverz.com
```

| Console | Purpose |
|---------|---------|
| preflight-console | Mirror customer UX for verification |
| preflight-fops | Founder ops verification (read-only) |

**Requirements:**
- No external exposure
- Feature flags enabled
- Read-only enforcement

---

## 3. Zero-Downtime Migration Phases

### Phase B-1: Parallel Availability

| Action | Details |
|--------|---------|
| Deploy | New subdomains live with app |
| Old routes | Still work, no redirects |
| Testing | Founders can test voluntarily |
| Duration | 3-5 days minimum |

**Rollback:** Disable new subdomain routing.

---

### Phase B-2: Soft Redirects

| Action | Details |
|--------|---------|
| Redirect type | 302 (temporary) |
| Old routes | Redirect to new subdomains |
| Monitoring | Log all redirects, watch errors |
| Duration | 3-5 days minimum |

**Rollback:** Remove 302 redirects, instant recovery.

---

### Phase B-3: Hard Redirects

| Action | Details |
|--------|---------|
| Redirect type | 301 (permanent) |
| Cookies | Fully migrated to new domains |
| Auth | New audiences active |
| Duration | Permanent |

**Rollback:** Revert to 302, restore cookie config.

---

### Phase B-4: Route Cleanup

| Action | Details |
|--------|---------|
| Old routes | Removed from codebase |
| 301s | Keep indefinitely for bookmarks |
| `/console/*` | Informational page with links |

**Rollback:** N/A (final state)

---

## 4. Canonical URL Mapping

| Current URL | Target URL | Redirect |
|-------------|------------|----------|
| `agenticverz.com/console/guard/*` | `console.agenticverz.com/guard/*` | 301 |
| `agenticverz.com/console/guard/runs` | `console.agenticverz.com/guard/runs` | 301 |
| `agenticverz.com/console/guard/incidents` | `console.agenticverz.com/guard/incidents` | 301 |
| `agenticverz.com/console/guard/keys` | `console.agenticverz.com/guard/keys` | 301 |
| `agenticverz.com/console/guard/limits` | `console.agenticverz.com/guard/limits` | 301 |
| `agenticverz.com/console/ops` | `fops.agenticverz.com/ops` | 301 |
| `agenticverz.com/console/founder/controls` | `fops.agenticverz.com/founder/controls` | 301 |
| `agenticverz.com/console/founder/timeline` | `fops.agenticverz.com/founder/timeline` | 301 |
| `agenticverz.com/console/traces` | `fops.agenticverz.com/traces` | 301 |

---

## 5. Rollback Playbook

### Trigger Conditions

Rollback if ANY of:
- Error rate > 1% on new subdomains
- Auth failures on new domains
- Cookie issues reported
- Navigation broken
- Any P0 signal during migration

### Rollback Steps

```
1. Disable redirects (Cloudflare or Nginx)
2. Traffic returns to old routes instantly
3. No data migration involved
4. Zero user impact
5. Investigate root cause
6. Fix and re-attempt
```

### Rollback Time

| Phase | Rollback Time |
|-------|---------------|
| B-1 (Parallel) | Instant |
| B-2 (Soft redirect) | < 1 minute |
| B-3 (Hard redirect) | < 5 minutes |
| B-4 (Cleanup) | Not applicable |

---

## 6. Auth & Cookie Isolation (Per Subdomain)

### console.agenticverz.com

| Setting | Value |
|---------|-------|
| Cookie domain | `console.agenticverz.com` |
| Auth audience | `aos-customer` |
| CSP | Standard |
| Access | Customer only |

### fops.agenticverz.com

| Setting | Value |
|---------|-------|
| Cookie domain | `fops.agenticverz.com` |
| Auth audience | `aos-founder` |
| CSP | Strict |
| Access | Founder only (RBAC enforced) |

### preflight-console.agenticverz.com

| Setting | Value |
|---------|-------|
| Cookie domain | `preflight-console.agenticverz.com` |
| Auth audience | `aos-internal` |
| CSP | Strict |
| Access | Internal only (IP/VPN restricted) |

### preflight-fops.agenticverz.com

| Setting | Value |
|---------|-------|
| Cookie domain | `preflight-fops.agenticverz.com` |
| Auth audience | `aos-internal` |
| CSP | Strict |
| Access | Internal only (read-only) |

---

## 7. Execution Checklist (Use When Triggered)

### Wave 1 Checklist

- [ ] DNS verified: `console.agenticverz.com`
- [ ] SSL verified: Full (Strict)
- [ ] Proxy config deployed
- [ ] Cookie domain updated
- [ ] Auth audience configured
- [ ] Parallel availability confirmed (B-1)
- [ ] Soft redirects enabled (B-2)
- [ ] Monitor 3-5 days
- [ ] Hard redirects enabled (B-3)
- [ ] Old routes removed (B-4)

### Wave 2 Checklist

- [ ] DNS verified: `fops.agenticverz.com`
- [ ] SSL verified: Full (Strict)
- [ ] Proxy config deployed
- [ ] Cookie domain updated
- [ ] Auth audience configured
- [ ] CSP strengthened
- [ ] RBAC verified
- [ ] Parallel availability confirmed (B-1)
- [ ] Soft redirects enabled (B-2)
- [ ] Monitor 3-5 days
- [ ] Hard redirects enabled (B-3)
- [ ] Old routes removed (B-4)

### Wave 3 Checklist

- [ ] DNS verified: `preflight-console.agenticverz.com`
- [ ] DNS verified: `preflight-fops.agenticverz.com`
- [ ] SSL verified: Full (Strict)
- [ ] IP/VPN restriction configured
- [ ] Read-only enforcement verified
- [ ] Feature flags enabled
- [ ] Internal access only confirmed

---

## What You Must NOT Do Yet

Even with this design locked:

- [ ] Do NOT point subdomains to app
- [ ] Do NOT add reverse-proxy rules
- [ ] Do NOT change auth cookie domain
- [ ] Do NOT let founders access via subdomains
- [ ] Do NOT remove the beta banner

**Design ≠ Deploy**

---

## Success Criteria

Phase B is complete when:

- [ ] All four subdomains live and routing
- [ ] All old routes redirect (301)
- [ ] Auth/cookies isolated per domain
- [ ] Beta banner removed
- [ ] No errors for 7 days
- [ ] Rollback tested and documented

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Created PIN-190 - Phase B Subdomain Rollout Plan (design-only, execute post-beta) |
