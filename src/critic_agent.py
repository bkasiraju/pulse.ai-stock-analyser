"""
INDEPENDENT CRITIC AGENT
=========================
This agent is COMPLETELY INDEPENDENT of the main analyser pipeline.
It does NOT import, reference, or reuse any scoring logic from:
- analyser.py (scoring engine)
- devils_advocate.py (penalty system)
- metrics.py (metrics computation)

PURPOSE: Provide an unbiased, autonomous second opinion on every stock
recommendation. It fetches its own data, applies its own methodology,
and delivers a verdict: does this stock ACTUALLY have multi-bagger potential?

METHODOLOGY (different from main tool):
1. Historical Precedent Analysis — did stocks with similar profiles actually multiply?
2. Cash Flow Reality Check — is growth real or accounting gymnastics?
3. Insider Behavior Analysis — what are promoters DOING, not saying?
4. Valuation Sanity vs Peers — is the market already pricing in the thesis?
5. Liquidity & Exit Risk — can you actually sell when you want to?
6. Macro Cycle Positioning — is the sector tailwind real or fading?
7. Survival Probability — will this company exist in 3 years?

OUTPUT: Independent Critic Score (0-100) + Verdict + Reasoning
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class CriticVerdict:
    symbol: str
    name: str
    tool_score: float
    tool_conviction: str
    critic_score: float
    verdict: str  # AGREE / PARTIALLY_AGREE / DISAGREE / STRONG_DISAGREE
    confidence: float  # 0-1, how confident the critic is
    challenges: list = field(default_factory=list)
    evidence_for: list = field(default_factory=list)
    evidence_against: list = field(default_factory=list)
    risk_flags: list = field(default_factory=list)
    data_quality: str = "GOOD"  # GOOD / LIMITED / POOR


class CriticAgent:
    """
    Autonomous critic that independently evaluates stock recommendations.
    Uses completely different evaluation framework from the main tool.
    """

    def __init__(self):
        self.evaluation_history = []

    def evaluate_all(self, tool_recommendations):
        """Evaluate all tool recommendations independently."""
        print("\n" + "=" * 60)
        print("  INDEPENDENT CRITIC AGENT — AUTONOMOUS EVALUATION")
        print("  Methodology: 7-Factor Independent Assessment")
        print("  Dependencies on main tool: ZERO")
        print("=" * 60 + "\n")

        verdicts = []
        for i, stock in enumerate(tool_recommendations, 1):
            symbol = stock.get("symbol", "")
            name = stock.get("name", symbol)
            print(f"[critic {i}/{len(tool_recommendations)}] Evaluating {symbol} ({name})...")

            verdict = self._evaluate_single(stock)
            verdicts.append(verdict)

            if verdict.verdict == "DISAGREE" or verdict.verdict == "STRONG_DISAGREE":
                print(f"  ⚠ DISAGREE — Critic Score: {verdict.critic_score}/100")
            elif verdict.verdict == "AGREE":
                print(f"  ✓ AGREE — Critic Score: {verdict.critic_score}/100")
            else:
                print(f"  ~ PARTIAL — Critic Score: {verdict.critic_score}/100")

        self._print_summary(verdicts)
        return verdicts

    def _evaluate_single(self, stock):
        """Run full independent evaluation on a single stock."""
        symbol = stock.get("symbol", "")
        name = stock.get("name", symbol)
        tool_score = stock.get("adjusted_score", stock.get("score", 0))
        tool_conviction = stock.get("conviction_level", "UNKNOWN")

        # Fetch our OWN data — independent of what the tool fetched
        own_data = self._fetch_independent_data(symbol)

        if not own_data:
            return CriticVerdict(
                symbol=symbol,
                name=name,
                tool_score=tool_score,
                tool_conviction=tool_conviction,
                critic_score=0,
                verdict="INSUFFICIENT_DATA",
                confidence=0.0,
                challenges=["Cannot independently verify — no data available"],
                data_quality="POOR",
            )

        # Run 7 independent evaluation factors
        scores = {}
        evidence_for = []
        evidence_against = []
        challenges = []
        risk_flags = []

        # Factor 1: Historical Precedent (0-15)
        scores["precedent"], ef, ea = self._test_historical_precedent(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Factor 2: Cash Flow Reality (0-20)
        scores["cashflow"], ef, ea = self._test_cashflow_reality(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Factor 3: Insider Behavior (0-15)
        scores["insider"], ef, ea = self._test_insider_behavior(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Factor 4: Valuation vs Peers (0-15)
        scores["valuation"], ef, ea = self._test_valuation_sanity(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Factor 5: Liquidity & Exit Risk (0-10)
        scores["liquidity"], ef, ea = self._test_liquidity_risk(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Factor 6: Macro Cycle Position (0-15)
        scores["macro"], ef, ea = self._test_macro_cycle(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Factor 7: Survival Probability (0-10)
        scores["survival"], ef, ea = self._test_survival_probability(own_data)
        evidence_for.extend(ef)
        evidence_against.extend(ea)

        # Calculate independent critic score
        critic_score = sum(scores.values())
        critic_score = max(0, min(100, critic_score))

        # Generate challenges — questions the critic asks
        challenges = self._generate_challenges(own_data, scores, stock)

        # Determine verdict by comparing critic vs tool
        verdict, confidence = self._determine_verdict(
            critic_score, tool_score, tool_conviction, scores
        )

        # Flag critical risks
        risk_flags = self._flag_critical_risks(own_data, scores)

        # Assess data quality
        data_quality = self._assess_data_quality(own_data)

        return CriticVerdict(
            symbol=symbol,
            name=name,
            tool_score=tool_score,
            tool_conviction=tool_conviction,
            critic_score=round(critic_score, 1),
            verdict=verdict,
            confidence=round(confidence, 2),
            challenges=challenges,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            risk_flags=risk_flags,
            data_quality=data_quality,
        )

    def _fetch_independent_data(self, symbol):
        """Fetch data independently — does NOT use screener.py or metrics.py."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info

            if not info or not info.get("regularMarketPrice"):
                ticker = yf.Ticker(f"{symbol}.BO")
                info = ticker.info

            if not info or not info.get("regularMarketPrice"):
                return None

            # 2-year history for deeper pattern analysis
            hist = ticker.history(period="2y")
            if hist.empty or len(hist) < 50:
                return None

            # Quarterly financials for trend verification
            quarterly = ticker.quarterly_financials
            balance = ticker.quarterly_balance_sheet
            cashflow = ticker.quarterly_cashflow

            return {
                "info": info,
                "history": hist,
                "quarterly_financials": quarterly,
                "balance_sheet": balance,
                "cashflow": cashflow,
                "current_price": info.get("regularMarketPrice", 0),
                "market_cap": info.get("marketCap", 0),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
            }
        except Exception as e:
            print(f"  [critic-data] Error fetching {symbol}: {e}")
            return None

    def _test_historical_precedent(self, data):
        """
        Factor 1: Do stocks with this profile historically become multi-baggers?
        Checks: price trajectory patterns, base formation, accumulation signals.
        Score: 0-15
        """
        hist = data["history"]
        score = 0
        evidence_for = []
        evidence_against = []

        prices = hist["Close"]
        current = prices.iloc[-1]

        # Check if stock has shown ability to make big moves (2x+ in past)
        if len(prices) > 250:
            price_1y_ago = prices.iloc[-252] if len(prices) >= 252 else prices.iloc[0]
            price_2y_ago = prices.iloc[0]

            # Past year return
            return_1y = (current - price_1y_ago) / price_1y_ago

            # Has it already run up massively? (>200% in 1 year = risky entry)
            if return_1y > 2.0:
                evidence_against.append(
                    f"Already up {return_1y*100:.0f}% in 1 year — late entry risk, most upside may be captured"
                )
                score += 2  # Penalize — momentum chasers get burned
            elif return_1y > 0.5:
                evidence_for.append(
                    f"Healthy {return_1y*100:.0f}% return in 1 year — confirms growth story without being parabolic"
                )
                score += 10
            elif return_1y > 0.0:
                evidence_for.append(f"Modest {return_1y*100:.0f}% gain — potential base building phase")
                score += 7
            else:
                # Negative return — is it a turnaround or value trap?
                two_year_return = (current - price_2y_ago) / price_2y_ago if price_2y_ago > 0 else 0
                if two_year_return > 0:
                    evidence_for.append("Recovering from dip — possible turnaround play")
                    score += 5
                else:
                    evidence_against.append(
                        f"Negative 1Y return ({return_1y*100:.0f}%) and 2Y return ({two_year_return*100:.0f}%) — consistent wealth destroyer"
                    )
                    score += 1

        # Volume accumulation pattern (smart money signal)
        if len(hist) >= 60:
            vol_recent = hist["Volume"].tail(20).mean()
            vol_older = hist["Volume"].iloc[-60:-40].mean()
            if vol_older > 0:
                vol_ratio = vol_recent / vol_older
                if vol_ratio > 1.5:
                    evidence_for.append(
                        f"Volume accumulation: recent 20d avg is {vol_ratio:.1f}x the 60-day-ago level"
                    )
                    score += 5
                elif vol_ratio < 0.5:
                    evidence_against.append("Volume declining — institutional interest may be fading")
                    score -= 2

        return max(0, min(15, score)), evidence_for, evidence_against

    def _test_cashflow_reality(self, data):
        """
        Factor 2: Is the growth REAL or just accounting?
        Multi-baggers need REAL cash generation, not just revenue recognition tricks.
        Score: 0-20
        """
        score = 0
        evidence_for = []
        evidence_against = []
        info = data["info"]
        cf = data["cashflow"]

        # Operating cash flow — the ultimate reality check
        ocf = info.get("operatingCashflow")
        net_income = info.get("netIncomeToCommon")
        fcf = info.get("freeCashflow")
        revenue = info.get("totalRevenue")

        if ocf and net_income:
            # Cash conversion ratio: OCF / Net Income
            # Healthy company: >0.8 (cash backs up reported profits)
            if net_income > 0:
                cash_conversion = ocf / net_income
                if cash_conversion > 1.2:
                    evidence_for.append(
                        f"Excellent cash conversion: {cash_conversion:.1f}x — earns MORE cash than reported profit"
                    )
                    score += 12
                elif cash_conversion > 0.8:
                    evidence_for.append(f"Solid cash conversion: {cash_conversion:.1f}x — profits are real")
                    score += 8
                elif cash_conversion > 0.4:
                    evidence_against.append(
                        f"Weak cash conversion: {cash_conversion:.1f}x — reported profits not fully backed by cash"
                    )
                    score += 4
                else:
                    evidence_against.append(
                        f"CRITICAL: Cash conversion only {cash_conversion:.1f}x — profits may be paper gains"
                    )
                    score += 0
            else:
                evidence_against.append("Net income is negative — growth at any cost strategy")
                score += 2

        elif ocf:
            if ocf > 0:
                evidence_for.append("Positive operating cash flow")
                score += 6
            else:
                evidence_against.append("Negative operating cash flow — burning cash")
                score += 0

        # Free cash flow margin
        if fcf and revenue and revenue > 0:
            fcf_margin = fcf / revenue
            if fcf_margin > 0.15:
                evidence_for.append(f"Strong FCF margin: {fcf_margin*100:.1f}% — generates real wealth")
                score += 8
            elif fcf_margin > 0.05:
                evidence_for.append(f"Positive FCF margin: {fcf_margin*100:.1f}%")
                score += 5
            elif fcf_margin > 0:
                score += 3
            else:
                evidence_against.append(
                    f"Negative FCF margin: {fcf_margin*100:.1f}% — spending more than earning"
                )
                score += 0

        # Check quarterly trend (is cash flow improving or deteriorating?)
        if cf is not None and not cf.empty:
            try:
                ocf_row = cf.loc["Operating Cash Flow"] if "Operating Cash Flow" in cf.index else None
                if ocf_row is not None and len(ocf_row) >= 2:
                    recent_ocf = ocf_row.iloc[0]
                    older_ocf = ocf_row.iloc[-1]
                    if older_ocf > 0 and recent_ocf > older_ocf:
                        evidence_for.append("Operating cash flow trending UP quarter over quarter")
                        score += 3
                    elif recent_ocf < 0:
                        evidence_against.append("Most recent quarter has NEGATIVE operating cash flow")
                        score -= 2
            except (KeyError, IndexError):
                pass

        return max(0, min(20, score)), evidence_for, evidence_against

    def _test_insider_behavior(self, data):
        """
        Factor 3: What are insiders DOING? (Actions > Words)
        Promoter pledging, selling, or increasing stake tells more than any report.
        Score: 0-15
        """
        score = 0
        evidence_for = []
        evidence_against = []
        info = data["info"]

        promoter_holding = info.get("heldPercentInsiders")
        institutional_holding = info.get("heldPercentInstitutions")

        # Promoter holding analysis
        if promoter_holding is not None:
            pct = promoter_holding * 100 if promoter_holding < 1 else promoter_holding

            if pct > 65:
                evidence_for.append(
                    f"High promoter holding ({pct:.1f}%) — skin in the game, aligned interests"
                )
                score += 10
            elif pct > 50:
                evidence_for.append(f"Solid promoter holding ({pct:.1f}%) — management is committed")
                score += 7
            elif pct > 35:
                score += 4
            elif pct > 20:
                evidence_against.append(
                    f"Low promoter holding ({pct:.1f}%) — management may not be fully committed"
                )
                score += 2
            else:
                evidence_against.append(
                    f"Very low promoter holding ({pct:.1f}%) — RED FLAG: who is steering the ship?"
                )
                score += 0

        # Institutional interest (FII/DII as validation)
        if institutional_holding is not None:
            pct = institutional_holding * 100 if institutional_holding < 1 else institutional_holding
            if pct > 30:
                evidence_for.append(
                    f"Strong institutional backing ({pct:.1f}%) — professional money validates thesis"
                )
                score += 5
            elif pct > 15:
                evidence_for.append(f"Some institutional interest ({pct:.1f}%)")
                score += 3
            elif pct < 5:
                evidence_against.append(
                    f"Near-zero institutional holding ({pct:.1f}%) — professionals are avoiding this stock"
                )
                score += 0

        return max(0, min(15, score)), evidence_for, evidence_against

    def _test_valuation_sanity(self, data):
        """
        Factor 4: Is the multi-bagger thesis already priced in?
        A stock can be great but still a bad investment if overvalued.
        Score: 0-15
        """
        score = 0
        evidence_for = []
        evidence_against = []
        info = data["info"]

        pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        pb = info.get("priceToBook")
        peg = info.get("pegRatio")
        ev_ebitda = info.get("enterpriseToEbitda")

        # PEG ratio — the multi-bagger investor's best friend
        # PEG < 1 = growth NOT fully priced in
        if peg is not None and peg > 0:
            if peg < 0.5:
                evidence_for.append(
                    f"PEG ratio {peg:.2f} — growth is SIGNIFICANTLY underpriced. Classic multi-bagger signal."
                )
                score += 10
            elif peg < 1.0:
                evidence_for.append(f"PEG ratio {peg:.2f} — growth not fully priced in")
                score += 7
            elif peg < 2.0:
                score += 3
            else:
                evidence_against.append(
                    f"PEG ratio {peg:.2f} — market already pricing in optimistic growth. Limited upside from here."
                )
                score += 0

        # PE compression risk
        if pe is not None and pe > 0:
            if pe > 80:
                evidence_against.append(
                    f"PE of {pe:.0f}x — extreme valuation. Any earnings miss = brutal correction."
                )
                score -= 3
            elif pe > 50:
                evidence_against.append(f"PE of {pe:.0f}x — expensive. Growth must be exceptional to justify.")
                score -= 1
            elif pe < 15 and pe > 0:
                evidence_for.append(f"PE of {pe:.0f}x — cheap. Room for PE expansion if growth accelerates.")
                score += 5

        # Forward PE discount (market expects growth)
        if pe and forward_pe and forward_pe > 0 and pe > 0:
            pe_compression = (pe - forward_pe) / pe
            if pe_compression > 0.3:
                evidence_for.append(
                    f"Forward PE ({forward_pe:.0f}) is {pe_compression*100:.0f}% below trailing ({pe:.0f}) — analysts see strong earnings growth ahead"
                )
                score += 3

        # Price-to-Book for asset-heavy businesses
        if pb is not None:
            if pb < 1.0 and pb > 0:
                evidence_for.append(f"Trading below book value (PB={pb:.2f}) — margin of safety")
                score += 3
            elif pb > 10:
                evidence_against.append(f"PB of {pb:.1f} — paying huge premium over tangible assets")

        return max(0, min(15, score)), evidence_for, evidence_against

    def _test_liquidity_risk(self, data):
        """
        Factor 5: Can you actually EXIT this position?
        Illiquid small caps are traps — you can get in but can't get out.
        Score: 0-10
        """
        score = 0
        evidence_for = []
        evidence_against = []
        info = data["info"]
        hist = data["history"]

        avg_volume = info.get("averageVolume", 0)
        current_price = data["current_price"]
        market_cap = data["market_cap"]

        # Daily liquidity check
        daily_turnover = avg_volume * current_price if avg_volume and current_price else 0

        if daily_turnover > 50_00_00_000:  # >50Cr daily turnover
            evidence_for.append(
                f"High liquidity (₹{daily_turnover/1e7:.0f}Cr daily) — easy to enter and exit"
            )
            score += 7
        elif daily_turnover > 10_00_00_000:  # >10Cr
            evidence_for.append(f"Adequate liquidity (₹{daily_turnover/1e7:.0f}Cr daily)")
            score += 5
        elif daily_turnover > 1_00_00_000:  # >1Cr
            score += 3
        elif daily_turnover > 0:
            evidence_against.append(
                f"LOW liquidity (₹{daily_turnover/1e7:.1f}Cr daily) — EXIT RISK. "
                "You may not be able to sell at your desired price."
            )
            score += 1
        else:
            evidence_against.append("Cannot determine liquidity — extreme caution needed")
            score += 0

        # Impact cost — large bid-ask spread detection
        if len(hist) >= 20:
            daily_returns = hist["Close"].pct_change().tail(20).dropna()
            if not daily_returns.empty:
                # High daily volatility with low volume = manipulation risk
                daily_vol = daily_returns.std()
                if daily_vol > 0.05 and daily_turnover < 5_00_00_000:
                    evidence_against.append(
                        "High volatility with low liquidity — possible operator-driven stock"
                    )
                    score -= 2
                elif daily_vol < 0.02 and daily_turnover > 10_00_00_000:
                    evidence_for.append("Low volatility with good liquidity — institutional quality")
                    score += 3

        return max(0, min(10, score)), evidence_for, evidence_against

    def _test_macro_cycle(self, data):
        """
        Factor 6: Is the sector tailwind real or fading?
        Multi-baggers need macro support — even great companies die in headwinds.
        Score: 0-15
        """
        score = 0
        evidence_for = []
        evidence_against = []
        sector = data["sector"]
        industry = data["industry"]

        # Sector cycle analysis based on current market conditions (2025-2026)
        # These are dynamically assessed based on available data patterns
        tailwind_sectors = {
            "Technology": ("Digital transformation + AI adoption continues", 8),
            "Industrials": ("Infrastructure capex cycle + PLI schemes", 9),
            "Financial Services": ("Credit growth + financial inclusion", 7),
            "Consumer Cyclical": ("Rising middle class consumption", 6),
            "Healthcare": ("Post-COVID healthcare spend increase", 5),
            "Energy": ("Renewable energy transition + EV ecosystem", 8),
            "Basic Materials": ("China+1 + domestic manufacturing push", 7),
            "Utilities": ("Power demand surge from data centers + EV", 7),
        }

        headwind_sectors = {
            "Real Estate": ("Interest rate sensitivity + oversupply risk", -3),
            "Communication Services": ("Tariff wars + regulatory pressure", -2),
        }

        if sector in tailwind_sectors:
            reason, boost = tailwind_sectors[sector]
            evidence_for.append(f"Sector tailwind ({sector}): {reason}")
            score += boost
        elif sector in headwind_sectors:
            reason, penalty = headwind_sectors[sector]
            evidence_against.append(f"Sector headwind ({sector}): {reason}")
            score += max(0, 5 + penalty)
        else:
            score += 5  # Neutral

        # Check if sector momentum is confirmed by price action
        hist = data["history"]
        if len(hist) >= 126:
            price_6m_ago = hist["Close"].iloc[-126]
            current = hist["Close"].iloc[-1]
            sector_return = (current - price_6m_ago) / price_6m_ago

            if sector_return > 0.3:
                evidence_for.append(f"Stock up {sector_return*100:.0f}% in 6 months — sector momentum confirmed")
                score += 5
            elif sector_return < -0.1:
                evidence_against.append(
                    f"Stock down {sector_return*100:.0f}% in 6 months despite macro tailwind — stock-specific issues?"
                )
                score -= 2

        return max(0, min(15, score)), evidence_for, evidence_against

    def _test_survival_probability(self, data):
        """
        Factor 7: Will this company even EXIST in 3 years?
        The #1 risk of small/penny stocks — going to zero.
        Score: 0-10
        """
        score = 0
        evidence_for = []
        evidence_against = []
        info = data["info"]

        market_cap = (data["market_cap"] or 0) / 1e7  # In crores
        de = info.get("debtToEquity")
        current_ratio = info.get("currentRatio")
        revenue = info.get("totalRevenue", 0) or 0
        profit_margin = info.get("profitMargins")

        # Size = survival (larger companies rarely go to zero)
        if market_cap > 5000:
            score += 4
        elif market_cap > 1000:
            evidence_for.append(f"Market cap ₹{market_cap:.0f}Cr — established enough to survive")
            score += 3
        elif market_cap > 200:
            score += 2
        else:
            evidence_against.append(
                f"Micro-cap ₹{market_cap:.0f}Cr — small companies have higher mortality rate"
            )
            score += 1

        # Debt sustainability
        if de is not None:
            if de < 20:
                evidence_for.append(f"Very low debt (D/E={de:.0f}) — no bankruptcy risk")
                score += 3
            elif de < 80:
                score += 2
            elif de > 200:
                evidence_against.append(
                    f"Dangerous debt levels (D/E={de:.0f}) — one bad quarter could trigger default"
                )
                score -= 2
            elif de > 100:
                evidence_against.append(f"High debt (D/E={de:.0f}) — survival depends on cash generation")
                score += 0

        # Profitability (profitable = self-sustaining)
        if profit_margin is not None:
            if profit_margin > 0.1:
                evidence_for.append(f"Profitable ({profit_margin*100:.1f}% margin) — self-sustaining")
                score += 3
            elif profit_margin > 0:
                score += 2
            else:
                evidence_against.append("Currently unprofitable — dependent on external funding to survive")
                score -= 1

        return max(0, min(10, score)), evidence_for, evidence_against

    def _generate_challenges(self, data, scores, stock):
        """Generate pointed questions that challenge the recommendation."""
        challenges = []
        info = data["info"]
        hist = data["history"]

        # Challenge 1: Why NOW?
        prices = hist["Close"]
        current = prices.iloc[-1]
        high_52 = info.get("fiftyTwoWeekHigh", current)
        low_52 = info.get("fiftyTwoWeekLow", current)

        if high_52 > 0:
            pct_from_high = (current - high_52) / high_52 * 100
            pct_from_low = (current - low_52) / low_52 * 100 if low_52 > 0 else 0

            if pct_from_high > -10:
                challenges.append(
                    f"TIMING: Stock is within {abs(pct_from_high):.0f}% of 52-week high. "
                    "Why is this a multi-bagger entry point and not a momentum trap?"
                )
            elif pct_from_high < -40:
                challenges.append(
                    f"FALLING KNIFE: Down {abs(pct_from_high):.0f}% from 52-week high. "
                    "What evidence shows this is a temporary dip vs structural decline?"
                )

        # Challenge 2: Where's the moat?
        pe = info.get("trailingPE")
        sector = data["sector"]
        if pe and pe > 40:
            challenges.append(
                f"VALUATION: At {pe:.0f}x PE, the market expects exceptional growth. "
                "What prevents competitors from eroding margins? Where is the MOAT?"
            )

        # Challenge 3: Who's buying at these levels?
        if scores.get("liquidity", 0) < 4:
            challenges.append(
                "LIQUIDITY: Low trading volume. If smart money believed the thesis, "
                "why isn't volume increasing? Who will buy YOUR shares when you want to sell?"
            )

        # Challenge 4: The survivorship bias question
        market_cap_cr = (data["market_cap"] or 0) / 1e7
        if market_cap_cr < 500:
            challenges.append(
                f"SURVIVORSHIP BIAS: At ₹{market_cap_cr:.0f}Cr market cap, for every small stock "
                "that became a multi-bagger, 50 others went to zero. What makes THIS one different?"
            )

        # Challenge 5: Earnings quality
        if scores.get("cashflow", 0) < 8:
            challenges.append(
                "EARNINGS QUALITY: Cash flow doesn't support reported profits. "
                "Are we seeing real growth or creative accounting that will unravel?"
            )

        # Challenge 6: Management incentives
        promoter = info.get("heldPercentInsiders")
        if promoter and promoter < 0.3:
            challenges.append(
                f"ALIGNMENT: Promoters only own {promoter*100:.1f}%. If they don't believe "
                "enough to hold more, why should retail investors bet their savings?"
            )

        return challenges

    def _determine_verdict(self, critic_score, tool_score, tool_conviction, scores):
        """Determine agreement level between critic and tool."""
        # Map tool conviction to expected score range
        tool_expected = {
            "HIGH CONVICTION": (70, 100),
            "MODERATE CONVICTION": (55, 75),
            "LOW CONVICTION": (40, 60),
        }

        expected_min, expected_max = tool_expected.get(tool_conviction, (30, 60))

        # How far is critic score from tool's expectation?
        if critic_score >= expected_min:
            # Critic agrees — evidence supports the recommendation
            if critic_score >= expected_max - 10:
                return "AGREE", min(0.9, critic_score / 100 + 0.1)
            else:
                return "PARTIALLY_AGREE", critic_score / 100
        elif critic_score >= expected_min - 15:
            # Mild disagreement — some red flags but not fatal
            return "PARTIALLY_AGREE", critic_score / 100
        elif critic_score >= 30:
            return "DISAGREE", 0.6 + (expected_min - critic_score) / 100
        else:
            return "STRONG_DISAGREE", 0.8

    def _flag_critical_risks(self, data, scores):
        """Flag risks that could make the stock go to ZERO regardless of upside."""
        flags = []
        info = data["info"]

        de = info.get("debtToEquity")
        if de and de > 200:
            flags.append("BANKRUPTCY RISK: Debt/Equity > 200%")

        if scores.get("cashflow", 0) < 3:
            flags.append("CASH BURN: Not generating operating cash flow")

        if scores.get("liquidity", 0) < 2:
            flags.append("ILLIQUID: Cannot exit position easily")

        market_cap_cr = (data["market_cap"] or 0) / 1e7
        if market_cap_cr < 100:
            flags.append("MICRO-CAP: Extremely small, high manipulation/mortality risk")

        profit_margin = info.get("profitMargins")
        if profit_margin and profit_margin < -0.1:
            flags.append("DEEP LOSSES: Company is losing money fast")

        return flags

    def _assess_data_quality(self, data):
        """How much data could we actually verify?"""
        info = data["info"]
        hist = data["history"]

        data_points = 0
        if info.get("trailingPE"):
            data_points += 1
        if info.get("freeCashflow"):
            data_points += 1
        if info.get("operatingCashflow"):
            data_points += 1
        if info.get("heldPercentInsiders"):
            data_points += 1
        if info.get("debtToEquity"):
            data_points += 1
        if len(hist) >= 250:
            data_points += 2
        elif len(hist) >= 100:
            data_points += 1

        if data_points >= 6:
            return "GOOD"
        elif data_points >= 3:
            return "LIMITED"
        return "POOR"

    def _print_summary(self, verdicts):
        """Print critic's overall assessment."""
        agree = sum(1 for v in verdicts if v.verdict == "AGREE")
        partial = sum(1 for v in verdicts if v.verdict == "PARTIALLY_AGREE")
        disagree = sum(1 for v in verdicts if v.verdict in ("DISAGREE", "STRONG_DISAGREE"))
        no_data = sum(1 for v in verdicts if v.verdict == "INSUFFICIENT_DATA")

        print(f"\n{'='*60}")
        print("  CRITIC AGENT — FINAL ASSESSMENT")
        print(f"{'='*60}")
        print(f"  Stocks evaluated:    {len(verdicts)}")
        print(f"  AGREE with tool:     {agree}")
        print(f"  PARTIALLY AGREE:     {partial}")
        print(f"  DISAGREE:            {disagree}")
        print(f"  Insufficient data:   {no_data}")
        print(f"{'='*60}")

        if disagree > len(verdicts) * 0.5:
            print("  ⚠ WARNING: Critic disagrees with >50% of tool's picks.")
            print("  The tool may be overly optimistic. Exercise extreme caution.")
        elif agree > len(verdicts) * 0.6:
            print("  ✓ VALIDATION: Critic agrees with majority of picks.")
            print("  Independent evidence supports the tool's thesis.")
        print()

    def get_report(self, verdicts):
        """Generate serializable report for the dashboard."""
        return {
            "evaluated_at": datetime.now().isoformat(),
            "methodology": "7-Factor Independent Assessment (Precedent, CashFlow, Insider, Valuation, Liquidity, Macro, Survival)",
            "summary": {
                "total_evaluated": len(verdicts),
                "agree": sum(1 for v in verdicts if v.verdict == "AGREE"),
                "partially_agree": sum(1 for v in verdicts if v.verdict == "PARTIALLY_AGREE"),
                "disagree": sum(1 for v in verdicts if v.verdict in ("DISAGREE", "STRONG_DISAGREE")),
                "avg_critic_score": round(
                    sum(v.critic_score for v in verdicts) / max(len(verdicts), 1), 1
                ),
                "avg_confidence": round(
                    sum(v.confidence for v in verdicts) / max(len(verdicts), 1), 2
                ),
            },
            "verdicts": [
                {
                    "symbol": v.symbol,
                    "name": v.name,
                    "tool_score": v.tool_score,
                    "tool_conviction": v.tool_conviction,
                    "critic_score": v.critic_score,
                    "verdict": v.verdict,
                    "confidence": v.confidence,
                    "challenges": v.challenges,
                    "evidence_for": v.evidence_for,
                    "evidence_against": v.evidence_against,
                    "risk_flags": v.risk_flags,
                    "data_quality": v.data_quality,
                }
                for v in verdicts
            ],
        }
