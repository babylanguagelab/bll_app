INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES
('R', 4, (SELECT id FROM speaker_types WHERE code_name='NA'), 'Reading');

INSERT INTO transcriber_codes (code, trans_index, speaker_type_id, display_desc) VALUES
('S', 4, (SELECT id FROM speaker_types WHERE code_name='NA'), 'Singing');