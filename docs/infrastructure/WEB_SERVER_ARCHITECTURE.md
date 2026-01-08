# Web Server Architecture

**Status:** REFERENCE
**Updated:** 2026-01-08
**Owner:** platform

---

## Quick Reference

```
INTERNET (80/443)
      │
      ▼
┌─────────────────────────────────────────┐
│  APACHE (Main Server)                   │
│  Ports: 80, 443                         │
│  Config: /etc/apache2/sites-enabled/    │
├─────────────────────────────────────────┤
│  agenticverz.com sites                  │
│  xuniverz.com sites                     │
│  mobiverz.com sites                     │
│  mail.xuniverz.com → proxy to nginx     │
└────────────────┬────────────────────────┘
                 │ (mail only)
                 ▼
┌─────────────────────────────────────────┐
│  NGINX (Internal Only)                  │
│  Port: 127.0.0.1:8081                   │
│  Config: /etc/nginx/sites-enabled/      │
├─────────────────────────────────────────┤
│  iRedMail apps only:                    │
│  - Roundcube (webmail)                  │
│  - iRedAdmin (mail admin)               │
│  - SOGo (groupware)                     │
└─────────────────────────────────────────┘
```

---

## Debugging Checklist

### Frontend Not Updating?

1. **Check which server owns the domain:**
   ```bash
   ss -tlnp | grep -E ":80|:443"
   # Apache owns 80/443 for all external traffic
   ```

2. **Find the Apache config:**
   ```bash
   grep -l "ServerName.*yourdomain" /etc/apache2/sites-enabled/*.conf
   ```

3. **Check DocumentRoot:**
   ```bash
   grep -A5 "ServerName yourdomain" /etc/apache2/sites-enabled/*.conf | grep DocumentRoot
   ```

4. **Rebuild frontend:**
   ```bash
   cd /root/agenticverz2.0/website/app-shell
   npm run build
   # For preflight: cp -r dist dist-preflight
   ```

5. **Reload Apache:**
   ```bash
   apache2ctl configtest && sudo systemctl reload apache2
   ```

---

## Domain → Config Mapping

| Domain | Config File | DocumentRoot |
|--------|-------------|--------------|
| console.agenticverz.com | `/etc/apache2/sites-available/console.agenticverz.com.conf` | `/root/agenticverz2.0/website/app-shell/dist` |
| preflight-console.agenticverz.com | `/etc/apache2/sites-available/preflight-console.agenticverz.com.conf` | `/root/agenticverz2.0/website/app-shell/dist-preflight` |
| agenticverz.com | `/etc/apache2/sites-enabled/agenticverz.com.conf` | Landing page |
| mail.xuniverz.com | `/etc/apache2/sites-enabled/mail.xuniverz.conf` | Proxy → nginx:8081 |

---

## Frontend Deployment

### Production (console.agenticverz.com)
```bash
cd /root/agenticverz2.0/website/app-shell
npm run build
sudo systemctl reload apache2
```

### Preflight (preflight-console.agenticverz.com)
```bash
cd /root/agenticverz2.0/website/app-shell
npm run build
cp -r dist dist-preflight
sudo systemctl reload apache2
```

---

## Cache Control (Already Configured)

Both Apache configs have cache-busting headers:

| Path Pattern | Cache Policy |
|--------------|--------------|
| `/assets/*` | `max-age=31536000, immutable` (hashed filenames) |
| `*.html` | `no-cache, no-store, must-revalidate` |
| SPA routes (`/cus/*`, `/precus/*`, etc.) | `no-cache, no-store, must-revalidate` |

**Browsers will auto-refresh** after deployment - no manual cache clear needed.

---

## Route Redirects (Already Configured)

| Old Route | New Route | Type |
|-----------|-----------|------|
| `/guard/*` | `/cus/*` | 301 Permanent |

---

## Common Issues

### Issue: Old frontend showing after deploy
**Cause:** Forgot to rebuild or copy to correct dist directory
**Fix:**
```bash
npm run build && cp -r dist dist-preflight && sudo systemctl reload apache2
```

### Issue: 404 on SPA routes
**Cause:** Apache not configured for SPA fallback
**Fix:** Ensure `RewriteRule . /index.html [L]` exists in config

### Issue: API calls failing
**Cause:** ProxyPass not configured
**Fix:** Check `/api` proxy rules in Apache config

---

## Service Commands

```bash
# Apache
sudo systemctl status apache2
sudo systemctl reload apache2
apache2ctl configtest

# Nginx (internal only - for mail)
sudo systemctl status nginx
sudo systemctl reload nginx
nginx -t
```

---

## Port Ownership Summary

| Port | Service | Purpose |
|------|---------|---------|
| 80 | Apache | HTTP (redirects to HTTPS) |
| 443 | Apache | HTTPS (all sites) |
| 8081 | Nginx (127.0.0.1 only) | iRedMail internal |
| 8000 | Uvicorn | FastAPI backend |

---

## Related Documents

- PIN-353: Routing Authority Infrastructure Freeze
- `/etc/apache2/sites-available/` - All Apache configs
- `/etc/nginx/sites-enabled/00-default.conf` - Nginx iRedMail config
