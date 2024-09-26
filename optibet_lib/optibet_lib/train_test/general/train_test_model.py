from train_test.split import train_test_split_expanding_windows
from train_test.metrics import accuracy_fn, recall_fn, precision_fn, f_mesure_fn, log_loss_fn, mse_loss_fn, classwise_ECE_fn
import numpy as np
import numbers
import pandas as pd

def train_test(matchs, pipeline, X_col, Y_col, 
    train_test_split_fn = lambda df : train_test_split_expanding_windows(df, split=5, test_prop=0.2, date_col="date"), 
    result_df_all_split=False, m=10, beta=1,
    keys = ["accuracy", "weighted_accuracy", "accuracy_home", "accuracy_draw", "accuracy_away",
            "macro_avg_recall", "micro_avg_recall", "weighted_recall", "recall_home", "recall_draw", "recall_away",
            "macro_avg_precision", "micro_avg_precision", "weighted_precision", "precision_home", "precision_draw", "precision_away",
            "macro_avg_f_mesure", "micro_avg_f_mesure", "weighted_f_mesure", "f_mesure_home", "f_mesure_draw", "f_mesure_away",
            "log_loss", "loss_home", "loss_draw", "loss_away",
            "mse", "mse_home", "mse_draw", "mse_away",
            "classwise_ECE", "ECE_home", "ECE_draw", "ECE_away", "home_ECE_y", "draw_ECE_y", "away_ECE_y", "home_ECE_p", "draw_ECE_p", "away_ECE_p", "home_ECE_size", "draw_ECE_size", "away_ECE_size"],
    result_col_name = 'FTR',
    model_predictions_col_name = 'model_predictions',
    model_predictions_prob_home_col_name = 'model_predictions_prob_home',
    model_predictions_prob_draw_col_name = 'model_predictions_prob_draw',
    model_predictions_prob_away_col_name = 'model_predictions_prob_away'):
    """
    Train and test the model on the dataset

    Parameters
    ----------
    matchs : pd.DataFrame
        The dataset containing the matchs
    pipeline : sklearn.pipeline.Pipeline
        The pipeline to train
    X_col : list of str
        The columns to use as input
    Y_col : str
        The column to predict
    train_test_split_fn : function, optional
        The function to split the dataset. The default is train_test_split_expanding_windows.
    result_df_all_split : bool, optional
        If True, return the result DataFrame for all splits. The default is False.
    m : int, optional
        The number of sub-intervals for the ECE. The default is 10.
    beta : float, optional
        The beta parameter for the f_mesure. The default is 1.
    Returns
    -------
    metrics_mean : dict
        The mean of the metrics
    metrics : dict
        The metrics for each split
    result_df_all_splits : list of pd.DataFrame
        The result DataFrame for all splits if result_df_all_split is True else []
    """

    train_test_split = train_test_split_fn(matchs)

    metrics = {key: [0 for _ in range(len(train_test_split))] for key in keys}

    result_df_all_splits = []

    for i, (train, test) in enumerate(train_test_split):
        X_train = train[X_col]
        Y_train = train[Y_col]
        X_test = test[X_col]

        pipeline.fit(X_train, Y_train.values.ravel())
        predictions = pipeline.predict(X_test)
        prob_predictions = pipeline.predict_proba(X_test)

        result_df = test.copy()
        ###
        result_df.loc[:, model_predictions_col_name] = predictions
        result_df.loc[:, model_predictions_prob_home_col_name] = prob_predictions[:, 2]
        result_df.loc[:, model_predictions_prob_draw_col_name] = prob_predictions[:, 1]
        result_df.loc[:, model_predictions_prob_away_col_name] = prob_predictions[:, 0]

        # accuracy, weighted_accuracy, (accuracy_home, accuracy_draw, accuracy_away)
        # macro_avg_recall, micro_avg_recall, weighted_recall, (recall_home, recall_draw, recall_away)
        # macro_avg_recall, micro_avg_recall, weighted_recall, (recall_home, recall_draw, recall_away)
        # macro_avg_f_mesure, micro_avg_f_mesure, weighted_f_mesure, (f_mesure_home, f_mesure_draw, f_mesure_away)
        # log_loss, (loss_home, loss_draw, loss_away)
        # mse, (mse_home, mse_draw, mse_away)
        # classwise_ECE, (ECE_home, ECE_draw, ECE_away), (home_ECE_y, draw_ECE_y, away_ECE_y), (home_ECE_p, draw_ECE_p, away_ECE_p), (home_ECE_size, draw_ECE_size, away_ECE_size)

        metrics["accuracy"][i], metrics["weighted_accuracy"][i], (metrics["accuracy_home"][i], metrics["accuracy_draw"][i], metrics["accuracy_away"][i]) = accuracy_fn(result_df, result_col_name, model_predictions_col_name)
        metrics["macro_avg_recall"][i], metrics["micro_avg_recall"][i], metrics["weighted_recall"][i], (metrics["recall_home"][i], metrics["recall_draw"][i], metrics["recall_away"][i]) = recall_fn(result_df, result_col_name, model_predictions_col_name)
        metrics["macro_avg_precision"][i], metrics["micro_avg_precision"][i], metrics["weighted_precision"][i], (metrics["precision_home"][i], metrics["precision_draw"][i], metrics["precision_away"][i]) = precision_fn(result_df, result_col_name, model_predictions_col_name)
        metrics["macro_avg_f_mesure"][i], metrics["micro_avg_f_mesure"][i], metrics["weighted_f_mesure"][i], (metrics["f_mesure_home"][i], metrics["f_mesure_draw"][i], metrics["f_mesure_away"][i]) = f_mesure_fn(result_df, result_col_name, model_predictions_col_name, beta=beta)
        metrics["log_loss"][i], (metrics["loss_home"][i], metrics["loss_draw"][i], metrics["loss_away"][i]) = log_loss_fn(result_df[result_col_name], result_df[model_predictions_prob_home_col_name], result_df[model_predictions_prob_draw_col_name], result_df[model_predictions_prob_away_col_name], all_results=True)
        metrics["mse"][i], (metrics["mse_home"][i], metrics["mse_draw"][i], metrics["mse_away"][i]) = mse_loss_fn(result_df[result_col_name], result_df[model_predictions_prob_home_col_name], result_df[model_predictions_prob_draw_col_name], result_df[model_predictions_prob_away_col_name], all_results=True)
        metrics["classwise_ECE"][i], (metrics["ECE_home"][i], metrics["ECE_draw"][i], metrics["ECE_away"][i]), (metrics["home_ECE_y"][i], metrics["draw_ECE_y"][i], metrics["away_ECE_y"][i]), (metrics["home_ECE_p"][i], metrics["draw_ECE_p"][i], metrics["away_ECE_p"][i]), (metrics["home_ECE_size"][i], metrics["draw_ECE_size"][i], metrics["away_ECE_size"][i]) = classwise_ECE_fn(result_df[result_col_name], result_df[model_predictions_prob_home_col_name], result_df[model_predictions_prob_draw_col_name], result_df[model_predictions_prob_away_col_name], all_results=True, m=m)

        metrics_mean = {key: np.mean(value) for key, value in metrics.items() if isinstance(value[0], numbers.Real)}
         
    if result_df_all_split:
        result_df_all_splits.append(result_df)

    return metrics_mean, metrics, result_df_all_splits
