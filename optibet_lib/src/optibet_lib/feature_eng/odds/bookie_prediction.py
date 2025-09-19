NO_RESULTS = -2
HOME_VICTORY = 1
DRAW = 0
AWAY_VICTORY = -1

def bookie_prediction(row, bookies):
    """
    Return 1 if the home team is the winner according to the bookie, 0 if it's a draw, -1 if the away team is the winner and -2 if the bookie is not able to predict the winner
    """
    if row[f'{bookies}H'] < row[f'{bookies}D'] and row[f'{bookies}H'] < row[f'{bookies}A']:
        return HOME_VICTORY
    elif row[f'{bookies}D'] < row[f'{bookies}H'] and row[f'{bookies}D'] < row[f'{bookies}A']:
        return DRAW
    elif row[f'{bookies}A'] < row[f'{bookies}H'] and row[f'{bookies}A'] < row[f'{bookies}D']:
        return AWAY_VICTORY
    else:
        return NO_RESULTS