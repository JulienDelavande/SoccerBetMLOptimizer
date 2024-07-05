"""
Recall by class on Home, Draw, Away

$\text{Recall all} = \frac{TP}{TP + FN}$

$\text{Recall}_i = \text{TPR}_i =  \frac{TP_i}{TP_i + FN_i}$ with $i$ the class

$\text{Weighted recall}_i = \sum_{i=1}^{n} \omega_i \times \text{Recall}_i$ with $\omega_i = \frac{TP_i + FN_i}{\sum_{i=1}^{n} TP_i + FN_i}$ (The distribution of class $i$)

$\text{Balanced accuracy} = \frac{1}{n}\sum_{i=1}^{n} \frac{TP_i}{TP_i + FN_i}$
"""

def recall_fn(df, result_col_name, class_predicted_col_name):
    """
    Recall on the outcome of the match

    $\text{Recall all} = \frac{TP}{TP + FN}$

    $\text{Recall}_i = \text{TPR}_i =  \frac{TP_i}{TP_i + FN_i}$ with $i$ the class

    $\text{Weighted recall}_i = \sum_{i=1}^{n} \omega_i \times \text{Recall}_i$ with $\omega_i = \frac{TP_i + FN_i}{\sum_{i=1}^{n} TP_i + FN_i}$ (The distribution of class $i$)

    $\text{Balanced accuracy} = \frac{1}{n}\sum_{i=1}^{n} \frac{TP_i}{TP_i + FN_i}$

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
    recall_all : float
        The recall of the model
    weighted_recall : float
        The weighted recall of the model
    balanced_accuracy : float
        The balanced accuracy of the model
    class_recalls : tuple(float, float, float)
        The recalls of the model for each class (recall_home, recall_draw, recall_away)
    """
    result_col = df[result_col_name]
    class_predicted_col = df[class_predicted_col_name]
    
    correct_predictions_home_win = df[(result_col == 1) & (class_predicted_col == 1)].shape[0]
    number_of_home_win = df[result_col == 1].shape[0]
    recall_home = correct_predictions_home_win / number_of_home_win if number_of_home_win != 0 else 0 

    correct_predictions_draw = df[(result_col == 0) & (class_predicted_col == 0)].shape[0]
    number_of_draw = df[result_col == 0].shape[0]
    recall_draw = correct_predictions_draw / number_of_draw if number_of_draw != 0 else 0

    correct_predictions_away_win = df[(result_col == -1) & (class_predicted_col == -1)].shape[0] 
    number_of_away_win = df[result_col == -1].shape[0]
    recall_away = correct_predictions_away_win / number_of_away_win if number_of_away_win != 0 else 0

    freq_home_win = df[result_col == 1].shape[0] / df.shape[0]
    freq_draw = df[result_col == 0].shape[0] / df.shape[0]
    freq_away_win = df[result_col == -1].shape[0] / df.shape[0]

    recall_all = recall_home + recall_draw + recall_away
    weighted_recall = freq_home_win * recall_home + freq_draw * recall_draw + freq_away_win * recall_away
    balanced_accuracy = (recall_home + recall_draw + recall_away) / 3

    return recall_all, weighted_recall, balanced_accuracy, (recall_home, recall_draw, recall_away)

