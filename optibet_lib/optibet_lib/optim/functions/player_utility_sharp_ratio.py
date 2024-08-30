from .player_gain_expected_value import player_gain_expected_value, player_gain_expected_value_numpy
from .player_gain_variance import player_gain_variance

def player_utility_sharp_ratio(f, o, r, B=1):
    """
    Calculates the utility of a player according to the Sharp ratio.
    
    Hypothesis: The matchs are independent and the outcomes are exclusive
    
    :param f: A list of lists, where each sublist f[k] contains the fractions of the bankroll allocated to different outcomes of match k
    :param o: A list of lists, where each sublist o[k] contains the odds for the different outcomes of match k
    :param r: A list of lists, where each sublist r[k] contains the probabilities of success for the different outcomes of match k
    
    :return: The utility of the player according to the Sharp ratio
    """
    M, N = o.shape
    f = f.reshape(M, N)

    E = player_gain_expected_value_numpy(f, o, r, B)
    V = player_gain_variance(f, o, r, B)

    U = E / V

    return -U