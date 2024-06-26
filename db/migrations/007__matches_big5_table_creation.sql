-- migrations/007__matches_big5_table_creation.sql

CREATE TABLE IF NOT EXISTS matches_big5 (
    index SERIAL PRIMARY KEY,
    game_id VARCHAR(255),
    league VARCHAR(255) NOT NULL,
    season VARCHAR(255) NOT NULL,
    game VARCHAR(255) NOT NULL,
    round VARCHAR(255),
    week INT,
    day VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    time TIME,
    home_team VARCHAR(255) NOT NULL,
    home_xg FLOAT,
    score VARCHAR(255),
    away_xg FLOAT,
    away_team VARCHAR(255) NOT NULL,
    attendance INT,
    venue VARCHAR(255),
    referee VARCHAR(255),
    match_report VARCHAR(255),
    notes VARCHAR(255),
    away_g INT,
    home_g INT,
    away_sat INT,
    home_sat INT
);