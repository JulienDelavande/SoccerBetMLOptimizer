-- Supprimer la contrainte de clé primaire actuelle
ALTER TABLE matches_euro DROP CONSTRAINT matches_euro_pkey;

-- Ajouter la nouvelle colonne 'index' et la définir comme clé primaire
ALTER TABLE matches_euro ADD COLUMN index SERIAL PRIMARY KEY;

-- Modifier la colonne 'game_id' pour qu'elle puisse être nulle
ALTER TABLE matches_euro ALTER COLUMN game_id DROP NOT NULL;

-- Ajouter les nouvelles colonnes 'away_g' et 'home_g'
ALTER TABLE matches_euro ADD COLUMN away_g INT;
ALTER TABLE matches_euro ADD COLUMN home_g INT;