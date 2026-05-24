"""
Social media & YouTube expert analysis scraper.
Fetches public expert opinions from YouTube search results
and Twitter/X trending discussions about recommended stocks.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}


def fetch_youtube_analysis(symbol, stock_name):
    """Search YouTube for expert analysis videos about a stock."""
    query = f"{symbol} {stock_name} stock analysis 2025 2026 target"
    search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []

        results = []
        json_matches = re.findall(r'var ytInitialData = ({.*?});</script>', resp.text)
        if not json_matches:
            json_matches = re.findall(r'ytInitialData\s*=\s*({.*?});\s*</script>', resp.text)

        if json_matches:
            try:
                data = json.loads(json_matches[0])
                contents = (
                    data.get("contents", {})
                    .get("twoColumnSearchResultsRenderer", {})
                    .get("primaryContents", {})
                    .get("sectionListRenderer", {})
                    .get("contents", [])
                )

                for section in contents:
                    items = (
                        section.get("itemSectionRenderer", {})
                        .get("contents", [])
                    )
                    for item in items[:8]:
                        video = item.get("videoRenderer")
                        if not video:
                            continue

                        title_runs = video.get("title", {}).get("runs", [])
                        title = "".join(r.get("text", "") for r in title_runs)

                        channel = video.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown")
                        video_id = video.get("videoId", "")
                        view_text = video.get("viewCountText", {}).get("simpleText", "")
                        published = video.get("publishedTimeText", {}).get("simpleText", "")

                        views = _parse_views(view_text)

                        if video_id and title:
                            results.append({
                                "title": title,
                                "channel": channel,
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "views": views,
                                "published": published,
                            })

                        if len(results) >= 5:
                            break
                    if len(results) >= 5:
                        break
            except (json.JSONDecodeError, KeyError):
                pass

        if not results:
            results = _fallback_youtube_scrape(resp.text)

        return results[:5]
    except Exception as e:
        print(f"[youtube] Error searching for {symbol}: {e}")
        return []


def _fallback_youtube_scrape(html):
    """Fallback: extract video titles from raw HTML patterns."""
    results = []
    video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"\}', html)

    seen_ids = set()
    for vid, title in zip(video_ids, titles):
        if vid in seen_ids:
            continue
        seen_ids.add(vid)
        results.append({
            "title": title.encode().decode('unicode_escape'),
            "channel": "",
            "url": f"https://www.youtube.com/watch?v={vid}",
            "views": "",
            "published": "",
        })
        if len(results) >= 5:
            break
    return results


def _parse_views(view_text):
    """Parse '1.2M views' or '45K views' etc."""
    if not view_text:
        return ""
    match = re.search(r'([\d,.]+[KMB]?)\s*view', view_text, re.IGNORECASE)
    if match:
        return match.group(1)
    return view_text.replace(" views", "").strip()


def fetch_moneycontrol_expert_views(symbol):
    """Fetch expert/analyst views from MoneyControl."""
    try:
        search_url = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data={symbol}&cid=&mbsearch_str=&board=&sharename=&my498=all&exchange=&myaction=search&ESSION_ID="
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.find_all("a", href=True)
        stock_link = None
        for link in links:
            if "/stockpricequote/" in link.get("href", ""):
                stock_link = link.get("href")
                break

        if not stock_link:
            return []

        if not stock_link.startswith("http"):
            stock_link = "https://www.moneycontrol.com" + stock_link

        resp2 = requests.get(stock_link, headers=HEADERS, timeout=10)
        if resp2.status_code != 200:
            return []

        soup2 = BeautifulSoup(resp2.text, "lxml")
        insights = []

        target_section = soup2.find("div", class_="analyst_rating")
        if target_section:
            reco = target_section.find("span", class_="recotext")
            if reco:
                insights.append({
                    "title": f"Analyst Consensus: {reco.text.strip()}",
                    "channel": "MoneyControl Analysts",
                    "url": stock_link,
                    "views": "",
                    "published": "",
                })

        return insights[:3]
    except Exception as e:
        print(f"[moneycontrol_expert] Error for {symbol}: {e}")
        return []


def fetch_twitter_mentions(symbol):
    """Fetch recent public Twitter/X mentions via nitter (public proxy)."""
    nitter_instances = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
    ]

    for base_url in nitter_instances:
        try:
            search_url = f"{base_url}/search?f=tweets&q=%23{symbol}+stock&since=&until=&near="
            resp = requests.get(search_url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            tweets = soup.find_all("div", class_="timeline-item")

            results = []
            for tweet in tweets[:5]:
                content_el = tweet.find("div", class_="tweet-content")
                user_el = tweet.find("a", class_="username")
                if content_el:
                    text = content_el.text.strip()[:200]
                    user = user_el.text.strip() if user_el else ""
                    results.append({
                        "title": text,
                        "channel": f"@{user}" if user else "Twitter/X",
                        "url": f"https://twitter.com/search?q=%23{symbol}+stock",
                        "views": "",
                        "published": "",
                    })

            if results:
                return results
        except Exception:
            continue

    return []


def fetch_expert_analysis_for_stocks(stocks, max_stocks=15):
    """
    Fetch YouTube/social media expert analysis for top stocks.
    Returns list of {symbol, source, insights[], sentiment}.
    """
    print("[expert] Fetching YouTube & social media expert analysis...")
    results = []

    for stock in stocks[:max_stocks]:
        symbol = stock["symbol"]
        name = stock.get("name", symbol)
        print(f"  Searching expert views for {symbol}...")

        yt_results = fetch_youtube_analysis(symbol, name)
        mc_results = fetch_moneycontrol_expert_views(symbol)
        twitter_results = fetch_twitter_mentions(symbol)

        all_insights = []
        if yt_results:
            all_insights.extend(yt_results[:3])
        if mc_results:
            all_insights.extend(mc_results[:2])
        if twitter_results:
            all_insights.extend(twitter_results[:2])

        if all_insights:
            sentiment = _derive_sentiment(all_insights, stock)
            results.append({
                "symbol": symbol,
                "name": name,
                "source": "YouTube + Social Media",
                "insights": all_insights,
                "sentiment": sentiment,
            })

        time.sleep(random.uniform(1.5, 3.0))

    print(f"[expert] Got expert analysis for {len(results)} stocks")
    return results


def _derive_sentiment(insights, stock):
    """Derive overall sentiment from expert content and stock data."""
    bullish_words = ["buy", "bullish", "target", "multibagger", "breakout", "growth", "outperform", "accumulate", "strong"]
    bearish_words = ["sell", "bearish", "avoid", "overvalued", "risk", "downgrade", "underperform", "caution"]

    text = " ".join(i.get("title", "").lower() for i in insights)

    bull_count = sum(1 for w in bullish_words if w in text)
    bear_count = sum(1 for w in bearish_words if w in text)

    conv = stock.get("conviction_level", "")
    if "HIGH" in conv:
        bull_count += 2
    elif "LOW" in conv or "REJECTED" in conv:
        bear_count += 1

    if bull_count > bear_count + 1:
        return "Bullish"
    elif bear_count > bull_count + 1:
        return "Bearish"
    elif bull_count > 0 and bear_count > 0:
        return "Mixed"
    return "Neutral"
