-- Modifier la colonne 'week' pour qu'elle puisse être nulle
ALTER TABLE matches_euro ALTER COLUMN week DROP NOT NULL;
