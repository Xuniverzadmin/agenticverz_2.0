# Cloudflare Configuration Checklist for AOS Console

## Domain: agenticverz.com

### 1. SSL/TLS Settings

- [ ] SSL Mode: **Full (Strict)**
- [ ] Always Use HTTPS: **ON**
- [ ] Minimum TLS Version: **1.2**
- [ ] Opportunistic Encryption: **ON**
- [ ] TLS 1.3: **ON**
- [ ] Automatic HTTPS Rewrites: **ON**

### 2. Origin Certificates

- [ ] Generate Cloudflare Origin Certificate
- [ ] Validity: 15 years
- [ ] Hostnames: `agenticverz.com`, `*.agenticverz.com`
- [ ] Key Format: PEM
- [ ] Install at:
  - `/etc/ssl/cf-origin/agenticverz_origin.crt`
  - `/etc/ssl/cf-origin/agenticverz_origin.key`

### 3. DNS Records

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | @ | YOUR_VPS_IP | Proxied |
| A | www | YOUR_VPS_IP | Proxied |
| AAAA | @ | YOUR_IPV6 (if available) | Proxied |
| CNAME | api | @ | Proxied |

### 4. Cache Rules

Create Page Rules or Cache Rules:

**Rule 1: API - Bypass Cache**
- URL: `agenticverz.com/api/*`
- Cache Level: Bypass
- Browser TTL: Respect Existing Headers

**Rule 2: Console Assets - Cache**
- URL: `agenticverz.com/console/assets/*`
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser TTL: 1 year

**Rule 3: Console HTML - No Cache**
- URL: `agenticverz.com/console/*.html`
- Cache Level: Bypass

### 5. Security Settings

- [ ] Security Level: **Medium**
- [ ] Browser Integrity Check: **ON**
- [ ] Challenge Passage: **30 minutes**

### 6. WAF Rules

**Allow AOS API paths:**
- Skip WAF for `/api/v1/*` with valid API key header
- Skip challenge for `/api/v1/events` (SSE)

**Block rules:**
- Rate limit `/api/v1/runtime/simulate` to 10 req/min per IP
- Block requests without User-Agent

### 7. Speed Settings

- [ ] Auto Minify: CSS, JS (not HTML)
- [ ] Brotli: **ON**
- [ ] HTTP/2: **ON**
- [ ] HTTP/3 (QUIC): **ON**
- [ ] Early Hints: **ON**
- [ ] Rocket Loader: **OFF** (can break React apps)

### 8. Network Settings

- [ ] WebSockets: **ON** (for SSE fallback)
- [ ] gRPC: **OFF** (not used)
- [ ] Pseudo IPv4: **OFF**
- [ ] IP Geolocation: **ON**

### 9. Firewall Rules

**Rate Limiting:**
```
(http.request.uri.path contains "/api/v1/runtime/simulate")
→ Rate limit: 10 requests per minute per IP
→ Action: Challenge
```

**API Key Requirement:**
```
(http.request.uri.path starts with "/api/v1/")
and not (http.request.headers["authorization"] exists
     or http.request.headers["x-api-key"] exists)
→ Action: Block (after grace period)
```

### 10. Workers (Optional)

Consider Cloudflare Workers for:
- API rate limiting
- Request logging
- A/B testing console versions
- Edge caching for /api/v1/runtime/capabilities

### 11. Verification Commands

After setup, verify:

```bash
# Check SSL
curl -I https://agenticverz.com/console/

# Check API proxy
curl https://agenticverz.com/api/v1/health

# Check cache headers
curl -I https://agenticverz.com/console/assets/index-xxx.js

# Check SSE (should stream)
curl -N https://agenticverz.com/api/v1/events
```

### 12. Monitoring

- [ ] Enable Analytics
- [ ] Enable Web Analytics (free)
- [ ] Set up Health Checks for `/health` endpoint
- [ ] Configure Notifications for:
  - SSL expiry
  - Origin health failures
  - DDoS attacks
  - WAF blocks

---

## Quick Reference

| Setting | Value |
|---------|-------|
| SSL Mode | Full (Strict) |
| Cache API | Bypass |
| Cache Assets | 1 year |
| HTTP/2 | ON |
| HTTP/3 | ON |
| Rocket Loader | OFF |
| WebSockets | ON |
