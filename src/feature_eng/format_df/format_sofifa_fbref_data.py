import datetime

def format_sofifa_fbref_data(fbref_df_date_filtered_concat, 
                             ftr_col='FTR', home_team_goal_col='home_g', away_team_goal_col='away_g', date_col='date',
                             dropna_cols=['home_overall', 'away_overall']):
    """
    Format the fbref data by adding the full time result column and dropping rows with NaN values in the sofifa columns.
    
    Parameters
    ----------
    fbref_df_date_filtered_concat : pd.DataFrame
        The dataset containing the fbref data.
    ftr_col : str (Optional, default='FTR')
        The column name of the full time result.
    home_team_goal_col : str (Optional, default='home_g')
        The column name of the home team goal.
    away_team_goal_col : str (Optional, default='away_g')
        The column name of the away team goal.
    date_col : str (Optional, default='date')
        The column name of the date.
    dropna_cols : list of str (Optional, default=['home_overall', 'away_overall'])
        The columns to drop rows with NaN values.
        
    Returns
    -------
    fbref_df_date_filtered_concat_no_nan : pd.DataFrame
        The formatted dataset.
    """

    # Add the full time result column
    fbref_df_date_filtered_concat[ftr_col] = fbref_df_date_filtered_concat.apply(lambda x: 1 if x[home_team_goal_col] > x[away_team_goal_col] else 0 if x[home_team_goal_col] == x[away_team_goal_col] else -1 if x[home_team_goal_col] < x[away_team_goal_col] else None, axis=1)
    
    # Drop rows with NaN values in the columns of dropna_cols (sofifa cols)
    fbref_df_date_filtered_concat_no_nan = fbref_df_date_filtered_concat.dropna(subset=dropna_cols)

    # Drop rows with NaN values in the ftr_col but keep future matches
    rule_is_null = (fbref_df_date_filtered_concat_no_nan[ftr_col].isnull())
    rule_is_future_match = (fbref_df_date_filtered_concat_no_nan[date_col] >= datetime.datetime.now())
    rule_remove_nan_and_keep_future_matches = ~rule_is_null | rule_is_future_match
    fbref_df_date_filtered_concat_no_nan = fbref_df_date_filtered_concat_no_nan[rule_remove_nan_and_keep_future_matches]
    
    return fbref_df_date_filtered_concat_no_nan
