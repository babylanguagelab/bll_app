ALTER TABLE tests ADD COLUMN adjusted_padding INTEGER NOT NULL DEFAULT 0;

UPDATE tests SET adjusted_padding = (SELECT c.context_padding FROM check_runs cr join checks c ON cr.check_id = c.id WHERE cr.id = tests.check_run_id);
UPDATE tests SET adjusted_padding = 0 WHERE with_context = 0;