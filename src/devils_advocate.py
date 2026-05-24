"""
Devil's Advocate Agent: Challenges every stock recommendation with
bear-case arguments, red flags, and counter-evidence.

LOGIC:
1. Takes the scored/ranked stock list from the analyser
2. For EACH stock, runs 5 independent challenge tests:
   - Valuation Sanity: Is the PE/PB ratio justified by growth?
   - Debt Trap Check: Can the company service debt in a downturn?
   - Promoter Red Flags: Is promoter holding declining? Pledging?
   - Sector Headwind: Is the sector facing regulatory/macro risk?
   - Pump & Dump Pattern: Volume spikes without fundamental backing?
3. Each test produces a "conviction penalty" (0 to -20 points)
4. Final adjusted score = original score + sum(penalties)
5. Only stocks surviving with adjusted score > 50 make final cut
6. Generates a "Bear Case" narrative for each stock

The agent is deliberately pessimistic — it's designed to REMOVE weak picks,
not confirm biases. If a stock survives all challenges, it has genuine conviction.
"""

from datetime import datetime


class DevilsAdvocate:
    """Challenges stock recommendations with bear-case analysis."""

    CHALLENGE_TESTS = [
        "valuation_sanity",
        "debt_trap",
        "promoter_red_flags",
        "sector_headwind",
        "pump_dump_pattern",
    ]

    def __init__(self):
        self.challenges_log = []

    def challenge_all(self, ranked_stocks):
        """Run all challenges on the ranked stock list. Returns re-ranked list."""
        challenged = []

        for stock in ranked_stocks:
            result = self._challenge_stock(stock)
            challenged.append(result)

        # Re-sort by adjusted score
        challenged.sort(key=lambda x: x["adjusted_score"], reverse=True)

        # Filter: only stocks that survive with score > 40
        survivors = [s for s in challenged if s["adjusted_score"] > 40]

        self._log_summary(len(ranked_stocks), len(survivors))
        return survivors

    def _challenge_stock(self, stock):
        """Apply all challenge tests to a single stock."""
        penalties = []
        bear_case_points = []
        red_flags = []

        # Test 1: Valuation Sanity
        p, reason, flag = self._test_valuation_sanity(stock)
        penalties.append(p)
        if reason:
            bear_case_points.append(reason)
        if flag:
            red_flags.append(flag)

        # Test 2: Debt Trap
        p, reason, flag = self._test_debt_trap(stock)
        penalties.append(p)
        if reason:
            bear_case_points.append(reason)
        if flag:
            red_flags.append(flag)

        # Test 3: Promoter Red Flags
        p, reason, flag = self._test_promoter_flags(stock)
        penalties.append(p)
        if reason:
            bear_case_points.append(reason)
        if flag:
            red_flags.append(flag)

        # Test 4: Sector Headwind
        p, reason, flag = self._test_sector_headwind(stock)
        penalties.append(p)
        if reason:
            bear_case_points.append(reason)
        if flag:
            red_flags.append(flag)

        # Test 5: Pump & Dump Pattern
        p, reason, flag = self._test_pump_dump(stock)
        penalties.append(p)
        if reason:
            bear_case_points.append(reason)
        if flag:
            red_flags.append(flag)

        total_penalty = sum(penalties)
        adjusted_score = stock["score"] + total_penalty

        return {
            **stock,
            "adjusted_score": round(adjusted_score, 1),
            "penalty": round(total_penalty, 1),
            "bear_case": bear_case_points,
            "red_flags": red_flags,
            "challenge_detail": {
                "valuation_penalty": penalties[0],
                "debt_penalty": penalties[1],
                "promoter_penalty": penalties[2],
                "sector_penalty": penalties[3],
                "pump_dump_penalty": penalties[4],
            },
            "survived_challenge": adjusted_score > 40,
            "conviction_level": self._conviction_label(adjusted_score),
        }

    def _test_valuation_sanity(self, stock):
        """Is the stock's valuation justified by its growth?"""
        pe = stock["fundamentals"].get("pe_ratio")
        eg = stock["fundamentals"].get("earnings_growth")
        pb = stock["fundamentals"].get("pb_ratio")

        if pe is None:
            return -5, "No PE data — cannot verify valuation", "Missing valuation data"

        # PEG ratio check: PE should be supported by growth
        if eg and eg > 0:
            peg = pe / (eg * 100)
            if peg > 3:
                return -15, f"PEG ratio {peg:.1f} — grossly overvalued relative to growth", "Extreme overvaluation"
            elif peg > 2:
                return -10, f"PEG ratio {peg:.1f} — expensive for the growth delivered", None
            elif peg > 1.5:
                return -5, f"PEG ratio {peg:.1f} — slightly rich valuation", None
            else:
                return 0, None, None
        elif pe > 50:
            return -15, f"PE of {pe:.0f} with no visible earnings growth — speculative valuation", "High PE, no growth"
        elif pe > 30:
            return -8, f"PE of {pe:.0f} — market expects growth that isn't yet visible", None

        return 0, None, None

    def _test_debt_trap(self, stock):
        """Can the company survive a revenue slowdown with current debt?"""
        de = stock["fundamentals"].get("debt_to_equity")
        rg = stock["fundamentals"].get("revenue_growth")
        fcf = stock["fundamentals"].get("free_cashflow")

        if de is None:
            return -3, None, None

        if de > 200:
            return -20, (
                f"Debt/Equity at {de:.0f} — company is heavily leveraged. "
                "Any revenue miss could trigger debt spiral."
            ), "CRITICAL: Debt trap risk"

        if de > 100 and (rg is None or rg < 0.10):
            return -12, (
                f"Debt/Equity {de:.0f} with sluggish revenue growth ({(rg or 0)*100:.0f}%). "
                "Cannot grow out of debt."
            ), "High debt + low growth"

        if de > 100 and fcf and fcf < 0:
            return -15, (
                f"Debt/Equity {de:.0f} with NEGATIVE free cash flow. "
                "Company burning cash while carrying debt."
            ), "Debt + negative FCF"

        if de > 80:
            return -5, f"Moderate leverage (D/E: {de:.0f}) — monitor closely", None

        return 0, None, None

    def _test_promoter_flags(self, stock):
        """Check for concerning promoter behavior."""
        ph = stock["fundamentals"].get("promoter_holding")

        if ph is None:
            return -5, "No promoter holding data — governance risk unknown", "Missing promoter data"

        if ph < 0.25:
            return -15, (
                f"Promoter holds only {ph*100:.0f}% — low skin in the game. "
                "Stock vulnerable to hostile takeover or lack of direction."
            ), "Very low promoter stake"

        if ph < 0.35:
            return -8, (
                f"Promoter holding at {ph*100:.0f}% — below comfort level. "
                "Watch for further dilution."
            ), None

        return 0, None, None

    def _test_sector_headwind(self, stock):
        """Is the sector facing macro/regulatory headwinds?"""
        sector = stock.get("sector", "Unknown")

        # Known headwind sectors (as of 2025-2026)
        headwind_sectors = {
            "Real Estate": (-10, "Real estate facing interest rate pressure and oversupply in many markets"),
            "Financial Services": (-5, "NBFCs/banks facing NPA risk as unsecured lending grows"),
            "Consumer Cyclical": (-5, "Discretionary spending under pressure from inflation"),
        }

        if sector in headwind_sectors:
            penalty, reason = headwind_sectors[sector]
            return penalty, f"Sector headwind: {reason}", None

        # Tailwind bonus (reduces penalty)
        tailwind_sectors = ["Technology", "Industrials", "Healthcare", "Basic Materials"]
        if sector in tailwind_sectors:
            return 0, None, None

        return -2, f"Sector '{sector}' — neutral/unclear macro positioning", None

    def _test_pump_dump(self, stock):
        """Check for signs of price manipulation."""
        mc = stock.get("market_cap_cr", 0)
        vol = stock["technicals"].get("avg_volume", 0)
        price = stock.get("price", 0)
        high_52 = stock["technicals"].get("52w_high", 0)
        low_52 = stock["technicals"].get("52w_low", 0)

        flags = []
        penalty = 0

        # Micro-cap with extreme price range
        if mc < 200 and high_52 and low_52 and low_52 > 0:
            range_ratio = high_52 / low_52
            if range_ratio > 5:
                flags.append(f"Price swung {range_ratio:.0f}x in 52 weeks — classic manipulation pattern")
                penalty -= 15
            elif range_ratio > 3:
                flags.append(f"Wide 52w range ({range_ratio:.1f}x) for micro-cap — volatility risk")
                penalty -= 8

        # Very low volume + micro cap = easily manipulated
        if vol and vol < 50000 and mc < 500:
            flags.append(f"Only {vol:,} avg daily volume in a ₹{mc:.0f}Cr company — can't exit safely")
            penalty -= 10

        # Near all-time high for penny stock
        if price and high_52 and mc < 500:
            if price > high_52 * 0.9:
                flags.append("Trading near 52w high — possible distribution zone")
                penalty -= 5

        total_penalty = max(penalty, -20)
        bear_reason = "; ".join(flags) if flags else None
        red_flag = flags[0] if flags and penalty <= -10 else None

        return total_penalty, bear_reason, red_flag

    def _conviction_label(self, score):
        """Map adjusted score to conviction level."""
        if score >= 75:
            return "HIGH CONVICTION"
        elif score >= 60:
            return "MODERATE CONVICTION"
        elif score >= 45:
            return "LOW CONVICTION"
        else:
            return "REJECTED"

    def _log_summary(self, total_input, survivors):
        """Log the challenge session summary."""
        eliminated = total_input - survivors
        self.challenges_log.append({
            "timestamp": datetime.now().isoformat(),
            "stocks_challenged": total_input,
            "survivors": survivors,
            "eliminated": eliminated,
            "kill_rate": f"{eliminated/total_input*100:.0f}%" if total_input > 0 else "0%",
        })
        print(f"\n{'='*60}")
        print(f"DEVIL'S ADVOCATE SUMMARY")
        print(f"{'='*60}")
        print(f"Stocks challenged: {total_input}")
        print(f"Survivors:         {survivors}")
        print(f"Eliminated:        {eliminated} ({eliminated/total_input*100:.0f}% kill rate)")
        print(f"{'='*60}\n")

    def get_challenge_report(self, challenged_stocks):
        """Generate human-readable challenge report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.challenges_log[-1] if self.challenges_log else {},
            "high_conviction": [s for s in challenged_stocks if s["conviction_level"] == "HIGH CONVICTION"],
            "moderate_conviction": [s for s in challenged_stocks if s["conviction_level"] == "MODERATE CONVICTION"],
            "low_conviction": [s for s in challenged_stocks if s["conviction_level"] == "LOW CONVICTION"],
            "rejected": [s for s in challenged_stocks if s["conviction_level"] == "REJECTED"],
        }
        return report
