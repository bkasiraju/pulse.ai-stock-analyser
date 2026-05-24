"""
Stock analyser: scores candidates, generates SWOT, produces ranked list.
"""

import json
import time
from pathlib import Path
from datetime import datetime

from .screener import fetch_nse_stock_data, SEED_STOCKS


def score_stock(stock_data, config):
    """Score a stock on 0-100 based on multi-bagger potential."""
    weights = config["scoring"]
    score = 0
    reasons = []

    # Revenue Growth (0-20)
    rg = stock_data.get("revenue_growth")
    if rg is not None:
        if rg > 0.30:
            s = weights["revenue_growth_weight"]
            reasons.append(f"Strong revenue growth: {rg*100:.0f}%")
        elif rg > 0.15:
            s = weights["revenue_growth_weight"] * 0.7
            reasons.append(f"Good revenue growth: {rg*100:.0f}%")
        elif rg > 0:
            s = weights["revenue_growth_weight"] * 0.4
        else:
            s = 0
            reasons.append(f"Negative revenue growth: {rg*100:.0f}%")
        score += s

    # Earnings Growth (0-20)
    eg = stock_data.get("earnings_growth")
    if eg is not None:
        if eg > 0.40:
            s = weights["profit_growth_weight"]
            reasons.append(f"Explosive earnings growth: {eg*100:.0f}%")
        elif eg > 0.20:
            s = weights["profit_growth_weight"] * 0.7
            reasons.append(f"Strong earnings growth: {eg*100:.0f}%")
        elif eg > 0:
            s = weights["profit_growth_weight"] * 0.4
        else:
            s = 0
        score += s

    # Promoter Holding (0-15)
    ph = stock_data.get("promoter_holding")
    if ph is not None:
        if ph > 0.60:
            s = weights["promoter_holding_weight"]
            reasons.append(f"High promoter holding: {ph*100:.0f}%")
        elif ph > 0.40:
            s = weights["promoter_holding_weight"] * 0.7
        else:
            s = weights["promoter_holding_weight"] * 0.3
        score += s

    # Debt to Equity (0-15, lower is better)
    de = stock_data.get("debt_to_equity")
    if de is not None:
        if de < 30:
            s = weights["debt_equity_weight"]
            reasons.append("Very low debt")
        elif de < 80:
            s = weights["debt_equity_weight"] * 0.7
            reasons.append("Manageable debt levels")
        elif de < 150:
            s = weights["debt_equity_weight"] * 0.3
        else:
            s = 0
            reasons.append(f"High debt/equity: {de:.0f}")
        score += s

    # ROE (0-10)
    roe = stock_data.get("roe")
    if roe is not None:
        if roe > 0.20:
            s = weights["roe_weight"]
            reasons.append(f"Excellent ROE: {roe*100:.0f}%")
        elif roe > 0.12:
            s = weights["roe_weight"] * 0.6
        else:
            s = weights["roe_weight"] * 0.2
        score += s

    # Momentum — distance from 52w low (0-10)
    price = stock_data.get("price", 0)
    low = stock_data.get("52w_low", 0)
    high = stock_data.get("52w_high", 0)
    if high and low and price:
        range_pct = (price - low) / (high - low) if (high - low) > 0 else 0
        if 0.3 < range_pct < 0.7:
            s = weights["momentum_weight"]
            reasons.append("Good momentum position (mid-range)")
        elif range_pct <= 0.3:
            s = weights["momentum_weight"] * 0.8
            reasons.append("Near 52w low — possible turnaround")
        else:
            s = weights["momentum_weight"] * 0.4
        score += s

    # Market cap bonus for small/penny (higher risk-reward)
    mc = stock_data.get("market_cap_cr", 0)
    if mc < 500:
        score += 5
        reasons.append("Micro-cap: high risk-reward potential")
    elif mc < 2000:
        score += 3

    return round(score, 1), reasons


