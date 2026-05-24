"""
NSE Bulk & Block Deals
=======================
Fetches bulk deal and block deal data from NSE India.
Bulk deals: Transactions > 0.5% of total equity shares.
Block deals: Trades of minimum 5 lakh shares or ₹10Cr+ in a single transaction.

Source: https://www.nseindia.com/market-data/bulk-block-deals
Legal: Yes — exchange-mandated disclosure under SEBI regulations.
"""

import requests
from datetime import datetime, timedelta


NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/bulk-block-deals",
}

BASE_URL = "https://www.nseindia.com"


def _get_nse_session():
    """Get a session with cookies from NSE."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get(BASE_URL, timeout=10)
    except Exception:
        pass
    return session


def fetch_bulk_deals(days=30):
    """
    Fetch recent bulk deals from NSE.
    Returns dict keyed by symbol: {symbol: [{date, client, txn_type, quantity, price}]}
    """
    session = _get_nse_session()
    deals_by_symbol = {}

    try:
        # NSE bulk deals API
        url = f"{BASE_URL}/api/historical-bulk-deals?from={_date_ago(days)}&to={_today()}"
        resp = session.get(url, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                sym = item.get("symbol", "")
                if not sym:
                    continue

                if sym not in deals_by_symbol:
                    deals_by_symbol[sym] = []

                deals_by_symbol[sym].append({
                    "date": item.get("dealDate", ""),
                    "client": item.get("clientName", "Unknown"),
                    "transaction_type": item.get("buySell", "").upper(),
                    "quantity": _parse_int(item.get("quantity")),
                    "price": _parse_float(item.get("avgPrice")),
                })
    except Exception as e:
        print(f"  [nse-bulk] Error fetching bulk deals: {e}")

    return deals_by_symbol


def fetch_block_deals(days=30):
    """
    Fetch recent block deals from NSE.
    Returns dict keyed by symbol.
    """
    session = _get_nse_session()
    deals_by_symbol = {}

    try:
        url = f"{BASE_URL}/api/block-deal?from={_date_ago(days)}&to={_today()}"
        resp = session.get(url, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                sym = item.get("symbol", "")
                if not sym:
                    continue

                if sym not in deals_by_symbol:
                    deals_by_symbol[sym] = []

                deals_by_symbol[sym].append({
                    "date": item.get("dealDate", ""),
                    "client": item.get("clientName", "Unknown"),
                    "transaction_type": item.get("buySell", "").upper(),
                    "quantity": _parse_int(item.get("quantity")),
                    "price": _parse_float(item.get("avgPrice")),
                })
    except Exception as e:
        print(f"  [nse-block] Error fetching block deals: {e}")

    return deals_by_symbol


def analyse_institutional_activity(symbol, bulk_deals, block_deals):
    """
    Analyse bulk/block deal activity for a stock.
    Returns: {signal, score_boost, summary, details, deals}
    """
    deals = []
    if symbol in bulk_deals:
        deals.extend(bulk_deals[symbol])
    if symbol in block_deals:
        deals.extend(block_deals[symbol])

    if not deals:
        return {
            "signal": "NO_DEALS",
            "score_boost": 0,
            "summary": "No bulk/block deals in last 30 days",
            "details": [],
            "deals": [],
        }

    buys = [d for d in deals if d["transaction_type"] == "BUY" or d["transaction_type"] == "B"]
    sells = [d for d in deals if d["transaction_type"] == "SELL" or d["transaction_type"] == "S"]

    total_buy_qty = sum(d["quantity"] for d in buys)
    total_sell_qty = sum(d["quantity"] for d in sells)
    total_buy_value = sum(d["quantity"] * d["price"] for d in buys if d["price"])
    total_sell_value = sum(d["quantity"] * d["price"] for d in sells if d["price"])

    details = []
    score_boost = 0

    if buys and not sells:
        signal = "ACCUMULATION"
        score_boost = 6
        details.append(
            f"Pure accumulation: {len(buys)} bulk/block BUY deals, zero sells. "
            f"Total: {total_buy_qty:,.0f} shares (₹{total_buy_value/1e7:.1f}Cr)"
        )
    elif total_buy_value > total_sell_value * 2:
        signal = "NET_BUY"
        score_boost = 4
        details.append(
            f"Net institutional buying: {len(buys)} buys vs {len(sells)} sells. "
            f"Buy value ₹{total_buy_value/1e7:.1f}Cr > Sell value ₹{total_sell_value/1e7:.1f}Cr"
        )
    elif sells and not buys:
        signal = "DISTRIBUTION"
        score_boost = -4
        details.append(
            f"Pure distribution: {len(sells)} bulk/block SELL deals, zero buys. "
            f"Total sold: {total_sell_qty:,.0f} shares (₹{total_sell_value/1e7:.1f}Cr)"
        )
    elif total_sell_value > total_buy_value * 2:
        signal = "NET_SELL"
        score_boost = -3
        details.append(
            f"Net institutional selling: Sell value ₹{total_sell_value/1e7:.1f}Cr > Buy value ₹{total_buy_value/1e7:.1f}Cr"
        )
    else:
        signal = "MIXED"
        score_boost = 0
        details.append(f"Mixed activity: {len(buys)} buys, {len(sells)} sells")

    # Add notable clients
    for d in deals[:5]:
        details.append(f"  {d['date']}: {d['client']} — {d['transaction_type']} {d['quantity']:,.0f} @ ₹{d['price']:.2f}")

    summary = f"{len(deals)} bulk/block deals (Buy: ₹{total_buy_value/1e7:.1f}Cr | Sell: ₹{total_sell_value/1e7:.1f}Cr)"

    return {
        "signal": signal,
        "score_boost": score_boost,
        "summary": summary,
        "details": details,
        "deals": deals[:10],
    }


def _parse_int(val):
    try:
        return int(str(val).replace(",", "").replace(" ", ""))
    except (ValueError, TypeError):
        return 0


def _parse_float(val):
    try:
        return float(str(val).replace(",", "").replace(" ", ""))
    except (ValueError, TypeError):
        return 0.0


def _today():
    return datetime.now().strftime("%d-%m-%Y")


def _date_ago(days):
    return (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")
