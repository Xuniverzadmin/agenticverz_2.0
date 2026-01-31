# MCP — RELOCATED

**Status:** RELOCATED
**Date:** 2026-01-29
**Previous path:** `backend/app/hoc/hoc_spine/mcp/`
**New path:** `backend/app/hoc/cus/integrations/adapters/mcp_server_registry.py`

---

## Decision

`hoc_spine/mcp/server_registry.py` does NOT belong in hoc_spine.

**Evidence:**
- Zero callers — orphaned module, not imported anywhere in the codebase
- Duplicate exists at `backend/app/services/mcp/server_registry.py`
- `cus/integrations/adapters/` already has 14 adapters (established pattern)
- MCP is tool discovery/integration, not system constitution

**Action taken:** File moved to `cus/integrations/adapters/mcp_server_registry.py`. Header updated to L3 layer. hoc_spine script count adjusted from 67 to 66.
