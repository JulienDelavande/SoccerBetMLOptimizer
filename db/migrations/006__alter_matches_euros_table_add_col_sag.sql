-- Ajouter les nouvelles colonnes 'away_sat' et 'home_sat'
ALTER TABLE matches_euro ADD COLUMN away_sat INT;
ALTER TABLE matches_euro ADD COLUMN home_sat INT;