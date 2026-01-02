-- M10: Recovery & Outbox Infrastructure
-- Layer: L5 (Execution & Workers)
-- Purpose: Work queue and outbox pattern for reliable recovery
-- Reference: PIN-276, PIN-265

-- NOTE: Schema m10_recovery already exists with full infrastructure
-- This migration adds SUPPLEMENTAL immutability guarantees

-- Existing objects (already created):
--   - m10_recovery.work_queue (with uq_work_queue_candidate_pending)
--   - m10_recovery.outbox (with uq_outbox_pending)
--   - m10_recovery.dead_letter_archive
--   - m10_recovery.replay_log
--   - m10_recovery.distributed_locks
--   - m10_recovery.suggestion_* tables
--   - m10_recovery.mv_top_pending (materialized view)

-- This migration adds:
--   - Immutability triggers for outbox (audit trail protection)
--   - Status transition enforcement for work_queue
--   - Views for operational monitoring
