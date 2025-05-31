UPDATE fbref_results
SET datetime_update = NULL
WHERE score IS NULL;
