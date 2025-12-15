# AOS Error Playbook

**Version:** 1.0
**Last Updated:** 2025-12-13

This playbook provides diagnostic steps and solutions for common errors in the AOS platform.

---

## Quick Error Reference

| Error Code | Category | Severity | Go To |
|------------|----------|----------|-------|
| 401 | Authentication | High | [AUTH-001](#auth-001-unauthorized) |
| 403 | Authorization | High | [AUTH-002](#auth-002-forbidden) |
| 404 | Not Found | Medium | [API-001](#api-001-not-found) |
| 422 | Validation | Medium | [API-002](#api-002-validation-error) |
| 429 | Rate Limit | Medium | [RATE-001](#rate-001-rate-limited) |
| 500 | Server Error | Critical | [SRV-001](#srv-001-internal-server-error) |
| 502 | Gateway | High | [SRV-002](#srv-002-bad-gateway) |
| 503 | Unavailable | Critical | [SRV-003](#srv-003-service-unavailable) |
| TIMEOUT | Network | High | [NET-001](#net-001-timeout) |
| ECONNREFUSED | Network | Critical | [NET-002](#net-002-connection-refused) |

---

## Authentication Errors

### AUTH-001: Unauthorized (401)

**Symptoms:**
```json
{"detail": "Unauthorized", "status_code": 401}
```

**Causes:**
1. Missing API key
2. Invalid API key
3. Expired API key

**Resolution:**

1. **Check API key is set:**
   ```bash
   echo $AOS_API_KEY
   ```

2. **Verify API key format:**
   - Should start with `aos_` or be a valid token
   - Minimum 32 characters

3. **Test API key:**
   ```bash
   curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/health
   ```

4. **Request new key if expired:**
   Contact admin or regenerate via console

---

### AUTH-002: Forbidden (403)

**Symptoms:**
```json
{"detail": "Permission denied", "status_code": 403}
```

**Causes:**
1. Insufficient role permissions
2. Resource not owned by user
3. RBAC policy violation

**Resolution:**

1. **Check current permissions:**
   ```bash
   curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/rbac/info
   ```

2. **Verify resource ownership:**
   - Ensure you created the resource
   - Or have admin/operator role

3. **Request role upgrade:**
   Contact admin to modify RBAC assignment

**RBAC Roles:**
| Role | Capabilities |
|------|--------------|
| viewer | Read-only access |
| operator | Read + Execute |
| admin | Full access |

---

## API Errors

### API-001: Not Found (404)

**Symptoms:**
```json
{"detail": "Not found", "status_code": 404}
```

**Causes:**
1. Invalid endpoint path
2. Resource deleted
3. Wrong resource ID

**Resolution:**

1. **Verify endpoint exists:**
   ```bash
   # Check API docs
   curl http://localhost:8000/docs
   ```

2. **Check resource exists:**
   ```bash
   # List resources first
   curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/agents
   ```

3. **Common endpoint typos:**
   - `/api/v1/runtime/capabilities` (not `/capabilities`)
   - `/api/v1/recovery/stats` (not `/api/v1/stats`)

---

### API-002: Validation Error (422)

**Symptoms:**
```json
{
  "detail": [
    {
      "loc": ["body", "plan"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Causes:**
1. Missing required fields
2. Wrong data type
3. Invalid field values

**Resolution:**

1. **Check request format:**
   ```json
   // Correct simulate request
   {
     "plan": [
       {"skill": "llm_invoke", "params": {"prompt": "test"}}
     ],
     "budget_cents": 1000
   }
   ```

2. **Common mistakes:**
   - Using `steps` instead of `plan`
   - Missing `skill` field in plan items
   - Non-integer budget value

3. **Validate against schema:**
   ```bash
   # Get OpenAPI schema
   curl http://localhost:8000/openapi.json | jq '.paths["/api/v1/runtime/simulate"]'
   ```

---

## Rate Limiting

### RATE-001: Rate Limited (429)

**Symptoms:**
```json
{"detail": "Rate limit exceeded", "retry_after": 60}
```

**Causes:**
1. Too many requests per minute
2. Burst limit exceeded
3. Skill-specific rate limit

**Resolution:**

1. **Check current rate limits:**
   ```bash
   curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities | jq '.rate_limits'
   ```

2. **Implement backoff:**
   ```python
   import time

   def retry_with_backoff(func, max_retries=3):
       for i in range(max_retries):
           try:
               return func()
           except RateLimitError as e:
               wait = e.retry_after or (2 ** i)
               time.sleep(wait)
       raise Exception("Max retries exceeded")
   ```

3. **Request limit increase:**
   Contact admin with use case justification

---

## Server Errors

### SRV-001: Internal Server Error (500)

**Symptoms:**
```json
{"detail": "Internal server error", "status_code": 500}
```

**Causes:**
1. Unhandled exception in backend
2. Database connection failure
3. External service failure

**Resolution:**

1. **Check backend logs:**
   ```bash
   docker compose logs backend --tail 100
   ```

2. **Check database:**
   ```bash
   docker compose exec nova_db pg_isready
   ```

3. **Restart services:**
   ```bash
   docker compose restart backend worker
   ```

4. **Report issue with logs:**
   Include error ID if shown in response

---

### SRV-002: Bad Gateway (502)

**Symptoms:**
Browser shows "502 Bad Gateway" or nginx error page

**Causes:**
1. Backend not running
2. Proxy misconfiguration
3. Backend crashed

**Resolution:**

1. **Check backend status:**
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

2. **Check proxy config:**
   ```bash
   # Apache
   apachectl configtest

   # Nginx
   nginx -t
   ```

3. **Restart stack:**
   ```bash
   docker compose down && docker compose up -d
   ```

---

### SRV-003: Service Unavailable (503)

**Symptoms:**
```json
{"detail": "Service temporarily unavailable"}
```

**Causes:**
1. System overloaded
2. Maintenance mode
3. Dependency failure

**Resolution:**

1. **Check system resources:**
   ```bash
   docker stats
   free -h
   df -h
   ```

2. **Check all services:**
   ```bash
   docker compose ps
   ```

3. **Wait and retry:**
   Usually resolves within minutes

---

## Network Errors

### NET-001: Timeout

**Symptoms:**
- Request hangs then fails
- "Connection timed out" error
- No response after 30 seconds

**Causes:**
1. Slow backend processing
2. Network latency
3. Resource exhaustion

**Resolution:**

1. **Increase timeout:**
   ```python
   import requests
   requests.get(url, timeout=60)  # Increase from default
   ```

2. **Check backend load:**
   ```bash
   docker stats nova_agent_manager
   ```

3. **Check for slow queries:**
   ```bash
   docker compose logs backend | grep -i slow
   ```

---

### NET-002: Connection Refused

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Causes:**
1. Backend not running
2. Wrong port
3. Firewall blocking

**Resolution:**

1. **Check backend is running:**
   ```bash
   docker compose ps
   # Should show "Up" for backend
   ```

2. **Verify port:**
   ```bash
   curl http://localhost:8000/health
   # If fails, check port binding
   docker compose logs backend | grep -i listening
   ```

3. **Start services:**
   ```bash
   docker compose up -d
   ```

---

## Skill-Specific Errors

### SKILL-001: Skill Not Available

**Symptoms:**
```json
{"feasible": false, "risks": ["skill_unavailable: custom_skill"]}
```

**Resolution:**
1. Check available skills via `/api/v1/runtime/capabilities`
2. Use only supported skills: `http_call`, `llm_invoke`, `json_transform`, `fs_read`, `fs_write`, `webhook_send`, `email_send`

### SKILL-002: LLM Invoke Failure

**Symptoms:**
```json
{"error": "LLM provider error", "detail": "..."}
```

**Resolution:**
1. Check LLM API key configured in backend
2. Verify quota not exceeded
3. Check prompt isn't too long (max 100k tokens)

### SKILL-003: HTTP Call Timeout

**Symptoms:**
Simulation shows `TIMEOUT` in known_failure_patterns

**Resolution:**
1. Target URL may be slow/unreliable
2. Consider shorter timeouts
3. Implement retry logic

---

## Console UI Errors

### UI-001: Login Failed

**Symptoms:**
"Authentication failed" message on login page

**Resolution:**
1. Verify API key is correct
2. Check browser console for details (F12)
3. Clear browser cache/cookies
4. Try incognito mode

### UI-002: Page Not Loading

**Symptoms:**
White screen or loading spinner stuck

**Resolution:**
1. Open DevTools (F12) → Console
2. Check for JavaScript errors
3. Verify API_BASE is correct in .env
4. Try hard refresh (Ctrl+Shift+R)

### UI-003: Data Not Refreshing

**Symptoms:**
Old data showing despite changes

**Resolution:**
1. Click refresh button in UI
2. Clear TanStack Query cache
3. Logout and login again

---

## Diagnostic Commands

```bash
# Full system check
docker compose ps
docker compose logs backend --tail 50
curl http://localhost:8000/health

# Database check
docker compose exec nova_pgbouncer psql -U nova -d nova_aos -c "SELECT 1"

# Redis check
docker compose exec nova_redis redis-cli ping

# API test
curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities

# Run smoke tests
python3 tests/aos-test-suite/smoke_test.py
```

---

## Escalation Path

1. **Self-service:** Use this playbook
2. **Community:** Discord #help channel
3. **Support ticket:** beta@agenticverz.com
4. **Critical:** On-call via PagerDuty (internal only)

---

## Error Logging

When reporting errors, always include:
- Timestamp (UTC)
- Request ID (from response headers)
- Full error response
- Steps to reproduce
- Environment details
