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

    $\text{Precision all} = \frac{1}{n} \sum_{i=1}^{n} \text{Precision}_i$ $n$ beeing the number of classes

    $\text{Weighted precision} = \sum_{i=1}^{n} \omega_i \times \text{Precision}_i$ with $\omega_i$ the ratio of the class

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
    precision_all : float
        The precision of the model
    weighted_precision : float
        The weighted precision of the model
    class_precisions : tuple(float, float, float)
        The precisions of the model for each class (precision_home, precision_draw, precision_away)
    """
    result_col = df[result_col_name]
    class_predicted_col = df[class_predicted_col_name
    ]
    correct_predictions_home_win = df[(result_col == 1) & (class_predicted_col == 1)].shape[0]
    number_of_home_win_predictions = df[class_predicted_col == 1].shape[0]
    freq_home_win = df[result_col == 1].shape[0] / df.shape[0]
    precision_home = correct_predictions_home_win / number_of_home_win_predictions if number_of_home_win_predictions != 0 else 0

    correct_predictions_draw = df[(result_col == 0) & (class_predicted_col == 0)].shape[0]
    number_of_draw_predictions = df[class_predicted_col == 0].shape[0]
    freq_draw = df[result_col == 0].shape[0] / df.shape[0]
    precision_draw = correct_predictions_draw / number_of_draw_predictions if number_of_draw_predictions != 0 else 0

    correct_predictions_away_win = df[(result_col == -1) & (class_predicted_col == -1)].shape[0]
    number_of_away_win_predictions = df[class_predicted_col == -1].shape[0]
    freq_away_win = df[result_col == -1].shape[0] / df.shape[0]
    precision_away = correct_predictions_away_win / number_of_away_win_predictions if number_of_away_win_predictions != 0 else 0

    precision_all = (precision_home + precision_draw + precision_away)/3
    weighted_precision = freq_home_win * precision_home + freq_draw * precision_draw + freq_away_win * precision_away

    return precision_all, weighted_precision, (precision_home, precision_draw, precision_away)