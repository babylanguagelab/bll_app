CREATE TABLE checks2
(id INTEGER PRIMARY KEY AUTOINCREMENT,
csv_file TEXT NOT NULL,
wav_folder TEXT NOT NULL,
activities TEXT NOT NULL,
environments TEXT NOT NULL,
blocks_per_activity INTEGER NOT NULL,
completed INTEGER NULL,
created INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
modified INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
test2_index NOT NULL DEFAULT 0
);

CREATE TABLE tests2
(id INTEGER PRIMARY KEY AUTOINCREMENT,
check2_id INTEGER NOT NULL,
wav_file TEXT NOT NULL,
child_vocs INTEGER NOT NULL,
transcription TEXT NOT NULL,
child_code TEXT NOT NULL,
spreadsheet_timestamp TEXT NOT NULL,
ui_save_data TEXT NULL,
FOREIGN KEY (check2_id) REFERENCES checks2 (id) ON DELETE CASCADE
);