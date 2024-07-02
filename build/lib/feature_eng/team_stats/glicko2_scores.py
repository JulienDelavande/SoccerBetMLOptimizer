import pandas as pd
import math

# Fonction principale pour ajouter les scores Glicko-2
def glicko2_scores(df, TAU=0.5,  START_RATING=1500., START_RD=350., START_VOL=0.06, CONVERGENCE_TOLERANCE=1e-5, date_stop=None,
                home_team_id_col='home_team_api_id', away_team_id_col='away_team_api_id',
                home_team_goal_col='home_team_goal', away_team_goal_col='away_team_goal',
                glicko2_home_before_col='glicko2_home_before', glicko2_away_before_col='glicko2_away_before',
                glicko2_rd_home_before_col='glicko2_rd_home_before', glicko2_rd_away_before_col='glicko2_rd_away_before',
                glicko2_vol_home_before_col='glicko2_vol_home_before', glicko2_vol_away_before_col='glicko2_vol_away_before',
                date_col='date'):
    """
    Add the Glicko-2 scores to the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to add the Glicko-2 scores.
    TAU : float, optional
        The system constant. The default is 0.5.
    START_RATING : float, optional
        The starting rating. The default is 1500.
    START_RD : float, optional
        The starting rating deviation. The default is 350.
    START_VOL : float, optional
        The starting volatility. The default is 0.06.
    CONVERGENCE_TOLERANCE : float, optional
        The convergence tolerance. The default is 1e-5.
    
    Returns
    -------
    None
    """

    # Fonctions utilitaires pour Glicko-2
    def g(phi):
        return 1 / math.sqrt(1 + 3 * phi**2 / math.pi**2)

    def E(mu, mu_j, phi_j):
        return 1 / (1 + math.exp(-g(phi_j) * (mu - mu_j)))

    def calculate_v(mu, phi_list, mu_list, s_list):
        return 1 / sum((g(phi) ** 2) * E(mu, mu_j, phi) * (1 - E(mu, mu_j, phi))
                    for phi, mu_j, s in zip(phi_list, mu_list, s_list))

    def calculate_delta(mu, phi_list, mu_list, s_list, v):
        return v * sum(g(phi) * (s - E(mu, mu_j, phi))
                    for phi, mu_j, s in zip(phi_list, mu_list, s_list))

    def update_volatility(mu, phi, v, delta, sigma):
        a = math.log(sigma ** 2)
        A = a
        B = 0
        if delta ** 2 > phi ** 2 + v:
            B = math.log(delta ** 2 - phi ** 2 - v)
        else:
            k = 1
            while f(a - k * math.sqrt(TAU ** 2), delta, phi, sigma, v) < 0:
                k += 1
            B = a - k * math.sqrt(TAU ** 2)
        
        fA = f(A, delta, phi, sigma, v)
        fB = f(B, delta, phi, sigma, v)
        
        while abs(B - A) > CONVERGENCE_TOLERANCE:
            C = A + (A - B) * fA / (fB - fA)
            fC = f(C, delta, phi, sigma, v)
            if fC * fB < 0:
                A = B
                fA = fB
            else:
                fA /= 2
            B = C
            fB = fC
        
        return math.exp(A / 2)

    def f(x, delta, phi, sigma, v):
        exp_x = math.exp(x)
        numerator = exp_x * (delta ** 2 - phi ** 2 - v - exp_x)
        denominator = 2 * (phi ** 2 + v + exp_x) ** 2
        return numerator / denominator - (x - math.log(sigma ** 2)) / (TAU ** 2)
    
    teams = list(set(df[home_team_id_col].unique()).union(set(df[away_team_id_col].unique())))
    ratings = {team: START_RATING for team in teams}
    rds = {team: START_RD for team in teams}
    vols = {team: START_VOL for team in teams}
    
    df[glicko2_home_before_col] = 0.
    df[glicko2_away_before_col] = 0.
    df[glicko2_rd_home_before_col] = 0.
    df[glicko2_rd_away_before_col] = 0.
    df[glicko2_vol_home_before_col] = 0.
    df[glicko2_vol_away_before_col] = 0.

    for index, row in df.iterrows():
        home_team = row[home_team_id_col]
        away_team = row[away_team_id_col]
        
        # Ajouter les scores Glicko-2 avant le match
        df.at[index, glicko2_home_before_col] = ratings[home_team]
        df.at[index, glicko2_away_before_col] = ratings[away_team]
        df.at[index, glicko2_rd_home_before_col] = rds[home_team]
        df.at[index, glicko2_rd_away_before_col] = rds[away_team]
        df.at[index, glicko2_vol_home_before_col] = vols[home_team]
        df.at[index, glicko2_vol_away_before_col] = vols[away_team]

        is_match_played = (not pd.isna(row[home_team_goal_col]) and not pd.isna(row[away_team_goal_col]))
        is_date_passed = (date_stop is not None and row[date_col] > date_stop)
        if not is_match_played or is_date_passed:
            continue
        
        # Convertir les ratings et RD en échelle Glicko-2
        mu_home = (ratings[home_team] - 1500) / 173.7178
        phi_home = rds[home_team] / 173.7178
        mu_away = (ratings[away_team] - 1500) / 173.7178
        phi_away = rds[away_team] / 173.7178
        
        # Calculer les scores attendus
        expected_home = E(mu_home, mu_away, phi_away)
        expected_away = E(mu_away, mu_home, phi_home)
        
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
        
        # Liste des paramètres pour l'équipe home et away
        phi_list_home = [phi_away]
        mu_list_home = [mu_away]
        s_list_home = [actual_home]
        
        phi_list_away = [phi_home]
        mu_list_away = [mu_home]
        s_list_away = [actual_away]
        
        # Calculer les paramètres intermédiaires
        v_home = calculate_v(mu_home, phi_list_home, mu_list_home, s_list_home)
        delta_home = calculate_delta(mu_home, phi_list_home, mu_list_home, s_list_home, v_home)
        
        v_away = calculate_v(mu_away, phi_list_away, mu_list_away, s_list_away)
        delta_away = calculate_delta(mu_away, phi_list_away, mu_list_away, s_list_away, v_away)
        
        # Mettre à jour la volatilité
        sigma_home = update_volatility(mu_home, phi_home, v_home, delta_home, vols[home_team])
        sigma_away = update_volatility(mu_away, phi_away, v_away, delta_away, vols[away_team])
        
        # Mettre à jour le rating et l'écart-type
        phi_prime_home = math.sqrt(phi_home**2 + sigma_home**2)
        phi_star_home = phi_prime_home / math.sqrt(1 + v_home * phi_prime_home**2)
        mu_prime_home = mu_home + phi_star_home**2 * sum(g(phi) * (s - E(mu_home, mu_j, phi))
                                                          for phi, mu_j, s in zip(phi_list_home, mu_list_home, s_list_home))
        
        phi_prime_away = math.sqrt(phi_away**2 + sigma_away**2)
        phi_star_away = phi_prime_away / math.sqrt(1 + v_away * phi_prime_away**2)
        mu_prime_away = mu_away + phi_star_away**2 * sum(g(phi) * (s - E(mu_away, mu_j, phi))
                                                          for phi, mu_j, s in zip(phi_list_away, mu_list_away, s_list_away))
        
        # Convertir les ratings et RD en échelle Glicko
        ratings[home_team] = 173.7178 * mu_prime_home + 1500
        rds[home_team] = 173.7178 * phi_star_home
        vols[home_team] = sigma_home
        
        ratings[away_team] = 173.7178 * mu_prime_away + 1500
        rds[away_team] = 173.7178 * phi_star_away
        vols[away_team] = sigma_away
