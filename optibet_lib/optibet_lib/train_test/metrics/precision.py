"""
Precision by class on Home, Draw, Away

$\text{Precision}_i = \frac{TP_i}{TP_i + FP_i}$ for each class $i$

$\text{Precision all} = \frac{1}{n} \sum_{i=1}^{n} \text{Precision}_i$ $n$ beeing the number of classes

$\text{Weighted precision} = \sum_{i=1}^{n} \omega_i \times \text{Precision}_i$ with $\omega_i$ the ratio of the class
"""

def precision_fn(df, result_col_name, class_predicted_col_name):
    """
    Precision by class on Home, Draw, Away

    $\text{Precision}_i = \frac{TP_i}{TP_i + FP_i}$ for each class $i$

    $\text{Precision all} = \frac{1}{n} \sum_{i=1}^{n} \text{Precision}_i$ $n$ beeing the number of classes - Macro-averaged Precision

    $\text{Weighted precision} = \sum_{i=1}^{n} \omega_i \times \text{Precision}_i$ with $\omega_i$ the ratio of the class - Weighted Precision

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the data
    result_col_name : str
        The column name containing the actual result
    class_predicted_col_name : str
        The column name containing the predicted result
    
    Returns
    -------
    macro_avg_precision : float
        The precision of the model - Macro-averaged Precision
    weighted_precision : float
        The weighted precision of the model - Weighted Precision
    class_precisions : tuple(float, float, float)
        The precisions of the model for each class (precision_home, precision_draw, precision_away)
    """
    result_col = df[result_col_name]
    class_predicted_col = df[class_predicted_col_name]

    tp_home = df[(result_col == 1) & (class_predicted_col == 1)].shape[0]
    fp_home = df[(result_col != 1) & (class_predicted_col == 1)].shape[0]
    freq_home = df[result_col == 1].shape[0] / df.shape[0]
    precision_home = tp_home / (tp_home + fp_home) if tp_home + fp_home != 0 else 0

    tp_draw = df[(result_col == 0) & (class_predicted_col == 0)].shape[0]
    fp_draw = df[(result_col != 0) & (class_predicted_col == 0)].shape[0]
    freq_draw = df[result_col == 0].shape[0] / df.shape[0]
    precision_draw = tp_draw / (tp_draw + fp_draw) if tp_draw + fp_draw != 0 else 0

    tp_away = df[(result_col == -1) & (class_predicted_col == -1)].shape[0]
    fp_away = df[(result_col != -1) & (class_predicted_col == -1)].shape[0]
    freq_away = df[result_col == -1].shape[0] / df.shape[0]
    precision_away = tp_away / (tp_away + fp_away) if tp_away + fp_away != 0 else 0

    macro_avg_precision = (precision_home + precision_draw + precision_away)/3
    micro_avg_precision = (tp_home + tp_draw + tp_away) / (tp_home + tp_draw + tp_away + fp_home + fp_draw + fp_away)
    weighted_precision = freq_home * precision_home + freq_draw * precision_draw + freq_away * precision_away
    
    return macro_avg_precision, micro_avg_precision, weighted_precision, (precision_home, precision_draw, precision_away)