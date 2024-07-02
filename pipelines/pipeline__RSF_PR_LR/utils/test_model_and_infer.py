from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from train_test.general import train_test
from train_test.split import train_test_split_expanding_windows
import pandas as pd

def test_model_and_infer(fbref_results_df__sofifa_merged__data_formated__signals_added__train, fbref_results_df__sofifa_merged__data_formated__signals_added__infer):
    pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', LogisticRegression())
        ])
    
    X_col_sofifa =  ['home_overall', 'home_attack', 
            'home_midfield', 'home_defence', 'home_transfer_budget', 'home_club_worth', 'home_defence_domestic_prestige', 'home_international_prestige', 
            'home_players', 'home_starting_xi_average_age', 'home_whole_team_average_age', 'away_overall', 'away_attack', 'away_midfield', 'away_defence', 
            'away_transfer_budget', 'away_club_worth', 'away_defence_domestic_prestige', 'away_international_prestige', 'away_players', 
            'away_starting_xi_average_age', 'away_whole_team_average_age']

    X_col_scores = [
        'home_team_number_of_match_played', 'away_team_number_of_match_played',
        'glicko2_home_before', 'glicko2_away_before', 'glicko2_rd_home_before',
        'glicko2_rd_away_before', 'glicko2_vol_home_before',
        'glicko2_vol_away_before', 'trueskill_home_before',
        'trueskill_away_before']

    Y_col = 'FTR'

    X_col = X_col_sofifa + X_col_scores

    train_test_split_fn = lambda df : train_test_split_expanding_windows(df, split=5, test_prop=0.2, date_col="date")
    result_df_all_splits = False
    m = 10
    beta = 1
    metrics_mean, metrics, _ = train_test(fbref_results_df__sofifa_merged__data_formated__signals_added__train, pipeline, X_col, Y_col, train_test_split_fn, result_df_all_splits, m, beta)
    train_test_metrics = pd.DataFrame({'metrics': metrics_mean.keys(), 'values': metrics_mean.values()})

    pipeline.fit(fbref_results_df__sofifa_merged__data_formated__signals_added__train[X_col], fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col])
    fbref_results_df__sofifa_merged__data_formated__signals_added__infer = fbref_results_df__sofifa_merged__data_formated__signals_added__infer.copy()
    fbref_results_df__sofifa_merged__data_formated__signals_added__infer.loc[:, 'pred'] = pipeline.predict(fbref_results_df__sofifa_merged__data_formated__signals_added__infer[X_col])
    fbref_results_df__sofifa_merged__data_formated__signals_added__infer.loc[:, 'prob_home_win'] = pipeline.predict_proba(fbref_results_df__sofifa_merged__data_formated__signals_added__infer[X_col])[:, 2]
    fbref_results_df__sofifa_merged__data_formated__signals_added__infer.loc[:, 'prob_draw'] = pipeline.predict_proba(fbref_results_df__sofifa_merged__data_formated__signals_added__infer[X_col])[:, 1]
    fbref_results_df__sofifa_merged__data_formated__signals_added__infer.loc[:, 'prob_away_win'] = pipeline.predict_proba(fbref_results_df__sofifa_merged__data_formated__signals_added__infer[X_col])[:, 0]

    return train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infer
