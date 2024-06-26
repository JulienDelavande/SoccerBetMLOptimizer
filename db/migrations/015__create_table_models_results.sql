CREATE TABLE models_results (
    datetime_inference TIMESTAMP NOT NULL,
    model VARCHAR(255) NOT NULL,
    game_id VARCHAR(255),
    game VARCHAR(255) NOT NULL,
    date_match DATE NOT NULL,
    time_match TIME,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    prob_home_win FLOAT,
    prob_draw FLOAT,
    prob_away_win FLOAT,
    prob_home_team_score INT,
    prob_away_team_score INT,
    UNIQUE (datetime_inference, model, game)
);
