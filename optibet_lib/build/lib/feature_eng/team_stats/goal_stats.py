import pandas as pd

def goal_stats(matchs, date_stop=None,
              home_team_id_col='home_team_api_id', away_team_id_col='away_team_api_id',
              home_team_goal_col='home_team_goal', away_team_goal_col='away_team_goal',
              season_col='season',
              home_team_goals_season_to_date_before_match_col='home_team_goals_season_to_date_before_match',
              away_team_goals_season_to_date_before_match_col='away_team_goals_season_to_date_before_match',
              home_team_number_of_match_played_col='home_team_number_of_match_played',
              away_team_number_of_match_played_col='away_team_number_of_match_played',
              avg_home_team_goals_season_to_date_before_match_col='avg_home_team_goals_season_to_date_before_match',
              avg_away_team_goals_season_to_date_before_match_col='avg_away_team_goals_season_to_date_before_match',
              date_col='date'):
    """
    Compute the goal stats for each team in each season.

    Parameters
    ----------
    matchs : pd.DataFrame
        The dataset containing the matchs.

    Returns
    -------
    None
    """
    teams = list(set(matchs[home_team_id_col].unique()).union(matchs[away_team_id_col].unique()))
    goals_by_season_team = { season: { team: 0 for team in teams } for season in matchs[season_col].unique() }
    number_of_match_played_season_team = { season: { team: 0 for team in teams } for season in matchs["season"].unique() }

    for index, row in matchs.iterrows():
        home_team = row[home_team_id_col]
        away_team = row[away_team_id_col]
        season = row[season_col]
        home_team_goals = row[home_team_goal_col]
        away_team_goals = row[away_team_goal_col]


        matchs.at[index, home_team_goals_season_to_date_before_match_col] = goals_by_season_team[season][home_team]
        matchs.at[index, away_team_goals_season_to_date_before_match_col] = goals_by_season_team[season][away_team]

        matchs.at[index, home_team_number_of_match_played_col] = number_of_match_played_season_team[season][home_team]
        matchs.at[index, away_team_number_of_match_played_col] = number_of_match_played_season_team[season][away_team]

        matchs.at[index, avg_home_team_goals_season_to_date_before_match_col] = goals_by_season_team[season][home_team] / number_of_match_played_season_team[season][home_team] if number_of_match_played_season_team[season][home_team] != 0 else 0
        matchs.at[index, avg_away_team_goals_season_to_date_before_match_col] = goals_by_season_team[season][away_team] / number_of_match_played_season_team[season][away_team] if number_of_match_played_season_team[season][away_team] != 0 else 0

        is_match_played = (not pd.isna(home_team_goals) and not pd.isna(away_team_goals))
        is_date_passed = (date_stop is not None and row[date_col] > date_stop)
        if not is_match_played or is_date_passed:
            continue
        
        number_of_match_played_season_team[season][home_team] += 1
        number_of_match_played_season_team[season][away_team] += 1

        goals_by_season_team[season][home_team] += home_team_goals
        goals_by_season_team[season][away_team] += away_team_goals