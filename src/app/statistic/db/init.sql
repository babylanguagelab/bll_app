-- speaker types table --
CREATE TABLE speaker_types
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT UNIQUE NOT NULL
);
INSERT INTO speaker_types (code_name) VALUES ('NA'); -- for speakers like SIL, NOF, NON
INSERT INTO speaker_types (code_name) VALUES ('TARGET_CHILD');
INSERT INTO speaker_types (code_name) VALUES ('FEMALE_ADULT');
INSERT INTO speaker_types (code_name) VALUES ('MALE_ADULT');
INSERT INTO speaker_types (code_name) VALUES ('OTHER_CHILD');
INSERT INTO speaker_types (code_name) VALUES ('UNCERTAIN_CHILD');
INSERT INTO speaker_types (code_name) VALUES ('UNCERTAIN');
INSERT INTO speaker_types (code_name) VALUES ('ADULT');
INSERT INTO speaker_types (code_name) VALUES ('SILENCE');


-- transcriber codes table --
CREATE TABLE transcriber_codes
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code TEXT NOT NULL,
trans_index INTEGER NOT NULL, -- note: begins at 1
speaker_type_id INTEGER NOT NULL,
display_desc TEXT NOT NULL,
FOREIGN KEY(speaker_type_id) REFERENCES speaker_types(id) ON DELETE CASCADE
);
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('M', 1, (SELECT id from speaker_types where code_name='MALE_ADULT'), 'Male Adult');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('F', 1, (SELECT id from speaker_types where code_name='FEMALE_ADULT'), 'Female Adult');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('T', 1, (SELECT id from speaker_types where code_name='TARGET_CHILD'), 'Target Adult');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('O', 1, (SELECT id from speaker_types where code_name='OTHER_CHILD'), 'Other Child');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('C', 1, (SELECT id from speaker_types where code_name='UNCERTAIN_CHILD'), 'Uncertain Child');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('U', 1, (SELECT id from speaker_types where code_name='UNCERTAIN'), 'Uncertain');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('T', 2, (SELECT id from speaker_types where code_name='TARGET_CHILD'), 'Target Child');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('O', 2, (SELECT id from speaker_types where code_name='OTHER_CHILD'), 'Other Child');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('C', 2, (SELECT id from speaker_types where code_name='UNCERTAIN_CHILD'), 'Uncertain Child');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('A', 2, (SELECT id from speaker_types where code_name='ADULT'), 'Adult');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('U', 2, (SELECT id from speaker_types where code_name='UNCERTAIN'), 'Uncertain');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('F', 3, (SELECT id from speaker_types where code_name='NA'), 'Complete');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('D', 3, (SELECT id from speaker_types where code_name='NA'), 'Disfluency');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('M', 3, (SELECT id from speaker_types where code_name='NA'), 'Mispronunciation');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('I', 3, (SELECT id from speaker_types where code_name='NA'), 'Continued');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('C', 3, (SELECT id from speaker_types where code_name='NA'), 'Continuation');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('U', 3, (SELECT id from speaker_types where code_name='NA'), 'Uncertain');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('Q', 4, (SELECT id from speaker_types where code_name='NA'), 'Question');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('D', 4, (SELECT id from speaker_types where code_name='NA'), 'Declarative/Statement');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('I', 4, (SELECT id from speaker_types where code_name='NA'), 'Imperitive (Command)');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('U', 4, (SELECT id from speaker_types where code_name='NA'), 'Uncertain');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('R', 4, (SELECT id from speaker_types where code_name='NA'), 'Reading');
INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES ('S', 4, (SELECT id from speaker_types where code_name='NA'), 'Singing');

