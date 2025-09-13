#!/usr/bin/env python3
"""
Goal-based Investment Planner
-----------------------------
Can be run either:
  1. As a CLI script (python goal_planner.py --goal ...)
  2. As a Python module (import run_plan) e.g. from FastAPI.

It downloads market data, computes risk/return metrics, optimises a portfolio,
and runs a Monte Carlo to estimate probability of reaching the investment goal.

⚠️ This version focuses on **immediate purchase planning**:
    - All recommended stock allocations and share counts
      are based **only on the starting capital** you invest today.
    - Monthly contributions are still included in Monte Carlo growth projections,
      but do not affect the buy-list calculation.
"""

import argparse
import sys
import math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Please install yfinance: pip install yfinance", file=sys.stderr)
    sys.exit(1)


# ================================================================
# Static universe helpers
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

def build_universe(include_sp500=True, include_ftse100=True, include_nasdaq100=True) -> list[str]:
    tickers: list[str] = []
    if include_sp500: tickers += get_sp500_tickers()
    if include_ftse100: tickers += get_ftse100_tickers()
    if include_nasdaq100: tickers += get_nasdaq100_tickers()
    seen, deduped = set(), []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


# ================================================================
# Data & metrics
# ================================================================
def download_prices(tickers: list[str], years: int = 5) -> pd.DataFrame:
    if not tickers:
        raise ValueError("No tickers to download.")
    start = datetime.utcnow() - timedelta(days=int(365.25 * years))
    frames: list[pd.Series] = []

    for t in tickers:
        try:
            print(f"Downloading {t} …")
            df = yf.download(t, start=start.strftime("%Y-%m-%d"),
                             progress=False, auto_adjust=True, threads=False)
            if df.empty:
                continue
            series = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]
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
    rets = np.log(prices / prices.shift(1)).dropna(how="all")
    mu_daily = rets.mean()
    cov_daily = rets.cov()
    TRADING_DAYS = 252
    mu_annual = mu_daily * TRADING_DAYS
    vol_annual = np.sqrt(np.diag(cov_daily)) * np.sqrt(TRADING_DAYS)
    cov_annual = cov_daily * TRADING_DAYS
    return mu_annual, vol_annual, cov_annual

def rank_candidates(mu: pd.Series, vol: np.ndarray, risk: str, max_candidates: int = 25) -> list[str]:
    vol = pd.Series(vol, index=mu.index)
    sharpe = mu / (vol.replace(0, np.nan))
    if risk == "conservative":
        score = 0.6 * sharpe + 0.4 * (-vol)
    elif risk == "balanced":
        score = 0.8 * sharpe + 0.2 * (-vol)
    else:
        score = sharpe
    return score.replace([np.inf, -np.inf], np.nan).fillna(-1e9)\
                .sort_values(ascending=False).head(max_candidates).index.tolist()


# ================================================================
# Optimisation & simulation
# ================================================================
def target_vol_for_risk(risk: str) -> float:
    return {"conservative": 0.10, "balanced": 0.18, "aggressive": 0.28}.get(risk, 0.18)

def risk_penalty_for_risk(risk: str) -> float:
    return {"conservative": 10.0, "balanced": 6.0, "aggressive": 3.0}.get(risk, 6.0)

def optimize_portfolio(mu: pd.Series, cov: pd.DataFrame, risk: str,
                       max_assets: int = 10, tries: int = 15000, seed: int | None = None):
    rng = np.random.default_rng(seed)
    assets = mu.index.tolist()[:max_assets]
    mu_vec = mu.loc[assets].values
    cov_mat = cov.loc[assets, assets].values
    tgt_vol = target_vol_for_risk(risk)
    penalty = risk_penalty_for_risk(risk)
    best, best_score = None, np.inf

    for _ in range(tries):
        w = rng.random(len(assets))
        w /= w.sum()
        exp_ret = float(w @ mu_vec)
        vol = float(np.sqrt(w @ cov_mat @ w))
        score = -exp_ret + penalty * abs(vol - tgt_vol)
        if score < best_score:
            best_score, best = score, (w, exp_ret, vol)

    if not best:
        raise RuntimeError("Optimization failed.")
    w_opt, exp_ret_opt, vol_opt = best
    return pd.Series(w_opt, index=assets), exp_ret_opt, vol_opt

