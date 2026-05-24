"""
Main pipeline: orchestrates scraping → analysis → metrics → challenge → output.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime

from .screener import build_candidate_list, fetch_nse_stock_data, SEED_STOCKS, get_trending_stocks_from_forums
from .analyser import analyse_stocks, classify_stock, score_stock, generate_swot
from .devils_advocate import DevilsAdvocate
from .metrics import fetch_historical_metrics, generate_multibagger_thesis, proactive_scan
from .social_media import fetch_expert_analysis_for_stocks
from .critic_agent import CriticAgent
from .nse_insider import fetch_insider_trades, analyse_insider_activity
from .nse_bulk_deals import fetch_bulk_deals, fetch_block_deals, analyse_institutional_activity
from .google_trends import fetch_search_interest, analyse_retail_interest
from .insights_tracker import generate_insights
from .compounder_framework import assess_all


CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
CACHE_DIR = Path(__file__).parent.parent / "cache"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def run_pipeline(symbols=None):
    """Run the full analysis pipeline."""
    config = load_config()
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  STOCK MULTIBAGGER ANALYSER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    # Phase 1: Gather candidates from web sources
    print("PHASE 1: Gathering candidates from open sources...")
    web_candidates = build_candidate_list(config)

    # Phase 2: Fetch detailed data for seed + discovered stocks
    print("\nPHASE 2: Fetching fundamentals via yfinance...")
    stock_symbols = symbols or SEED_STOCKS
    ranked_stocks = analyse_stocks(config, stock_symbols)
    print(f"  → {len(ranked_stocks)} stocks scored and ranked")

    # Phase 3: Fetch historical metrics (3/6 month)
    print("\nPHASE 3: Fetching historical metrics (3/6 month trends)...")
    for stock in ranked_stocks:
        metrics = fetch_historical_metrics(stock["symbol"])
        stock["metrics"] = metrics
        thesis = generate_multibagger_thesis(stock, metrics)
        stock["multibagger_thesis"] = thesis
        if metrics:
            print(f"  {stock['symbol']}: 6m return {metrics['return_6m_pct']}%, trend: {metrics['trend']}")

    # Phase 4: NSE Insider Trades + Bulk/Block Deals
    print("\nPHASE 4: Fetching NSE insider trades & bulk/block deals...")
    bulk_deals = fetch_bulk_deals(days=30)
    block_deals = fetch_block_deals(days=30)
    print(f"  → Bulk deals for {len(bulk_deals)} symbols, Block deals for {len(block_deals)} symbols")

    for stock in ranked_stocks:
        sym = stock["symbol"]
        insider_trades = fetch_insider_trades(sym, days=90)
        stock["insider_activity"] = analyse_insider_activity(sym, insider_trades)
        stock["institutional_activity"] = analyse_institutional_activity(sym, bulk_deals, block_deals)
        if stock["insider_activity"]["signal"] not in ("NO_DATA", "NEUTRAL"):
            print(f"  {sym}: Insider {stock['insider_activity']['signal']}")
        if stock["institutional_activity"]["signal"] != "NO_DEALS":
            print(f"  {sym}: Institutional {stock['institutional_activity']['signal']}")

    # Phase 5: Google Trends — retail interest detection
    print("\nPHASE 5: Fetching Google Trends retail interest...")
    all_symbols = [s["symbol"] for s in ranked_stocks]
    trends_data = fetch_search_interest(all_symbols)
    for stock in ranked_stocks:
        stock["retail_interest"] = analyse_retail_interest(stock["symbol"], trends_data)
        if stock["retail_interest"]["signal"] not in ("NO_DATA", "NORMAL"):
            print(f"  {stock['symbol']}: Retail interest {stock['retail_interest']['signal']}")

    # Phase 6: Devil's Advocate challenges
    print("\nPHASE 6: Devil's Advocate challenging recommendations...")
    advocate = DevilsAdvocate()
    ranked_stocks = advocate.challenge_all(ranked_stocks)
    report = advocate.get_challenge_report(ranked_stocks)

    # Phase 7: Proactive breakout scanner
    print("\nPHASE 7: Proactive breakout scanner (independent signals)...")
    proactive_picks = proactive_scan(config)

    # Phase 8: Expert analysis from YouTube/Social Media
    print("\nPHASE 8: Fetching expert analysis from YouTube & Social Media...")
    expert_analysis = fetch_expert_analysis_for_stocks(ranked_stocks)

    # Phase 9: Independent Critic Agent evaluation
    print("\nPHASE 9: Independent Critic Agent — autonomous evaluation...")
    critic = CriticAgent()
    critic_verdicts = critic.evaluate_all(ranked_stocks)
    critic_report = critic.get_report(critic_verdicts)

    # Phase 10: Merge proactive breakout signals into main stock list
    print("\nPHASE 10: Merging proactive breakout signals...")
    breakout_map = {p["symbol"]: p["signals"] for p in proactive_picks}
    for stock in ranked_stocks:
        stock["breakout_signals"] = breakout_map.get(stock["symbol"], [])

    # Phase 11: Structural Compounder Framework assessment
    print("\nPHASE 11: Structural Compounder Framework assessment...")
    ranked_stocks = assess_all(ranked_stocks)

    # Phase 12: Pulse.AI Insights — performance tracking
    print("\nPHASE 12: Pulse.AI Insights — performance time-series...")
    generate_insights(ranked_stocks)

    # Phase 13: Assemble final output
    print("\nPHASE 13: Generating output...")
    output = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "penny_max_price": config["market"]["penny_max_price"],
            "small_cap_max_cr": config["market"]["small_cap_max_cr"],
            "mid_cap_max_cr": config["market"]["mid_cap_max_cr"],
        },
        "summary": {
            "total_analysed": len(ranked_stocks),
            "survived_challenge": len([s for s in ranked_stocks if s.get("survived_challenge")]),
            "high_conviction": len(report["high_conviction"]),
            "moderate_conviction": len(report["moderate_conviction"]),
            "low_conviction": len(report["low_conviction"]),
            "rejected": len(report["rejected"]),
            "proactive_breakouts": len(proactive_picks),
        },
        "top_picks": ranked_stocks,
        "proactive_breakouts": proactive_picks[:15],
        "expert_analysis": expert_analysis[:15],
        "critic_report": critic_report,
        "forum_sentiment": web_candidates.get("forum_mentions", [])[:20],
        "full_challenge_report": report,
        "disclaimer": (
            "DISCLAIMER: Investments in stocks based on these recommendations carry significant risk. "
            "This information is purely informational and does NOT constitute financial advice. "
            "All investments are subject to market risk. Past performance does not guarantee future results. "
            "You must analyse and decide to invest on your own. The creators of this tool accept "
            "NO responsibility for any financial losses. Consult a SEBI-registered financial advisor "
            "before making investment decisions."
        ),
    }

    # Save output
    output_file = OUTPUT_DIR / "analysis.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"  → Saved to {output_file}")

    # Also save dated cache
    cache_file = CACHE_DIR / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(cache_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    return output


def run_quick(symbols=None):
    """Quick run with fewer stocks for testing."""
    test_symbols = symbols or ["SUZLON", "NHPC", "IRFC", "RVNL", "COCHINSHIP",
                                "KAYNES", "ZAGGLE", "NETWEB", "ZOMATO", "JIOFIN"]
    return run_pipeline(test_symbols)
