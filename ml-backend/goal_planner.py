#!/usr/bin/env python3
"""
Goal-based Investment Planner
-----------------------------
This script builds an investment plan to help a user reach a savings goal within a time frame
by optimising a portfolio of global stocks and indices.

Main steps:
1. Build a static universe of stocks (S&P500, NASDAQ100, FTSE100).
2. Download historical price data with yfinance.
3. Compute annualised expected returns, volatilities and covariance matrix.
4. Rank candidates by risk adjusted return.
5. Optimise portfolio weights using random search to meet a target volatility.
6. Simulate wealth growth using Monte Carlo to estimate probability of reaching the goal.
"""

import argparse
import sys
import math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# ---------------------------
# External dependency
# ---------------------------
# requires yfinance for live market data
try:
    import yfinance as yf
except ImportError:
    print("Please install yfinance: pip install yfinance", file=sys.stderr)
    sys.exit(1)


# ================================================================
# Static Stock Symbols
# ================================================================

def get_sp500_tickers() -> list[str]:
    return [
        "AAPL","MSFT","AMZN","GOOGL","GOOG","META","NVDA","TSLA","BRK-B","UNH","JNJ","V","PG",
        "XOM","JPM","MA","HD","CVX","LLY","ABBV","PEP","KO","MRK","PFE","BAC","AVGO","COST",
        "WMT","MCD","DIS","ADBE","CSCO","ACN","TMO","NFLX","TXN","ABT","CMCSA","VZ","ORCL",
        "CRM","INTC","AMD","QCOM","HON","LOW","LIN","AMT","CAT","NKE","UPS"
    ]

def get_nasdaq100_tickers() -> list[str]:
    return [
        "AAPL","MSFT","AMZN","NVDA","GOOG","GOOGL","META","TSLA","PEP","AVGO","COST","ADBE",
        "NFLX","INTC","CSCO","AMD","TXN","QCOM","AMAT","INTU","ISRG","PYPL","MU","LRCX",
        "ADI","REGN","VRTX","MELI","CRWD","PANW","SHOP","WDAY","MRVL","KLAC","CDNS","SNPS",
        "ORLY","MAR","ADSK","TEAM","ZS"
    ]

def get_ftse100_tickers() -> list[str]:
    return [
        "BP.L","SHEL.L","HSBA.L","ULVR.L","AZN.L","GSK.L","RIO.L","GLEN.L","BATS.L","DGE.L",
        "VOD.L","LLOY.L","BARC.L","RKT.L","IMB.L","NG.L","BT-A.L","RR.L","BA.L","TSCO.L",
        "SPX.L","AAL.L","STAN.L","REL.L","ABF.L","AUTO.L","CNA.L","CCEP.L","SMIN.L","INF.L",
        "SGRO.L","EXPN.L","HIK.L","HLMA.L","JD.L","PRU.L","SSE.L","ENT.L","MNDI.L","LAND.L"
    ]

def build_universe(include_sp500=True, include_ftse100=True, include_nasdaq100=True,
                   include_indices=True, fallback_if_empty=True) -> list[str]:
    """
    Build the full list of symbols to consider.

    Options allow toggling S&P500, NASDAQ100, FTSE100, and broad market indices.
    Deduplicates symbols while preserving order.
    """
    tickers: list[str] = []

    if include_sp500:
        tickers += get_sp500_tickers()
    if include_ftse100:
        tickers += get_ftse100_tickers()
    if include_nasdaq100:
        tickers += get_nasdaq100_tickers()

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    return deduped


# ================================================================
# Data Download and Metric Computation
# ================================================================

def download_prices(tickers: list[str], years: int = 5) -> pd.DataFrame:
    """
    Download historical prices for each symbol individually from Yahoo Finance.

    - Uses close prices
    - Forward fills any missing data and drops assets with no usable data.

    Args:
        tickers: list of symbols to download
        years: number of years of lookback history

    Returns:
        DataFrame of daily prices with one column per ticker.
    """
    if not tickers:
        raise ValueError("No tickers to download.")

    start = datetime.utcnow() - timedelta(days=int(365.25 * years))
    frames: list[pd.Series] = []

    for t in tickers:
        try:
            print(f"Downloading {t} …")
            df = yf.download(
                t,
                start=start.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
                threads=False
            )

            if df.empty:
                print(f"Warning: {t} returned no data")
                continue

            # Use adjusted close if available, else regular close
            if "Adj Close" in df.columns:
                series = df["Adj Close"].copy()
            elif "Close" in df.columns:
                series = df["Close"].copy()
            else:
                print(f"Warning: {t} has neither Adj Close nor Close column")
                continue

            series.name = t
            frames.append(series)

        except Exception as e:
            print(f"Warning: {t} failed: {e}")

    if not frames:
        raise RuntimeError("Failed to retrieve prices for any tickers.")

    prices = pd.concat(frames, axis=1).ffill().dropna(how="all", axis=1)
    if prices.empty:
        raise RuntimeError("No valid prices found after filtering.")
    return prices


