import numpy as np

def simulate_prob(M, N, bias_bookmaker, bias_player, std_bookmaker, std_player, margin_bookmaker, min_prob, max_prob):
    r = np.random.dirichlet(np.ones(N), size=M)

    b = r + bias_bookmaker + np.random.normal(0, std_bookmaker, r.shape)
    b = np.clip(b, min_prob, max_prob)
    b = b / (b.sum(axis=1, keepdims=True) - margin_bookmaker)
    o = 1 / b

    t = r + bias_player + np.random.normal(0, std_player, r.shape)
    t = np.clip(t, min_prob, max_prob)
    t = t / t.sum(axis=1, keepdims=True)

    return r, o, t