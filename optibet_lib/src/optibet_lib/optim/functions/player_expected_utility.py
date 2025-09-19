import numpy as np
from collections import defaultdict

def player_expected_utility(f, o, t, bankroll, utility_function):
    """
    Calcule l'espérance de l'utilité de la bankroll après avoir placé des paris sur plusieurs matchs
    en utilisant la convolution des distributions de gains pour optimiser le temps de calcul.

    Paramètres :
    - f : numpy array de taille (matchs, issues), fractions de la bankroll à investir sur chaque issue.
    - o : numpy array de taille (matchs, issues), cotes offertes par le bookmaker pour chaque issue.
    - t : numpy array de taille (matchs, issues), probabilités estimées pour chaque issue.
    - bankroll : float, la bankroll actuelle du parieur.
    - utility_function : fonction lambda, la fonction d'utilité U(BF).

    Retourne :
    - total_expected_utility : float, l'espérance de l'utilité de la bankroll.
    """
    M, N = o.shape  # Nombre de matchs et nombre d'issues par match
    f = f.reshape(M, N)
    total_bet = np.sum(f)  # Total des mises sur tous les matchs

    # Liste des distributions de gains pour chaque match
    gain_distributions = []

    for k in range(M):
        total_bet_k = np.sum(f[k])  # Total misé sur le match k
        gains_k = defaultdict(float)

        for i_k in range(N):
            # Calcul du gain net pour l'issue i_k du match k
            net_gain = f[k, i_k] * o[k, i_k] - total_bet_k
            probability = t[k, i_k]

            # Agrégation des probabilités pour les gains identiques
            gains_k[net_gain] += probability

        # Ajout de la distribution de gains du match k à la liste
        gain_distributions.append(gains_k)

    # Fonction pour convoluer deux distributions de gains
    def convolve_distributions(dist1, dist2):
        result = defaultdict(float)
        for gain1, prob1 in dist1.items():
            for gain2, prob2 in dist2.items():
                total_gain = gain1 + gain2
                total_prob = prob1 * prob2
                result[total_gain] += total_prob
        return result

    # Convolution de toutes les distributions de gains
    from functools import reduce
    total_gain_distribution = reduce(convolve_distributions, gain_distributions)

    # Calcul de l'espérance de l'utilité
    total_expected_utility = 0.0
    for net_gain, probability in total_gain_distribution.items():
        final_bankroll = bankroll + net_gain
        utility = utility_function(final_bankroll)
        weighted_utility = utility * probability
        total_expected_utility += weighted_utility

    return total_expected_utility
