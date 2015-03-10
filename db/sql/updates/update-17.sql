--add reading and singing codes to stats app dropdown options
INSERT INTO combo_options
(code_name, combo_group_id, disp_desc, hidden) VALUES (
'R',
(SELECT id FROM COMBO_GROUPS where code_name = 'UTTERANCE_TYPES'),
'Reading',
0
);

INSERT INTO combo_options
(code_name, combo_group_id, disp_desc, hidden) VALUES (
'S',
(SELECT id FROM COMBO_GROUPS where code_name = 'UTTERANCE_TYPES'),
'Singing',
0
);
