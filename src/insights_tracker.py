"""
Pulse.AI Insights Tracker: Captures daily performance of recommended stocks
to validate multi-bagger potential over time.

Produces a time-series dataset showing:
- Daily closing price
- Daily return %
- Cumulative return from recommendation date
- Whether the stock is on track for multi-bagger status
"""

import yfinance as yf
import json
from pathlib import Path
from datetime import datetime, timedelta


INSIGHTS_FILE = Path(__file__).parent.parent / "docs" / "insights.json"


def fetch_stock_timeseries(symbol, days=180):
    """Fetch daily OHLCV for a stock over N days."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=f"{days}d")
        if hist.empty:
            ticker = yf.Ticker(f"{symbol}.BO")
            hist = ticker.history(period=f"{days}d")
        if hist.empty:
            return None

        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })
        return data
    except Exception:
        return None


def compute_returns(timeseries):
    """Compute daily and cumulative returns from time-series data."""
    if not timeseries or len(timeseries) < 2:
        return timeseries

    base_price = timeseries[0]["close"]
    prev_close = base_price

    for point in timeseries:
        daily_return = ((point["close"] - prev_close) / prev_close) * 100 if prev_close else 0
        cumulative_return = ((point["close"] - base_price) / base_price) * 100
        point["daily_return_pct"] = round(daily_return, 2)
        point["cumulative_return_pct"] = round(cumulative_return, 2)
        prev_close = point["close"]

    return timeseries


def assess_multibagger_trajectory(timeseries, months=6):
    """Assess if stock is on multi-bagger trajectory."""
    if not timeseries or len(timeseries) < 20:
        return {"verdict": "INSUFFICIENT_DATA", "annualized_return": None}

    base = timeseries[0]["close"]
    current = timeseries[-1]["close"]
    total_return = ((current - base) / base) * 100
    trading_days = len(timeseries)
    annualized = (total_return / trading_days) * 252 if trading_days > 0 else 0

    if annualized >= 100:
        verdict = "STRONG_MULTIBAGGER"
    elif annualized >= 50:
        verdict = "ON_TRACK"
    elif annualized >= 20:
        verdict = "MODERATE_GROWTH"
    elif annualized >= 0:
        verdict = "FLAT"
    else:
        verdict = "UNDERPERFORMING"

    max_price = max(p["close"] for p in timeseries)
    drawdown_from_peak = ((current - max_price) / max_price) * 100

    return {
        "verdict": verdict,
        "total_return_pct": round(total_return, 2),
        "annualized_return_pct": round(annualized, 1),
        "drawdown_from_peak_pct": round(drawdown_from_peak, 2),
        "trading_days": trading_days,
        "base_price": base,
        "current_price": current,
    }


def generate_insights(recommended_stocks):
    """Generate insights data for all recommended stocks."""
    print("\n  [insights] Generating Pulse.AI Insights time-series data...")
    insights = {
        "generated_at": datetime.now().isoformat(),
        "stocks": [],
    }

    for stock in recommended_stocks:
        symbol = stock["symbol"]
        print(f"    {symbol}: fetching 180-day history...")

        timeseries = fetch_stock_timeseries(symbol, days=180)
        if not timeseries:
            print(f"    {symbol}: no data available")
            continue

        timeseries = compute_returns(timeseries)
        assessment = assess_multibagger_trajectory(timeseries)

        insights["stocks"].append({
            "symbol": symbol,
            "name": stock.get("name", symbol),
            "classification": stock.get("classification", "unknown"),
            "conviction_level": stock.get("conviction_level", "N/A"),
            "pulse_score": stock.get("score"),
            "da_score": stock.get("adjusted_score"),
            "timeseries": timeseries,
            "assessment": assessment,
        })

        print(f"    {symbol}: {assessment['verdict']} ({assessment.get('total_return_pct', 0)}% / {assessment.get('annualized_return_pct', 0)}% ann.)")

    with open(INSIGHTS_FILE, "w") as f:
        json.dump(insights, f, indent=2, default=str)
    print(f"  [insights] Saved to {INSIGHTS_FILE}")

    return insights
