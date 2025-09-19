import numpy as np

def prob_by_bookies(row, bookie):
    if np.isnan(row[f'{bookie}H']) or np.isnan(row[f'{bookie}D']) or np.isnan(row[f'{bookie}A']):
        (np.nan, np.nan, np.nan)
    margin = 1/row[f'{bookie}H'] + 1/row[f'{bookie}D'] + 1/row[f'{bookie}A'] - 1
    return 1 / row[f'{bookie}H'] - margin/3, 1 / row[f'{bookie}D'] - margin/3, 1 / row[f'{bookie}A'] - margin/3
