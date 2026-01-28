# PIN-476: Optimize amavisd — reduce to 1 worker, disable broken ClamAV

**Status:** ✅ COMPLETE
**Created:** 2026-01-27
**Category:** Infrastructure / Optimization

---

## Summary

Reduced amavisd from 3 processes (553 MB) to 1 master (186 MB). Disabled broken ClamAV scanner that was failing on every email. Postfix master.cf maxproc aligned to 1.

---

## Details

## Problem

amavisd (mail content filter) was running 3 processes consuming 553 MB total:
- Master: 187 MB
- Worker ch6-avail: 189 MB
- Worker ch4-avail: 177 MB

Issues:
1. Only processing ~15 emails/day (mostly cron reports) — 2 always-on workers massively overprovisioned
2. ClamAV scanner was BROKEN — socket /var/run/clamav/clamd.ctl missing
   - Every email logged: '(\!)clamav-socket av-scanner FAILED' and '(\!\!)AV: ALL VIRUS SCANNERS FAILED'
   - All email passed as UNCHECKED despite appearing to have AV scanning
3. SpamAssassin running embedded in amavisd (adds memory per process)
4. Integration: Postfix → amavis:10024 → content filter → re-inject via :10025

## Changes Made

### 1. /etc/amavis/conf.d/50-user
- $max_servers: 2 → 1
  - 1 worker is more than sufficient for 15 emails/day
  - amavis forks child on demand when mail arrives, no idle children
- @av_scanners: disabled (was \['clamav-socket', ...])
  - ClamAV daemon not installed, socket doesn't exist
  - Eliminates error log spam on every email
  - Original config preserved in comment for re-enabling
  - @av_scanners_backup already empty (no change needed)

### 2. /etc/postfix/master.cf
- smtp-amavis transport maxproc: 2 → 1
  - Must match amavis $max_servers per amavis docs
  - Line: 'smtp-amavis unix - - n - 1 smtp'

### 3. Services restarted
- /etc/init.d/amavis restart
- postfix reload

## What still works
- SpamAssassin spam scoring (embedded in amavisd)
- DKIM signing for outbound mail
- DKIM/DMARC verification for inbound mail
- All Postfix content_filter routing (ports 10024, 10026, 10027)
- Quarantine on port 9998

## What was removed
- ClamAV virus scanning (was already non-functional)
- Second idle worker process

## To re-enable ClamAV later
1. Install ClamAV: apt install clamav clamav-daemon
2. Start daemon: systemctl start clamav-daemon
3. Verify socket: ls /var/run/clamav/clamd.ctl
4. Edit /etc/amavis/conf.d/50-user — uncomment @av_scanners block
5. Restart amavis: /etc/init.d/amavis restart
Note: ClamAV itself uses 200-400 MB — weigh against mail volume

## Memory impact

| Metric | Before | After |
|--------|--------|-------|
| amavisd processes | 3 | 1 (forks on demand) |
| amavisd RSS | 553 MB | 186 MB |
| Freed | 367 MB | - |

## Cumulative session savings (PIN-474 + PIN-475 + this)

| Optimization | Memory freed |
|--------------|-------------|
| PIN-474: continuous_validator → scheduled scan | 600 MB |
| PIN-475: worker pool killed | 666 MB |
| PIN-476: amavisd reduced | 367 MB |
| **Total** | **1,633 MB (~1.6 GB)** |

System memory used: 4.1 Gi → 3.0 Gi
System memory available: 7.5 Gi → 8.7 Gi

## Files changed
- /etc/amavis/conf.d/50-user (max_servers, av_scanners)
- /etc/postfix/master.cf (smtp-amavis maxproc)

## Mail server context
- Installation: iRedMail 1.7.4
- MTA: Postfix
- Domain: agenticverz.com
- Hostname: vmi2788299.contaboserver.net
- Ports: 10024 (inbound), 10026 (outbound/DKIM), 10027 (MLMMJ), 9998 (quarantine)
- DB backend: PostgreSQL (amavisd user lookups)

---

## Related PINs

- [PIN-474](PIN-474-.md)
- [PIN-475](PIN-475-.md)
