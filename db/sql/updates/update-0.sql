--correct error in speaker_codes table
UPDATE speaker_codes SET is_linkable=1 WHERE code='OLN';

--new tables for stats app
INSERT INTO combo_groups (code_name) VALUES ('COUNT_OUTPUT_CALC_TYPES');
INSERT INTO combo_groups (code_name) VALUES ('RATE_OUTPUT_CALC_TYPES');
INSERT INTO combo_groups (code_name) VALUES ('BREAKDOWN_OUTPUT_CALC_CRITERIA');
INSERT INTO combo_groups (code_name) VALUES ('FILTER_LINKAGE_OPTIONS');

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COUNT_OUTPUT_CALC_TYPES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COUNT_OUTPUT_CALC_TYPES'), 'PER_SEG', 'Per Seg', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COUNT_OUTPUT_CALC_TYPES'), 'AVG_ACROSS_SEGS', 'Avg Across Segs', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COUNT_OUTPUT_CALC_TYPES'), 'SUM_ACROSS_SEGS', 'Sum Across Segs', 0);

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='RATE_OUTPUT_CALC_TYPES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='RATE_OUTPUT_CALC_TYPES'), 'PER_SEG', 'Per Seg', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='RATE_OUTPUT_CALC_TYPES'), 'AVG_ACROSS_SEGS', 'Avg Across Segs', 0);

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='BREAKDOWN_OUTPUT_CALC_CRITERIA'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='BREAKDOWN_OUTPUT_CALC_CRITERIA'), 'SPEAKER_TYPE', 'Speaker Type', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='BREAKDOWN_OUTPUT_CALC_CRITERIA'), 'TARGET_LISTENER', 'Target Listener', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='BREAKDOWN_OUTPUT_CALC_CRITERIA'), 'COMPLETENESS', 'Gramaticality/Completeness', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='BREAKDOWN_OUTPUT_CALC_CRITERIA'), 'UTTERANCE_TYPE', 'Utterance Type', 0);

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='FILTER_LINKAGE_OPTIONS'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='FILTER_LINKAGE_OPTIONS'), 'LINKED', 'Linked', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='FILTER_LINKAGE_OPTIONS'), 'UNLINKED', 'Unlinked', 0);

CREATE TABLE output_configs
(id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
desc TEXT NOT NULL,
created INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE outputs
(id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
desc TEXT NOT NULL,
calc_class_name TEXT NOT NULL,
calc_args TEXT NOT NULL
);

CREATE TABLE output_configs_to_outputs
(id INTEGER PRIMARY KEY AUTOINCREMENT,
config_id INTEGER NOT NULL,
output_id INTEGER NOT NULL,
FOREIGN KEY(config_id) REFERENCES output_configs(id) ON DELETE CASCADE,
FOREIGN KEY(output_id) REFERENCES outputs(id) ON DELETE CASCADE
);

CREATE TABLE outputs_to_seg_filters
(id INTEGER PRIMARY KEY AUTOINCREMENT,
output_id INTEGER NOT NULL,
seg_filter_id INTEGER NOT NULL,
FOREIGN KEY(output_id) REFERENCES outputs(id) ON DELETE CASCADE,
FOREIGN KEY(seg_filter_id) REFERENCES seg_filters(id) ON DELETE CASCADE
);

--move the relation between segments and tests
--segments has a column test_id - move this to a new column in tests called segment_id.
--unfortunately, we have to drop and re-create the segments table because sqlite doesn't currently support adding constraints to an existing table
--these commands make the modifications, and transfer all of the existing data
PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
CREATE TEMPORARY TABLE temp_tests(id, check_run_id, category_input, with_context, segment_id);
INSERT INTO temp_tests (id, check_run_id, category_input, with_context, segment_id) SELECT t.id, t.check_run_id, t.category_input, t.with_context, s.id from tests t join segments s on s.test_id = t.id ORDER BY t.id ASC;
DROP TABLE tests;
CREATE TABLE tests
(id INTEGER PRIMARY KEY AUTOINCREMENT,
check_run_id INTEGER NOT NULL,
category_input INTEGER NOT NULL,
with_context INTEGER NOT NULL,
segment_id INTEGER NOT NULL,
FOREIGN KEY(check_run_id) REFERENCES check_runs(id) ON DELETE CASCADE,
FOREIGN KEY(category_input) REFERENCES combo_options(id),
FOREIGN KEY(segment_id) REFERENCES segments(id)
);
INSERT INTO tests (id, check_run_id, category_input, with_context, segment_id) SELECT id, check_run_id, category_input, with_context, segment_id FROM temp_tests ORDER BY id ASC;
DROP TABLE temp_tests;

CREATE TEMPORARY TABLE temp_segs(id, start_time, end_time);
INSERT INTO temp_segs (id, start_time, end_time) SELECT id, start_time, end_time FROM segments ORDER BY id ASC;
DROP TABLE segments;
CREATE TABLE segments
(id INTEGER PRIMARY KEY AUTOINCREMENT,
start_time REAL NOT NULL,
end_time REAL NOT NULL
);
INSERT INTO segments (id, start_time, end_time) SELECT id, start_time, end_time FROM temp_segs ORDER BY id ASC;
COMMIT;
PRAGMA foreign_keys = ON;