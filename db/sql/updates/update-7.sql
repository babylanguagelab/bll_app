--VOID code from file splitter - if split files are processed, the apps should ignore this speaker
--(Split files were originally never intended to be processed)
INSERT INTO speaker_codes (
code,
speaker_type_id,
display_desc,
distance,
is_linkable,
is_media,
is_nonverbal_noise,
is_overlapping
) VALUES (
'VOID',
(SELECT id FROM speaker_types WHERE code_name='NA'),
'Void',
0, --indicates that distance is NA
0, --not linkable
0, --not media
0, --not nonverbal noise
0 --not overlapping
);