def compute_metrics(prices: pd.DataFrame):
    """
    Compute annualised expected returns, volatilities and covariance matrix
    from daily log returns.

    Returns:
        mu_annual: expected annual return per asset
        vol_annual: annualised volatility per asset
        cov_annual: annualised covariance matrix
        rets: daily log returns DataFrame
    """
    rets = np.log(prices / prices.shift(1)).dropna(how="all")
    rets = rets.dropna(axis=1, how="all")
    mu_daily = rets.mean()
    cov_daily = rets.cov()
    TRADING_DAYS = 252
    mu_annual = mu_daily * TRADING_DAYS
    vol_annual = np.sqrt(np.diag(cov_daily)) * np.sqrt(TRADING_DAYS)
    cov_annual = cov_daily * TRADING_DAYS
    return mu_annual, vol_annual, cov_annual, rets


def rank_candidates(mu: pd.Series, vol: np.ndarray, risk: str, max_candidates: int = 25) -> list[str]:
    """
    Rank assets by risk adjusted performance
    with weighting depending on user risk tolerance.

    Args:
        mu: expected annual returns
        vol: annualised volatilities
        risk: conservative / balanced / aggressive
        max_candidates: limit to top-N candidates
    """
    vol = pd.Series(vol, index=mu.index)
    sharpe = mu / (vol.replace(0, np.nan))

    if risk == "conservative":
        score = 0.6 * sharpe + 0.4 * (-vol)
    elif risk == "balanced":
        score = 0.8 * sharpe + 0.2 * (-vol)
    else:
        score = sharpe

    score = score.replace([np.inf, -np.inf], np.nan).fillna(-1e9)
    return score.sort_values(ascending=False).head(max_candidates).index.tolist()


# ================================================================
# Portfolio Optimisation and Simulation
# ================================================================

def target_vol_for_risk(risk: str) -> float:
    """Map risk tolerance to target annualised portfolio volatility."""
    return {"conservative": 0.10, "balanced": 0.18, "aggressive": 0.28}.get(risk, 0.18)

def risk_penalty_for_risk(risk: str) -> float:
    """Penalty factor for deviating from target volatility during optimisation."""
    return {"conservative": 10.0, "balanced": 6.0, "aggressive": 3.0}.get(risk, 6.0)


def optimize_portfolio(mu: pd.Series, cov: pd.DataFrame, risk: str,
                       max_assets: int = 10, tries: int = 15000, seed: int | None = None):
    """
    Random search portfolio optimiser.

    - Samples random weight allocations
    - Calculates expected return and volatility
    - Minimises a score = -expected_return + penalty * deviation from target volatility

    Args:
        mu, cov: expected returns and covariance matrix
        risk: user risk level
        max_assets: limit the number of assets in final portfolio
        tries: number of random portfolios to test
        seed: RNG seed for reproducibility
    """
    rng = np.random.default_rng(seed)
    assets = mu.index.tolist()[:max_assets]
    mu_vec = mu.loc[assets].values
    cov_mat = cov.loc[assets, assets].values
    tgt_vol = target_vol_for_risk(risk)
    penalty = risk_penalty_for_risk(risk)

    best = None
    best_score = np.inf
    for _ in range(tries):
        w = rng.random(len(assets))
        w /= w.sum()
        exp_ret = float(w @ mu_vec)
        vol = float(np.sqrt(w @ cov_mat @ w))
        score = -exp_ret + penalty * abs(vol - tgt_vol)
        if score < best_score:
            best_score = score
            best = (w, exp_ret, vol)

    if best is None:
        raise RuntimeError("Optimization failed to find a portfolio.")

    w_opt, exp_ret_opt, vol_opt = best
    return pd.Series(w_opt, index=assets), exp_ret_opt, vol_opt


def simulate_goal(weights: pd.Series, mu: pd.Series, cov: pd.DataFrame,
                  years: int, start_capital: float, monthly_contrib: float,
                  runs: int = 10000, seed: int | None = None):
    """
    Monte Carlo simulation of the goal value after 'years' years.

    - Simulates monthly portfolio returns using normal approximation.
    - Adds monthly contributions.
    - Computes a distribution of final outcomes.

    Returns:
        outcomes: array of ending portfolio values
        mu_port_annual: expected annual return of the portfolio
        vol_port_annual: expected annual volatility of the portfolio
    """
    rng = np.random.default_rng(seed)
    months = years * 12

    mu_port_annual = float(weights @ mu.loc[weights.index])
    cov_port_annual = float(weights @ cov.loc[weights.index, weights.index] @ weights)
    mu_month = mu_port_annual / 12.0
    vol_month = math.sqrt(cov_port_annual) / math.sqrt(12.0)

    outcomes = np.zeros(runs, dtype=float)
    for i in range(runs):
        value = start_capital
        for _ in range(months):
            r = rng.normal(mu_month, vol_month)
            value *= (1.0 + r)
            value += monthly_contrib
        outcomes[i] = value

    return outcomes, mu_port_annual, math.sqrt(cov_port_annual)


