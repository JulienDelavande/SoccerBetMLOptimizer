DELETE FROM sofifa_teams_stats
WHERE team = 'Paris Saint-Germain'
  AND update IN (
    SELECT update
    FROM sofifa_teams_stats
    WHERE team = 'Paris Saint Germain'
  );

UPDATE sofifa_teams_stats
SET team = 'Paris Saint-Germain'
WHERE team = 'Paris Saint Germain';
