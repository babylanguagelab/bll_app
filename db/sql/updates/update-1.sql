INSERT INTO combo_groups (code_name) VALUES ('OUTPUT_CALC_TYPES');

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='OUTPUT_CALC_TYPES'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='OUTPUT_CALC_TYPES'), 'COUNT', 'Count', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='OUTPUT_CALC_TYPES'), 'RATE', 'Rate', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='OUTPUT_CALC_TYPES'), 'TIME_PERIOD', 'Time Period', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='OUTPUT_CALC_TYPES'), 'BREAKDOWN', 'Breakdown', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='OUTPUT_CALC_TYPES'), 'LIST', 'List', 0);

INSERT INTO combo_groups (code_name) VALUES ('LIST_OUTPUT_CALC_CATS');

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='LIST_OUTPUT_CALC_CATS'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='LIST_OUTPUT_CALC_CATS'), 'SPEAKER_TYPE', 'Speaker Type', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='LIST_OUTPUT_CALC_CATS'), 'TARGET_LISTENER', 'Target Listener', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='LIST_OUTPUT_CALC_CATS'), 'COMPLETENESS', 'Grammaticality/Completeness', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='LIST_OUTPUT_CALC_CATS'), 'UTTERANCE_TYPE', 'Utterance Type', 0);

ALTER TABLE outputs ADD COLUMN chained INTEGER NOT NULL DEFAULT 0;

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SEG_FILTER_TYPES'), 'SPEAKER_TYPE', 'Speaker Type', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SEG_FILTER_TYPES'), 'TARGET_LISTENER', 'Target Listener', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SEG_FILTER_TYPES'), 'GRAMMATICALITY', 'Grammaticality/Completeness', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SEG_FILTER_TYPES'), 'UTTERANCE_TYPE', 'Utterance Type', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SEG_FILTER_TYPES'), 'OVERLAPPING_VOCALS', 'Overlapping Vocals', 0);

UPDATE combo_options SET disp_desc='Speaker Code' WHERE code_name='SPEAKER'; --to distinguish from the new SPEAKER_TYPE option inserted above. SPEAKER TYPE is transcriber code 1 (eg. 'M', 'F'), while SPEAKER is the speaker code itself (seg. 'FAN', 'MAN')

--additional transcriber codes combos
INSERT INTO combo_groups (code_name) VALUES ('TARGET_LISTENERS');
INSERT INTO combo_groups (code_name) VALUES ('GRAMMATICALITY');
INSERT INTO combo_groups (code_name) VALUES ('UTTERANCE_TYPES');

--insert missing values into SPEAKER_TYPES group
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SPEAKER_TYPES'), 'CHILD_UNCERTAIN', 'Child Uncertain', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='SPEAKER_TYPES'), 'UNCERTAIN', 'Uncertain', 0);
--correct mistake in description text
UPDATE transcriber_codes SET display_desc='Target Child' WHERE code='T' and trans_index=1;

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='TARGET_LISTENERS'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='TARGET_LISTENERS'), 'TARGET_CHILD', 'Target Child', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='TARGET_LISTENERS'), 'OTHER_CHILD', 'Other Child', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='TARGET_LISTENERS'), 'CHILD_UNCERTAIN', 'Child Uncertain', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='TARGET_LISTENERS'), 'ADULT', 'Adult', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='TARGET_LISTENERS'), 'UNCERTAIN', 'Uncertain', 0);

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'EMPTY', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'COMPLETE', 'Complete', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'DISFLUENCY', 'Disfluency', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'MISPRONUNCIATION', 'Mispronunciation', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'CONTINUATION', 'Continuation', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'CONTINUED', 'Continued', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='GRAMMATICALITY'), 'UNCERTAIN', 'Uncertain', 0);

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='UTTERANCE_TYPES'), 'Empty', '', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='UTTERANCE_TYPES'), 'QUESTION', 'Question', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='UTTERANCE_TYPES'), 'DECLARATIVE', 'Declarative', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='UTTERANCE_TYPES'), 'IMPERATIVE', 'Imperative', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='UTTERANCE_TYPES'), 'UNCERTAIN', 'Uncertain', 0);

CREATE TABLE common_regexs
(id INTEGER PRIMARY KEY AUTOINCREMENT,
combo_option_id INTEGER NOT NULL,
code_name TEXT UNIQUE NOT NULL,
regex TEXT NOT NULL,
FOREIGN KEY(combo_option_id) REFERENCES combo_options(id) ON DELETE CASCADE
);

INSERT INTO COMBO_GROUPS (code_name) VALUES ('COMMON_REGEXS');

INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COMMON_REGEXS'), 'EMPTY', 'Custom Pattern:', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COMMON_REGEXS'), 'ANY_WORD', 'Any Word', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COMMON_REGEXS'), 'SPECIFIC_WORD', 'Specific Word', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COMMON_REGEXS'), 'WH_WORD', 'WH Word', 0);
INSERT INTO combo_options (combo_group_id, code_name, disp_desc, hidden) VALUES ((SELECT id from combo_groups WHERE code_name='COMMON_REGEXS'), 'ANY_TRANS', 'Any Transcription', 0);

INSERT INTO common_regexs (combo_option_id, code_name, regex) VALUES ((SELECT id FROM combo_options WHERE code_name='ANY_WORD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='COMMON_REGEXS')), 'ANY_WORD', '\\b[\\w\\-\\''\\"]+\\b');
INSERT INTO common_regexs (combo_option_id, code_name, regex) VALUES ((SELECT id FROM combo_options WHERE code_name='SPECIFIC_WORD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='COMMON_REGEXS')), 'SPECIFIC_WORD', '\\b\\<type word here\\>\\b');
INSERT INTO common_regexs (combo_option_id, code_name, regex) VALUES ((SELECT id FROM combo_options WHERE code_name='WH_WORD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='COMMON_REGEXS')), 'WH_WORD', '\\bwh|\\bhow\\b');
INSERT INTO common_regexs (combo_option_id, code_name, regex) VALUES ((SELECT id FROM combo_options WHERE code_name='EMPTY' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='COMMON_REGEXS')), 'EMPTY', '');
INSERT INTO common_regexs (combo_option_id, code_name, regex) VALUES ((SELECT id FROM combo_options WHERE code_name='EMPTY' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='COMMON_REGEXS')), 'ANY_TRANS', '(?:[^\\n\\r]+(?:[\\n\\r]+)?)+');
