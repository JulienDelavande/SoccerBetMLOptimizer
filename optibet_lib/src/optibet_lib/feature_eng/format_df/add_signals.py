import pandas as pd
from optibet_lib.feature_eng.team_stats import goal_stats, elo_scores, glicko2_scores, trueskill_scores, form_stats

def add_signals(fbref_df_date_filtered_concat_no_nan, 
                home_team_id_col='home_team', away_team_id_col='away_team',
                home_team_goal_col='home_g', away_team_goal_col='away_g',
                datetime_stop=None, datetime_col='datetime', 
                X_cat=(),
                ):
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
    datetime_stop : datetime (Optional)
        The date to stop the analysis.
    date_col : str (Optional, default='date')
        The column name of the date.

    Returns
    -------
    fbref_df_date_filtered_concat_no_nan : pd.DataFrame
        The dataset with the signals.
    """
    
    # Ratings are sequential: process matches in chronological order (the SQL view has none).
    fbref_df_date_filtered_concat_no_nan = fbref_df_date_filtered_concat_no_nan.sort_values(datetime_col, kind='stable').copy()

    elo_scores(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
               home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, datetime_stop=datetime_stop, datetime_col=datetime_col)
    fbref_df_date_filtered_concat_no_nan['elo_diff_before'] = (
        fbref_df_date_filtered_concat_no_nan['elo_home_before'] - fbref_df_date_filtered_concat_no_nan['elo_away_before']
    )
    goal_stats(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
               home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, datetime_stop=datetime_stop, datetime_col=datetime_col)
    glicko2_scores(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
                   home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, datetime_stop=datetime_stop, datetime_col=datetime_col)
    trueskill_scores(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col, 
                     home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, datetime_stop=datetime_stop, datetime_col=datetime_col)
    form_stats(fbref_df_date_filtered_concat_no_nan, home_team_id_col=home_team_id_col, away_team_id_col=away_team_id_col,
               home_team_goal_col=home_team_goal_col, away_team_goal_col=away_team_goal_col, datetime_stop=datetime_stop, datetime_col=datetime_col)
    if not X_cat:
        return fbref_df_date_filtered_concat_no_nan
    df_cat_onehot = pd.get_dummies(fbref_df_date_filtered_concat_no_nan[list(X_cat)], drop_first=True)
    df_all = pd.concat([fbref_df_date_filtered_concat_no_nan, df_cat_onehot], axis=1)
    
    return df_all
