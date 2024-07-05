import trueskill
import pandas as pd
def trueskill_scores(df, date_stop=None,
                    MU=trueskill.MU, SIGMA=trueskill.SIGMA, BETA=trueskill.BETA, 
                    TAU=trueskill.TAU, DRAW_PROBABILITY=trueskill.DRAW_PROBABILITY, 
                    K=3,
                    home_team_id_col='home_team_api_id', away_team_id_col='away_team_api_id',
                    home_team_goal_col='home_team_goal', away_team_goal_col='away_team_goal',
                    trueskill_home_before_col='trueskill_home_before', trueskill_away_before_col='trueskill_away_before',
                    date_col='date'):
    """
    Add the TrueSkill scores to the dataset.

    True_skill = mu - 3 * sigma
    mu = mean of the skill
    sigma = standard deviation of the skill

    The skill is the ability of the team to win a match.
    rating is a Gaussian distribution which starts from N(25,(25/3)**2).
    μ is an average skill of player, and σ is a confidence of the guessed rating. A real skill of player is between μ±2σ with 95% confidence.
.
    (Source Microsoft research)[https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/?from=https://research.microsoft.com/en-us/projects/trueskill&type=exact]
    
    Parameters
    ----------
    df : pd.DataFrame
        The dataset to add the TrueSkill scores.
    MU : float, optional
        The mean of the skill. The default is trueskill.MU = 25.0
    SIGMA : float, optional
        The standard deviation of the skill. The default is trueskill.SIGMA = 25.0/3
    BETA : float, optional
        The dynamic factor. The default is trueskill.BETA = 25.0/6
    TAU : float, optional
        The factor to control the draw probability. The default is trueskill.TAU = 25.0/300
    DRAW_PROBABILITY : float, optional
        The draw probability. The default is trueskill.DRAW_PROBABILITY = 0.1
    K : float, optional
        The scaling factor to convert the TrueSkill score to a normal scale. The default is 3.

    Returns
    -------
    None
    """

    # Initialisation des paramètres TrueSkill
    env = trueskill.TrueSkill(mu=MU, sigma=SIGMA, beta=BETA, tau=TAU, draw_probability=DRAW_PROBABILITY)
    teams = list(set(df[home_team_id_col].unique()).union(df[away_team_id_col].unique()))
    ratings = {team: env.create_rating() for team in teams}

    # Fonction pour convertir les ratings TrueSkill en échelle normale
    def convert_rating(rating):
        return rating.mu - K * rating.sigma

    # Ajouter les scores TrueSkill avant le match
    df[trueskill_home_before_col] = 0.
    df[trueskill_away_before_col] = 0.

    for index, row in df.iterrows():
        home_team = row[home_team_id_col]
        away_team = row[away_team_id_col]

        is_match_played = (not pd.isna(row[home_team_goal_col]) and not pd.isna(row[away_team_goal_col]))
        is_date_passed = (date_stop is not None and row[date_col] > date_stop)
        if not is_match_played or is_date_passed:
            continue
        
        # Ajouter les scores TrueSkill avant le match
        df.at[index, trueskill_home_before_col] = convert_rating(ratings[home_team])
        df.at[index, trueskill_away_before_col] = convert_rating(ratings[away_team])
        
        # Mettre à jour les scores TrueSkill
        if row[home_team_goal_col] > row[away_team_goal_col]:
            ratings[home_team], ratings[away_team] = env.rate_1vs1(ratings[home_team], ratings[away_team])
        elif row[home_team_goal_col] < row[away_team_goal_col]:
            ratings[away_team], ratings[home_team] = env.rate_1vs1(ratings[away_team], ratings[home_team])
        else:
            ratings[home_team], ratings[away_team] = env.rate_1vs1(ratings[home_team], ratings[away_team], drawn=True)