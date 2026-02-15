# PIN-549: Neon Connection Audit (Docker + systemd)

**Status:** ✅ COMPLETE  
**Created:** 2026-02-09  
**Category:** Infrastructure / Ops

---

## Summary

Audit confirmed multiple runtime components were still pointing to Neon, even after local staging DB was prepared. PgBouncer routing is correct (local 127.0.0.1:5433), but two Docker services and four systemd timers were still configured with Neon `DATABASE_URL` via `.env`.

---

## Evidence

### Docker
- `nova_agent_manager` — direct to Neon (always running)
- `nova_worker` — direct to Neon (always running)

### systemd timers
- `aos-cost-snapshot-hourly` — `.env → Neon` (hourly)
- `aos-cost-snapshot-daily` — `.env → Neon` (daily)
- `agenticverz-r2-retry` — `.env → Neon` (every 15 min)
- `agenticverz-failure-aggregation` — `.env → Neon` (daily)

### PgBouncer
- Routes to local `127.0.0.1:5433`
- Cron jobs confirmed pointing to local

---

## Next Action

Switch `.env` to local DB and rebuild the Docker containers so all runtime paths use the local staging database.

---

## Status Update (Post-Switch Confirmation)

Everything is confirmed healthy and running on local DB:

- **/health:** healthy, database connected, 118 operations frozen
- **Local DB connections:** active and serving
- **Backend logs:** clean — health checks + metrics every ~5s, zero errors
- **Neon:** fully disconnected — no config points to it

**Runtime confirmation:** Both Docker containers (`nova_agent_manager`, `nova_worker`) are healthy and serving from `localhost:6432` (PgBouncer) → `localhost:5433` (local Postgres). The 4 systemd timers will use the updated `.env` on their next scheduled run.
