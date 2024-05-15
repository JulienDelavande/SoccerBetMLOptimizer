"""
Accuracy on the outcome of the match

$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$

$\text{Accuracy}_i = \frac{TP_i + TN_i}{TP + TN + FP + FN}$

$\text{Weighted accuracy}_i = \sum_{i=1}^{n_{\text{classes}}} \omega_i \times \text{Accuracy}_i$ with $\omega_i$, the ratio of class $i$
"""


def accuracy_fn(df, result_col_name, class_predicted_col_name):
    """
    Calculate the accuracy of the model

    $\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$

    $\text{Accuracy}_i = \frac{TP_i + TN_i}{TP + TN + FP + FN}$

    $\text{Weighted accuracy}_i = \sum_{i=1}^{n_{\text{classes}}} \omega_i \times \text{Accuracy}_i$ with $\omega_i$, the ratio of class $i$

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
    accuracy : float
        The accuracy of the model
    weighted_accuracy : float
        The weighted accuracy of the model
    class_accuracies : tuple(float, float, float)
        The accuracies of the model for each class (accuracy_home, accuracy_draw, accuracy_away)
    """

    result_col = df[result_col_name]
    class_predicted_col = df[class_predicted_col_name]

    correct_predictions = df[result_col == class_predicted_col].shape[0]
    number_of_predictions = df.shape[0]
    accuracy = correct_predictions / number_of_predictions

    tp_home = df[(result_col == 1) & (class_predicted_col == 1)].shape[0]
    tn_home = df[(result_col != 1) & (class_predicted_col != 1)].shape[0]
    accuracy_home = (tp_home + tn_home) / number_of_predictions
    freq_home = df[result_col == 1].shape[0] / number_of_predictions

    tp_draw = df[(result_col == 0) & (class_predicted_col == 0)].shape[0]
    tn_draw = df[(result_col != 0) & (class_predicted_col != 0)].shape[0]
    accuracy_draw = (tp_draw + tn_draw) / number_of_predictions
    freq_draw = df[result_col == 0].shape[0] / number_of_predictions

    tp_away = df[(result_col == -1) & (class_predicted_col == -1)].shape[0]
    tn_away = df[(result_col != -1) & (class_predicted_col != -1)].shape[0]
    accuracy_away = (tp_away + tn_away) / number_of_predictions
    freq_away = df[result_col == -1].shape[0] / number_of_predictions

    weighted_accuracy = freq_home * accuracy_home + freq_draw * accuracy_draw + freq_away * accuracy_away
    
    return accuracy, weighted_accuracy, (accuracy_home, accuracy_draw, accuracy_away)