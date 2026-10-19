from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from optibet_lib.train_test.general import train_test
from optibet_lib.train_test.split import train_test_split_expanding_windows
import pandas as pd

# Team-strength features computed from FBref results only (SoFIFA dropped: blocked since 2025-11).
FEATURES = [
    'elo_home_before', 'elo_away_before', 'elo_diff_before',
    'glicko2_home_before', 'glicko2_away_before',
    'glicko2_rd_home_before', 'glicko2_rd_away_before',
    'glicko2_vol_home_before', 'glicko2_vol_away_before',
    'trueskill_home_before', 'trueskill_away_before',
    'home_team_number_of_match_played', 'away_team_number_of_match_played',
    'home_form_ppg', 'away_form_ppg', 'home_form_gd', 'away_form_gd',
    'home_xg_for', 'home_xg_against', 'away_xg_for', 'away_xg_against', 'xg_diff_form',
    'home_rest_days', 'away_rest_days',
]


def make_model():
    """Gradient boosting on team-strength features (research/models.py candidate `hgb_xg_rest`).

    Walk-forward 2024-08..2026-10: log loss 0.9783 vs 0.9819 for the previous logistic regression.
    Missing xG/rest values (no history yet) are imputed with the training median.
    """
    return Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('model', HistGradientBoostingClassifier(max_iter=300, learning_rate=0.04, max_leaf_nodes=15,
                                                 min_samples_leaf=80, l2_regularization=1.0, random_state=0)),
    ])

def test_model_and_infer(fbref_results_df__sofifa_merged__data_formated__signals_added__train, fbref_results_df__sofifa_merged__data_formated__signals_added__infer):
    pipeline = make_model()
    
    Y_col = 'FTR'
    X_col = FEATURES

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
