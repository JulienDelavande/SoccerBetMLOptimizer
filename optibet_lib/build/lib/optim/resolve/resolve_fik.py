
import numpy as np
from scipy.optimize import minimize

def resolve_fik(o, r, objectif):

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
    result = minimize(objectif, f0, constraints=constraints, bounds=bounds, args=(o, r))

    # Résultats
    if result.success:
        f_optimal = result.x.reshape(M, N)
        #print("Répartition optimale de la bankroll:")
        #print(f_optimal)
        return f_optimal
    else:
        print("L'optimisation a échoué:", result.message)
        return np.zeros((M, N))

    
