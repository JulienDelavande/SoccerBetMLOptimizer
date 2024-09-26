from train_test.general.train_test_model import train_test
from train_test.split import train_test_split_expanding_windows
from train_test.metrics import accuracy_fn, recall_fn, precision_fn, f_mesure_fn, log_loss_fn, mse_loss_fn, classwise_ECE_fn
import numpy as np
import numbers
import pandas as pd

NO_RESULTS = -2
HOME_VICTORY = 1
DRAW = 0
AWAY_VICTORY = -1


def train_test_bookies_comparison(matchs, pipeline, X_cols, Y_col, 
    train_test_split_fn = lambda df : train_test_split_expanding_windows(df, split=5, test_prop=0.2, date_col="date"),
    bookies=['B365', 'BW', 'IW', 'LB', 'PS', 'WH', 'SJ', 'VC', 'GB', 'BS']):
    """
    Compare the prediction of the model and the bookies for the matchs dataset for different features set.

    Parameters
    ----------
    matchs : pd.DataFrame
        The matchs dataset.
    pipeline : sklearn.pipeline.Pipeline
        The model to evaluate.
    X_cols : list of tuple
        The features set to evaluate.
    Y_col : str
        The target column.
    train_test_split_fn : function, optional
        The function to split the dataset. The default is lambda df : train_test_split_expanding_windows(df, split=5, test_prop=0.2, date_col="date").
    bookies : list of str, optional
        The bookies to evaluate. The default is ['B365', 'BW', 'IW', 'LB', 'PS', 'WH', 'SJ', 'VC', 'GB', 'BS'].

    Returns
    -------
    dict
        The metrics of the model and the bookies for the different features set.
        { bookie : { "model_mean_all" : { metric : value }, 
                     "model_all" : { metric : [value] }, 
                     "bookie_mean" : { metric : value }, 
                     "bookie" : { metric : [value] } } 
                     }
    """

    keys = ["accuracy", "weighted_accuracy", "accuracy_home", "accuracy_draw", "accuracy_away",
            "macro_avg_recall", "micro_avg_recall", "weighted_recall", "recall_home", "recall_draw", "recall_away",
            "macro_avg_precision", "micro_avg_precision", "weighted_precision", "precision_home", "precision_draw", "precision_away",
            "macro_avg_f_mesure", "micro_avg_f_mesure", "weighted_f_mesure", "f_mesure_home", "f_mesure_draw", "f_mesure_away",
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

            # accuracy, weighted_accuracy, (accuracy_home, accuracy_draw, accuracy_away)
            # macro_avg_recall, micro_avg_recall, weighted_recall, (recall_home, recall_draw, recall_away)
            # macro_avg_precision, micro_avg_precision, weighted_precision, (precision_home, precision_draw, precision_away)
            # macro_avg_f_mesure, micro_avg_f_mesure, weighted_f_mesure, (f_mesure_home, f_mesure_draw, f_mesure_away)
            # log_loss, (loss_home, loss_draw, loss_away)
            # mse, (mse_home, mse_draw, mse_away)
            # classwise_ECE, (ECE_home, ECE_draw, ECE_away), (home_ECE_y, draw_ECE_y, away_ECE_y), (home_ECE_p, draw_ECE_p, away_ECE_p), (home_ECE_size, draw_ECE_size, away_ECE_size)

            metrics_bookie["accuracy"][i], metrics_bookie["weighted_accuracy"][i], (metrics_bookie["accuracy_home"][i], metrics_bookie["accuracy_draw"][i], metrics_bookie["accuracy_away"][i]) = accuracy_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["macro_avg_recall"][i], metrics_bookie["micro_avg_recall"][i], metrics_bookie["weighted_recall"][i], (metrics_bookie["recall_home"][i], metrics_bookie["recall_draw"][i], metrics_bookie["recall_away"][i]) = recall_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["macro_avg_precision"][i], metrics_bookie["micro_avg_precision"][i], metrics_bookie["weighted_precision"][i], (metrics_bookie["precision_home"][i], metrics_bookie["precision_draw"][i], metrics_bookie["precision_away"][i]) = precision_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["macro_avg_f_mesure"][i], metrics_bookie["micro_avg_f_mesure"][i], metrics_bookie["weighted_f_mesure"][i], (metrics_bookie["f_mesure_home"][i], metrics_bookie["f_mesure_draw"][i], metrics_bookie["f_mesure_away"][i]) = f_mesure_fn(test, result_col_name, bookie_pred_col_name(bookie))
            metrics_bookie["log_loss"][i], (metrics_bookie["loss_home"][i], metrics_bookie["loss_draw"][i], metrics_bookie["loss_away"][i]) = log_loss_fn(test[result_col_name], test[bookie_prob_home_col_name(bookie)], test[bookie_prob_draw_col_name(bookie)], test[bookie_prob_away_col_name(bookie)], all_results=True)
            metrics_bookie["mse"][i], (metrics_bookie["mse_home"][i], metrics_bookie["mse_draw"][i], metrics_bookie["mse_away"][i]) = mse_loss_fn(test[result_col_name], test[bookie_prob_home_col_name(bookie)], test[bookie_prob_draw_col_name(bookie)], test[bookie_prob_away_col_name(bookie)], all_results=True)
            metrics_bookie["classwise_ECE"][i], (metrics_bookie["ECE_home"][i], metrics_bookie["ECE_draw"][i], metrics_bookie["ECE_away"][i]), (metrics_bookie["home_ECE_y"][i], metrics_bookie["draw_ECE_y"][i], metrics_bookie["away_ECE_y"][i]), (metrics_bookie["home_ECE_p"][i], metrics_bookie["draw_ECE_p"][i], metrics_bookie["away_ECE_p"][i]), (metrics_bookie["home_ECE_size"][i], metrics_bookie["draw_ECE_size"][i], metrics_bookie["away_ECE_size"][i]) = classwise_ECE_fn(test[result_col_name], test[bookie_prob_home_col_name(bookie)], test[bookie_prob_draw_col_name(bookie)], test[bookie_prob_away_col_name(bookie)], all_results=True)

        metrics_bookies[bookie]["bookie_mean"] = {key: np.mean(metrics_bookie[key]) for key in keys if isinstance(metrics_bookie[key][0], numbers.Real)}
        metrics_bookies[bookie]["bookie"] = metrics_bookie
    
    metrics_bookies["all_df"] = {}
    for (name, X_col) in X_cols:
        metrics_bookies["all_df"][f"model_mean_{name}"], metrics_bookies["all_df"][f"model_{name}"], _ = train_test(matchs_bookie, pipeline, X_col, Y_col, train_test_split_fn=train_test_split_fn)
    metrics_bookies["all_df"][f"bookie_mean"] = {key: np.mean([metrics_bookies[bookie]["bookie_mean"][key] for bookie in bookies]) for key in keys if isinstance(metrics_bookies[bookie]["bookie"][key][0], numbers.Real)}
    
    return metrics_bookies

def display_train_test_bookies_comparison(metrics_bookies,
                                          X_cols,
                                          cols=['B365', 'BW', 'IW', 'LB', 'PS', 'WH', 'SJ', 'VC', 'GB', 'BS', "all_df"],
                                          metrics_of_interrest=["balanced_accuracy"]):
    metrics_bookies_dict = {}

    for bookie in cols:
        metrics_one_bookie_list = [metrics_bookies[bookie]["bookie_mean"][metric] for metric in metrics_of_interrest]
        for (name, _) in X_cols:
            for metric in metrics_of_interrest:
                metrics_one_bookie_list.append(metrics_bookies[bookie][f"model_mean_{name}"][metric])
        metrics_bookies_dict[bookie] = metrics_one_bookie_list

    df_display = pd.DataFrame(metrics_bookies_dict, index=metrics_of_interrest + 
    [f"{metric}_model_{name}" for (name, _) in X_cols for metric in metrics_of_interrest])

    return df_display
