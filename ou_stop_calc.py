def ornstein_uhlenbeck(price_series):
    import numpy as np

    prices = np.log(price_series)
    x = np.array(prices)
    if len(x) < 5:
        return np.exp(np.mean(x)), 0.005  # fallback SL size = 0.5%

    dx = x[1:] - x[:-1]

    mu = np.mean(x)
    sigma = np.std(dx)

    # extra safety: if volatility = 0, force fallback SL size
    stop_distance = max(sigma * 2, 0.005)

    mean_reversion_level = np.exp(mu)

    return mean_reversion_level, stop_distance  # returns target mean + SL size