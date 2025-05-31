-- Ajouter la nouvelle colonne datetime_insert
ALTER TABLE fbref_results
    ADD COLUMN datetime_insert TIMESTAMP DEFAULT CURRENT_TIMESTAMP;