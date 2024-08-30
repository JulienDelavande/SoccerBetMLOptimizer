def player_gain_expected_value(f, o, r, B=1):
    """
    Calculates the expected value of gain for a player.

    :param f: A list of lists, where each sublist f[k] contains the fractions of the bankroll allocated to different outcomes of match k
    :param o: A list of lists, where each sublist o[k] contains the odds for the different outcomes of match k
    :param r: A list of lists, where each sublist r[k] contains the probabilities of success for the different outcomes of match k
    :param B: The bankroll

    :return: The expected value of the player's gain
    """
    expected_value = 0

    # For each match k
    for k in range(len(f)):
        # For each outcome i of match k
        for i in range(len(f[k])):
            expected_value += f[k][i] * (o[k][i] * r[k][i] - 1)

    return expected_value * B


import numpy as np

def player_gain_expected_value_numpy(f, o, r, B=1):
    """
    Optimized version of the player_gain_expected_value function using NumPy.

    :param f: A 2D numpy array, where each row contains the fractions of the bankroll allocated to different outcomes of match k
    :param o: A 2D numpy array, where each row contains the odds for the different outcomes of match k
    :param r: A 2D numpy array, where each row contains the probabilities of success for the different outcomes of match k
    :param B: The bankroll

    :return: The expected value of the player's gain
    """
    f = np.array(f)
    o = np.array(o)
    r = np.array(r)
    
    expected_value = np.sum(f * (o * r - 1))
    
    return expected_value * B
