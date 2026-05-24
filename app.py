"""
Entry point for the Stock Multibagger Analyser.

Usage:
    python3 app.py              — Start web dashboard on :8400
    python3 app.py --run        — Run analysis once (CLI mode)
    python3 app.py --quick      — Quick analysis (10 stocks)
    python3 app.py --schedule   — Run on daily schedule (8:30 AM IST)
"""

import sys
import argparse

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from src.pipeline import run_pipeline, run_quick
from src.web_server import start_server


def main():
    parser = argparse.ArgumentParser(description="Stock Multibagger Analyser")
    parser.add_argument("--run", action="store_true", help="Run full analysis (CLI)")
    parser.add_argument("--quick", action="store_true", help="Quick analysis (10 stocks)")
    parser.add_argument("--schedule", action="store_true", help="Run on daily schedule")
    parser.add_argument("--port", type=int, default=8400, help="Dashboard port (default: 8400)")
    args = parser.parse_args()

    if args.run:
        result = run_pipeline()
        print(f"\nDone. Top {len(result['top_picks'])} picks saved to output/analysis.json")
        print_top_picks(result)
    elif args.quick:
        result = run_quick()
        print(f"\nDone. {len(result['top_picks'])} picks saved to output/analysis.json")
        print_top_picks(result)
    elif args.schedule:
        run_scheduled()
    else:
        start_server(port=args.port)


def print_top_picks(result):
    """Print top picks to terminal."""
    picks = result.get("top_picks", [])
    if not picks:
        print("No stocks survived the analysis.")
        return

    print(f"\n{'='*80}")
    print(f"{'#':<3} {'Symbol':<12} {'Price':<10} {'MCap(Cr)':<12} {'Score':<8} {'Adj':<8} {'Conviction':<18} {'Flags'}")
    print(f"{'='*80}")

    for i, s in enumerate(picks[:25], 1):
        flags = ", ".join(s.get("red_flags", [])[:2]) or "-"
        print(f"{i:<3} {s['symbol']:<12} ₹{s['price']:<8.2f} ₹{s['market_cap_cr']:<10,.0f} "
              f"{s['score']:<8} {s['adjusted_score']:<8} {s['conviction_level']:<18} {flags}")

    print(f"{'='*80}")


def run_scheduled():
    """Run on daily schedule at 8:30 AM IST."""
    import schedule
    import time
    from datetime import datetime
    import pytz

    ist = pytz.timezone('Asia/Kolkata')

    def job():
        now = datetime.now(ist)
        print(f"\n[{now.strftime('%Y-%m-%d %H:%M IST')}] Scheduled run starting...")
        run_pipeline()

    schedule.every().day.at("08:30").do(job)
    print("Scheduler active. Will run daily at 08:30 AM IST.")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
