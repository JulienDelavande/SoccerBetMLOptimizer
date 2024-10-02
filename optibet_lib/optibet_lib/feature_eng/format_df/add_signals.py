import pandas as pd
from feature_eng.team_stats import goal_stats, elo_scores, glicko2_scores, trueskill_scores

def add_signals(fbref_df_date_filtered_concat_no_nan, 
                home_team_id_col='home_team', away_team_id_col='away_team',
                home_team_goal_col='home_g', away_team_goal_col='away_g',
                date_stop=None, date_col='date', 
                X_cat=['home_league',
                    'home_build_up_speed',
                    'home_build_up_dribbling',
                    'home_build_up_passing',
                    'home_build_up_positioning',
                    'home_chance_creation_crossing',
                    'home_chance_creation_passing',
                    'home_chance_creation_shooting',
                    'home_chance_creation_positioning',
                    'home_defence_aggression',
                    'home_defence_pressure',
                    'home_defence_team_width',
                    'home_defence_defender_line',
                    'away_league',
                    'away_build_up_speed',
                    'away_build_up_dribbling',
                    'away_build_up_passing',
                    'away_build_up_positioning',
                    'away_chance_creation_crossing',
                    'away_chance_creation_passing',
                    'away_chance_creation_shooting',
                    'away_chance_creation_positioning',
                    'away_defence_aggression',
                    'away_defence_pressure',
                    'away_defence_team_width',
                    'away_defence_defender_line',]
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
    df_cat_onehot = pd.get_dummies(fbref_df_date_filtered_concat_no_nan[X_cat], drop_first=True)
    df_all = pd.concat([fbref_df_date_filtered_concat_no_nan, df_cat_onehot], axis=1)
    
    return df_all