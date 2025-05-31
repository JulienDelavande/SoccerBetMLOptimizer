ALTER TABLE fbref_results
    ADD COLUMN datetime_update TIMESTAMP DEFAULT NOW();
