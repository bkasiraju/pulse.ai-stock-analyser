"""
Historical metrics analyser: fetches 3/6 month price history,
computes momentum patterns, volume trends, and multi-bagger thesis.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_historical_metrics(symbol):
    """Fetch 1-year historical data and compute key metrics."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="1y")

        if hist.empty:
            ticker = yf.Ticker(f"{symbol}.BO")
            hist = ticker.history(period="1y")

        if hist.empty or len(hist) < 20:
            return None

        current_price = hist['Close'].iloc[-1]
        price_3m_ago = hist['Close'].iloc[-min(63, len(hist))]
        price_6m_ago = hist['Close'].iloc[-min(126, len(hist))]

        return_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        return_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100

        # Volume analysis
        avg_vol_recent = hist['Volume'].tail(20).mean()
        avg_vol_older = hist['Volume'].head(20).mean()
        volume_surge = ((avg_vol_recent - avg_vol_older) / avg_vol_older * 100) if avg_vol_older > 0 else 0

        # Volatility (annualised)
        daily_returns = hist['Close'].pct_change().dropna()
        volatility = daily_returns.std() * (252 ** 0.5) * 100

        # Moving averages
        ma_20 = hist['Close'].tail(20).mean()
        ma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else ma_20

        # Trend strength: price above both MAs = strong uptrend
        above_20ma = current_price > ma_20
        above_50ma = current_price > ma_50

        # RSI (14-day)
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50

        # Monthly breakdown
        hist_monthly = hist['Close'].resample('ME').last()
        monthly_returns = hist_monthly.pct_change().dropna() * 100

        # Consecutive green months
        green_months = sum(1 for r in monthly_returns.tail(6) if r > 0)

        # Max drawdown in period
        peak = hist['Close'].expanding(min_periods=1).max()
        drawdown = ((hist['Close'] - peak) / peak) * 100
        max_drawdown = drawdown.min()

        # Period returns: 1D, 1W, 1M, 3M, 6M, YTD, 1Y
        price_1d_ago = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
        price_1w_ago = hist['Close'].iloc[-min(5, len(hist))]
        price_1m_ago = hist['Close'].iloc[-min(21, len(hist))]
        price_1y_ago = hist['Close'].iloc[0]

        # YTD: from Jan 1 of current year
        ytd_start = hist[hist.index >= str(datetime.now().year) + '-01-01']
        price_ytd = ytd_start['Close'].iloc[0] if not ytd_start.empty else price_1y_ago

        return_1d = ((current_price - price_1d_ago) / price_1d_ago) * 100
        return_1w = ((current_price - price_1w_ago) / price_1w_ago) * 100
        return_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100
        return_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
        return_ytd = ((current_price - price_ytd) / price_ytd) * 100

        return {
            "return_1d_pct": round(return_1d, 2),
            "return_1w_pct": round(return_1w, 2),
            "return_1m_pct": round(return_1m, 1),
            "return_3m_pct": round(return_3m, 1),
            "return_6m_pct": round(return_6m, 1),
            "return_1y_pct": round(return_1y, 1),
            "return_ytd_pct": round(return_ytd, 1),
            "volume_surge_pct": round(volume_surge, 1),
            "avg_volume_20d": int(avg_vol_recent),
            "volatility_annual_pct": round(volatility, 1),
            "rsi_14": round(current_rsi, 1),
            "above_20ma": above_20ma,
            "above_50ma": above_50ma,
            "ma_20": round(ma_20, 2),
            "ma_50": round(ma_50, 2),
            "green_months_of_6": green_months,
            "max_drawdown_pct": round(max_drawdown, 1),
            "monthly_returns": [round(r, 1) for r in monthly_returns.tail(6).tolist()],
            "trend": _classify_trend(above_20ma, above_50ma, return_3m, current_rsi),
        }
    except Exception as e:
        print(f"[metrics] Error for {symbol}: {e}")
        return None


