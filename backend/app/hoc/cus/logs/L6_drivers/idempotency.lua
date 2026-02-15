--[[
AOS Idempotency Lua Script

Atomic idempotency check with Redis.
Returns:
  - "new": First time seeing this key, lock acquired
  - "duplicate": Key exists with same hash (idempotent replay)
  - "conflict": Key exists with different hash (conflict)

Arguments:
  KEYS[1] = idempotency key (e.g., "idem:{tenant}:{key}")
  ARGV[1] = request hash (sha256 of canonical request)
  ARGV[2] = TTL in seconds
  ARGV[3] = tenant_id
  ARGV[4] = trace_id (for audit)

M8 Deliverable: Atomic idempotency enforcement
]]--

local key = KEYS[1]
local request_hash = ARGV[1]
local ttl = tonumber(ARGV[2]) or 86400  -- Default 24h
local tenant_id = ARGV[3] or "default"
local trace_id = ARGV[4] or ""

-- Check if key exists
local existing = redis.call("HGETALL", key)

if #existing == 0 then
    -- New key: acquire lock
    redis.call("HSET", key,
        "hash", request_hash,
        "tenant_id", tenant_id,
        "trace_id", trace_id,
        "created_at", redis.call("TIME")[1],
        "status", "pending"
    )
    redis.call("EXPIRE", key, ttl)
    return {"new", request_hash, ""}
end

-- Key exists: check hash
local stored_hash = ""
local stored_trace_id = ""
for i = 1, #existing, 2 do
    if existing[i] == "hash" then
        stored_hash = existing[i + 1]
    elseif existing[i] == "trace_id" then
        stored_trace_id = existing[i + 1]
    end
end

if stored_hash == request_hash then
    -- Idempotent duplicate
    return {"duplicate", stored_hash, stored_trace_id}
else
    -- Hash mismatch: conflict
    return {"conflict", stored_hash, stored_trace_id}
end
