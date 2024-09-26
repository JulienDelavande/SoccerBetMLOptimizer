-- Supprimer les contraintes NOT NULL existantes
ALTER TABLE sofifa_teams_stats
    ALTER COLUMN league DROP NOT NULL,
    ALTER COLUMN team DROP NOT NULL,
    ALTER COLUMN overall DROP NOT NULL,
    ALTER COLUMN attack DROP NOT NULL,
    ALTER COLUMN midfield DROP NOT NULL,
    ALTER COLUMN defence DROP NOT NULL,
    ALTER COLUMN transfer_budget DROP NOT NULL,
    ALTER COLUMN club_worth DROP NOT NULL,
    ALTER COLUMN build_up_speed DROP NOT NULL,
    ALTER COLUMN build_up_dribbling DROP NOT NULL,
    ALTER COLUMN build_up_passing DROP NOT NULL,
    ALTER COLUMN build_up_positioning DROP NOT NULL,
    ALTER COLUMN chance_creation_crossing DROP NOT NULL,
    ALTER COLUMN chance_creation_passing DROP NOT NULL,
    ALTER COLUMN chance_creation_shooting DROP NOT NULL,
    ALTER COLUMN chance_creation_positioning DROP NOT NULL,
    ALTER COLUMN defence_aggression DROP NOT NULL,
    ALTER COLUMN defence_pressure DROP NOT NULL,
    ALTER COLUMN defence_team_width DROP NOT NULL,
    ALTER COLUMN defence_defender_line DROP NOT NULL,
    ALTER COLUMN defence_domestic_prestige DROP NOT NULL,
    ALTER COLUMN international_prestige DROP NOT NULL,
    ALTER COLUMN players DROP NOT NULL,
    ALTER COLUMN starting_xi_average_age DROP NOT NULL,
    ALTER COLUMN whole_team_average_age DROP NOT NULL,
    ALTER COLUMN fifa_edition DROP NOT NULL,
    ALTER COLUMN update DROP NOT NULL;

-- Ajouter la nouvelle colonne datetime_insert
ALTER TABLE sofifa_teams_stats
    ADD COLUMN datetime_insert TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
