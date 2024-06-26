-- Modifier le type des colonnes prob_home_team_score et prob_away_team_score de models_results
ALTER TABLE models_results ALTER COLUMN prob_home_team_score TYPE FLOAT;
ALTER TABLE models_results ALTER COLUMN prob_away_team_score TYPE FLOAT;