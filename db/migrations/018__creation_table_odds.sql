CREATE TABLE odds (
    match_id VARCHAR(50),
    sport_key VARCHAR(100),
    sport_title VARCHAR(100),
    commence_time TIMESTAMP,
    home_team VARCHAR(100),
    away_team VARCHAR(100),
    bookmaker_key VARCHAR(50),
    bookmaker_title VARCHAR(100),
    bookmaker_last_update TIMESTAMP,
    market_key VARCHAR(50),
    market_last_update TIMESTAMP,
    outcome_name VARCHAR(100),
    outcome_price DECIMAL(10, 2),
    PRIMARY KEY (match_id, bookmaker_key, market_key, outcome_name, market_last_update)
);
