-- M10: Lifecycle Constraints (STEP 2)
-- Purpose: Make completion semantics explicit in DB
-- Rule: Cannot be processed AND claimed simultaneously

-- First check if claimed_at column exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'm10_recovery'
        AND table_name = 'outbox'
        AND column_name = 'claimed_at'
    ) THEN
        -- Add constraint: valid completion lifecycle
        -- Cannot be processed and claimed at the same time
        ALTER TABLE m10_recovery.outbox
        DROP CONSTRAINT IF EXISTS valid_completion;

        ALTER TABLE m10_recovery.outbox
        ADD CONSTRAINT valid_completion CHECK (
            -- State 1: Unclaimed, unprocessed (pending)
            (processed_at IS NULL AND claimed_at IS NULL)
            OR
            -- State 2: Claimed, not yet processed (in progress)
            (processed_at IS NULL AND claimed_at IS NOT NULL)
            OR
            -- State 3: Processed, must not be claimed (complete)
            (processed_at IS NOT NULL AND claimed_at IS NULL)
        );

        COMMENT ON CONSTRAINT valid_completion ON m10_recovery.outbox IS
            'Lifecycle: pending -> claimed -> processed. Cannot be both claimed and processed.';
    ELSE
        -- If no claimed_at column, simpler constraint
        RAISE NOTICE 'claimed_at column not found - skipping lifecycle constraint';
    END IF;
END
$$;

-- Constraint: processed_by required when processed_at is set
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'm10_recovery'
        AND table_name = 'outbox'
        AND column_name = 'processed_by'
    ) THEN
        ALTER TABLE m10_recovery.outbox
        DROP CONSTRAINT IF EXISTS processed_requires_processor;

        ALTER TABLE m10_recovery.outbox
        ADD CONSTRAINT processed_requires_processor CHECK (
            (processed_at IS NULL) OR (processed_at IS NOT NULL AND processed_by IS NOT NULL)
        );

        COMMENT ON CONSTRAINT processed_requires_processor ON m10_recovery.outbox IS
            'When processed_at is set, processed_by must identify the processor';
    END IF;
END
$$;
