-- PB-S4: Policy Proposals & Versions
-- Layer: L5 (Execution & Workers)
-- Purpose: Policy evolution with explicit versioning, no silent overwrite
-- Reference: PIN-204, PIN-265

-- Schema: pb_s4
-- Policy versioning lives here. Policies are immutable once created.

CREATE SCHEMA IF NOT EXISTS pb_s4;

COMMENT ON SCHEMA pb_s4 IS 'PB-S4: Policy Evolution with Versioning and Provenance';
