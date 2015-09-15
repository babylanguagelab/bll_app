insert into combo_options(code_name, combo_group_id, disp_desc, hidden) values (
'WH_QUESTION_WORD',
(select id from combo_groups where code_name='COMMON_REGEXS'),
'WH Question Word',
0
);

insert into common_regexs(combo_option_id, code_name, regex) values (
(select id from combo_options where code_name='WH_QUESTION_WORD'),
'WH_QUESTION_WORD',
'\b(who|what|when|where|why|how)s?\b'
);