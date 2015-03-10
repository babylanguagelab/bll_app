-- Create tables --
CREATE TABLE speaker_types
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT UNIQUE NOT NULL
);

CREATE TABLE transcriber_codes
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code TEXT NOT NULL,
trans_index INTEGER NOT NULL, -- note: begins at 1
speaker_type_id INTEGER NOT NULL,
display_desc TEXT NOT NULL,
FOREIGN KEY(speaker_type_id) REFERENCES speaker_types(id) ON DELETE CASCADE
);

CREATE TABLE lena_notes_codes
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code TEXT UNIQUE NOT NULL,
speaker_type_id INTEGER NOT NULL,
display_desc TEXT NOT NULL,
FOREIGN KEY(speaker_type_id) REFERENCES speaker_types(id) ON DELETE CASCADE
);

CREATE TABLE speaker_codes
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code TEXT UNIQUE NOT NULL,
speaker_type_id INTEGER NOT NULL,
display_desc TEXT NOT NULL,
distance INTEGER NOT NULL, -- 0=near, 1=far, 2=n/a (eg. silence)
is_linkable INTEGER NOT NULL,
is_media INTEGER NOT NULL,
is_nonverbal_noise INTEGER NOT NULL,
is_overlapping INTEGER NOT NULL,
FOREIGN KEY(speaker_type_id) REFERENCES speaker_types(id) ON DELETE CASCADE
);

CREATE TABLE combo_groups
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT UNIQUE NOT NULL
);

CREATE TABLE combo_options
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT NOT NULL,
combo_group_id INTEGER NOT NULL,
disp_desc TEST NOT NULL,
hidden INTEGER NOT NULL DEFAULT 0,
FOREIGN KEY(combo_group_id) REFERENCES combo_groups(id) ON DELETE CASCADE
);

CREATE TABLE seg_filters
(id INTEGER PRIMARY KEY AUTOINCREMENT,
class_name TEXT NOT NULL,
args TEXT NOT NULL
);

CREATE TABLE checks_to_seg_filters
(id INTEGER PRIMARY KEY AUTOINCREMENT,
seg_filter_id INTEGER NOT NULL,
check_id INTGER NOT NULL,
FOREIGN KEY(seg_filter_id) REFERENCES seg_filters(id) ON DELETE CASCADE,
FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE CASCADE
);

CREATE TABLE checks
(id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
created INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
trs_filename TEXT NOT NULL,
wav_filename TEXT NOT NULL,
percent_segs INTEGER NOT NULL,
num_segs_limit INTEGER NOT NULL,
context_padding INTEGER NOT NULL,
completed INTEGER NULL, --this is a timestamp column. A value of NULL indicates not completed
pick_randomly INTEGER NOT NULL, --boolean
deleted INTEGER NOT NULL DEFAULT 0 --boolean
);

CREATE TABLE check_runs
(id INTEGER PRIMARY KEY AUTOINCREMENT,
check_id INTEGER NOT NULL,
run_timestamp INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE CASCADE
);

CREATE TABLE segments
(id INTEGER PRIMARY KEY AUTOINCREMENT,
test_id INTEGER NOT NULL,
start_time REAL NOT NULL,
end_time REAL NOT NULL,
FOREIGN KEY(test_id) REFERENCES tests(id) ON DELETE CASCADE
);

CREATE TABLE tests
(id INTEGER PRIMARY KEY AUTOINCREMENT,
check_run_id INTEGER NOT NULL,
category_input INTEGER NOT NULL,
with_context INTEGER NOT NULL, -- boolean
FOREIGN KEY(check_run_id) REFERENCES check_runs(id) ON DELETE CASCADE,
FOREIGN KEY(category_input) REFERENCES combo_options(id)
);

CREATE TABLE segs_to_speaker_codes
(id INTEGER PRIMARY KEY AUTOINCREMENT,
seg_id INTEGER NOT NULL,
speaker_code_id INTEGER NOT NULL,
FOREIGN KEY(seg_id) REFERENCES segments(id) ON DELETE CASCADE,
FOREIGN KEY(speaker_code_id) REFERENCES speaker_codes(id)
);

CREATE TABLE settings
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT NOT NULL UNIQUE,
val TEXT NULL
);