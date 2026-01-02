-- M26: Triggers
-- Immutability and snapshot maintenance

-- Function: Prevent cost_event updates
CREATE OR REPLACE FUNCTION m26.prevent_cost_event_update()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'm26.cost_event is immutable. Cost events cannot be modified.';
END;
$$ LANGUAGE plpgsql;

-- Trigger: Block updates on cost_event
CREATE TRIGGER trg_cost_event_no_update
BEFORE UPDATE ON m26.cost_event
FOR EACH ROW
EXECUTE FUNCTION m26.prevent_cost_event_update();

-- Function: Prevent cost_event deletes
CREATE OR REPLACE FUNCTION m26.prevent_cost_event_delete()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'm26.cost_event is immutable. Cost events cannot be deleted.';
END;
$$ LANGUAGE plpgsql;

-- Trigger: Block deletes on cost_event
CREATE TRIGGER trg_cost_event_no_delete
BEFORE DELETE ON m26.cost_event
FOR EACH ROW
EXECUTE FUNCTION m26.prevent_cost_event_delete();

-- Function: Update snapshot on new cost_event
CREATE OR REPLACE FUNCTION m26.update_snapshot()
RETURNS trigger AS $$
BEGIN
    INSERT INTO m26.cost_snapshot (snapshot_at, tenant_id, cost_type, total_units, event_count)
    VALUES (
        DATE(NEW.occurred_at),
        NEW.tenant_id,
        NEW.cost_type,
        NEW.cost_units,
        1
    )
    ON CONFLICT (snapshot_at, tenant_id, cost_type)
    DO UPDATE SET
        total_units = m26.cost_snapshot.total_units + NEW.cost_units,
        event_count = m26.cost_snapshot.event_count + 1,
        updated_at = now();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update snapshot on cost_event insert
CREATE TRIGGER trg_cost_event_snapshot
AFTER INSERT ON m26.cost_event
FOR EACH ROW
EXECUTE FUNCTION m26.update_snapshot();

-- Function: Update timestamp on cost_snapshot
CREATE OR REPLACE FUNCTION m26.update_snapshot_timestamp()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at on cost_snapshot
CREATE TRIGGER trg_cost_snapshot_updated
BEFORE UPDATE ON m26.cost_snapshot
FOR EACH ROW
EXECUTE FUNCTION m26.update_snapshot_timestamp();

COMMENT ON TRIGGER trg_cost_event_no_update ON m26.cost_event IS
    'Immutability guarantee: no updates allowed';
COMMENT ON TRIGGER trg_cost_event_no_delete ON m26.cost_event IS
    'Immutability guarantee: no deletes allowed';
COMMENT ON TRIGGER trg_cost_event_snapshot ON m26.cost_event IS
    'Auto-update daily snapshot on new cost event';
