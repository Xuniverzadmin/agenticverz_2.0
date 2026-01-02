-- PB-S4: Triggers
-- Immutability and versioning enforcement

-- Function: Prevent updates to immutable columns
CREATE OR REPLACE FUNCTION pb_s4.prevent_definition_update()
RETURNS trigger AS $$
BEGIN
    -- These columns are immutable after creation
    IF OLD.definition IS DISTINCT FROM NEW.definition THEN
        RAISE EXCEPTION 'policy_version.definition is immutable. Create a new version instead.';
    END IF;

    IF OLD.version IS DISTINCT FROM NEW.version THEN
        RAISE EXCEPTION 'policy_version.version is immutable. Create a new version instead.';
    END IF;

    IF OLD.policy_id IS DISTINCT FROM NEW.policy_id THEN
        RAISE EXCEPTION 'policy_version.policy_id is immutable.';
    END IF;

    IF OLD.created_by IS DISTINCT FROM NEW.created_by THEN
        RAISE EXCEPTION 'policy_version.created_by is immutable.';
    END IF;

    IF OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION 'policy_version.created_at is immutable.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Enforce immutability on policy_version
CREATE TRIGGER trg_policy_version_immutable
BEFORE UPDATE ON pb_s4.policy_version
FOR EACH ROW
EXECUTE FUNCTION pb_s4.prevent_definition_update();

-- Function: Prevent delete of policy_version
CREATE OR REPLACE FUNCTION pb_s4.prevent_version_delete()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'policy_version rows cannot be deleted. History must be preserved.';
END;
$$ LANGUAGE plpgsql;

-- Trigger: Block deletes
CREATE TRIGGER trg_policy_version_no_delete
BEFORE DELETE ON pb_s4.policy_version
FOR EACH ROW
EXECUTE FUNCTION pb_s4.prevent_version_delete();

-- Function: Auto-increment version number
CREATE OR REPLACE FUNCTION pb_s4.auto_version()
RETURNS trigger AS $$
DECLARE
    max_version INTEGER;
BEGIN
    -- Get current max version for this policy
    SELECT COALESCE(MAX(version), 0) INTO max_version
    FROM pb_s4.policy_version
    WHERE policy_id = NEW.policy_id;

    -- Set version to max + 1
    NEW.version = max_version + 1;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-assign version number on insert
CREATE TRIGGER trg_policy_version_auto_version
BEFORE INSERT ON pb_s4.policy_version
FOR EACH ROW
EXECUTE FUNCTION pb_s4.auto_version();

COMMENT ON TRIGGER trg_policy_version_immutable ON pb_s4.policy_version IS
    'Enforce immutability of definition and core columns';
COMMENT ON TRIGGER trg_policy_version_no_delete ON pb_s4.policy_version IS
    'Prevent deletion of policy versions';
COMMENT ON TRIGGER trg_policy_version_auto_version ON pb_s4.policy_version IS
    'Auto-assign monotonically increasing version numbers';
