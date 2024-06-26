from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd

def test_model_and_infer(fbref_results_df__sofifa_merged__data_formated__signals_added__train, 
                         fbref_results_df__sofifa_merged__data_formated__signals_added__infer):

    Y_col_home = 'home_g'
    Y_col_away = 'away_g'

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

    X_col = X_col_sofifa + X_col_scores

    # Define the pipeline
    pipeline_home = Pipeline([
            ('scaler', StandardScaler()),
            ('model', LinearRegression())
        ])

    pipeline_away = Pipeline([
            ('scaler', StandardScaler()),
            ('model', LinearRegression())
        ])

    # Fit the models
    pipeline_home.fit(fbref_results_df__sofifa_merged__data_formated__signals_added__train[X_col], 
                      fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col_home])
    pipeline_away.fit(fbref_results_df__sofifa_merged__data_formated__signals_added__train[X_col], 
                      fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col_away])

    # Predict goals
    fbref_results_df__sofifa_merged__data_formated__signals_added__train['pred_home_goals'] = pipeline_home.predict(
        fbref_results_df__sofifa_merged__data_formated__signals_added__train[X_col])
    fbref_results_df__sofifa_merged__data_formated__signals_added__train['pred_away_goals'] = pipeline_away.predict(
        fbref_results_df__sofifa_merged__data_formated__signals_added__train[X_col])

    # Calculate metrics
    mse_home = mean_squared_error(fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col_home], 
                                  fbref_results_df__sofifa_merged__data_formated__signals_added__train['pred_home_goals'])
    mse_away = mean_squared_error(fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col_away], 
                                  fbref_results_df__sofifa_merged__data_formated__signals_added__train['pred_away_goals'])
    r2_home = r2_score(fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col_home], 
                       fbref_results_df__sofifa_merged__data_formated__signals_added__train['pred_home_goals'])
    r2_away = r2_score(fbref_results_df__sofifa_merged__data_formated__signals_added__train[Y_col_away], 
                       fbref_results_df__sofifa_merged__data_formated__signals_added__train['pred_away_goals'])

    # Display metrics
    metrics_train_set = pd.DataFrame({
        'metrics': ['mse_home', 'mse_away', 'r2_home', 'r2_away'],
        'values': [mse_home, mse_away, r2_home, r2_away]
    })

    fbref_results_df__sofifa_merged__data_formated__signals_added__infer["pred_home_goals"] = pipeline_home.predict(
        fbref_results_df__sofifa_merged__data_formated__signals_added__infer[X_col])
    fbref_results_df__sofifa_merged__data_formated__signals_added__infer["pred_away_goals"] = pipeline_away.predict(
        fbref_results_df__sofifa_merged__data_formated__signals_added__infer[X_col])

    return metrics_train_set, fbref_results_df__sofifa_merged__data_formated__signals_added__infer
