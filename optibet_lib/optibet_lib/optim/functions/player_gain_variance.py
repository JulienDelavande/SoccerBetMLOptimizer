
def player_gain_variance(f, o, r, B=1):
    """
    Calculates the gain variance for a player.

    Hypothesis 1: The matches are independent (We can sum the variance of each match)
    Hypothesis 2: The outcomes of the matches complete each other (We can calulate the covariance)

    $\text{Var}[G_{joueur}(t)] = B_joueur **2 * \sum_{k=1}^{M}  [\sum_{i=1}^{N} (f_i^k)^2 (o_i^k)^2  r_i^k(1 - r_i^k) - 2 \sum_{j < i}^{N} f_i^k f_j^k  o_i^k  o_j^k r_i^k r_j^k]$

    :param f: A list of lists, where each sublist f[k] contains the fractions of the bankroll allocated to different outcomes of match k
    :param o: A list of lists, where each sublist o[k] contains the odds for the different outcomes of match k
    :param r: A list of lists, where each sublist r[k] contains the probabilities of success for the different outcomes of match k
    :param B: The bankroll

    :return: The gain variance of the player
    """
    total_variance = 0

    # For each match k
    for k in range(len(f)):
        variance_k = 0
        covariance_k = 0

        # For each outcome i of match k
        for i in range(len(f[k])):
            variance_k += (f[k][i] ** 2) * (o[k][i] ** 2) * r[k][i] * (1 - r[k][i])
            
            # Calculate the covariances
            for j in range(len(f[k])):
                if i != j:
                    covariance_k += f[k][i] * f[k][j] * o[k][i] * o[k][j] * (-r[k][i] * r[k][j])

        total_variance += variance_k + covariance_k 

    return total_variance * B**2


import numpy as np

def player_gain_variance_numpy(f, o, r, B=1):
    """
    Optimized version of the player_gain_variance function using NumPy.

    :param f: A 2D numpy array, where each row contains the fractions of the bankroll allocated to different outcomes of match k
    :param o: A 2D numpy array, where each row contains the odds for the different outcomes of match k
    :param r: A 2D numpy array, where each row contains the probabilities of success for the different outcomes of match k
    :param B: The bankroll

    :return: The gain variance of the player
    """
    f = np.array(f)
    o = np.array(o)
    r = np.array(r)

    variance_k = np.sum((f ** 2) * (o ** 2) * r * (1 - r), axis=1)
    
    covariance_k = 0
    for k in range(len(f)):
        covariance_matrix = np.outer(f[k] * o[k] * r[k], f[k] * o[k] * r[k])
        np.fill_diagonal(covariance_matrix, 0)
        covariance_k += np.sum(-covariance_matrix)
    
    total_variance = np.sum(variance_k + covariance_k)
    
    return total_variance * B**2