# ================================================================
# Main CLI entry point
# ================================================================

def main():
    """
    Command-line entry:
    - Parses user inputs (goal amount, time frame, risk level, etc.)
    - Builds universe, downloads prices, computes metrics
    - Optimises portfolio and simulates wealth distribution
    - Prints a human readable investment plan
    """
    parser = argparse.ArgumentParser(description="Goal-based Investment Planner (auto universe)")
    parser.add_argument("--goal", type=float, required=True, help="Target amount to reach (e.g. 250000)")
    parser.add_argument("--years", type=int, required=True, help="Investment horizon in years (e.g. 5)")
    parser.add_argument("--risk", type=str, default="balanced",
                        choices=["conservative", "balanced", "aggressive"], help="Risk tolerance level")
    parser.add_argument("--start-capital", type=float, default=0.0, help="Initial capital to invest")
    parser.add_argument("--monthly-contrib", type=float, default=0.0, help="Monthly contribution")
    parser.add_argument("--lookback-years", type=int, default=5, help="Historical data window for returns")
    parser.add_argument("--max-candidates", type=int, default=25, help="Number of top assets to consider")
    parser.add_argument("--max-assets", type=int, default=10, help="Max number of assets in the final portfolio")
    parser.add_argument("--tries", type=int, default=15000, help="Random search iterations for optimisation")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--no-ftse", action="store_true", help="Exclude FTSE100 universe")
    parser.add_argument("--no-sp500", action="store_true", help="Exclude S&P500 universe")
    parser.add_argument("--no-nasdaq100", action="store_true", help="Exclude NASDAQ100 universe")
    parser.add_argument("--no-indices", action="store_true", help="Exclude broad market indices")
    args = parser.parse_args()

    # Build universe of symbols based on CLI switches
    tickers = build_universe(
        include_sp500=not args.no_sp500,
        include_ftse100=not args.no_ftse,
        include_nasdaq100=not args.no_nasdaq100,
        include_indices=not args.no_indices,
        fallback_if_empty=True,
    )
    if not tickers:
        print("Failed to build universe.", file=sys.stderr)
        sys.exit(2)

    # Download historical prices
    prices = download_prices(tickers, years=args.lookback_years)
    if prices.shape[1] < 3:
        print("Too few valid assets after downloading data.", file=sys.stderr)
        sys.exit(2)

    # Compute annualised return and risk metrics
    mu, vol, cov, rets = compute_metrics(prices)
    valid = mu.dropna().index.intersection(prices.columns)
    mu = mu.loc[valid]
    cov = cov.loc[valid, valid]

    # Rank assets and keep top candidates
    top = rank_candidates(mu, np.sqrt(np.diag(cov)), args.risk, max_candidates=args.max_candidates)
    mu_top = mu.loc[top]
    cov_top = cov.loc[top, top]

    # Find optimal portfolio weights
    weights, exp_ret, exp_vol = optimize_portfolio(
        mu_top, cov_top, risk=args.risk,
        max_assets=args.max_assets, tries=args.tries, seed=args.seed
    )

    # Simulate goal attainment via Monte Carlo
    outcomes, mu_port_annual, vol_port_annual = simulate_goal(
        weights, mu, cov, args.years, args.start_capital, args.monthly_contrib,
        runs=10000, seed=args.seed
    )

    # Final reporting
    goal = float(args.goal)
    prob = float((outcomes >= goal).mean() * 100.0)
    p5, p50, p95 = np.percentile(outcomes, [5, 50, 95])

    print("\n=== Goal-based Investment Plan ===")
    print(f"Universe size     : {len(prices.columns)} (after cleaning)")
    print(f"Risk              : {args.risk}")
    print(f"Horizon           : {args.years} years")
    print(f"Goal              : £{goal:,.0f}")
    print(f"Start capital     : £{args.start_capital:,.0f}")
    print(f"Monthly contrib   : £{args.monthly_contrib:,.0f}\n")
    print("Recommended weights (sum=1):")
    for t, w in weights.sort_values(ascending=False).items():
        print(f"  {t:<10} {w*100:5.1f}%")
    print("\nPortfolio characteristics (annualized):")
    print(f"  Expected return : {mu_port_annual*100:5.2f}%")
    print(f"  Volatility      : {vol_port_annual*100:5.2f}%\n")
    print("Monte Carlo (ending value distribution):")
    print(f"  Prob reach goal : {prob:5.1f}%")
    print(f"  5th percentile  : £{p5:,.0f}")
    print(f"  Median          : £{p50:,.0f}")
    print(f"  95th percentile : £{p95:,.0f}\n")


if __name__ == "__main__":
    main()