def _classify_trend(above_20ma, above_50ma, return_3m, rsi):
    """Classify the stock's current trend."""
    if above_20ma and above_50ma and return_3m > 10:
        return "STRONG UPTREND"
    elif above_20ma and above_50ma:
        return "UPTREND"
    elif above_20ma and not above_50ma:
        return "RECOVERING"
    elif not above_20ma and not above_50ma and return_3m < -10:
        return "DOWNTREND"
    elif rsi < 30:
        return "OVERSOLD"
    elif rsi > 70:
        return "OVERBOUGHT"
    return "SIDEWAYS"


def generate_multibagger_thesis(stock_data, metrics):
    """Generate a multi-bagger thesis explaining WHY this stock could multiply."""
    thesis_points = []
    timeframe = "1-3 years"

    mc = stock_data.get("market_cap_cr", 0)
    rg = stock_data.get("fundamentals", {}).get("revenue_growth")
    eg = stock_data.get("fundamentals", {}).get("earnings_growth")
    de = stock_data.get("fundamentals", {}).get("debt_to_equity")
    roe = stock_data.get("fundamentals", {}).get("roe")
    ret_6m = metrics.get("return_6m_pct", 0) if metrics else 0

    # Small/micro cap advantage
    if mc < 500:
        thesis_points.append(
            f"Micro-cap (₹{mc:.0f}Cr) — even modest institutional buying can move price 2-3x. "
            "Under-researched by analysts, creating information asymmetry edge."
        )
    elif mc < 2000:
        thesis_points.append(
            f"Small-cap (₹{mc:.0f}Cr) — large enough to be real, small enough to 3-5x. "
            "One quarter of strong results can trigger re-rating."
        )
    elif mc < 5000:
        thesis_points.append(
            f"Mid-cap (₹{mc:.0f}Cr) — growth runway before hitting large-cap saturation. "
            "Potential for 2-3x if execution continues."
        )

    # Revenue growth = multi-bagger fuel
    if rg and rg > 0.30:
        thesis_points.append(
            f"Revenue growing at {rg*100:.0f}% — at this rate, revenue doubles in ~2.3 years. "
            "Market typically rewards sustained high-growth with PE expansion."
        )
    elif rg and rg > 0.20:
        thesis_points.append(
            f"Healthy {rg*100:.0f}% revenue growth — compounding at this rate for 3 years yields 73% revenue increase."
        )

    # Earnings leverage
    if eg and eg > 0.30:
        thesis_points.append(
            f"Earnings exploding at {eg*100:.0f}% — operating leverage kicking in. "
            "Profit growth > revenue growth signals scalable business model."
        )

    # Low debt = runway
    if de is not None and de < 30:
        thesis_points.append(
            "Near-zero debt gives management optionality — can invest in growth, "
            "acquire competitors, or return capital without interest burden."
        )

    # High ROE = compounding machine
    if roe and roe > 0.18:
        thesis_points.append(
            f"ROE of {roe*100:.0f}% means every ₹1 retained generates ₹{roe:.2f} in returns. "
            "Sustained high ROE + reinvestment = compounding wealth creator."
        )

    # Momentum confirmation
    if metrics and metrics.get("trend") in ["STRONG UPTREND", "UPTREND"]:
        thesis_points.append(
            f"Technical momentum confirms fundamentals — {metrics['trend'].lower()} with "
            f"{ret_6m:.0f}% return in 6 months. Smart money is already accumulating."
        )

    # Recovery play
    if metrics and metrics.get("trend") == "OVERSOLD":
        thesis_points.append(
            "Currently oversold (RSI < 30) — contrarian opportunity. If fundamentals "
            "are intact, this is the market handing you a discount on a quality business."
        )

    if not thesis_points:
        thesis_points.append("Limited quantitative thesis — monitor for improving fundamentals.")

    return {
        "thesis": thesis_points,
        "timeframe": timeframe,
        "target_multiple": _estimate_multiple(mc, rg, eg),
    }


