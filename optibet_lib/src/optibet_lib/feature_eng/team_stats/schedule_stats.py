from collections import defaultdict, deque

import numpy as np
import pandas as pd


def rest_days(df, home_team_id_col='home_team', away_team_id_col='away_team',
              home_team_goal_col='home_g', away_team_goal_col='away_g', datetime_col='datetime', cap=30):
    """Days since each team's previous played match (NaN if none), capped at `cap`. Rows must be chronological."""
    last = {}
    home, away = [], []
    for row in df[[home_team_id_col, away_team_id_col, home_team_goal_col, away_team_goal_col, datetime_col]].itertuples(index=False):
        h, a, hg, ag, when = row
        home.append((when - last[h]).days if h in last else np.nan)
        away.append((when - last[a]).days if a in last else np.nan)
        if not (pd.isna(hg) or pd.isna(ag)):
            last[h] = last[a] = when
    df['home_rest_days'] = np.clip(home, 0, cap)
    df['away_rest_days'] = np.clip(away, 0, cap)


def xg_form(df, window=10, home_team_id_col='home_team', away_team_id_col='away_team',
            home_xg_col='home_xg', away_xg_col='away_xg'):
    """Average xG for/against over each team's last `window` matches with xG (NaN without history).

    Adds home/away_xg_for, home/away_xg_against and xg_diff_form. Rows must be chronological;
    upcoming matches (no xG yet) get the current form.
    """
    xg_for = defaultdict(lambda: deque(maxlen=window))
    xg_against = defaultdict(lambda: deque(maxlen=window))
    mean = lambda q: float(np.mean(q)) if q else np.nan
    cols = {k: [] for k in ('home_xg_for', 'home_xg_against', 'away_xg_for', 'away_xg_against')}
    home_xg = pd.to_numeric(df[home_xg_col], errors='coerce').to_numpy()
    away_xg = pd.to_numeric(df[away_xg_col], errors='coerce').to_numpy()
    for (h, a), hx, ax in zip(df[[home_team_id_col, away_team_id_col]].itertuples(index=False), home_xg, away_xg):
        cols['home_xg_for'].append(mean(xg_for[h]))
        cols['home_xg_against'].append(mean(xg_against[h]))
        cols['away_xg_for'].append(mean(xg_for[a]))
        cols['away_xg_against'].append(mean(xg_against[a]))
        if not (np.isnan(hx) or np.isnan(ax)):
            xg_for[h].append(hx); xg_against[h].append(ax)
            xg_for[a].append(ax); xg_against[a].append(hx)
    for k, v in cols.items():
        df[k] = v
    df['xg_diff_form'] = (df['home_xg_for'] - df['home_xg_against']) - (df['away_xg_for'] - df['away_xg_against'])
