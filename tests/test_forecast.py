import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.forecast import backtest, mae, mape, predict, rolling_backtest  # noqa: E402

SEASON = np.array([10, 12, 15, 20, 18, 14, 11, 9, 8, 10, 22, 30], dtype=float)


def test_naive_and_mean():
    assert predict("naive", [1, 2, 3], 2).tolist() == [3, 3]
    assert predict("mean_3", [1, 2, 3, 4, 5], 1).tolist() == [4.0]


def test_seasonal_naive_repeats_last_year_and_wraps():
    y = np.tile(SEASON, 2)
    out = predict("seasonal_naive", y, 14)
    assert out[:12].tolist() == SEASON.tolist()
    assert out[12:].tolist() == SEASON[:2].tolist()


def test_trend_seasonal_is_exact_on_trend_plus_season():
    n = np.arange(48)
    y = 100 + 5 * n + np.tile(SEASON, 4) * 10
    assert predict("trend_seasonal", y[:36], 12) == pytest.approx(y[36:], rel=1e-6)


def test_seasonal_models_need_a_full_year():
    for m in ("seasonal_naive", "trend_seasonal"):
        with pytest.raises(ValueError):
            predict(m, [1.0] * 11, 3)
    with pytest.raises(ValueError):
        predict("nope", [1.0] * 12, 1)


def test_error_metrics():
    assert mape([100, 200], [110, 180]) == pytest.approx(10.0)
    assert mae([100, 200], [110, 180]) == pytest.approx(15.0)


def test_backtest_ranks_seasonal_first_on_seasonal_data():
    y = np.tile(SEASON, 3) * 1000
    assert backtest(y, 6)[0]["mape"] == 0.0
    rb = rolling_backtest(y)
    assert rb[0]["model"] in ("seasonal_naive", "trend_seasonal")
    assert rb[-1]["model"] in ("naive", "mean_3")
    assert all(r["origins"] == len(y) - 12 - 3 + 1 for r in rb)


def test_backtest_does_not_peek_at_the_test_months():
    y = np.arange(1, 25, dtype=float)
    rows = {r["model"]: r for r in backtest(y, 6)}
    assert rows["naive"]["forecast"] == [18] * 6  # last training value, not a test value