def _estimate_multiple(mc, rg, eg):
    """Rough estimate of potential return multiple."""
    base = 1.0
    if mc < 500:
        base += 1.5
    elif mc < 2000:
        base += 1.0
    elif mc < 5000:
        base += 0.5

    if rg and rg > 0.30:
        base += 1.0
    elif rg and rg > 0.15:
        base += 0.5

    if eg and eg > 0.40:
        base += 1.0
    elif eg and eg > 0.20:
        base += 0.5

    return f"{base:.0f}-{base+1:.0f}x in 1-3 years (estimated)"


def proactive_scan(config):
    """
    PROACTIVE SCANNER: Instead of relying on forums/screener lists,
    this scans a broad universe of NSE small/mid caps for breakout signals.

    Signals checked:
    1. Volume breakout (20-day avg volume > 2x 50-day avg)
    2. Price breaking above 50-day MA after being below
    3. RSI recovering from oversold (<30) territory
    4. New 52-week high on small/mid cap
    """
    print("[proactive] Running independent breakout scanner...")

    # Broad scan universe: NSE small/mid cap indices
    scan_symbols = [
        "TTML", "OLECTRA", "AETHER", "KRSNAA", "MEDPLUS",
        "DATAPATTNS", "BIKAJI", "FIVESTAR", "DREAMFOLKS", "MANKIND",
        "SBCL", "PHANTOM", "APARINDS", "EXPLEOSOL", "SAPPHIRE",
        "CRAFTSMAN", "GANESHHOUC", "RPSGVENT", "VAIBHAVGBL", "IIFL",
        "AURIONPRO", "NEWGEN", "INTELLECT", "PERSISTENT", "COFORGE",
        "KPITTECH", "TRENT", "DMART", "MUTHOOTFIN", "CANFINHOME",
        "MANAPPURAM", "RADICO", "EIDPARRY", "CERA", "SUPRAJIT",
        "GARFIBRES", "GRINDWELL", "SUNPHARMA", "ABFRL", "METROPOLIS",
    ]

    breakouts = []

    for symbol in scan_symbols:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period="3mo")

            if hist.empty or len(hist) < 50:
                continue

            current_price = hist['Close'].iloc[-1]
            ma_50 = hist['Close'].tail(50).mean()
            ma_20 = hist['Close'].tail(20).mean()
            vol_20 = hist['Volume'].tail(20).mean()
            vol_50 = hist['Volume'].tail(50).mean()

            info = ticker.info or {}
            mc = (info.get("marketCap", 0) or 0) / 1e7

            # Filter: only small/mid cap
            if mc > config["market"]["mid_cap_max_cr"] or mc < 10:
                continue

            signals = []

            # Volume breakout
            if vol_50 > 0 and vol_20 / vol_50 > 2:
                signals.append(f"Volume breakout: 20d avg {vol_20/vol_50:.1f}x above 50d avg")

            # MA crossover (price just crossed above 50MA)
            prices_5d = hist['Close'].tail(5)
            if current_price > ma_50 and prices_5d.iloc[0] < ma_50:
                signals.append("Bullish MA crossover: price just broke above 50-day MA")

            # RSI recovery from oversold
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_now = rsi.iloc[-1]
            rsi_5d_ago = rsi.iloc[-5] if len(rsi) >= 5 else rsi_now

            if rsi_5d_ago < 30 and rsi_now > 35:
                signals.append(f"RSI recovery from oversold: {rsi_5d_ago:.0f} → {rsi_now:.0f}")

            # 52-week high
            high_52 = info.get("fiftyTwoWeekHigh", 0)
            if high_52 and current_price > high_52 * 0.95:
                signals.append("Trading within 5% of 52-week high — breakout imminent")

            if signals:
                breakouts.append({
                    "symbol": symbol,
                    "name": info.get("longName") or info.get("shortName", symbol),
                    "price": round(current_price, 2),
                    "market_cap_cr": round(mc, 0),
                    "signals": signals,
                    "signal_count": len(signals),
                })

        except Exception:
            continue

    breakouts.sort(key=lambda x: x["signal_count"], reverse=True)
    print(f"[proactive] Found {len(breakouts)} stocks with breakout signals")
    return breakouts
