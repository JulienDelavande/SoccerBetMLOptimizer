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
    
    tp_home = df[(result_col == 1) & (class_predicted_col == 1)].shape[0]
    fn_home = df[(result_col == 1) & (class_predicted_col != 1)].shape[0]
    recall_home = tp_home / (tp_home + fn_home) if tp_home + fn_home != 0 else 0

    tp_draw = df[(result_col == 0) & (class_predicted_col == 0)].shape[0]
    fn_draw = df[(result_col == 0) & (class_predicted_col != 0)].shape[0]
    recall_draw = tp_draw / (tp_draw + fn_draw) if tp_draw + fn_draw != 0 else 0

    tp_away = df[(result_col == -1) & (class_predicted_col == -1)].shape[0] 
    fn_away = df[(result_col == -1) & (class_predicted_col != -1)].shape[0]
    recall_away = tp_away / (tp_away + fn_away) if tp_away + fn_away != 0 else 0

    freq_home = df[result_col == 1].shape[0] / df.shape[0]
    freq_draw = df[result_col == 0].shape[0] / df.shape[0]
    freq_away = df[result_col == -1].shape[0] / df.shape[0]

    micro_avg_recall = (tp_home + tp_draw + tp_away) / (tp_home + tp_draw + tp_away + fn_home + fn_draw + fn_away)
    macro_avg_recall = (recall_home + recall_draw + recall_away) / 3 # Also known as balanced accuracy
    weighted_recall = freq_home * recall_home + freq_draw * recall_draw + freq_away * recall_away

    return macro_avg_recall, micro_avg_recall, weighted_recall, (recall_home, recall_draw, recall_away)

