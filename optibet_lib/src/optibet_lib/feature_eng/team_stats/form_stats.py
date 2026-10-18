from collections import defaultdict, deque

import pandas as pd


def form_stats(df, window=5, datetime_stop=None,
               home_team_id_col='home_team', away_team_id_col='away_team',
               home_team_goal_col='home_g', away_team_goal_col='away_g',
               datetime_col='datetime'):
    """
    Add each team's recent form before the match, over its last `window` played matches.

    Columns added (NaN-free, 0 when a team has no history yet):
    - home_form_ppg / away_form_ppg: points per game (win 3, draw 1)
    - home_form_gd / away_form_gd: average goal difference per game

    Rows must be in chronological order. Matches not played yet, or after
    datetime_stop, get the current form but do not update it.
    """
    points = defaultdict(lambda: deque(maxlen=window))
    goal_diffs = defaultdict(lambda: deque(maxlen=window))

    def mean(values):
        return sum(values) / len(values) if values else 0.

    home_ppg, away_ppg, home_gd, away_gd = [], [], [], []
    for row in df.itertuples(index=False):
        home = getattr(row, home_team_id_col)
        away = getattr(row, away_team_id_col)
        home_ppg.append(mean(points[home]))
        away_ppg.append(mean(points[away]))
        home_gd.append(mean(goal_diffs[home]))
        away_gd.append(mean(goal_diffs[away]))

        home_goals = getattr(row, home_team_goal_col)
        away_goals = getattr(row, away_team_goal_col)
        is_match_played = not pd.isna(home_goals) and not pd.isna(away_goals)
        is_date_passed = datetime_stop is not None and getattr(row, datetime_col) > datetime_stop
        if not is_match_played or is_date_passed:
            continue

        diff = home_goals - away_goals
        points[home].append(3 if diff > 0 else 1 if diff == 0 else 0)
        points[away].append(3 if diff < 0 else 1 if diff == 0 else 0)
        goal_diffs[home].append(diff)
        goal_diffs[away].append(-diff)

    df['home_form_ppg'] = home_ppg
    df['away_form_ppg'] = away_ppg
    df['home_form_gd'] = home_gd
    df['away_form_gd'] = away_gd
