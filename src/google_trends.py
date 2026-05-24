"""
Google Trends — Retail Interest Detection
==========================================
Detects spikes in retail investor interest by tracking
Google search volume for stock names.

Source: Google Trends (trends.google.com)
Legal: Yes — Google explicitly provides this for public programmatic access.
Library: pytrends (unofficial but widely used, Google-tolerant)
"""

import time
import random

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("[google-trends] pytrends not installed. Run: pip install pytrends")


def fetch_search_interest(symbols, timeframe="today 3-m", geo="IN"):
    """
    Fetch Google Trends interest data for stock symbols.
    Returns dict: {symbol: {current_interest, avg_interest, spike_pct, is_trending}}
    """
    if not PYTRENDS_AVAILABLE:
        return {}

    results = {}

    # Google Trends allows max 5 keywords per request
    chunks = [symbols[i:i+5] for i in range(0, len(symbols), 5)]

    for chunk in chunks:
        try:
            keywords = [f"{sym} share" for sym in chunk]
            pytrends = TrendReq(hl='en-IN', tz=330)
            pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)

            interest = pytrends.interest_over_time()

            if interest.empty:
                continue

            for sym, kw in zip(chunk, keywords):
                if kw not in interest.columns:
                    continue

                series = interest[kw]
                current = series.iloc[-1] if len(series) > 0 else 0
                avg = series.mean()
                recent_avg = series.tail(7).mean() if len(series) >= 7 else current
                older_avg = series.head(30).mean() if len(series) >= 30 else avg

                spike_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

                results[sym] = {
                    "current_interest": int(current),
                    "avg_interest": round(avg, 1),
                    "recent_7d_avg": round(recent_avg, 1),
                    "spike_pct": round(spike_pct, 1),
                    "is_trending": spike_pct > 50,
                    "peak_interest": int(series.max()),
                }

            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"  [google-trends] Error for {chunk}: {e}")
            continue

    return results


def analyse_retail_interest(symbol, trends_data):
    """
    Analyse Google Trends data for a stock.
    Returns: {signal, score_boost, summary, details}
    """
    if not trends_data or symbol not in trends_data:
        return {
            "signal": "NO_DATA",
            "score_boost": 0,
            "summary": "No Google Trends data available",
            "details": [],
        }

    data = trends_data[symbol]
    details = []
    score_boost = 0

    spike = data["spike_pct"]
    current = data["current_interest"]
    peak = data["peak_interest"]

    if data["is_trending"] and spike > 100:
        signal = "VIRAL"
        score_boost = 3
        details.append(
            f"Search interest SURGING +{spike:.0f}% vs 30-day avg. "
            "Retail investors are discovering this stock — could drive near-term momentum."
        )
    elif data["is_trending"]:
        signal = "RISING"
        score_boost = 2
        details.append(
            f"Growing retail interest: +{spike:.0f}% search volume increase. "
            "Stock gaining mindshare among retail investors."
        )
    elif spike < -30:
        signal = "FADING"
        score_boost = -1
        details.append(
            f"Retail interest declining ({spike:.0f}%). "
            "Attention moving away — momentum may slow."
        )
    elif current > 70:
        signal = "HIGH_ATTENTION"
        score_boost = 1
        details.append(
            f"High search interest ({current}/100). Stock is well-known — "
            "less chance of being an undiscovered gem."
        )
    else:
        signal = "NORMAL"
        score_boost = 0
        details.append(f"Normal search interest ({current}/100, avg: {data['avg_interest']})")

    # Contrarian signal: very low interest on good fundamentals = hidden gem
    if current < 20 and data["avg_interest"] < 25:
        signal = "UNDER_RADAR"
        score_boost = 2
        details.append(
            "Very low retail attention — this is UNDER THE RADAR. "
            "If fundamentals are strong, this is exactly where multi-baggers hide."
        )

    summary = f"Interest: {current}/100 | Spike: {'+' if spike > 0 else ''}{spike:.0f}% | Peak: {peak}/100"

    return {
        "signal": signal,
        "score_boost": score_boost,
        "summary": summary,
        "details": details,
    }
