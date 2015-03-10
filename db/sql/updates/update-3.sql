--alter combo option code names for transcriber code combo-options, to make naming convention (name option after code) consistent with speaker code combo options. This helps with code in util/filters_frame.py. As code names are never stored in the DB (only combo_option ids), this should have no effect on saved stuff.
UPDATE combo_options SET code_name='M' WHERE code_name='MALE_ADULT' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='SPEAKER_TYPES');
UPDATE combo_options SET code_name='F' WHERE code_name='FEMALE_ADULT' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='SPEAKER_TYPES');
UPDATE combo_options SET code_name='T' WHERE code_name='TARGET_CHILD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='SPEAKER_TYPES');
UPDATE combo_options SET code_name='O' WHERE code_name='OTHER_CHILD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='SPEAKER_TYPES');
UPDATE combo_options SET code_name='C' WHERE code_name='CHILD_UNCERTAIN' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='SPEAKER_TYPES');
UPDATE combo_options SET code_name='U' WHERE code_name='UNCERTAIN' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='SPEAKER_TYPES');

UPDATE combo_options SET code_name='T' WHERE code_name='TARGET_CHILD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='TARGET_LISTENERS');
UPDATE combo_options SET code_name='O' WHERE code_name='OTHER_CHILD' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='TARGET_LISTENERS');
UPDATE combo_options SET code_name='C' WHERE code_name='CHILD_UNCERTAIN' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='TARGET_LISTENERS');
UPDATE combo_options SET code_name='A' WHERE code_name='ADULT' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='TARGET_LISTENERS');
UPDATE combo_options SET code_name='U' WHERE code_name='UNCERTAIN' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='TARGET_LISTENERS');

UPDATE combo_options SET code_name='F' WHERE code_name='COMPLETE' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='GRAMMATICALITY');
UPDATE combo_options SET code_name='D' WHERE code_name='DISFLUENCY' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='GRAMMATICALITY');
UPDATE combo_options SET code_name='M' WHERE code_name='MISPRONUNCIATION' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='GRAMMATICALITY');
UPDATE combo_options SET code_name='I' WHERE code_name='CONTINUED' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='GRAMMATICALITY');
UPDATE combo_options SET code_name='C' WHERE code_name='CONTINUATION' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='GRAMMATICALITY');
UPDATE combo_options SET code_name='U' WHERE code_name='UNCERTAIN' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='GRAMMATICALITY');

UPDATE combo_options SET code_name='Q' WHERE code_name='QUESTION' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='UTTERANCE_TYPES');
UPDATE combo_options SET code_name='D' WHERE code_name='DECLARATIVE' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='UTTERANCE_TYPES');
UPDATE combo_options SET code_name='I' WHERE code_name='IMPERATIVE' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='UTTERANCE_TYPES');
UPDATE combo_options SET code_name='U' WHERE code_name='UNCERTAIN' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='UTTERANCE_TYPES');
