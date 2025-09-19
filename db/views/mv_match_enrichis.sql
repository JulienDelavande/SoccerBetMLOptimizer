-- Nettoyage des anciennes MVs si existantes
DROP MATERIALIZED VIEW IF EXISTS mv_fbref_matches_norm CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_fbref_matches_norm_2006 CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_sofifa_stats_norm CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_sofifa_team_ids CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_fbref_matches_filtered CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_sofifa_stats_filtered CASCADE;
DROP VIEW IF EXISTS v_matches_enrichis CASCADE;


-- Vue normalisée des matchs FBref
CREATE MATERIALIZED VIEW mv_fbref_matches_norm AS
SELECT
  fr.*,
  tah.team_id AS home_team_id,
  taa.team_id AS away_team_id,
  (fr.date::timestamp + COALESCE(fr.time, '00:00:00'::time)) AS match_ts
FROM fbref_results fr
JOIN team_alias AS tah
  ON tah.source = 'fbref' AND tah.raw_name = fr.home_team
JOIN team_alias AS taa
  ON taa.source = 'fbref' AND taa.raw_name = fr.away_team;

CREATE INDEX ix_mv_fbref_matches_norm_home ON mv_fbref_matches_norm (home_team_id);
CREATE INDEX ix_mv_fbref_matches_norm_away ON mv_fbref_matches_norm (away_team_id);
CREATE INDEX ix_mv_fbref_matches_norm_match_ts ON mv_fbref_matches_norm (match_ts);
CREATE INDEX ix_mv_fbref_matches_norm_date ON mv_fbref_matches_norm (date);

-- Version filtrée à partir de 2006
CREATE MATERIALIZED VIEW mv_fbref_matches_norm_2006 AS
SELECT *
FROM mv_fbref_matches_norm
WHERE date >= DATE '2006-01-01';

CREATE INDEX ix_mv_fbref_matches_norm_2006_home ON mv_fbref_matches_norm_2006 (home_team_id);
CREATE INDEX ix_mv_fbref_matches_norm_2006_away ON mv_fbref_matches_norm_2006 (away_team_id);

-- Vue normalisée SoFIFA avec team_id
CREATE MATERIALIZED VIEW mv_sofifa_stats_norm AS
SELECT
  s.*,
  ta.team_id
FROM sofifa_teams_stats s
JOIN team_alias ta
  ON ta.source = 'sofifa' AND ta.raw_name = s.team;

-- Index sur team_id et update pour le tri latéral
CREATE INDEX ix_mv_sofifa_stats_norm_team_update_desc
ON mv_sofifa_stats_norm (team_id, update DESC);

-- Les team_id présents dans SoFIFA
CREATE MATERIALIZED VIEW mv_sofifa_team_ids AS
SELECT DISTINCT team_id
FROM mv_sofifa_stats_norm;

CREATE INDEX ix_mv_sofifa_team_ids ON mv_sofifa_team_ids (team_id);

-- Matches FBref avec équipes existant dans SoFIFA
CREATE MATERIALIZED VIEW mv_fbref_matches_filtered AS
SELECT m.*
FROM mv_fbref_matches_norm_2006 m
JOIN mv_sofifa_team_ids s1 ON s1.team_id = m.home_team_id
JOIN mv_sofifa_team_ids s2 ON s2.team_id = m.away_team_id;

CREATE INDEX ix_mv_fbref_matches_filtered_game ON mv_fbref_matches_filtered (game);
CREATE INDEX ix_mv_fbref_matches_filtered_match_ts ON mv_fbref_matches_filtered (match_ts);

-- Filtrage des stats SoFIFA sur les équipes réellement utilisées
CREATE MATERIALIZED VIEW mv_sofifa_stats_filtered AS
SELECT s.*
FROM mv_sofifa_stats_norm s
WHERE s.team_id IN (
  SELECT home_team_id FROM mv_fbref_matches_norm_2006
  UNION
  SELECT away_team_id FROM mv_fbref_matches_norm_2006
);

