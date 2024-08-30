from feature_eng.team_stats import goal_stats, elo_scores, glicko2_scores, trueskill_scores

def add_signals(fbref_df_date_filtered_concat_no_nan, 
                home_team_id_col='home_team', away_team_id_col='away_team',
                home_team_goal_col='home_g', away_team_goal_col='away_g',
                date_stop=None, date_col='date'):
    """
    Add the signals to the dataset.
    - Elo scores
    - Goal stats
    - Glicko-2 scores
    - Trueskill scores

    Parameters
    ----------
    fbref_df_date_filtered_concat_no_nan : pd.DataFrame
        The dataset containing the fbref data.
    home_team_id_col : str (Optional, default='home_team')
        The column name of the home team id.
    away_team_id_col : str (Optional, default='away_team')
        The column name of the away team id.
    home_team_goal_col : str (Optional, default='home_g')
        The column name of the home team goal.
    away_team_goal_col : str (Optional, default='away_g')
        The column name of the away team goal.
    date_stop : datetime (Optional)
        The date to stop the analysis.
    date_col : str (Optional, default='date')
        The column name of the date.

    Returns
    -------
    fbref_df_date_filtered_concat_no_nan : pd.DataFrame
        The dataset with the signals.
    """
    
    elo_scores(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
               home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, date_stop=date_stop, date_col=date_col)
    goal_stats(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
               home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, date_stop=date_stop, date_col=date_col)
    glicko2_scores(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
                   home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, date_stop=date_stop, date_col=date_col)
    trueskill_scores(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
                     home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, date_stop=date_stop, date_col=date_col)
    
    return fbref_df_date_filtered_concat_no_nan