def generate_swot(stock_data):
    """Generate SWOT analysis from available data."""
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    # Strengths
    if stock_data.get("revenue_growth") and stock_data["revenue_growth"] > 0.15:
        strengths.append(f"Revenue growing at {stock_data['revenue_growth']*100:.0f}% — above industry average")
    if stock_data.get("roe") and stock_data["roe"] > 0.15:
        strengths.append(f"High Return on Equity ({stock_data['roe']*100:.0f}%) indicates efficient capital use")
    if stock_data.get("promoter_holding") and stock_data["promoter_holding"] > 0.50:
        strengths.append(f"Strong promoter confidence — {stock_data['promoter_holding']*100:.0f}% holding")
    if stock_data.get("debt_to_equity") and stock_data["debt_to_equity"] < 50:
        strengths.append("Low leverage — financial flexibility for growth")
    if stock_data.get("free_cashflow") and stock_data["free_cashflow"] > 0:
        strengths.append("Positive free cash flow — self-funding growth")

    # Weaknesses
    de = stock_data.get("debt_to_equity")
    pe = stock_data.get("pe_ratio")
    roe = stock_data.get("roe")
    eg = stock_data.get("earnings_growth")
    rg = stock_data.get("revenue_growth")
    ph = stock_data.get("promoter_holding")
    vol = stock_data.get("avg_volume")
    fcf = stock_data.get("free_cashflow")

    if de and de > 100:
        weaknesses.append(f"High debt/equity ({de:.0f}) — interest burden risk")
    elif de and de > 50:
        weaknesses.append(f"Moderate leverage (D/E: {de:.0f}) — limits financial flexibility")
    if roe is not None and roe < 0.08:
        weaknesses.append(f"Low ROE ({roe*100:.1f}%) — poor capital efficiency")
    elif roe is not None and roe < 0.12:
        weaknesses.append(f"Below-average ROE ({roe*100:.1f}%) — room for improvement")
    if pe and pe > 60:
        weaknesses.append(f"Expensive valuation (PE: {pe:.1f}) — priced for perfection")
    elif pe and pe > 35:
        weaknesses.append(f"Rich valuation (PE: {pe:.1f}) — growth must sustain to justify")
    if vol and vol < 100000:
        weaknesses.append(f"Low trading volume ({vol:,.0f}/day) — hard to exit large positions")
    elif vol and vol < 500000:
        weaknesses.append(f"Moderate liquidity ({vol:,.0f}/day) — large orders may impact price")
    if eg is not None and eg < 0:
        weaknesses.append(f"Declining earnings ({eg*100:.1f}%) — growth thesis at risk")
    elif eg is None or eg == 0:
        weaknesses.append("No visible earnings growth — unclear profitability trajectory")
    if rg is not None and rg < 0.05:
        weaknesses.append(f"Slow revenue growth ({rg*100:.1f}%) — limited top-line momentum")
    if ph is not None and ph < 0.40:
        weaknesses.append(f"Promoter holding only {ph*100:.0f}% — low skin in the game")
    if fcf is not None and fcf < 0:
        weaknesses.append("Negative free cash flow — burning cash, dependent on external funding")
    if not pe and not roe:
        weaknesses.append("Limited financial data available — transparency concern")

    # Opportunities
    mc = stock_data.get("market_cap_cr", 0)
    if mc < 2000:
        opportunities.append("Small-cap with room for institutional discovery")
    if stock_data.get("revenue_growth") and stock_data["revenue_growth"] > 0.20:
        opportunities.append("Rapid revenue growth could attract re-rating")
    price = stock_data.get("price", 0)
    low = stock_data.get("52w_low", 0)
    if price and low and price < low * 1.3:
        opportunities.append("Trading near 52-week low — potential turnaround candidate")
    sector = stock_data.get("sector", "")
    if sector in ["Technology", "Industrials", "Healthcare"]:
        opportunities.append(f"Tailwind sector: {sector} — government/policy support likely")

    # Threats
    if mc < 500:
        threats.append("Micro-cap: susceptible to operator manipulation and pump-dump")
    if stock_data.get("avg_volume") and stock_data["avg_volume"] < 50000:
        threats.append("Very low volume — price can be easily manipulated")
    threats.append("Market-wide correction risk in overheated small/mid-cap space")
    if stock_data.get("debt_to_equity") and stock_data["debt_to_equity"] > 150:
        threats.append("Solvency risk if business cycle turns down")
    if stock_data.get("pe_ratio") and stock_data["pe_ratio"] and stock_data["pe_ratio"] > 80:
        threats.append("Bubble territory valuation — sharp correction possible")

    return {
        "strengths": strengths or ["Insufficient data for strength analysis"],
        "weaknesses": weaknesses or ["Insufficient data for weakness analysis"],
        "opportunities": opportunities or ["Insufficient data for opportunity analysis"],
        "threats": threats,
    }


def classify_stock(stock_data, config):
    """Classify as penny/small/mid based on config thresholds."""
    price = stock_data.get("price", 0)
    mc = stock_data.get("market_cap_cr", 0)

    if price <= config["market"]["penny_max_price"]:
        return "penny"
    elif mc <= config["market"]["small_cap_max_cr"]:
        return "small_cap"
    elif mc <= config["market"]["mid_cap_max_cr"]:
        return "mid_cap"
    return "large_cap"


def analyse_stocks(config, symbols=None):
    """Run full analysis on candidate stocks."""
    if symbols is None:
        symbols = SEED_STOCKS

    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{total}] Analysing {symbol}...")
        data = fetch_nse_stock_data(symbol)
        if not data:
            continue

        # Filter by config
        classification = classify_stock(data, config)
        if classification == "large_cap":
            continue

        score, reasons = score_stock(data, config)
        swot = generate_swot(data)

        results.append({
            "symbol": symbol,
            "name": data["name"],
            "price": data["price"],
            "market_cap_cr": data["market_cap_cr"],
            "classification": classification,
            "sector": data["sector"],
            "industry": data["industry"],
            "score": score,
            "score_reasons": reasons,
            "swot": swot,
            "fundamentals": {
                "pe_ratio": data.get("pe_ratio"),
                "pb_ratio": data.get("pb_ratio"),
                "roe": data.get("roe"),
                "debt_to_equity": data.get("debt_to_equity"),
                "revenue_growth": data.get("revenue_growth"),
                "earnings_growth": data.get("earnings_growth"),
                "promoter_holding": data.get("promoter_holding"),
                "eps": data.get("eps"),
                "book_value": data.get("book_value"),
                "dividend_yield": data.get("dividend_yield"),
                "free_cashflow": data.get("free_cashflow"),
            },
            "technicals": {
                "52w_high": data.get("52w_high"),
                "52w_low": data.get("52w_low"),
                "avg_volume": data.get("avg_volume"),
            },
            "analysed_at": datetime.now().isoformat(),
        })

        time.sleep(0.5)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:config["analysis"]["top_n"]]
