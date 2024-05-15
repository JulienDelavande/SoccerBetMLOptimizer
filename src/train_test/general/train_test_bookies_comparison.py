from train_test.general.train_test_model import train_test
from train_test.split import train_test_split_expanding_windows
from train_test.metrics import accuracy_fn, recall_fn, precision_fn, f_mesure_fn, log_loss_fn, mse_loss_fn, classwise_ECE_fn
import numpy as np
import numbers

NO_RESULTS = -2


def train_test_bookies_comparison(matchs, pipeline, X_cols, Y_col, 
    train_test_split_fn = lambda df : train_test_split_expanding_windows(df, split=5, test_prop=0.2, date_col="date"),
    bookies=['B365', 'BW', 'IW', 'LB', 'PS', 'WH', 'SJ', 'VC', 'GB', 'BS']):

    keys = ["accuracy", "weighted_accuracy", "accuracy_home", "accuracy_draw", "accuracy_away",
            "recall_all", "weighted_recall", "balanced_accuracy", "recall_home", "recall_draw", "recall_away",
            "precision_all", "weighted_precision", "precision_home", "precision_draw", "precision_away",
            "f_mesure_all", "f_mesure_weighted", "f_mesure_home", "f_mesure_draw", "f_mesure_away",
            "log_loss", "loss_home", "loss_draw", "loss_away",
            "mse", "mse_home", "mse_draw", "mse_away",
            "classwise_ECE", "ECE_home", "ECE_draw", "ECE_away", "home_ECE_y", "draw_ECE_y", "away_ECE_y", "home_ECE_p", "draw_ECE_p", "away_ECE_p", "home_ECE_size", "draw_ECE_size", "away_ECE_size"]
    
    result_col_name = 'FTR'
    bookie_pred_col_name = lambda bookie : f'{bookie}_prediction'
    bookie_prob_home_col_name = lambda bookie : f'{bookie}H_prob'
    bookie_prob_draw_col_name = lambda bookie : f'{bookie}D_prob'
    bookie_prob_away_col_name = lambda bookie : f'{bookie}A_prob'

    metrics_bookies = {}

    for bookie in bookies:

        matchs_bookie = matchs[matchs[f"{bookie}_prediction"] != NO_RESULTS]

        metrics_bookies[bookie] = {}

        for (name, X_col) in X_cols:
            metrics_bookies[bookie][f"model_mean_{name}"], metrics_bookies[bookie][f"model_{name}"], _ = train_test(matchs_bookie, pipeline, X_col, Y_col, train_test_split_fn=train_test_split_fn)
            

        train_test_split = train_test_split_fn(matchs_bookie)
        metrics_bookie = {key: [0 for _ in range(len(train_test_split))] for key in keys}
        
        for i, (_, test) in enumerate(train_test_split):

            metrics_bookie["accuracy"][i], metrics_bookie["weighted_accuracy"][i], (metrics_bookie["accuracy_home"][i], metrics_bookie["accuracy_draw"][i], metrics_bookie["accuracy_away"][i]) = accuracy_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["recall_all"][i], metrics_bookie["weighted_recall"][i], metrics_bookie["balanced_accuracy"][i], (metrics_bookie["recall_home"][i], metrics_bookie["recall_draw"][i], metrics_bookie["recall_away"][i]) = recall_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["precision_all"][i], metrics_bookie["weighted_precision"][i], (metrics_bookie["precision_home"][i], metrics_bookie["precision_draw"][i], metrics_bookie["precision_away"][i]) = precision_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["f_mesure_all"][i], metrics_bookie["f_mesure_weighted"][i], (metrics_bookie["f_mesure_home"][i], metrics_bookie["f_mesure_draw"][i], metrics_bookie["f_mesure_away"][i]) = f_mesure_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["log_loss"][i], (metrics_bookie["loss_home"][i], metrics_bookie["loss_draw"][i], metrics_bookie["loss_away"][i]) = log_loss_fn(test[result_col_name], test[bookie_prob_home_col_name(bookie)], test[bookie_prob_draw_col_name(bookie)], test[bookie_prob_away_col_name(bookie)], all_results=True)
            metrics_bookie["mse"][i], (metrics_bookie["mse_home"][i], metrics_bookie["mse_draw"][i], metrics_bookie["mse_away"][i]) = mse_loss_fn(test[result_col_name], test[bookie_prob_home_col_name(bookie)], test[bookie_prob_draw_col_name(bookie)], test[bookie_prob_away_col_name(bookie)], all_results=True)
            metrics_bookie["classwise_ECE"][i], (metrics_bookie["ECE_home"][i], metrics_bookie["ECE_draw"][i], metrics_bookie["ECE_away"][i]), (metrics_bookie["home_ECE_y"][i], metrics_bookie["draw_ECE_y"][i], metrics_bookie["away_ECE_y"][i]), (metrics_bookie["home_ECE_p"][i], metrics_bookie["draw_ECE_p"][i], metrics_bookie["away_ECE_p"][i]), (metrics_bookie["home_ECE_size"][i], metrics_bookie["draw_ECE_size"][i], metrics_bookie["away_ECE_size"][i]) = classwise_ECE_fn(test[result_col_name], test[bookie_prob_home_col_name(bookie)], test[bookie_prob_draw_col_name(bookie)], test[bookie_prob_away_col_name(bookie)], all_results=True)

        metrics_bookies[bookie]["bookie_mean"] = {key: np.mean(metrics_bookie[key]) for key in keys if isinstance(metrics_bookie[key][0], numbers.Real)}
        metrics_bookies[bookie]["bookie"] = metrics_bookie

    metrics_bookies["all_df"] = {}
    for (name, X_col) in X_cols:
        metrics_bookies["all_df"][f"model_mean_{name}"], metrics_bookies[bookie][f"model_{name}"], _ = train_test(matchs_bookie, pipeline, X_col, Y_col, train_test_split_fn=train_test_split_fn)

    return metrics_bookies

