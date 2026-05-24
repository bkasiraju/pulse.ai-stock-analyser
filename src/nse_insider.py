"""
NSE Insider Trading Disclosures
================================
Fetches insider/promoter buy/sell transactions from NSE India.
This is PUBLICLY mandated data under SEBI PIT Regulations —
companies MUST disclose insider trades within 2 days.

Source: https://www.nseindia.com/companies-listing/corporate-filings-insider-trading
Legal: Yes — regulatory disclosure for public consumption.
"""

import requests
import json
from datetime import datetime, timedelta


NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-insider-trading",
}

BASE_URL = "https://www.nseindia.com"


def _get_nse_session():
    """Get a session with cookies from NSE (required for API access)."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get(BASE_URL, timeout=10)
    except Exception:
        pass
    return session


def fetch_insider_trades(symbol, days=90):
    """
    Fetch insider trading data for a stock from NSE.
    Returns list of {date, person, category, transaction_type, shares, value}.
    """
    session = _get_nse_session()

    try:
        url = f"{BASE_URL}/api/corporates-pit?index=equities&from_date={_date_ago(days)}&to_date={_today()}&symbol={symbol}"
        resp = session.get(url, timeout=15)

        if resp.status_code != 200:
            return []

        data = resp.json()
        trades = []

        for item in data.get("data", []):
            acq_mode = (item.get("acqMode") or "").lower()
            txn_type = "BUY" if "buy" in acq_mode or "acquisition" in acq_mode else "SELL"

            shares = _parse_number(item.get("secAcq"))
            value = _parse_number(item.get("secVal"))

            trades.append({
                "date": item.get("date", ""),
                "person": item.get("acqName", "Unknown"),
                "category": item.get("personCategory", ""),
                "transaction_type": txn_type,
                "shares": shares,
                "value_lakhs": round(value / 100000, 2) if value else 0,
                "mode": item.get("acqMode", ""),
            })

        return trades
    except Exception as e:
        print(f"  [nse-insider] Error for {symbol}: {e}")
        return []


def fetch_bulk_insider_trades(days=30):
    """Fetch ALL insider trades across market for recent days."""
    session = _get_nse_session()

    try:
        url = f"{BASE_URL}/api/corporates-pit?index=equities&from_date={_date_ago(days)}&to_date={_today()}"
        resp = session.get(url, timeout=20)

        if resp.status_code != 200:
            return {}

        data = resp.json()
        by_symbol = {}

        for item in data.get("data", []):
            sym = item.get("symbol", "")
            if not sym:
                continue
            if sym not in by_symbol:
                by_symbol[sym] = {"buys": 0, "sells": 0, "net_value": 0}

            acq_mode = (item.get("acqMode") or "").lower()
            value = _parse_number(item.get("secVal"))

            if "buy" in acq_mode or "acquisition" in acq_mode:
                by_symbol[sym]["buys"] += 1
                by_symbol[sym]["net_value"] += value
            else:
                by_symbol[sym]["sells"] += 1
                by_symbol[sym]["net_value"] -= value

        return by_symbol
    except Exception as e:
        print(f"  [nse-insider] Bulk fetch error: {e}")
        return {}


def analyse_insider_activity(symbol, trades):
    """
    Analyse insider trades and return a signal.
    Returns: {signal, score_boost, summary, details}
    """
    if not trades:
        return {
            "signal": "NO_DATA",
            "score_boost": 0,
            "summary": "No insider trading data available",
            "details": [],
            "trades": [],
        }

    buys = [t for t in trades if t["transaction_type"] == "BUY"]
    sells = [t for t in trades if t["transaction_type"] == "SELL"]

    total_buy_value = sum(t["value_lakhs"] for t in buys)
    total_sell_value = sum(t["value_lakhs"] for t in sells)
    net_value = total_buy_value - total_sell_value

    # Promoter-specific trades (strongest signal)
    promoter_buys = [t for t in buys if "promoter" in t.get("category", "").lower()]
    promoter_sells = [t for t in sells if "promoter" in t.get("category", "").lower()]

    details = []
    score_boost = 0

    if promoter_buys and not promoter_sells:
        signal = "STRONG_BUY"
        score_boost = 8
        details.append(f"Promoters bought {len(promoter_buys)} times (₹{total_buy_value:.0f}L) with ZERO selling — very bullish")
    elif len(buys) > len(sells) * 2 and total_buy_value > total_sell_value:
        signal = "BUY"
        score_boost = 5
        details.append(f"Net insider buying: {len(buys)} buys vs {len(sells)} sells, net +₹{net_value:.0f}L")
    elif promoter_sells and not promoter_buys:
        signal = "SELL_WARNING"
        score_boost = -5
        details.append(f"Promoters selling {len(promoter_sells)} times (₹{total_sell_value:.0f}L) with NO buying — bearish signal")
    elif len(sells) > len(buys) * 2:
        signal = "SELL"
        score_boost = -3
        details.append(f"Net insider selling: {len(sells)} sells vs {len(buys)} buys")
    elif not buys and not sells:
        signal = "NEUTRAL"
        score_boost = 0
        details.append("No significant insider activity")
    else:
        signal = "MIXED"
        score_boost = 0
        details.append(f"Mixed activity: {len(buys)} buys, {len(sells)} sells")

    summary = f"{len(buys)} buys, {len(sells)} sells in 90 days (Net: {'+'if net_value>0 else ''}₹{net_value:.0f}L)"

    return {
        "signal": signal,
        "score_boost": score_boost,
        "summary": summary,
        "details": details,
        "trades": trades[:10],
    }


def _parse_number(val):
    """Parse numeric string with commas."""
    if not val:
        return 0
    try:
        return float(str(val).replace(",", "").replace(" ", ""))
    except (ValueError, TypeError):
        return 0


def _today():
    return datetime.now().strftime("%d-%m-%Y")


def _date_ago(days):
    return (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")
