"""
Stock screener: fetches small/mid/penny cap stocks from NSE via yfinance
and open web sources (Screener.in, MoneyControl).
"""

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def fetch_screener_results(page=1, category="small"):
    """Fetch stock list from Screener.in open queries."""
    urls = {
        "penny": "https://www.screener.in/screens/357338/penny-stocks-with-good-fundamentals/",
        "small": "https://www.screener.in/screens/218498/small-cap-multibaggers/",
        "mid": "https://www.screener.in/screens/132456/mid-cap-growth-stocks/",
    }
    url = urls.get(category, urls["small"])
    if page > 1:
        url += f"?page={page}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[screener] {category} page {page}: HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", class_="data-table")
        if not table:
            return []

        rows = table.find_all("tr")[1:]
        stocks = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            link = cols[0].find("a")
            if link:
                name = link.text.strip()
                href = link.get("href", "")
                bse_code = href.split("/")[-2] if href else ""
                stocks.append({
                    "name": name,
                    "screener_url": f"https://www.screener.in{href}",
                    "category": category,
                })
        return stocks
    except Exception as e:
        print(f"[screener] Error fetching {category}: {e}")
        return []


def fetch_nse_stock_data(symbol):
    """Fetch detailed stock data from yfinance for an NSE symbol."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        if not info or info.get("regularMarketPrice") is None:
            ticker = yf.Ticker(f"{symbol}.BO")
            info = ticker.info

        if not info:
            return None

        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName", symbol),
            "price": info.get("regularMarketPrice", 0) or info.get("currentPrice", 0),
            "market_cap_cr": round((info.get("marketCap", 0) or 0) / 1e7, 2),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "promoter_holding": info.get("heldPercentInsiders"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "dividend_yield": info.get("dividendYield"),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "book_value": info.get("bookValue"),
            "eps": info.get("trailingEps"),
            "free_cashflow": info.get("freeCashflow"),
        }
    except Exception as e:
        print(f"[yfinance] Error fetching {symbol}: {e}")
        return None


def scrape_moneycontrol_gainers():
    """Scrape top gainers from MoneyControl for momentum signals."""
    url = "https://www.moneycontrol.com/stocks/marketstats/nsegainer/index.php"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", class_="tbldata14")
        if not table:
            return []

        rows = table.find_all("tr")[1:30]
        gainers = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                name = cols[0].text.strip()
                gainers.append({"name": name, "source": "moneycontrol_gainers"})
        return gainers
    except Exception as e:
        print(f"[moneycontrol] Error: {e}")
        return []


def get_trending_stocks_from_forums():
    """Scrape stock mentions from Reddit r/IndianStreetBets and ValuePickr."""
    stocks_mentioned = []

    # Reddit r/IndianStreetBets (old.reddit for easier parsing)
    try:
        url = "https://old.reddit.com/r/IndianStreetBets/hot/.json"
        resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts[:25]:
                title = post["data"].get("title", "")
                selftext = post["data"].get("selftext", "")[:500]
                stocks_mentioned.append({
                    "source": "reddit_isb",
                    "title": title,
                    "text": selftext,
                    "url": f"https://reddit.com{post['data'].get('permalink', '')}",
                    "score": post["data"].get("score", 0),
                })
    except Exception as e:
        print(f"[reddit] Error: {e}")

    # Reddit r/IndianStockMarket
    try:
        url = "https://old.reddit.com/r/IndianStockMarket/hot/.json"
        resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts[:25]:
                title = post["data"].get("title", "")
                selftext = post["data"].get("selftext", "")[:500]
                stocks_mentioned.append({
                    "source": "reddit_ism",
                    "title": title,
                    "text": selftext,
                    "url": f"https://reddit.com{post['data'].get('permalink', '')}",
                    "score": post["data"].get("score", 0),
                })
    except Exception as e:
        print(f"[reddit_ism] Error: {e}")

    # ValuePickr forum
    try:
        url = "https://forum.valuepickr.com/latest.json"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            topics = data.get("topic_list", {}).get("topics", [])
            for topic in topics[:20]:
                stocks_mentioned.append({
                    "source": "valuepickr",
                    "title": topic.get("title", ""),
                    "text": "",
                    "url": f"https://forum.valuepickr.com/t/{topic.get('slug', '')}/{topic.get('id', '')}",
                    "score": topic.get("like_count", 0),
                })
    except Exception as e:
        print(f"[valuepickr] Error: {e}")

    return stocks_mentioned


def build_candidate_list(config):
    """Build master candidate list from all sources."""
    penny_max = config["market"]["penny_max_price"]
    small_max_cr = config["market"]["small_cap_max_cr"]
    mid_max_cr = config["market"]["mid_cap_max_cr"]

    print("[screener] Fetching penny stocks...")
    penny = fetch_screener_results(category="penny")
    time.sleep(random.uniform(1, 3))

    print("[screener] Fetching small cap stocks...")
    small = fetch_screener_results(category="small")
    time.sleep(random.uniform(1, 3))

    print("[screener] Fetching mid cap stocks...")
    mid = fetch_screener_results(category="mid")

    print("[forums] Fetching trending stocks from forums...")
    forum_data = get_trending_stocks_from_forums()

    print("[moneycontrol] Fetching momentum gainers...")
    gainers = scrape_moneycontrol_gainers()

    all_candidates = penny + small + mid
    print(f"[screener] Total candidates from screener: {len(all_candidates)}")
    print(f"[forums] Forum mentions: {len(forum_data)}")
    print(f"[moneycontrol] Gainers: {len(gainers)}")

    return {
        "screener_candidates": all_candidates,
        "forum_mentions": forum_data,
        "momentum_gainers": gainers,
    }


# Curated stocks organized by category
PENNY_STOCKS = [
    # Price < ₹20 — high risk/reward
    "IDEA", "JPPOWER", "RPOWER", "GTLINFRA", "UNITECH",
    "JAIPRAKASH", "JPASSOCIAT", "ORIENTBELL", "SPML",
    "DBCORP", "NRBBEARING", "JKTYRE", "SOUTHBANK",
    "IDFCFIRSTB", "CENTRALBK", "UCOBANK", "IOB",
    "MAHABANK", "INDIANB", "BANKINDIA", "CANBK",
]

SMALL_CAP_STOCKS = [
    # MCap < ₹2000Cr — small but growing
    "ZAGGLE", "NETWEB", "SYRMA", "IDEAFORGE", "MASTEK",
    "CAMPUS", "MOLDTKPAC", "LXCHEM", "PRIVISCL", "HBLPOWER",
    "GPIL", "TITAGARH", "RAILTEL", "IRCON", "RATNAMANI",
    "TANLA", "HAPPSTMNDS", "ROUTE", "CLEAN", "AFFLE",
    "KFINTECH", "CAMS", "MAPMYINDIA", "LATENTVIEW", "SENCO",
]

MID_CAP_STOCKS = [
    # MCap ₹2000-10000Cr — potential multi-baggers
    "KAYNES", "GRSE", "COCHINSHIP", "BDL",
    "FLUOROCHEM", "APLAPOLLO", "ASTRAL", "SAFARI", "DEEPAKNTR",
    "RVNL", "IRFC", "NHPC", "TATAELXSI", "POLYCAB",
    "CELLO", "TBOTEK", "JSWINFRA", "DOMS",
    "INOXGREEN", "KIRLPNU", "GRAVITA", "ELECON", "PNCINFRA",
    "GPPL", "PERSISTENT", "COFORGE",
]

# Combined list for full run
SEED_STOCKS = PENNY_STOCKS + SMALL_CAP_STOCKS + MID_CAP_STOCKS
