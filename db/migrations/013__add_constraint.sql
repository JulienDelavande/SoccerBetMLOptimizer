ALTER TABLE sofifa_teams_stats
ADD CONSTRAINT unique_team_update UNIQUE (team, update);
