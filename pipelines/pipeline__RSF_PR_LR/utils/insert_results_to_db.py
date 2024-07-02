import datetime

def insert_results_to_db(engine, results_df, DB_TN_MODELS_RESULTS):

    results_df.loc[:, "date_match"] = results_df["date"]
    results_df.loc[:, "time_match"] = results_df["time"]
    results_df = results_df[['game', 'game_id', 'date_match', 'time_match', 'home_team', 'away_team', 'prob_home_win', 'prob_draw', 'prob_away_win']].copy()
    results_df.loc[:, 'datetime_inference'] = datetime.datetime.now()
    
    results_df.loc[:, 'model'] = 'RSF_PR_LR' # Ranking  + SoFifa features -- Probability on the results -- Logistic Regression
    results_df.loc[:, 'prob_home_team_score'] = None
    results_df.loc[:, 'prob_away_team_score'] = None

    with engine.begin() as connection:  # Using begin() to manage transactions
        results_df.to_sql(DB_TN_MODELS_RESULTS, connection, if_exists='append', index=False)
        