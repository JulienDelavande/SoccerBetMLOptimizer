import numpy as np

def player_expected_utility_exp(f, o, r, B=1, alpha=1):
    """
    Calculate the negative expected exponential utility for a bettor.

    :param f: numpy array of shape (matches, outcomes), fractions of the bankroll allocated to each outcome.
    :param o: numpy array of shape (matches, outcomes), odds offered for each outcome.
    :param r: numpy array of shape (matches, outcomes), estimated probabilities of success for each outcome.
    :param B: float, the current bankroll of the bettor.
    :param alpha: float, coefficient of absolute risk aversion.

    :return: float, the negative expected exponential utility.
    """
    f = np.array(f)
    o = np.array(o)
    r = np.array(r)

    M, N = o.shape  # Number of matches and number of outcomes per match
    f = f.reshape(M, N)
    
    # Total fraction bet
    F_total = np.sum(f)
    
    # Compute exponentials for each outcome
    exponentials = np.exp(-alpha * B * f * o)
    
    # Weight by the estimated probabilities
    weighted_exponentials = r * exponentials
    
    # Sum over outcomes for each match
    sum_over_issues = np.sum(weighted_exponentials, axis=1)
    
    # Product over all matches
    product_over_matches = np.prod(sum_over_issues)
    
    # Calculate the negative expected exponential utility
    negative_expected_utility = np.exp(-alpha * B * (1 - F_total)) * product_over_matches
    
    return negative_expected_utility
