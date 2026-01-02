-- M26: Cost Intelligence Tables
-- Layer: L6 (Platform Substrate)
-- Purpose: Deterministic cost accounting for decisions (no hidden math)
-- Reference: PIN-141, PIN-265

-- Schema: m26
-- Cost intelligence lives here. Events are raw truth, snapshots are derived.

CREATE SCHEMA IF NOT EXISTS m26;

COMMENT ON SCHEMA m26 IS 'M26: Cost Intelligence - Deterministic cost accounting';
