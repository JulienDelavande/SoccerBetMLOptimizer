def train_test_split_expanding_windows(df, split=5, test_prop=0.2, date_col="date"):
    """
    Split the dataset into training and testing set using expanding windows.

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
    train_size = int(df.shape[0] / (split + test_prop))
    test_size = int(train_size * test_prop)

    df = df.sort_values(by=date_col, ascending=False)

    for i in range(split):
        train = df.iloc[:train_size*(i+1)]
        test = df.iloc[train_size*(i+1):train_size*(i+1) + test_size]
        train_test_split.append((train, test))

    return train_test_split
