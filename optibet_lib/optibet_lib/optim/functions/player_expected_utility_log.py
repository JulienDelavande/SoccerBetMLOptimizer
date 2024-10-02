import numpy as np

def player_expected_utility_log(f, o, r, B=1, epsilon=1e-8):
    """
    Compute the expected logarithmic utility of the bettor's bankroll at time t+1 without approximation.

    :param f: A 2D numpy array, where each row contains the fractions of the bankroll allocated to different outcomes of match k.
    :param o: A 2D numpy array, where each row contains the odds for the different outcomes of match k.
    :param r: A 2D numpy array, where each row contains the estimated probabilities for the different outcomes of match k.
    :param B: The current bankroll of the bettor.
    :param epsilon: A small value to prevent logarithm arguments from becoming non-positive.

    :return: The expected logarithmic utility of the future bankroll.
    """
    # Ensure f, o, and r are numpy arrays
    f = np.array(f)
    o = np.array(o)
    r = np.array(r)
    
    # Number of matches and outcomes per match
    M, N = o.shape
    f = f.reshape(M, N)

    # Initialize expected log utility
    expected_log_utility = 0.0
    
    # Iterate over each match
    for k in range(M):
        # Calculate the total fraction bet on match k
        F_k = np.sum(f[k])
        
        # Compute the expected log utility for match k
        expected_log_utility_k = 0.0
        for i in range(N):
            if f[k, i] > 0:  # Only consider outcomes with non-zero bets
                # Prevent log arguments from being zero or negative
                log_argument = 1 - F_k + f[k, i] * o[k, i]
                log_argument = max(log_argument, epsilon)  # Ensure positivity
                
                expected_log_utility_k += r[k, i] * np.log(log_argument)
        
        # Add the result for match k to the total expected log utility
        expected_log_utility += expected_log_utility_k
    
    # Final expected log utility (including current bankroll log)
    total_expected_log_utility = np.log(B) + expected_log_utility
    
    return total_expected_log_utility
