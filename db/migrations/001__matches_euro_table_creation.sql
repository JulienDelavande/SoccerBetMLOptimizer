-- migrations/001_create_matches_euro_table.sql

CREATE TABLE IF NOT EXISTS matches_euro (
    game_id SERIAL PRIMARY KEY,
    league VARCHAR(255) NOT NULL,
    season VARCHAR(255) NOT NULL,
    game VARCHAR(255) NOT NULL,
    round VARCHAR(255),
    week INT NOT NULL,
    day VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    home_xg FLOAT,
    score VARCHAR(255),
    away_xg FLOAT,
    away_team VARCHAR(255) NOT NULL,
    attendance INT,
    venue VARCHAR(255),
    referee VARCHAR(255),
    match_report VARCHAR(255),
    notes VARCHAR(255)
);