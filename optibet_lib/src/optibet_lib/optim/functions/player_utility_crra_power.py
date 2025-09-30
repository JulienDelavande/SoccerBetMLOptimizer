import numpy as np
from .player_gain_expected_value import player_gain_expected_value_numpy

def player_utility_crra_power(f, o, r, B=1, gamma=0.5):
    """
    Calculates the utility of a player using CRRA (Constant Relative Risk Aversion) power utility function.
    
    This is a generalization of the Kelly criteria for different risk preferences:
    - U(w) = (w^(1-γ))/(1-γ) for γ ≠ 1
    - U'(w) = w^(-γ)
    - U''(w) = -γ * w^(-γ-1)
    
    Where γ is the risk aversion parameter:
    - γ = 0: risk neutral (linear utility)
    - γ = 0.5: moderate risk aversion
    - γ = 1: logarithmic utility (Kelly criterion)
    - γ > 1: high risk aversion
    
    :param f: A list of lists, where each sublist f[k] contains the fractions of the bankroll allocated to different outcomes of match k
    :param o: A list of lists, where each sublist o[k] contains the odds for the different outcomes of match k
    :param r: A list of lists, where each sublist r[k] contains the probabilities of success for the different outcomes of match k
    :param B: Initial bankroll (default: 1)
    :param gamma: Risk aversion parameter (default: 0.5)
    
    :return: The negative utility of the player (for minimization)
    """
    M, N = o.shape
    f = f.reshape(M, N)
    
    # Calculate expected final wealth
    expected_gain = player_gain_expected_value_numpy(f, o, r, B)
    final_wealth = B + expected_gain
    
    # Ensure wealth is positive (add small epsilon to avoid numerical issues)
    final_wealth = np.maximum(final_wealth, 1e-10)
    
    if abs(gamma - 1.0) < 1e-10:
        # Special case: γ = 1 corresponds to logarithmic utility (Kelly criterion)
        utility = np.log(final_wealth)
    else:
        # General CRRA utility: U(w) = w^(1-γ)/(1-γ)
        utility = (final_wealth**(1 - gamma)) / (1 - gamma)
    
    return -utility