-- PB-S2: Crash Recovery State
-- Layer: L5 (Execution & Workers)
-- Purpose: Resume workflows after process death (not retry failure)
-- Reference: PIN-202, PIN-265

-- Schema: pb_s2
-- Crash recovery state lives here. Separate from retry logic (PB-S1).

CREATE SCHEMA IF NOT EXISTS pb_s2;

COMMENT ON SCHEMA pb_s2 IS 'PB-S2: Crash Recovery - Resume workflows after process death';
