-- Ajouter la nouvelle colonne datetime_insert
ALTER TABLE soccer_odds
    ADD COLUMN datetime_insert TIMESTAMP DEFAULT CURRENT_TIMESTAMP;