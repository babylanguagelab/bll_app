--remove erroneous lena codes (these are actually transcriber-inserted)
DELETE FROM lena_notes_codes WHERE code='xxx' or code='BBL';

--correct mistyped "is_linkable" property of OLF speaker
UPDATE speaker_codes SET is_linkable=1 WHERE code='OLF';