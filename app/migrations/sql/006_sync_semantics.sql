-- The old column stored how many rows were present after the load, not how many
-- entered it: the second run of the same file wrote the full count while
-- inserting nothing. It was a real integrity proof carrying the wrong name.
ALTER TABLE sync_runs RENAME COLUMN transactions_count TO transactions_present;
ALTER TABLE sync_runs RENAME COLUMN accounts_count TO accounts_present;

-- Null for every run written before this migration: the number of rows a past
-- run inserted exists nowhere, and inventing it would be worse than not having
-- it.
ALTER TABLE sync_runs ADD COLUMN transactions_count INTEGER;
ALTER TABLE sync_runs ADD COLUMN accounts_count INTEGER;
