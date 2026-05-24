"""
Main pipeline: orchestrates scraping → analysis → challenge → output.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime

from .screener import build_candidate_list, fetch_nse_stock_data, SEED_STOCKS, get_trending_stocks_from_forums
from .analyser import analyse_stocks, classify_stock, score_stock, generate_swot
from .devils_advocate import DevilsAdvocate


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

    # Phase 3: Devil's Advocate challenges
    print("\nPHASE 3: Devil's Advocate challenging recommendations...")
    advocate = DevilsAdvocate()
    challenged = advocate.challenge_all(ranked_stocks)
    report = advocate.get_challenge_report(challenged)

    # Phase 4: Assemble final output
    print("\nPHASE 4: Generating output...")
    output = {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "penny_max_price": config["market"]["penny_max_price"],
            "small_cap_max_cr": config["market"]["small_cap_max_cr"],
            "mid_cap_max_cr": config["market"]["mid_cap_max_cr"],
        },
        "summary": {
            "total_analysed": len(ranked_stocks),
            "survived_challenge": len(challenged),
            "high_conviction": len(report["high_conviction"]),
            "moderate_conviction": len(report["moderate_conviction"]),
            "low_conviction": len(report["low_conviction"]),
            "rejected": len(report["rejected"]),
        },
        "top_picks": challenged[:25],
        "forum_sentiment": web_candidates.get("forum_mentions", [])[:20],
        "full_challenge_report": report,
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