-- lena notes codes table --
CREATE TABLE lena_notes_codes
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code TEXT UNIQUE NOT NULL,
speaker_type_id INTEGER NOT NULL,
display_desc TEXT NOT NULL,
FOREIGN KEY(speaker_type_id) REFERENCES speaker_types(id) ON DELETE CASCADE
);
INSERT INTO lena_notes_codes (code, speaker_type_id, display_desc) VALUES ('VOC', (SELECT id from speaker_types where code_name='NA'), 'Vocal');
INSERT INTO lena_notes_codes (code, speaker_type_id, display_desc) VALUES ('SIL', (SELECT id from speaker_types where code_name='SILENCE'), 'Silence');
INSERT INTO lena_notes_codes (code, speaker_type_id, display_desc) VALUES ('FAN', (SELECT id from speaker_types where code_name='FEMALE_ADULT'), 'Female Adult');
INSERT INTO lena_notes_codes (code, speaker_type_id, display_desc) VALUES ('VFX', (SELECT id from speaker_types where code_name='NA'), ''); --not sure what LENA uses this one for...
INSERT INTO lena_notes_codes (code, speaker_type_id, display_desc) VALUES ('CRY', (SELECT id from speaker_types where code_name='NA'), 'Cry');


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
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('CHF', 'Target Child Far', (SELECT id from speaker_types where code_name='TARGET_CHILD'), 1,  2, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('CHN', 'Target Child Near', (SELECT id from speaker_types where code_name='TARGET_CHILD'), 1,  1, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('CXF', 'Other Child Far', (SELECT id from speaker_types where code_name='OTHER_CHILD'),  1,  2, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('CXN', 'Other Child Near', (SELECT id from speaker_types where code_name='OTHER_CHILD'),  1,  1, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('FAF', 'Female Adult Far', (SELECT id from speaker_types where code_name='FEMALE_ADULT'), 1,  2, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('FAN', 'Female Adult Near', (SELECT id from speaker_types where code_name='FEMALE_ADULT'), 1,  1, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('MAF', 'Male Adult Far', (SELECT id from speaker_types where code_name='MALE_ADULT'), 1,  2, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('MAN', 'Male Adult Near', (SELECT id from speaker_types where code_name='MALE_ADULT'),   1,  1, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('NOF', 'Noise Far', (SELECT id from speaker_types where code_name='NA'), 0,  2, 0, 1, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('NON', 'Noise Near', (SELECT id from speaker_types where code_name='NA'), 0,  1, 0, 1, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('OLF', 'Overlapping Vocals Far', (SELECT id from speaker_types where code_name='NA'), 0,  2, 0, 0, 1);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('OLN', 'Overlapping Vocals Near',  (SELECT id from speaker_types where code_name='NA'), 0,  1, 0, 0, 1);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('SIL', 'Silence', (SELECT id from speaker_types where code_name='SILENCE'), 0,  0, 0, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('TVF', 'TV/Electronic Media Far',  (SELECT id from speaker_types where code_name='NA'), 0,  2, 1, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('TVN', 'TV/Electronic Media Near', (SELECT id from speaker_types where code_name='NA'), 0,  1, 1, 0, 0);
INSERT INTO speaker_codes (code, display_desc, speaker_type_id, is_linkable, distance, is_media, is_nonverbal_noise, is_overlapping) VALUES ('FUZ', 'Uncertain/Fuzzy', (SELECT id from speaker_types where code_name='NA'), 0,  0, 0, 0, 0);


-- combo groups table --
CREATE TABLE combo_groups
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT UNIQUE NOT NULL
);
INSERT INTO combo_groups (code_name) VALUES ('RELIABILITY_CATEGORIES');
INSERT INTO combo_groups (code_name) VALUES ('DISTANCES');
INSERT INTO combo_groups (code_name) VALUES ('SPEAKER_TYPES');
INSERT INTO combo_groups (code_name) VALUES ('SPEAKER_CODES');
INSERT INTO combo_groups (code_name) VALUES ('SEG_FILTER_TYPES');
INSERT INTO combo_groups (code_name) VALUES ('SEG_FILTER_TIME');

-- combo options table --
CREATE TABLE combo_options
(id INTEGER PRIMARY KEY AUTOINCREMENT,
code_name TEXT NOT NULL,
combo_group_id INTEGER NOT NULL,
disp_desc TEST NOT NULL,
hidden INTEGER NOT NULL DEFAULT 0,
FOREIGN KEY(combo_group_id) REFERENCES combo_groups(id) ON DELETE CASCADE
);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'SILENCE', 'Silence', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'OVERLAPPING_SPEECH', 'Overlapping Speech', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'MEDIA', 'TV/Electronic', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'TARGET_CHILD', 'Target Child', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'OTHER_CHILD', 'Other Child', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'FEMALE_ADULT', 'Female Adult', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'MALE_ADULT', 'Male Adult', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'DISTANT', 'Distant', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'NON_VERBAL_NOISE', 'Non-Verbal Noise', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='RELIABILITY_CATEGORIES'), 'FUZ', 'Fuzz', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='DISTANCES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='DISTANCES'), 'NEAR', 'Near', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='DISTANCES'), 'FAR', 'Far', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SPEAKER_TYPES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SPEAKER_TYPES'), 'TARGET_CHILD', 'Target Child', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SPEAKER_TYPES'), 'OTHER_CHILD', 'Other Child', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SPEAKER_TYPES'), 'FEMALE_ADULT', 'Female Adult', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SPEAKER_TYPES'), 'MALE_ADULT', 'Male Adult', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TYPES'), 'EMPTY',  '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TYPES'), 'SPEAKER', 'Speaker', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TYPES'), 'TIME', 'Time', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TIME'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TIME'), 'START_TIME_BEFORE', 'Starts Before', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TIME'), 'START_TIME_AFTER', 'Starts After', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TIME'), 'END_TIME_BEFORE', 'Ends Before', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups where code_name='SEG_FILTER_TIME'), 'END_TIME_AFTER', 'Ends After', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SPEAKER_CODES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) SELECT cg.id, sc.code, sc.code, zeros.hidden FROM (SELECT id from combo_groups WHERE code_name='SPEAKER_CODES') cg LEFT JOIN speaker_codes sc LEFT JOIN (SELECT 0 as hidden) as zeros;
