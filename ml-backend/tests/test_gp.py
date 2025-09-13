import os
import sys
import numpy as np
import pandas as pd
import pytest

# --- Ensure goal_planner.py (one directory above) is importable ---
# Get absolute path to the parent directory of this tests folder
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import goal_planner as gp  # noqa: E402  # import after sys.path fix


def test_compute_metrics_shapes_and_values():
    """compute_metrics should return correct shapes and sensible values on small data."""
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    prices = pd.DataFrame({
        "A": [100, 101, 102, 103, 104, 105],
        "B": [50, 50.5, 51, 51.5, 52, 52.5],
        "C": [200, 198, 199, 201, 202, 204],
    }, index=dates)

    mu, vol, cov, rets = gp.compute_metrics(prices)

    assert isinstance(mu, pd.Series)
    assert isinstance(vol, np.ndarray)
    assert isinstance(cov, pd.DataFrame)
    assert mu.index.tolist() == ["A", "B", "C"]
    assert cov.shape == (3, 3)
    assert rets.shape[1] == 3
    assert np.isfinite(mu).all()
    assert np.isfinite(vol).all()
    assert np.isfinite(cov.values).all()


def test_rank_candidates_prefers_higher_sharpe():
    """rank_candidates should put higher expected return assets first if vol is equal."""
    mu = pd.Series({"A": 0.2, "B": 0.1, "C": 0.05})
    vol = np.array([0.1, 0.1, 0.1])

    top = gp.rank_candidates(mu, vol, risk="aggressive", max_candidates=2)
    assert top[0] == "A"
    assert len(top) == 2


def test_optimize_portfolio_returns_valid_weights():
    """optimize_portfolio should return weights summing to ~1 and finite metrics."""
    mu = pd.Series({"A": 0.15, "B": 0.1})
    cov = pd.DataFrame(
        [[0.04, 0.01],
         [0.01, 0.03]],
        index=["A", "B"], columns=["A", "B"]
    )

    weights, exp_ret, exp_vol = gp.optimize_portfolio(
        mu, cov, risk="balanced", max_assets=2, tries=500, seed=42
    )

    assert pytest.approx(weights.sum(), rel=1e-2) == 1.0
    assert np.isfinite(exp_ret)
    assert np.isfinite(exp_vol)


def test_simulate_goal_distribution_monotonicity():
    """simulate_goal should return a distribution of outcomes and portfolio stats."""
    weights = pd.Series({"A": 0.6, "B": 0.4})
    mu = pd.Series({"A": 0.12, "B": 0.08})
    cov = pd.DataFrame(
        [[0.04, 0.01],
         [0.01, 0.03]],
        index=["A", "B"], columns=["A", "B"]
    )

    outcomes, mu_port, vol_port = gp.simulate_goal(
        weights, mu, cov,
        years=1, start_capital=1000, monthly_contrib=100,
        runs=200, seed=123
    )

    assert len(outcomes) == 200
    assert np.isfinite(outcomes).all()
    assert np.isfinite(mu_port)
    assert np.isfinite(vol_port)
