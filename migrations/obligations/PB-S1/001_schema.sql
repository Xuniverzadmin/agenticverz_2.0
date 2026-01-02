-- PB-S1: Retry Semantics + Immutability
-- Layer: L5 (Execution & Workers)
-- Purpose: Deterministic retries with immutable attempt history
-- Reference: PIN-199, PIN-265

-- Schema: pb_s1
-- All retry state lives here. No sharing with other obligations.

CREATE SCHEMA IF NOT EXISTS pb_s1;

COMMENT ON SCHEMA pb_s1 IS 'PB-S1: Retry Semantics with Immutability Guarantee';
