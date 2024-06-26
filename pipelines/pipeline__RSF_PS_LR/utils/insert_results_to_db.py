import datetime

def insert_results_to_db(engine, results_df, DB_TN_MODELS_RESULTS):

    results_df["date_match"] = results_df["date"]
    results_df["time_match"] = results_df["time"]
    results_df['prob_home_team_score'] = results_df['pred_home_goals']
    results_df['prob_away_team_score'] = results_df['pred_away_goals']
    results_df = results_df[['game', 'game_id', 'date_match', 'time_match', 'home_team', 'away_team', 'prob_home_team_score', 'prob_away_team_score']]
    results_df['datetime_inference'] = datetime.datetime.now()
    
    results_df['model'] = 'RSF_PS_LR' # Ranking  + SoFifa features -- Probability on the results -- Logistic Regression


    with engine.begin() as connection:  # Using begin() to manage transactions
        results_df.to_sql(DB_TN_MODELS_RESULTS, connection, if_exists='append', index=False)
        