def simulate_goal(weights: pd.Series, mu: pd.Series, cov: pd.DataFrame,
                  years: int, start_capital: float, monthly_contrib: float,
                  runs: int = 10000, seed: int | None = None):
    """
    Monte Carlo simulation of portfolio growth, still including
    monthly contributions for final-value forecasts.
    """
    rng = np.random.default_rng(seed)
    months = years * 12
    mu_port = float(weights @ mu.loc[weights.index])
    cov_port = float(weights @ cov.loc[weights.index, weights.index] @ weights)
    mu_m, vol_m = mu_port / 12.0, math.sqrt(cov_port) / math.sqrt(12.0)
    outcomes = np.zeros(runs)
    for i in range(runs):
        v = start_capital
        for _ in range(months):
            v *= 1.0 + rng.normal(mu_m, vol_m)
            v += monthly_contrib
        outcomes[i] = v
    return outcomes, mu_port, math.sqrt(cov_port)


# ================================================================
# New reusable entry point for FastAPI or CLI
# ================================================================
def run_plan(goal: float, years: int, risk: str,
             start_capital: float, monthly_contrib: float,
             lookback_years: int = 5,
             max_candidates: int = 25,
             max_assets: int = 10,
             tries: int = 15000,
             seed: int | None = None) -> dict:
    """
    Core function to compute an investment plan with enriched output
    for immediate purchase allocations.
    """
    # Ensure start_capital is a valid float
    start_capital = float(start_capital or 0.0)

    tickers = build_universe()
    prices = download_prices(tickers, years=lookback_years)
    mu, vol, cov = compute_metrics(prices)
    valid = mu.dropna().index.intersection(prices.columns)
    mu, cov, prices = mu.loc[valid], cov.loc[valid, valid], prices[valid]

    top = rank_candidates(mu, np.sqrt(np.diag(cov)), risk, max_candidates=max_candidates)
    mu_top, cov_top = mu.loc[top], cov.loc[top, top]

    weights, exp_ret, exp_vol = optimize_portfolio(
        mu_top, cov_top, risk, max_assets=max_assets, tries=tries, seed=seed
    )

    outcomes, mu_port, vol_port = simulate_goal(
        weights, mu, cov, years, start_capital, monthly_contrib,
        runs=10000, seed=seed
    )

    p5, p50, p95 = np.percentile(outcomes, [5, 50, 95])
    prob = float((outcomes >= goal).mean())

    # Immediate purchase allocations (only start_capital)
    enriched_weights = []
    for t, w in weights.items():
        try:
            info = yf.Ticker(t).info
            company_name = info.get("longName", t)
        except Exception:
            company_name = t

        # Handle missing or empty price series gracefully
        if prices[t].dropna().empty:
            current_price = 0.0
        else:
            current_price = float(prices[t].iloc[-1])

        # Compute allocation and shares safely
        initial_allocation_gbp = float(w * start_capital) if start_capital > 0 else 0.0
        shares_to_buy = (
            float(initial_allocation_gbp / current_price)
            if current_price > 0 and initial_allocation_gbp > 0
            else 0.0
        )

        enriched_weights.append({
            "ticker": t,
            "company_name": company_name,
            "weight": float(w),
            "current_price": current_price,
            "initial_allocation_gbp": initial_allocation_gbp,
            "shares_to_buy": shares_to_buy
        })

    return {
        "weights": enriched_weights,
        "expected_return": float(mu_port),
        "volatility": float(vol_port),
        "prob_reach_goal": prob,
        "expected_final_value": float(p50),
        "low_estimate": float(p5),
        "high_estimate": float(p95),
        "initial_capital": start_capital
    }


# ================================================================
# CLI entry point
# ================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--goal", type=float, required=True)
    p.add_argument("--years", type=int, required=True)
    p.add_argument("--risk", type=str, default="balanced",
                   choices=["conservative", "balanced", "aggressive"])
    p.add_argument("--start-capital", type=float, default=0.0)
    p.add_argument("--monthly-contrib", type=float, default=0.0)
    args = p.parse_args()

    result = run_plan(args.goal, args.years, args.risk,
                      args.start_capital, args.monthly_contrib)

    print("\n=== Goal-based Investment Plan ===")
    print(f"Expected return : {result['expected_return']*100:5.2f}%")
    print(f"Volatility      : {result['volatility']*100:5.2f}%")
    print(f"Prob reach goal : {result['prob_reach_goal']*100:5.1f}%")
    print(f"Median final value : £{result['expected_final_value']:,.0f}")
    print("\nImmediate purchase allocations (from starting capital only):")
    for w in result["weights"]:
        print(f"{w['ticker']:<8} {w['company_name']:<30} "
              f"{w['weight']*100:5.1f}%  £{w['initial_allocation_gbp']:,.0f}  ~{w['shares_to_buy']:.1f} shares")

if __name__ == "__main__":
    main()