CREATE INDEX ix_mv_sofifa_stats_filtered_team_update_desc
ON mv_sofifa_stats_filtered (team_id, update DESC);


-- Vue enrichie finale
CREATE VIEW v_matches_enrichis AS
SELECT
  m.*,

  -- Canonical names
  th.canonical_name AS home_team_canonical_name,
  ta.canonical_name AS away_team_canonical_name,

  -- Colonnes home
  sh.team_id      AS home_team_id_stats,
  sh.update       AS home_update,
  sh.league       AS home_league,
  sh.overall      AS home_overall,
  sh.attack       AS home_attack,
  sh.midfield     AS home_midfield,
  sh.defence      AS home_defence,
  sh.build_up_speed AS home_build_up_speed,
  sh.build_up_dribbling AS home_build_up_dribbling,
  sh.build_up_passing AS home_build_up_passing,
  sh.build_up_positioning AS home_build_up_positioning,
  sh.chance_creation_crossing AS home_chance_creation_crossing,
  sh.chance_creation_passing AS home_chance_creation_passing,
  sh.chance_creation_shooting AS home_chance_creation_shooting,
  sh.chance_creation_positioning AS home_chance_creation_positioning,
  sh.defence_aggression AS home_defence_aggression,
  sh.defence_pressure AS home_defence_pressure,
  sh.defence_team_width AS home_defence_team_width,
  sh.defence_defender_line AS home_defence_defender_line,
  sh.transfer_budget AS home_transfer_budget,
  sh.club_worth AS home_club_worth,
  sh.defence_domestic_prestige AS home_defence_domestic_prestige,
  sh.international_prestige AS home_international_prestige,
  sh.players AS home_players,
  sh.starting_xi_average_age AS home_starting_xi_average_age,
  sh.whole_team_average_age AS home_whole_team_average_age,

  -- Colonnes away
  sa.team_id      AS away_team_id_stats,
  sa.update       AS away_update,
  sa.league       AS away_league,
  sa.overall      AS away_overall,
  sa.attack       AS away_attack,
  sa.midfield     AS away_midfield,
  sa.defence      AS away_defence,
  sa.build_up_speed AS away_build_up_speed,
  sa.build_up_dribbling AS away_build_up_dribbling,
  sa.build_up_passing AS away_build_up_passing,
  sa.build_up_positioning AS away_build_up_positioning,
  sa.chance_creation_crossing AS away_chance_creation_crossing,
  sa.chance_creation_passing AS away_chance_creation_passing,
  sa.chance_creation_shooting AS away_chance_creation_shooting,
  sa.chance_creation_positioning AS away_chance_creation_positioning,
  sa.defence_aggression AS away_defence_aggression,
  sa.defence_pressure AS away_defence_pressure,
  sa.defence_team_width AS away_defence_team_width,
  sa.defence_defender_line AS away_defence_defender_line,
  sa.transfer_budget AS away_transfer_budget,
  sa.club_worth AS away_club_worth,
  sa.defence_domestic_prestige AS away_defence_domestic_prestige,
  sa.international_prestige AS away_international_prestige,
  sa.players AS away_players,
  sa.starting_xi_average_age AS away_starting_xi_average_age,
  sa.whole_team_average_age AS away_whole_team_average_age

FROM mv_fbref_matches_filtered m
JOIN teams th ON th.team_id = m.home_team_id
JOIN teams ta ON ta.team_id = m.away_team_id
JOIN LATERAL (
  SELECT s.*
  FROM mv_sofifa_stats_filtered s
  WHERE s.team_id = m.home_team_id
    AND s.update <= m.match_ts
  ORDER BY s.update DESC
  LIMIT 1
) sh ON TRUE
JOIN LATERAL (
  SELECT s.*
  FROM mv_sofifa_stats_filtered s
  WHERE s.team_id = m.away_team_id
    AND s.update <= m.match_ts
  ORDER BY s.update DESC
  LIMIT 1
) sa ON TRUE;


-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sofifa_stats_norm;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sofifa_stats_filtered;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_fbref_matches_norm;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_fbref_matches_norm_2006;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_fbref_matches_filtered;
