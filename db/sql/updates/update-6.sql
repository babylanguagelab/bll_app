UPDATE speaker_codes SET is_linkable=1 WHERE code='TVF' OR code='TVN';
ALTER TABLE tests ADD COLUMN is_uncertain INTEGER DEFAULT 0;