bookies = ['B365', 'BW', 'IW', 'LB', 'PS', 'WH', 'SJ', 'VC', 'GB', 'BS']


def bookie_prediction(row, bookies):
    """
    Return 1 if the home team is the winner according to the bookie, 0 if it's a draw, -1 if the away team is the winner and -2 if the bookie is not able to predict the winner
    """
    if row[f'{bookies}H'] < row[f'{bookies}D'] and row[f'{bookies}H'] < row[f'{bookies}A']:
        return 1
    elif row[f'{bookies}D'] < row[f'{bookies}H'] and row[f'{bookies}D'] < row[f'{bookies}A']:
        return 0
    elif row[f'{bookies}A'] < row[f'{bookies}H'] and row[f'{bookies}A'] < row[f'{bookies}D']:
        return -1
    else:
        return -2


def prob_by_bookies(row, bookie):
    if np.isnan(row[f'{bookie}H']) or np.isnan(row[f'{bookie}D']) or np.isnan(row[f'{bookie}A']):
        (np.nan, np.nan, np.nan)
    margin = 1/row[f'{bookie}H'] + 1/row[f'{bookie}D'] + 1/row[f'{bookie}A'] - 1
    return 1 / row[f'{bookie}H'] - margin/3, 1 / row[f'{bookie}D'] - margin/3, 1 / row[f'{bookie}A'] - margin/3



if __name__ == "__main__":
    
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    import sqlite3
    import pandas as pd
    import os

    # Retrieval pf the matchs dataset
    python_script_path = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = f'{python_script_path}/../../../data/soccer/European_Soccer_Database/database.sqlite'
    conn = sqlite3.connect(DATA_PATH)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    matchs = pd.read_sql("SELECT * FROM Match", conn)

    # Features enginnering (minimun col to add to be able to test the prediction of the bookmakers)
    matchs['FTR'] = matchs.apply(lambda x: 1 if x['home_team_goal'] > x['away_team_goal'] else 0 if x['home_team_goal'] == x['away_team_goal'] else -1, axis=1)
    bookies = ['B365', 'BW', 'IW', 'LB', 'PS', 'WH', 'SJ', 'VC', 'GB', 'BS']
    for bookie in bookies:
        matchs[f'{bookie}_prediction'] = matchs.apply(lambda x: bookie_prediction(x, bookie), axis=1)
    for bookie in bookies:
        matchs[f'{bookie}H_prob'], matchs[f'{bookie}D_prob'], matchs[f'{bookie}A_prob'] = zip(*matchs.apply(lambda x: prob_by_bookies(x, bookie), axis=1))

    # Replacing missing odd by the mean of the other bookies
    for bookie in bookies:
        matchs[f'{bookie}H'] = matchs[f'{bookie}H'].fillna(matchs[f'{bookie}H'].mean())
        matchs[f'{bookie}D'] = matchs[f'{bookie}D'].fillna(matchs[f'{bookie}D'].mean())
        matchs[f'{bookie}A'] = matchs[f'{bookie}A'].fillna(matchs[f'{bookie}A'].mean())

    # Pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', LogisticRegression())
    ])

    # Feature selection
    X_cols = [("all", ["B365H", "B365D", "B365A", "BWH", "BWD", "BWA", "IWH", "IWD", "IWA", "LBH", "LBD", "LBA", "PSH", "PSD", "PSA", "WHH", "WHD", "WHA", "SJH", "SJD", "SJA", "VCH", "VCD", "VCA", "GBH", "GBD", "GBA", "BSH", "BSD", "BSA"])]
    Y_col = "FTR"

    # Test of the function
    metrics_bookies = train_test_bookies_comparison(matchs, pipeline, X_cols, Y_col)

    df = pd.DataFrame.from_dict({(i,j): metrics_bookies[i][j] 
                           for i in metrics_bookies.keys() 
                           for j in metrics_bookies[i].keys()},
                           orient='index')

    # Réinitialisez l'index du DataFrame
    df.reset_index(inplace=True)

    # Renommez les colonnes
    df.columns = ['Bookmaker', 'Metric', 'Value']

    # Transformez le DataFrame en un format long
    df_melted = df.melt(id_vars=['Bookmaker', 'Metric'], var_name='X_col', value_name='Value')

    # Affichez le DataFrame
    print(df_melted)