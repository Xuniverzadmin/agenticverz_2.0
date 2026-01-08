# PIN-354: Web Server Infrastructure Documentation

**Status:** COMPLETE
**Created:** 2026-01-08
**Category:** Infrastructure / Documentation
**Owner:** platform

---

## Summary

Documented the web server architecture and added operational debugging knowledge to CLAUDE.md for session persistence. Also optimized mail services (amavis) and fixed frontend deployment issues.

---

## Problem

During debugging of a frontend routing issue:
1. Both Apache and Nginx were running
2. It was unclear which served what
3. Frontend wasn't rebuilding to correct directory
4. Old routes were cached in browser
5. Mail services were consuming excessive memory

---

## Solution

### 1. Web Server Architecture Documented

Created `docs/infrastructure/WEB_SERVER_ARCHITECTURE.md` with:
- Server role diagram (Apache = main, Nginx = iRedMail internal only)
- Domain → config mapping
- Debugging checklist
- Deployment commands

### 2. CLAUDE.md Updated

Added "Web Server Infrastructure (Debugging Reference)" section so future sessions automatically know:
- Apache owns ports 80/443 (all external traffic)
- Nginx is internal only (127.0.0.1:8081 for iRedMail)
- Frontend deployment commands
- Config file locations

### 3. Frontend Deployment Fixed

- Rebuilt frontend with new routing (`/guard` → `/cus`)
- Copied to `dist-preflight/` for preflight console
- Added cache-busting headers for SPA routes
- Added 301 redirect from `/guard/*` to `/cus/*`

### 4. Mail Services Optimized

- Reduced amavis workers: 12 → 2
- Memory savings: ~287MB → ~168MB (41% reduction)
- Updated `/etc/amavis/conf.d/50-user`: `$max_servers = 2`
- Updated `/etc/postfix/master.cf`: smtp-amavis maxproc = 2

### 5. Cleaned Up Duplicate Configs

Removed unused nginx configs that duplicated Apache sites:
- `/etc/nginx/sites-enabled/console.agenticverz.com.conf`
- `/etc/nginx/sites-enabled/api.xuniverz.com.conf`
- `/etc/nginx/sites-enabled/crm.xuniverz.com.conf`

---

## Files Created/Modified

| File | Action |
|------|--------|
| `docs/infrastructure/WEB_SERVER_ARCHITECTURE.md` | Created |
| `CLAUDE.md` | Added infrastructure section |
| `/etc/apache2/sites-available/preflight-console.agenticverz.com.conf` | Cache headers + redirect |
| `/etc/apache2/sites-available/console.agenticverz.com.conf` | Cache headers + redirect |
| `/etc/amavis/conf.d/50-user` | Reduced workers |
| `/etc/postfix/master.cf` | Reduced smtp-amavis maxproc |

---

## Debugging Checklist (For Future Sessions)

When frontend isn't updating:

```bash
# 1. Verify Apache is the main server
ss -tlnp | grep -E ":80|:443"

# 2. Find config for domain
grep -l "ServerName.*yourdomain" /etc/apache2/sites-enabled/*.conf

# 3. Check DocumentRoot
grep DocumentRoot /etc/apache2/sites-enabled/yourdomain.conf

# 4. Rebuild and deploy
cd /root/agenticverz2.0/website/app-shell
npm run build
cp -r dist dist-preflight  # if preflight
sudo systemctl reload apache2
```

---

## Related PINs

- PIN-353: Routing Authority Infrastructure Freeze
- PIN-352: L2.1 UI Projection Pipeline

---

## Verification

```bash
# Redirect working
curl -sI https://preflight-console.agenticverz.com/guard/overview | grep -E "301|location"
# Output: HTTP/2 301, location: .../cus/overview

# Cache headers working
curl -sI https://preflight-console.agenticverz.com/cus/overview | grep -i cache
# Output: cache-control: no-cache, no-store, must-revalidate

# Amavis memory reduced
systemctl status amavis | grep Memory
# Output: Memory: ~168M (was ~287M)
```
