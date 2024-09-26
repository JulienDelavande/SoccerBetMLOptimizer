"""
This module contains the implementation of the F-Mesure metric.

The F-Mesure metric is a metric that combines the precision and recall metrics into a single metric. It is defined as:

$\text{F-Mesure}_i = \frac{(1 + \beta^2) \times \text{Precision}_i \times \text{Recall}_i}{\beta^2 \times \text{Precision}_i + \text{Recall}_i}$

$\text{F-Mesure all} = \frac{1}{n} \sum_{i=1}^{n} \text{F-Mesure}_i$

$\text{Weighted F-Mesure} = \sum_{i=1}^{n} \omega_i \times \text{F-Mesure}_i$ with $\omega_i$, the ratio of class $i$
"""

from train_test.metrics import precision_fn
from train_test.metrics import recall_fn

def f_mesure_fn(df, result_col_name, class_predicted_col_name, beta=1):
    """
    Calculate the F-Mesure of the model

    $\text{F-Mesure}_i = \frac{(1 + \beta^2) \times \text{Precision}_i \times \text{Recall}_i}{\beta^2 \times \text{Precision}_i + \text{Recall}_i}$

    $\text{F-Mesure all} = \frac{1}{n} \sum_{i=1}^{n} \text{F-Mesure}_i$

    $\text{Weighted F-Mesure} = \sum_{i=1}^{n} \omega_i \times \text{F-Mesure}_i$ with $\omega_i$, the ratio of class $i$

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the data
    result_col_name : str
        The column name containing the actual result
    class_predicted_col_name : str
        The column name containing the predicted result
    beta : float
        The beta parameter of the F-Mesure

    Returns
    -------
    macro_avg_f_mesure : float
        The F-Mesure of the model
    weighted_f_mesure : float
        The weighted F-Mesure of the model
    class_f_mesure : tuple(float, float, float)
        The F-Mesure of the model for each class (f_mesure_home, f_mesure_draw, f_mesure_away)
    """
    result_col = df[result_col_name]
    class_predicted_col = df[class_predicted_col_name]

    macro_avg_precision, micro_avg_precison, weighted_precision, (precision_home, precision_draw, precision_away) = precision_fn(df, result_col_name, class_predicted_col_name)
    macro_avg_recall, micro_avg_recall, weighted_recall, (recall_home, recall_draw, recall_away) = recall_fn(df, result_col_name, class_predicted_col_name)

    tp_home = df[(result_col == 1) & (class_predicted_col == 1)].shape[0]
    fn_home = df[(result_col == 1) & (class_predicted_col != 1)].shape[0]
    fp_home = df[(result_col != 1) & (class_predicted_col == 1)].shape[0]

    tp_draw = df[(result_col == 0) & (class_predicted_col == 0)].shape[0]
    fn_draw = df[(result_col == 0) & (class_predicted_col != 0)].shape[0]
    fp_draw = df[(result_col != 0) & (class_predicted_col == 0)].shape[0]

    tp_away = df[(result_col == -1) & (class_predicted_col == -1)].shape[0]
    fn_away = df[(result_col == -1) & (class_predicted_col != -1)].shape[0]
    fp_away = df[(result_col != -1) & (class_predicted_col == -1)].shape[0]

    f_mesure_home = (1 + beta**2) * (precision_home * recall_home) / (beta**2 * precision_home + recall_home) if precision_home + recall_home != 0 else 0
    f_mesure_draw = (1 + beta**2) * (precision_draw * recall_draw) / (beta**2 * precision_draw + recall_draw) if precision_draw + recall_draw != 0 else 0
    f_mesure_away = (1 + beta**2) * (precision_away * recall_away) / (beta**2 * precision_away + recall_away) if precision_away + recall_away != 0 else 0

    freq_home_win = df[result_col== 1].shape[0] / df.shape[0]
    freq_draw = df[result_col == 0].shape[0] / df.shape[0]
    freq_away_win = df[result_col == -1].shape[0] / df.shape[0]

    macro_avg_f_mesure = (f_mesure_home + f_mesure_draw + f_mesure_away) / 3
    weighted_f_mesure = freq_home_win * f_mesure_home + freq_draw * f_mesure_draw + freq_away_win * f_mesure_away
    micro_avg_f_mesure = (1+beta**2)*(tp_home + tp_draw + tp_away) / (beta**2 * (tp_home + tp_draw + tp_away) + fn_home + fn_draw + fn_away + fp_home + fp_draw + fp_away)

    return macro_avg_f_mesure, micro_avg_f_mesure, weighted_f_mesure, (f_mesure_home, f_mesure_draw, f_mesure_away)