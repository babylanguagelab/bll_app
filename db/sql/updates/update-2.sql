--correct silly typo from previous update script
UPDATE common_regexs SET combo_option_id=(SELECT id FROM combo_options WHERE code_name='ANY_TRANS' AND combo_group_id=(SELECT id FROM combo_groups WHERE code_name='COMMON_REGEXS')) WHERE code_name='ANY_TRANS';

--correct escape chars from previous update script
UPDATE common_regexs set regex='\b[\w\-\''\"]+\b' where code_name='ANY_WORD';
UPDATE common_regexs set regex='\b\<type word here\>\b' where code_name='SPECIFIC_WORD';
UPDATE common_regexs set regex='\bwh|\bhow\b' where code_name='WH_WORD';
UPDATE common_regexs set regex='(?:[^\n\r]+(?:[\n\r]+)?)+' where code_name='ANY_TRANS';