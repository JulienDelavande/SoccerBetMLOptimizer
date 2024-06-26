-- Supprimer la contrainte de clé primaire
ALTER TABLE matches_euro DROP CONSTRAINT matches_euro_pkey;

-- Modifier le type de la colonne game_id
ALTER TABLE matches_euro ALTER COLUMN game_id TYPE VARCHAR(255);

-- Ajouter à nouveau la contrainte de clé primaire
ALTER TABLE matches_euro ADD PRIMARY KEY (game_id);