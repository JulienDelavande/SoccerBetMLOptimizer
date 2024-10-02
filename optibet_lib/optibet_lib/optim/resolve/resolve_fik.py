
import numpy as np
from scipy.optimize import minimize
import logging

def resolve_fik(o, r, objectif, logger = None, method='SLSQP'):
    if logger is None:
        logger = logging.getLogger(__name__)

    M = len(o)
    N = len(o[0])
    

    # Contraintes
    constraints = []

    # Contrainte : somme des fractions de la bankroll <= 1 pour chaque événement
    constraints.append({'type': 'ineq', 'fun': lambda f : 1 - np.sum(f.reshape(M, N))})

    # Contrainte : non-négativité
    bounds = [(0, 1) for _ in range(M * N)]

    # Solution initiale (répartition uniforme)
    f0 = np.ones(M * N) / (M * N)

    # Résolution de l'optimisation
    try:
        logger.info(f"Optimisation started with method: {method}")
        result = minimize(objectif, f0, constraints=constraints, bounds=bounds, args=(o, r), method=method)
        if result.success:
            f_optimal = result.x.reshape(M, N)
            return f_optimal
    except Exception as e:
        print("L'optimisation a échoué:", e)
        if logger:
            logger.error(f"Optimisation failed: {e}")
        return np.zeros((M, N))
    
    return np.zeros((M, N))
    
    
