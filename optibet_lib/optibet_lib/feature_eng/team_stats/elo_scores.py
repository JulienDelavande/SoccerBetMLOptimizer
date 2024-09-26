import pandas as pd

def elo_scores(df, BASE_RATING=1500., K=25, HOME_ADVANTAGE=100, C=0, date_stop=None,
                home_team_id_col='home_team_api_id', away_team_id_col='away_team_api_id',
                home_team_goal_col='home_team_goal', away_team_goal_col='away_team_goal',
                elo_home_before_col='elo_home_before', elo_away_before_col='elo_away_before',
                date_col='date'):
    """
    Calculate the Elo ratings of the teams in the dataset and add two new columns to the DataFrame containing the Elo ratings of the home and away teams before the match.

    ELO_{i+1} = ELO_i + K * G (actual_i - expected_i)
    ELO_{0} = BASE_RATING
    K : scaling parameter concerning the impact of more recent events
    G : goal difference factor
    actual_i : 1 for win, 0.5 for draw, 0 for loss
    expected_i : expected result of the match ]0, 1[ E_i = 1 / (1 + 10^((R_j - R_i - HOME_ADVANTAGE) / 400 - C))

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the data
    BASE_RATING : float (Optional, default=1500.)
        The base rating of the teams
    K : float (Optional, default=25)
        The K factor
    HOME_ADVANTAGE : float (Optional, default=100)
        The home advantage
    C : float (Optional, default=0)
        The constant

    Returns
    -------
    None
    """
    teams = pd.concat([df[home_team_id_col], df[away_team_id_col]]).unique()
    ratings = {team: BASE_RATING for team in teams}
    
    df[elo_home_before_col] = 0.
    df[elo_away_before_col] = 0.
    
    for index, row in df.iterrows():
        home_team = row[home_team_id_col]
        away_team = row[away_team_id_col]
        
        # Ajouter les scores Elo avant le match
        df.at[index, elo_home_before_col] = ratings[home_team]
        df.at[index, elo_away_before_col] = ratings[away_team]
        
        # Calculer le score attendu
        expected_home = 1 / (1 + 10 ** (((ratings[away_team] - ratings[home_team] - HOME_ADVANTAGE) / 400) - C))
        expected_away = 1 / (1 + 10 ** ((-(ratings[away_team] - ratings[home_team] - HOME_ADVANTAGE) / 400) - C))

        is_match_played = (not pd.isna(row[home_team_goal_col]) and not pd.isna(row[away_team_goal_col])) 
        is_date_passed = (date_stop is not None and row[date_col] > date_stop)
        if not is_match_played or is_date_passed:
            continue
        
        # Résultats réels (1 pour victoire, 0.5 pour nul, 0 pour défaite)
        if row[home_team_goal_col] > row[away_team_goal_col]:
            actual_home = 1
            actual_away = 0
        elif row[home_team_goal_col] < row[away_team_goal_col]:
            actual_home = 0
            actual_away = 1
        else:
            actual_home = 0.5
            actual_away = 0.5

        # G
        G = 0
        goal_diff = abs(row[home_team_goal_col] - row[away_team_goal_col])
        if goal_diff in [0, 1] :
            G = 1
        elif goal_diff == 2:
            G = 1.5
        else:
            G = (11 + goal_diff)/8

        
        # Mettre à jour les scores Elo
        ratings[home_team] += K * G * (actual_home - expected_home)
        ratings[away_team] += K * G * (actual_away - expected_away)