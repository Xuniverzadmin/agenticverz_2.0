# Stagetest Subdomain Deploy Plan (2026-02-15)

## Objective

Deploy the Stagetest Evidence Console at `stagetest.agenticverz.com` as a read-only, founder-authenticated subdomain serving audit-ready test artifact evidence.

## Architecture

```
Browser → stagetest.agenticverz.com (Apache)
  ├── Static: dist/ (Vite app-shell build)
  └── API proxy: /hoc/api/stagetest/* → backend:8000
```

## Host Routing

| Subdomain | Apache Config | DocumentRoot | Proxy Target |
|-----------|--------------|--------------|--------------|
| `stagetest.agenticverz.com` | `stagetest.agenticverz.com.conf` | `/root/agenticverz2.0/website/app-shell/dist/` | `http://localhost:8000` |

### Apache VirtualHost Config

```apache
<VirtualHost *:443>
    ServerName stagetest.agenticverz.com
    DocumentRoot /root/agenticverz2.0/website/app-shell/dist

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/agenticverz.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/agenticverz.com/privkey.pem

    <Directory "/root/agenticverz2.0/website/app-shell/dist">
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
        FallbackResource /index.html
    </Directory>

    # API proxy — canonical stagetest prefix only
    ProxyPass /hoc/api/stagetest http://localhost:8000/hoc/api/stagetest
    ProxyPassReverse /hoc/api/stagetest http://localhost:8000/hoc/api/stagetest

    # Access logging
    CustomLog /var/log/apache2/stagetest-access.log combined
    ErrorLog /var/log/apache2/stagetest-error.log
</VirtualHost>

# HTTP → HTTPS redirect
<VirtualHost *:80>
    ServerName stagetest.agenticverz.com
    Redirect permanent / https://stagetest.agenticverz.com/
</VirtualHost>
```

## Auth Enforcement

| Layer | Mechanism | Details |
|-------|-----------|---------|
| Backend API | `verify_fops_token` | Router-level dependency on all `/hoc/api/stagetest/*` endpoints |
| Frontend | `FounderRoute` guard | React Router wrapper requires FOUNDER role |
| Cookie/JWT | Clerk | Human auth via JWT; verified by backend middleware |

**CRITICAL:** No anonymous access. Every API call requires valid founder auth token.

## Caching Policy

| Resource | Cache Strategy | TTL | Rationale |
|----------|---------------|-----|-----------|
| Static assets (JS/CSS) | `Cache-Control: public, max-age=31536000, immutable` | 1 year | Vite hashed filenames |
| `index.html` | `Cache-Control: no-cache` | 0 | SPA entry — always fresh |
| `/hoc/api/stagetest/runs` | `Cache-Control: no-store` | 0 | Artifact list may change |
| `/hoc/api/stagetest/runs/{id}` | `Cache-Control: public, max-age=86400` | 24h | Run summary is immutable once written |
| `/hoc/api/stagetest/runs/{id}/cases` | `Cache-Control: public, max-age=86400` | 24h | Case list is immutable per run |
| `/hoc/api/stagetest/runs/{id}/cases/{cid}` | `Cache-Control: public, max-age=86400` | 24h | Case detail is immutable |
| `/hoc/api/stagetest/apis` | `Cache-Control: public, max-age=3600` | 1h | API snapshot changes infrequently |

## TLS Requirements

- Certificate: Let's Encrypt wildcard (`*.agenticverz.com`) or SAN cert
- Protocol: TLS 1.2+ only
- HSTS: `Strict-Transport-Security: max-age=63072000; includeSubDomains`
- DNS: Add `stagetest` CNAME/A record pointing to server IP

## Access Logging

- Apache access log: `/var/log/apache2/stagetest-access.log`
- Apache error log: `/var/log/apache2/stagetest-error.log`
- Backend structured log: `nova.api.stagetest` logger
- Log rotation: logrotate, 7-day retention

## Prerequisites Checklist

| # | Prerequisite | Status |
|---|-------------|--------|
| 1 | DNS record for `stagetest.agenticverz.com` | PENDING |
| 2 | TLS certificate covers `stagetest.agenticverz.com` | PENDING |
| 3 | Apache VirtualHost config deployed | PENDING |
| 4 | Backend running with stagetest router registered | DONE |
| 5 | `npm run build` produces dist/ with stagetest route | PENDING |
| 6 | Founder auth tokens work on subdomain (Clerk domain config) | PENDING |

## Release Checklist

| # | Gate | Command | Expected |
|---|------|---------|----------|
| 1 | Route prefix guard | `python3 scripts/verification/stagetest_route_prefix_guard.py` | exit 0, 0 forbidden |
| 2 | Artifact integrity | `python3 scripts/verification/stagetest_artifact_check.py --strict --latest-run` | exit 0 |
| 3 | API tests | `pytest -q tests/api/test_stagetest_read_api.py` | 8 passed |
| 4 | Governance tests | `pytest -q tests/governance/t4/test_stagetest_route_prefix_guard.py` | 3 passed |
| 5 | CI hygiene | `python3 scripts/ci/check_init_hygiene.py --ci` | exit 0 |
| 6 | Frontend build | `npm run build` | exit 0 |
| 7 | Playwright tests | `npx playwright test --config tests/uat/playwright.config.ts stagetest.spec.ts` | all passed |
| 8 | Manual smoke test | Open `https://stagetest.agenticverz.com/fops/stagetest` | Page renders |

## Rollback Plan

1. Remove Apache VirtualHost config
2. Reload Apache: `systemctl reload apache2`
3. No backend changes needed (stagetest router is read-only, zero side effects)

## References

- Canonical API prefix: `/hoc/api/stagetest/*`
- FORBIDDEN prefix: `/api/v1/stagetest/*`
- Router source: `backend/app/hoc/api/fdr/ops/stagetest.py`
- Facade: `backend/app/hoc/api/facades/fdr/ops.py`
- UI route: `/prefops/stagetest` and `/fops/stagetest`
