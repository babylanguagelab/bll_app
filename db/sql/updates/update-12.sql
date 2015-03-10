--This script will delete all previous reliability 1 program data! This was deemed ok because the data collection was completely restarted from scratch due to various lab issues.

PRAGMA foreign_keys = OFF;
DELETE FROM seg_filters WHERE id IN (SELECT seg_filter_id FROM checks_to_seg_filters);
DELETE FROM checks_to_seg_filters;

DELETE FROM segments WHERE id IN (SELECT segment_id FROM tests);
DELETE FROM tests;
DELETE FROM checks;
DELETE FROM check_runs;

DROP TABLE tests;

CREATE TABLE tests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
check_id INTEGER NOT NULL,
category_input INTEGER NULL,
syllables_w_context INTEGER NULL,
syllables_wo_context INTEGER NULL,
segment_id INTEGER NOT NULL,
is_uncertain INTEGER NULL,
context_padding INTEGER NOT NULL,
FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE CASCADE,
FOREIGN KEY(category_input) REFERENCES combo_options(id),
FOREIGN KEY(segment_id) REFERENCES segments(id)
);

ALTER TABLE segments ADD COLUMN user_adj_start REAL NULL;
ALTER TABLE segments ADD COLUMN user_adj_end REAL NULL;

drop table checks;

CREATE TABLE checks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
created INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
input_filename TEXT NOT NULL,
wav_filename TEXT NOT NULL,
num_segs INTEGER NOT NULL,
default_context_padding INTEGER NOT NULL,
test_index INTEGER NOT NULL,
completed INTEGER NULL, --this is a timestamp colum
pick_randomly INTEGER NOT NULL, --boolean
last_run INTEGER NULL --this is a timestamp column for last time check was run
);

DROP TABLE check_runs;

PRAGMA foreign_keys = ON;
