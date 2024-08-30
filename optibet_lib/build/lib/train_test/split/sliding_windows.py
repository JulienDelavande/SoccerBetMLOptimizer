def train_test_split_sliding_windows(df, split=5, test_prop=0.2, date_col="date", df_shape_0=None):
    """ 
    Split the dataset into training and testing set using sliding windows.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to split.
    split : int, optional
        The number of split. The default is 5.
    test_prop : float, optional
        The proportion of the testing set. The default is 0.2.
    date_col : str, optional
        The column containing the date. The default is "date".

    Returns
    -------
    train_test_split : list of tuple
        The list of tuple containing the training and testing set.
    """
    train_test_split = []
    if df_shape_0 is None:
        df_shape_0 = df.shape[0]
    train_size = int(df_shape_0 / (split + test_prop))
    test_size = int(train_size * test_prop)

    df = df.sort_values(by=date_col, ascending=True)

    for i in range(split):
        train = df.iloc[i*train_size:(i+1)*train_size]
        test = df.iloc[(i+1)*train_size:(i+1)*train_size + test_size]
        train_test_split.append((train, test))

    return train_test_split