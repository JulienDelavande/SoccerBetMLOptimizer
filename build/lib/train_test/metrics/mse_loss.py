"""
Mean square error

$\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} \frac{1}{m} \sum_{j=1}^m(y_{ij} - p_{ij})^2$

where:

- $n$ is the number of games
- $m$ is the number of classes
- $y_{ij}$ is 1 if the game $i$ is of class $j$ and 0 otherwise
- $p_{ij}$ is the probability that the game $i$ is of class $j$
"""

def mse_loss_fn(result_serie, home_prob_serie, draw_prob_serie, away_prob_serie, all_results=False):
    """
    Compute the mean squared error of the prediction.

    $\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} \frac{1}{m} \sum_{j=1}^m(y_{ij} - p_{ij})^2$

    where:

    - $n$ is the number of games
    - $m$ is the number of classes
    - $y_{ij}$ is 1 if the game $i$ is of class $j$ and 0 otherwise
    - $p_{ij}$ is the probability that the game $i$ is of class $j$

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
    all_result : bool, optional
        If True, return all the intermediate results. The default is False.
    
    Returns
    -------
    mse_loss : float
        The mean squared error of the prediction.
    (loss_home, loss_draw, loss_away) : tuple of float
        The loss for each class.
    """

    loss_home, loss_draw, loss_away = 0, 0, 0

    result_serie = result_serie.reset_index(drop=True)
    home_prob_serie = home_prob_serie.reset_index(drop=True)
    draw_prob_serie = draw_prob_serie.reset_index(drop=True)
    away_prob_serie = away_prob_serie.reset_index(drop=True)

    for index, result in result_serie.items():
        home_prob = home_prob_serie[index]
        draw_prob = draw_prob_serie[index]
        away_prob = away_prob_serie[index]

        loss_home += (float(result == 1) - home_prob) ** 2
        loss_draw += (float(result == 0) - draw_prob) ** 2
        loss_away += (float(result == -1) - away_prob) ** 2

    loss_home /= len(result_serie)
    loss_draw /= len(result_serie)
    loss_away /= len(result_serie)

    mse_loss = (loss_home + loss_draw + loss_away)/3

    if all_results:
        return mse_loss, (loss_home, loss_draw, loss_away)
    return mse_loss