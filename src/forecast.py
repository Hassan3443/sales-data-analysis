"""Monthly revenue forecasting with an honest backtest.

Four simple models, all in numpy so they are easy to read and test:

  naive             next month = last month
  mean_3            next month = mean of the last 3 months
  seasonal_naive    next month = the same month one year ago
  trend_seasonal    linear trend plus a fixed effect for each calendar month,
                    fitted together by least squares

Each model is scored on a hold-out: fit on the first n - h months, predict the last h.
With only 24 monthly points, the numbers are a demonstration of method, not a
promise about the future.
"""
import numpy as np

MODELS = ("naive", "mean_3", "seasonal_naive", "trend_seasonal")


def predict(model, history, horizon, season=12):
    """Forecast `horizon` months ahead from a 1-D array of monthly values."""
    y = np.asarray(history, dtype=float)
    n = len(y)
    if model == "naive":
        return np.repeat(y[-1], horizon)
    if model == "mean_3":
        return np.repeat(y[-3:].mean(), horizon)
    if model == "seasonal_naive":
        if n < season:
            raise ValueError("seasonal_naive needs at least one full season of history")
        return np.array([y[n - season + (h % season)] for h in range(horizon)])
    if model == "trend_seasonal":
        if n < season:
            raise ValueError("trend_seasonal needs at least one full season of history")
        # Trend and month effects are fitted together. Fitting the trend first would let
        # the seasonal shape leak into the slope. Months not seen yet get no effect.
        def design(t):
            return np.column_stack([np.ones(len(t)), t] + [(t % season == s).astype(float) for s in range(season)])
        t = np.arange(n)
        coef, *_ = np.linalg.lstsq(design(t), y, rcond=None)
        return design(np.arange(n, n + horizon)) @ coef
    raise ValueError(f"unknown model: {model}")


def mape(actual, forecast):
    a, f = np.asarray(actual, float), np.asarray(forecast, float)
    return float(np.mean(np.abs((a - f) / a)) * 100)


def mae(actual, forecast):
    return float(np.mean(np.abs(np.asarray(actual, float) - np.asarray(forecast, float))))


def backtest(series, holdout=6, models=MODELS):
    """Score every model on the last `holdout` months. Returns rows sorted by MAPE."""
    y = np.asarray(series, dtype=float)
    train, test = y[:-holdout], y[-holdout:]
    rows = []
    for m in models:
        f = predict(m, train, holdout)
        rows.append({"model": m, "mape": round(mape(test, f), 1), "mae": round(mae(test, f)),
                     "forecast": [round(float(v)) for v in f]})
    return sorted(rows, key=lambda r: r["mape"])


def rolling_backtest(series, min_train=12, horizon=3, models=MODELS):
    """Rolling-origin test: fit on months [0, k), predict k..k+horizon, for every k.

    One hold-out split can flatter or punish a model by luck. Averaging over every
    possible origin uses the short history better. Returns rows sorted by mean MAPE,
    each with the number of origins used.
    """
    y = np.asarray(series, dtype=float)
    origins = range(min_train, len(y) - horizon + 1)
    rows = []
    for m in models:
        errs = [mape(y[k:k + horizon], predict(m, y[:k], horizon)) for k in origins]
        rows.append({"model": m, "mape": round(float(np.mean(errs)), 1), "origins": len(errs)})
    return sorted(rows, key=lambda r: r["mape"])
