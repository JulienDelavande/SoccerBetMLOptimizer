-- Matches used by the Elo pipeline: every aliased FBref match since 2006, no SoFIFA
-- dependency. Applied after mv_match_enrichis.sql (its DROP ... CASCADE removes this view).
DROP VIEW IF EXISTS v_matches_fbref;

CREATE VIEW v_matches_fbref AS
SELECT
  m.*,
  th.canonical_name AS home_team_canonical_name,
  ta.canonical_name AS away_team_canonical_name
FROM mv_fbref_matches_norm_2006 m
JOIN teams th ON th.team_id = m.home_team_id
JOIN teams ta ON ta.team_id = m.away_team_id
ORDER BY m.match_ts, m.game;
