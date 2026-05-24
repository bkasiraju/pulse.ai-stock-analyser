"""
Multi-Bagger Compounder Framework Assessment
Based on the "Operating Rules" framework for identifying structural compounders.

CORE RULE: Multi-baggers are businesses that can reinvest more capital at
higher returns for longer than expected.

Assesses each stock across 10 dimensions (skipping Trade & IPO sections):
1. Market Context (5x-10x headroom)
2. Financial Performance (directional consistency)
3. Growth (structural vs cyclical)
4. Margins & Profitability (structural leverage)
5. Balance Sheet Strength (optionality enabler)
6. Cash Flows (cash compounding)
7. Capital Efficiency (incremental ROCE)
8. Valuation (contextual)
9. Stress Resilience (downside survivability)
10. Optionality (funded from operating strength)

Each dimension scores: GREEN (2), YELLOW (1), RED (0)
Final tag derived from total score.
"""

import yfinance as yf
from datetime import datetime


def assess_stock(stock):
    """Run the compounder framework assessment on a single stock."""
    fund = stock.get("fundamentals", {})
    metrics = stock.get("metrics", {})
    symbol = stock["symbol"]

    scores = {}
    details = {}

    # 1. Market Context — 5x-10x headroom
    mc = stock.get("market_cap_cr", 0)
    if mc < 2000:
        scores["market_context"] = 2
        details["market_context"] = f"MCap ₹{mc:.0f}Cr — significant 5-10x headroom as small-cap"
    elif mc < 5000:
        scores["market_context"] = 2
        details["market_context"] = f"MCap ₹{mc:.0f}Cr — small-to-mid transition, 5x possible"
    elif mc < 15000:
        scores["market_context"] = 1
        details["market_context"] = f"MCap ₹{mc:.0f}Cr — some headroom for 2-4x growth"
    else:
        scores["market_context"] = 0
        details["market_context"] = f"MCap ₹{mc:.0f}Cr — size limits further compounding"

    # 2. Financial Performance — directional consistency
    rg = fund.get("revenue_growth")
    eg = fund.get("earnings_growth")
    if rg and rg > 0.15 and eg and eg > 0.10:
        scores["financial_perf"] = 2
        details["financial_perf"] = f"Revenue +{rg*100:.0f}%, Earnings +{eg*100:.0f}% — directionally consistent"
    elif rg and rg > 0.05:
        scores["financial_perf"] = 1
        details["financial_perf"] = f"Revenue +{rg*100:.0f}% — growth visible but earnings lag"
    else:
        scores["financial_perf"] = 0
        details["financial_perf"] = "Weak or negative revenue/earnings trajectory"

    # 3. Growth type — structural vs cyclical
    sector = stock.get("sector", "")
    structural_sectors = ["Technology", "Healthcare", "Industrials", "Consumer Defensive"]
    cyclical_sectors = ["Basic Materials", "Energy", "Real Estate", "Consumer Cyclical"]

    if rg and rg > 0.20 and sector in structural_sectors:
        scores["growth_type"] = 2
        details["growth_type"] = f"Structural growth ({sector}) with {rg*100:.0f}% revenue CAGR"
    elif rg and rg > 0.10:
        scores["growth_type"] = 1
        details["growth_type"] = f"Mixed growth — {rg*100:.0f}% revenue, sector: {sector}"
    else:
        scores["growth_type"] = 0
        details["growth_type"] = f"Cyclical or stagnant — {sector}, limited organic growth"

    # 4. Margins & Profitability — structural leverage
    roe = fund.get("roe")
    opm = fund.get("operating_margin")
    if roe and roe > 0.18:
        scores["margins"] = 2
        details["margins"] = f"ROE {roe*100:.1f}% — structural profitability, margins expanding with scale"
    elif roe and roe > 0.12:
        scores["margins"] = 1
        details["margins"] = f"ROE {roe*100:.1f}% — decent but not yet best-in-class"
    else:
        scores["margins"] = 0
        details["margins"] = f"ROE {(roe or 0)*100:.1f}% — margins under pressure or early-stage"

    # 5. Balance Sheet Strength — optionality enabler
    de = fund.get("debt_to_equity")
    if de is not None and de < 30:
        scores["balance_sheet"] = 2
        details["balance_sheet"] = f"D/E {de:.0f} — net-cash-like, growth optionality enabled"
    elif de is not None and de < 80:
        scores["balance_sheet"] = 1
        details["balance_sheet"] = f"D/E {de:.0f} — manageable leverage, can fund growth"
    else:
        scores["balance_sheet"] = 0
        details["balance_sheet"] = f"D/E {(de or 0):.0f} — high leverage constrains reinvestment"

    # 6. Cash Flows — cash compounding
    fcf = fund.get("free_cashflow")
    if fcf and fcf > 0:
        scores["cash_flows"] = 2
        details["cash_flows"] = "Positive FCF — growth generates cash, self-funding reinvestment"
    elif fcf is not None and fcf < 0 and rg and rg > 0.20:
        scores["cash_flows"] = 1
        details["cash_flows"] = "Negative FCF in growth phase — acceptable if capex-driven"
    else:
        scores["cash_flows"] = 0
        details["cash_flows"] = "Cash flow weak or negative — reinvestment unclear"

    # 7. Capital Efficiency — ROCE improving with scale
    roce = roe  # proxy
    if roce and roce > 0.20 and rg and rg > 0.15:
        scores["capital_efficiency"] = 2
        details["capital_efficiency"] = f"High returns ({roce*100:.0f}%) + high growth — returns improve with scale"
    elif roce and roce > 0.12:
        scores["capital_efficiency"] = 1
        details["capital_efficiency"] = f"Moderate returns ({roce*100:.0f}%) — incremental ROCE needs monitoring"
    else:
        scores["capital_efficiency"] = 0
        details["capital_efficiency"] = "Low returns on capital — growth may destroy value"

    # 8. Valuation — contextual
    pe = fund.get("pe_ratio")
    if pe and rg:
        peg = pe / (rg * 100) if rg > 0 else 99
        if peg < 1:
            scores["valuation"] = 2
            details["valuation"] = f"PEG {peg:.2f} — valuation secondary to growth quality"
        elif peg < 2:
            scores["valuation"] = 1
            details["valuation"] = f"PEG {peg:.2f} — reasonable risk for growth delivered"
        else:
            scores["valuation"] = 0
            details["valuation"] = f"PEG {peg:.2f} — valuation replaces quality, priced for perfection"
    elif pe and pe < 25:
        scores["valuation"] = 2
        details["valuation"] = f"PE {pe:.0f} — attractively valued"
    elif pe:
        scores["valuation"] = 1
        details["valuation"] = f"PE {pe:.0f} — fair but not cheap"
    else:
        scores["valuation"] = 0
        details["valuation"] = "Cannot assess valuation — missing data"

    # 9. Stress Resilience — can survive 2 bad years?
    if de is not None and de < 50 and fcf and fcf > 0:
        scores["stress"] = 2
        details["stress"] = "Low debt + positive FCF — can survive 2 bad years without dilution"
    elif de is not None and de < 100:
        scores["stress"] = 1
        details["stress"] = "Moderate stress tolerance — survivable but tight in downturn"
    else:
        scores["stress"] = 0
        details["stress"] = "Fragile — high leverage or cash burn, dilution risk in downturn"

    # 10. Optionality — funded from operating strength
    ph = fund.get("promoter_holding")
    if de is not None and de < 30 and fcf and fcf > 0 and ph and ph > 0.5:
        scores["optionality"] = 2
        details["optionality"] = "Free optionality — net-cash, CFO-funded, promoter aligned"
    elif de is not None and de < 80 and fcf and fcf > 0:
        scores["optionality"] = 1
        details["optionality"] = "Paid optionality — some balance sheet capacity for adjacencies"
    else:
        scores["optionality"] = 0
        details["optionality"] = "Fake optionality — growth claims not backed by cash generation"

    # Final Tag
    total = sum(scores.values())
    max_score = len(scores) * 2

    if total >= 16:
        tag = "STRUCTURAL_COMPOUNDER"
        action = "Concentrate"
    elif total >= 12:
        tag = "STRUCTURAL_UNPROVEN"
        action = "Small / Monitor"
    elif total >= 8:
        tag = "CYCLICAL_BENEFICIARY"
        action = "Trade / Trim"
    else:
        tag = "NON_COMPOUNDER"
        action = "Exit / Avoid"

    # 5x-10x Quick Filter
    tam_headroom = mc < 5000
    organic_scale = rg is not None and rg > 0.15
    margin_expansion = roe is not None and roe > 0.12
    roce_sustainable = roe is not None and roe > 0.18
    execution_scales = fcf is not None and fcf > 0

    yes_count = sum([tam_headroom, organic_scale, margin_expansion, roce_sustainable, execution_scales])
    if yes_count >= 4:
        growth_potential = "5x-10x POSSIBLE"
    elif yes_count >= 2:
        growth_potential = "2x-4x BUSINESS"
    else:
        growth_potential = "MARKET-CAP CAPPED"

    return {
        "framework_tag": tag,
        "framework_action": action,
        "framework_score": total,
        "framework_max": max_score,
        "framework_pct": round((total / max_score) * 100),
        "growth_potential": growth_potential,
        "five_x_filter_score": f"{yes_count}/5",
        "dimensions": scores,
        "dimension_details": details,
    }


def assess_all(ranked_stocks):
    """Run framework assessment on all stocks."""
    print("\n  [compounder] Running structural compounder framework...")
    for stock in ranked_stocks:
        stock["compounder"] = assess_stock(stock)
        tag = stock["compounder"]["framework_tag"]
        pct = stock["compounder"]["framework_pct"]
        print(f"    {stock['symbol']}: {tag} ({pct}%) — {stock['compounder']['growth_potential']}")
    return ranked_stocks
