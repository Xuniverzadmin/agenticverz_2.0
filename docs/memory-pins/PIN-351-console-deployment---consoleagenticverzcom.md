# PIN-351: Console Deployment - console.agenticverz.com

**Status:** ✅ COMPLETE
**Created:** 2026-01-07
**Category:** Infrastructure / Deployment

---

## Summary

Deployed console.agenticverz.com with admin user, Apache vhost, safety switches, and UI contract serving

---

## Details

## Console Deployment Summary

**Date:** 2026-01-07
**URL:** https://console.agenticverz.com

### What Was Deployed

1. **Admin User Bootstrap**
   - Created `backend/scripts/seed_admin.py` - Admin seeding script
   - User: admin1@agenticverz.com (owner role)
   - Tenant: AgenticVerz Internal (enterprise plan)
   - API Key generated for programmatic access
   - Fixed: API key prefix truncation (varchar(10) limit)

2. **Apache Virtual Host**
   - Config: `/etc/apache2/sites-available/console.agenticverz.com.conf`
   - SSL via Cloudflare Origin Certificate
   - DocumentRoot: `/root/agenticverz2.0/website/app-shell/dist`
   - API proxy to localhost:8000
   - SPA fallback routing

3. **UI Contract Serving**
   - Path: `/contracts/ui_contract.v1.json`
   - Served from: `dist/contracts/` (copied from src/contracts)
   - Status: DRAFT_UI_DRIVING

4. **Safety Switches (.env)**
   ```
   CONSOLE_MODE=DRAFT
   DATA_MODE=SYNTHETIC
   ACTION_MODE=NOOP
   DEV_AUTH_ENABLED=true
   DEV_DEFAULT_ROLE=founder
   ```

### Key Files Created/Modified

| File | Purpose |
|------|---------|
| `backend/scripts/seed_admin.py` | Admin user bootstrap script |
| `backend/app/config/console_modes.py` | Runtime safety switch helpers |
| `/etc/apache2/sites-available/console.agenticverz.com.conf` | Apache vhost |
| `.env` | Added safety switches |

### Architecture Notes

- Apache handles port 443 (not nginx)
- Nginx configs exist but Apache is primary
- Permission fix: `chmod 711 /root` for www-data access
- Contracts copied to dist/ for simpler serving

### Pending

- [ ] Create admin1@agenticverz.com in Clerk dashboard
- [ ] Update clerk_user_id after Clerk user creation
- [ ] Wire real Clerk authentication (currently DEV_AUTH_ENABLED)

### Verification Commands

```bash
# Test contracts
curl -s https://console.agenticverz.com/contracts/ui_contract.v1.json | jq .version

# Test health
curl -s https://console.agenticverz.com/healthz | jq .status

# Run admin seed (dry-run)
python3 backend/scripts/seed_admin.py --dry-run
```
---

## Updates

### Update (2026-01-07)

## 2026-01-07: Clerk User Synced

- Created user in Clerk dashboard: admin1@agenticverz.com
- Clerk User ID: `user_37wGBuejeUGNS3ID2nUBcRgRvF5`
- Database updated: clerk_user_id synced
- Admin user now fully configured for Clerk authentication
