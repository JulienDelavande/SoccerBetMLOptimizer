-- Renommer trois colonnes
ALTER TABLE optim_results
    RENAME COLUMN f_home_kelly TO f_home;

ALTER TABLE optim_results
    RENAME COLUMN f_draw_kelly TO f_draw;

ALTER TABLE optim_results
    RENAME COLUMN f_away_kelly TO f_away;

-- Ajouter une nouvelle colonne avec une valeur par défaut 'Kelly'
ALTER TABLE optim_results
    ADD COLUMN utility_fn VARCHAR(255) DEFAULT 'Kelly';

ALTER TABLE optim_results
    ADD COLUMN odds_home_datetime TIMESTAMP DEFAULT NULL;

ALTER TABLE optim_results
    ADD COLUMN odds_draw_datetime TIMESTAMP DEFAULT NULL;

ALTER TABLE optim_results
    ADD COLUMN odds_away_datetime TIMESTAMP DEFAULT NULL;
