INSERT INTO settings (code_name, val) VALUES ('PRAAT_IPC_PORT', '6667');
INSERT INTO settings (code_name, val) VALUES ('PRAAT_PATH', 'C:/Program Files/Praat/Praat.exe');
INSERT INTO settings (code_name, val) VALUES ('SENDPRAAT_PATH', 'C:/Program Files/Praat/sendpraat.exe');

ALTER TABLE tests ADD COLUMN adjusted_start REAL NOT NULL DEFAULT 0;
ALTER TABLE tests ADD COLUMN adjusted_end REAL NOT NULL DEFAULT 0;

UPDATE tests set adjusted_start = (SELECT start_time FROM (SELECT s.start_time, t.id FROM segments s JOIN tests t ON t.segment_id = s.id) time_table WHERE time_table.id = id);

UPDATE tests set adjusted_end = (SELECT end_time FROM (SELECT s.end_time, t.id FROM segments s JOIN tests t ON t.segment_id = s.id) time_table WHERE time_table.id = id);