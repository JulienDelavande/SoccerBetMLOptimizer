DROP MATERIALIZED VIEW IF EXISTS mv_models_results_last_inferred CASCADE;

CREATE MATERIALIZED VIEW mv_models_results_last_inferred AS
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY game ORDER BY datetime_inference DESC) AS rk
  FROM models_results
) sub
WHERE rk = 1;

CREATE INDEX idx_mv_models_results_last_inferred_game ON mv_models_results_last_inferred (game);
CREATE INDEX idx_mv_models_results_last_inferred_date_match ON mv_models_results_last_inferred (date_match);

DROP MATERIALIZED VIEW IF EXISTS mv_soccer_odds_normalized CASCADE;

CREATE MATERIALIZED VIEW mv_soccer_odds_normalized AS
SELECT
  o.*,
  tah.team_id AS home_team_id,
  tahn.canonical_name AS home_team_canonical,
  taa.team_id AS away_team_id,
  taan.canonical_name AS away_team_canonical
FROM soccer_odds o
JOIN team_alias tah ON tah.source = 'theoddsapi' AND tah.raw_name = o.home_team
JOIN team_alias taa ON taa.source = 'theoddsapi' AND taa.raw_name = o.away_team
JOIN teams tahn ON tah.team_id = tahn.team_id
JOIN teams taan ON taa.team_id = taan.team_id;

-- Index utiles
CREATE INDEX idx_soccer_odds_norm_match_outcome ON mv_soccer_odds_normalized(match_id, bookmaker_key, outcome_name);
CREATE INDEX idx_soccer_odds_norm_team_date ON mv_soccer_odds_normalized(home_team_canonical, away_team_canonical, commence_time);

DROP MATERIALIZED VIEW IF EXISTS mv_soccer_odds_last_normalized CASCADE;

CREATE MATERIALIZED VIEW mv_soccer_odds_last_normalized AS
SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
             PARTITION BY match_id, bookmaker_key, outcome_name
             ORDER BY bookmaker_last_update DESC
           ) AS rk
    FROM mv_soccer_odds_normalized
) sub
WHERE rk = 1;

-- Index utile
CREATE INDEX idx_soccer_odds_last_norm_match ON mv_soccer_odds_last_normalized(match_id);

DROP MATERIALIZED VIEW IF EXISTS mv_models_results_last_inferred CASCADE;

CREATE MATERIALIZED VIEW mv_models_results_last_inferred AS
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY game ORDER BY datetime_inference DESC) AS rk
  FROM models_results
) sub
WHERE rk = 1;

CREATE INDEX idx_models_results_last_inferred_game ON mv_models_results_last_inferred(game);
