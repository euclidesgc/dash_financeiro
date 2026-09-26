-- Null only for runs written before this migration: who or what fed that
-- run is recorded nowhere, and inventing it would be worse than not having
-- it.
ALTER TABLE sync_runs ADD COLUMN origin TEXT NULL CHECK (origin IS NULL OR origin IN ('pluggy', 'file'));
