"""
Classwise ECE

$\text{classewise-ECE} = \frac{1}{k} \sum_{i=1}^{k} \sum_{j=1}^{m} \frac{|B_{ij}|}{n_i} | y_{ij} - \bar{p}_{ij} |$

where:

- $k$ is the number of classes
- $m$ is the number of bins
- $n_i$ is the number of observation for the class $i$
- $B_i$ is the set of instances of class $i$ for the $j$ bin
- $y_{ij}$ is the real frequency of the instances of class $i$ in the bin $j$, number of true instances of the class $i$ in the bin $j$ divided by the number of instances of the class $i$ in the bin $j$
- $\bar{p}_{ij}$ is the average probability of the instances of class $i$ in the bin $j$

The classwise Expected Calibration Error (ECE) is a measure of how well the predicted probabilities of a model align with the actual outcomes for each class. It calculates the average difference between the actual frequency of instances in each class (yij) and the average predicted probability (p-bar ij) for that class, across all bins. It then averages these differences across all classes. In essence, it's a measure of the model's reliability in its predictions for each class.

La Classwise Expected Calibration Error (ECE) est une mesure de la précision des probabilités prédites par un modèle par rapport aux résultats réels pour chaque classe. Elle calcule la différence moyenne entre la fréquence réelle des instances dans chaque classe (yij) et la probabilité prédite moyenne (p-bar ij) pour cette classe, sur tous les intervalles. Elle fait ensuite la moyenne de ces différences pour toutes les classes. En essence, c'est une mesure de la fiabilité du modèle dans ses prédictions pour chaque classe.
"""


def classwise_ECE_fn(result_serie, home_prob_serie, draw_prob_serie, away_prob_serie, m=10, all_results=False):
    """
    Compute the Expected Calibration Error (ECE) for each class (home win, draw, away win) and the overall ECE.

    $\text{classewise-ECE} = \frac{1}{k} \sum_{i=1}^{k} \sum_{j=1}^{m} \frac{|B_{ij}|}{n_i} | y_{ij} - \bar{p}_{ij} |$

    where:

    - $k$ is the number of classes
    - $m$ is the number of bins
    - $n_i$ is the number of observation for the class $i$
    - $B_i$ is the set of instances of class $i$ for the $j$ bin
    - $y_{ij}$ is the real frequency of the instances of class $i$ in the bin $j$, number of true instances of the class $i$ in the bin $j$ divided by the number of instances of the class $i$ in the bin $j$
    - $\bar{p}_{ij}$ is the average probability of the instances of class $i$ in the bin $j$

    Parameters
    ----------
    result_serie : pd.Series
        The true result of the match. 1 if the home team is the winner, 0 if it's a draw, -1 if the away team is the winner.
    home_prob_serie : pd.Series
        The predicted probability that the home team is the winner.
    draw_prob_serie : pd.Series
        The predicted probability that it's a draw.
    away_prob_serie : pd.Series
        The predicted probability that the away team is the winner.
    m : int, optional
        The number of sub-intervals. The default is 10.
    all_result : bool, optional
        If True, return all the intermediate results. The default is False.
    
    Returns
    -------
    classwise_ECE : float
        The ECE for each class (home win, draw, away win) : the overall ECE.
    (ECE_home, ECE_draw, ECE_away) : tuple
        The ECE for each class (home win, draw, away win).
    (home_ECE_y, draw_ECE_y, away_ECE_y) : tuple
        The true probability for each sub-interval for each class.
    (home_ECE_p, draw_ECE_p, away_ECE_p) : tuple
        The predicted probability for each sub-interval for each class.
    (home_ECE_size, draw_ECE_size, away_ECE_size) : tuple
        The number of match for each sub-interval for each class.
    """

    ECE_home, ECE_draw, ECE_away = 0, 0, 0
    home_ECE_y, draw_ECE_y, away_ECE_y = [], [], []
    home_ECE_p, draw_ECE_p, away_ECE_p = [], [], []
    home_ECE_size, draw_ECE_size, away_ECE_size = [], [], []

    result_serie = result_serie.reset_index(drop=True)
    home_prob_serie = home_prob_serie.reset_index(drop=True)
    draw_prob_serie = draw_prob_serie.reset_index(drop=True)
    away_prob_serie = away_prob_serie.reset_index(drop=True)

    for j in range(m):
        home_ECE_mask = result_serie[(home_prob_serie > j/m) & (home_prob_serie <= (j+1)/m)]
        home_ECE_yij = home_ECE_mask[home_ECE_mask == 1].shape[0] / home_ECE_mask.shape[0] if home_ECE_mask.shape[0] != 0 else 0
        home_ECE_pij = home_prob_serie[home_ECE_mask.index].mean() if home_ECE_mask.shape[0] != 0 else 0
        ECE_home += abs(home_ECE_yij - home_ECE_pij) * home_ECE_mask.shape[0]/home_prob_serie.shape[0]
        home_ECE_y.append(home_ECE_yij)
        home_ECE_p.append(home_ECE_pij)
        home_ECE_size.append(home_ECE_mask.shape[0])

        draw_ECE_mask = result_serie[(draw_prob_serie > j/m) & (draw_prob_serie <= (j+1)/m)]
        draw_ECE_yij = draw_ECE_mask[draw_ECE_mask == 0].shape[0] / draw_ECE_mask.shape[0] if draw_ECE_mask.shape[0] != 0 else 0
        draw_ECE_pij = draw_prob_serie[draw_ECE_mask.index].mean() if draw_ECE_mask.shape[0] != 0 else 0
        ECE_draw += abs(draw_ECE_yij - draw_ECE_pij) * draw_ECE_mask.shape[0]/draw_prob_serie.shape[0]
        draw_ECE_y.append(draw_ECE_yij)
        draw_ECE_p.append(draw_ECE_pij)
        draw_ECE_size.append(draw_ECE_mask.shape[0])
        
        away_ECE_mask = result_serie[(away_prob_serie > j/m) & (away_prob_serie <= (j+1)/m)]
        away_ECE_yij = away_ECE_mask[away_ECE_mask == -1].shape[0] / away_ECE_mask.shape[0] if away_ECE_mask.shape[0] != 0 else 0
        away_ECE_pij = away_prob_serie[away_ECE_mask.index].mean() if away_ECE_mask.shape[0] != 0 else 0
        ECE_away += abs(away_ECE_yij - away_ECE_pij) * away_ECE_mask.shape[0]/away_prob_serie.shape[0]
        away_ECE_y.append(away_ECE_yij)
        away_ECE_p.append(away_ECE_pij)
        away_ECE_size.append(away_ECE_mask.shape[0])

    classwise_ECE = (ECE_home + ECE_draw + ECE_away) / 3

    if all_results:
        return classwise_ECE, \
        (ECE_home, ECE_draw, ECE_away), \
        (home_ECE_y, draw_ECE_y, away_ECE_y), \
        (home_ECE_p, draw_ECE_p, away_ECE_p), \
        (home_ECE_size, draw_ECE_size, away_ECE_size)

    return classwise_ECE