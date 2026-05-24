let analysisData = null;
let currentSort = { key: 'adjusted_score', dir: 'desc' };

async function loadAnalysis() {
    try {
        const resp = await fetch('analysis.json');
        const data = await resp.json();
        if (data.error) return;
        analysisData = data;
        renderDashboard();
    } catch (e) {
        console.error('Failed to load analysis:', e);
        const tbody = document.getElementById('stock-tbody');
        tbody.textContent = '';
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 11;
        td.className = 'empty-state';
        td.textContent = 'Failed to load analysis data. Please check back later.';
        tr.appendChild(td);
        tbody.appendChild(tr);
    }
}

function renderDashboard() {
    if (!analysisData) return;

    const summary = analysisData.summary;
    setText('card-total', '.card-value', summary.total_analysed);
    setText('card-survived', '.card-value', summary.survived_challenge);
    setText('card-high', '.card-value', summary.high_conviction);
    setText('card-moderate', '.card-value', summary.moderate_conviction);
    setText('card-rejected', '.card-value', summary.rejected);

    const dt = new Date(analysisData.generated_at);
    document.getElementById('last-updated').textContent = 'Last analysed: ' + dt.toLocaleString('en-IN');

    populateSectorFilter();
    renderTable(analysisData.top_picks);
}

function setText(parentId, selector, value) {
    document.getElementById(parentId).querySelector(selector).textContent = value;
}

function populateSectorFilter() {
    const sectors = [...new Set(analysisData.top_picks.map(s => s.sector))].sort();
    const select = document.getElementById('filter-sector');
    select.textContent = '';
    const defaultOpt = document.createElement('option');
    defaultOpt.value = 'all';
    defaultOpt.textContent = 'All Sectors';
    select.appendChild(defaultOpt);
    sectors.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        select.appendChild(opt);
    });
}

let activeTab = 'all';

function switchTab(tab) {
    activeTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
    });
    applyFilters();
}

function applyFilters() {
    if (!analysisData) return;
    let stocks = analysisData.top_picks;

    if (activeTab !== 'all') stocks = stocks.filter(s => s.classification === activeTab);

    const conv = document.getElementById('filter-conviction').value;
    const sector = document.getElementById('filter-sector').value;
    const search = document.getElementById('filter-search').value.toLowerCase();

    if (conv !== 'all') stocks = stocks.filter(s => s.conviction_level === conv);
    if (sector !== 'all') stocks = stocks.filter(s => s.sector === sector);
    if (search) stocks = stocks.filter(s =>
        s.symbol.toLowerCase().includes(search) ||
        s.name.toLowerCase().includes(search)
    );

    renderTable(stocks);
}

function getCriticVerdict(symbol) {
    if (!analysisData || !analysisData.critic_report) return null;
    return (analysisData.critic_report.verdicts || []).find(v => v.symbol === symbol);
}

function renderTable(stocks) {
    const tbody = document.getElementById('stock-tbody');
    tbody.textContent = '';

    if (!stocks.length) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 12;
        td.className = 'empty-state';
        td.textContent = 'No stocks match filters';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    stocks.sort((a, b) => {
        let va = a[currentSort.key] ?? '';
        let vb = b[currentSort.key] ?? '';
        if (currentSort.key === 'critic_score') {
            const ca = getCriticVerdict(a.symbol);
            const cb = getCriticVerdict(b.symbol);
            va = ca ? ca.critic_score : -1;
            vb = cb ? cb.critic_score : -1;
        }
        if (currentSort.key === 'critic_verdict') {
            const ca = getCriticVerdict(a.symbol);
            const cb = getCriticVerdict(b.symbol);
            va = ca ? ca.verdict : '';
            vb = cb ? cb.verdict : '';
        }
        if (typeof va === 'number') {
            return currentSort.dir === 'asc' ? va - vb : vb - va;
        }
        return currentSort.dir === 'asc'
            ? String(va).localeCompare(String(vb))
            : String(vb).localeCompare(String(va));
    });

    stocks.forEach((s, i) => {
        const tr = document.createElement('tr');
        tr.addEventListener('click', () => showDetail(s.symbol));

        const cells = [
            i + 1,
            s.symbol,
            s.name,
            '₹' + (s.price || 0).toFixed(2),
            '₹' + (s.market_cap_cr || 0).toLocaleString('en-IN') + 'Cr',
        ];

        cells.forEach((val, idx) => {
            const td = document.createElement('td');
            if (idx === 1) {
                const strong = document.createElement('strong');
                strong.textContent = val;
                td.appendChild(strong);
                if (s.breakout_signals && s.breakout_signals.length) {
                    const bo = document.createElement('span');
                    bo.className = 'badge badge-breakout';
                    bo.textContent = 'BO';
                    bo.title = s.breakout_signals[0];
                    td.appendChild(bo);
                }
            } else {
                td.textContent = val;
            }
            tr.appendChild(td);
        });

        const catTd = document.createElement('td');
        const catBadge = document.createElement('span');
        catBadge.className = 'badge badge-' + (s.classification === 'penny' ? 'penny' : s.classification === 'small_cap' ? 'small' : 'mid');
        catBadge.textContent = s.classification;
        catBadge.title = s.classification === 'penny' ? 'Price < ₹100' : s.classification === 'small_cap' ? 'MCap < ₹5,000Cr' : 'MCap < ₹20,000Cr';
        catTd.appendChild(catBadge);
        tr.appendChild(catTd);

        const scoreTd = document.createElement('td');
        scoreTd.textContent = s.score;
        scoreTd.title = 'Raw score from fundamental + technical + momentum analysis';
        tr.appendChild(scoreTd);

        const adjTd = document.createElement('td');
        const adjStrong = document.createElement('strong');
        adjStrong.textContent = s.adjusted_score;
        adjTd.title = 'Penalty: ' + (s.penalty || 0) + ' (Valuation + Debt + Promoter + Sector + Pump/Dump checks)';
        adjTd.appendChild(adjStrong);
        tr.appendChild(adjTd);

        const convTd = document.createElement('td');
        const convBadge = document.createElement('span');
        convBadge.className = 'badge badge-' + convictionClass(s.conviction_level);
        convBadge.textContent = s.conviction_level;
        convBadge.title = s.conviction_level === 'HIGH CONVICTION' ? 'Score ≥ 75 — strong multi-bagger candidate' : s.conviction_level === 'MODERATE CONVICTION' ? 'Score 60-74 — promising with some risks' : s.conviction_level === 'LOW CONVICTION' ? 'Score 45-59 — speculative, needs more research' : 'Score < 45 — failed challenge, avoid';
        convTd.appendChild(convBadge);
        tr.appendChild(convTd);

        // Critic Score column
        const criticData = getCriticVerdict(s.symbol);
        const criticTd = document.createElement('td');
        if (criticData) {
            const criticVal = document.createElement('strong');
            criticVal.textContent = criticData.critic_score;
            criticVal.style.color = criticData.critic_score >= 60 ? 'var(--success)' : criticData.critic_score >= 40 ? 'var(--warning)' : 'var(--error)';
            criticTd.appendChild(criticVal);
            criticTd.title = 'Independent 7-factor assessment: Precedent, CashFlow, Insider, Valuation, Liquidity, Macro, Survival';
        } else {
            criticTd.textContent = '—';
            criticTd.style.color = 'var(--text-secondary)';
            criticTd.title = 'Critic agent has not evaluated this stock';
        }
        tr.appendChild(criticTd);

        // Critic Verdict column
        const verdictTd = document.createElement('td');
        if (criticData) {
            const verdictBadge = document.createElement('span');
            const vClass = criticData.verdict === 'AGREE' ? 'agree' : (criticData.verdict === 'PARTIALLY_AGREE' ? 'partial' : 'disagree');
            verdictBadge.className = 'critic-verdict-badge ' + vClass;
            verdictBadge.textContent = criticData.verdict === 'PARTIALLY_AGREE' ? 'PARTIAL' : criticData.verdict;
            verdictBadge.title = criticData.verdict === 'AGREE' ? 'Critic fully agrees with tool recommendation' : criticData.verdict === 'PARTIALLY_AGREE' ? 'Critic has reservations but sees some merit' : 'Critic disagrees — independent analysis shows different conclusion';
            verdictTd.appendChild(verdictBadge);
        } else {
            verdictTd.textContent = '—';
            verdictTd.style.color = 'var(--text-secondary)';
        }
        tr.appendChild(verdictTd);

        const actTd = document.createElement('td');
        const btn = document.createElement('button');
        btn.className = 'btn btn-secondary';
        btn.textContent = 'Details';
        btn.addEventListener('click', (e) => { e.stopPropagation(); showDetail(s.symbol); });
        actTd.appendChild(btn);
        tr.appendChild(actTd);

        tbody.appendChild(tr);
    });
}

function convictionClass(level) {
    if (level === 'HIGH CONVICTION') return 'high';
    if (level === 'MODERATE CONVICTION') return 'moderate';
    if (level === 'LOW CONVICTION') return 'low';
    return 'rejected';
}

function sortTable(key) {
    if (currentSort.key === key) {
        currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.key = key;
        currentSort.dir = 'desc';
    }
    applyFilters();
}

function showDetail(symbol) {
    const stock = analysisData.top_picks.find(s => s.symbol === symbol);
    if (!stock) return;

    const panel = document.getElementById('detail-panel');
    panel.style.display = 'block';

    document.getElementById('detail-name').textContent =
        stock.symbol + ' — ' + stock.name + ' (₹' + (stock.price || 0).toFixed(2) + ' | ' + stock.conviction_level + ')';

    // Performance pills (period returns)
    renderPerfRow(stock);

    const grid = document.querySelector('.detail-grid');
    grid.textContent = '';

    const fund = stock.fundamentals || {};
    const m = stock.metrics;
    const criticReport = analysisData.critic_report;
    const criticVerdict = criticReport ? (criticReport.verdicts || []).find(v => v.symbol === stock.symbol) : null;
    const expertData = (analysisData.expert_analysis || []).find(e => e.symbol === stock.symbol);

    // --- Section 1: Multi-Bagger Thesis ---
    const thesisSummary = stock.multibagger_thesis && stock.multibagger_thesis.target_multiple ? stock.multibagger_thesis.target_multiple : 'See details';
    grid.appendChild(createCollapsible('Multi-Bagger Thesis', thesisSummary, el => {
        const thesis = stock.multibagger_thesis;
        if (thesis && thesis.thesis && thesis.thesis.length) {
            thesis.thesis.forEach(point => {
                const div = document.createElement('div');
                div.className = 'thesis-point';
                div.textContent = point;
                el.appendChild(div);
            });
        } else {
            el.textContent = 'Insufficient data for multi-bagger thesis.';
        }
    }));

    // --- Section 2: Fundamentals & Metrics ---
    const fundSummary = 'PE: ' + (fund.pe_ratio != null ? fund.pe_ratio.toFixed(1) : 'N/A') +
        ' | ROE: ' + (fund.roe != null ? (fund.roe * 100).toFixed(0) + '%' : 'N/A') +
        ' | D/E: ' + (fund.debt_to_equity != null ? fund.debt_to_equity.toFixed(0) : 'N/A') +
        (m ? ' | RSI: ' + m.rsi_14 + ' | Trend: ' + m.trend : '');
    grid.appendChild(createCollapsible('Fundamentals & Metrics', fundSummary, el => {
        const items = [
            ['PE Ratio', fund.pe_ratio != null ? fund.pe_ratio.toFixed(1) : 'N/A'],
            ['PB Ratio', fund.pb_ratio != null ? fund.pb_ratio.toFixed(2) : 'N/A'],
            ['ROE', fund.roe != null ? (fund.roe * 100).toFixed(1) + '%' : 'N/A'],
            ['Debt/Equity', fund.debt_to_equity != null ? fund.debt_to_equity.toFixed(0) : 'N/A'],
            ['Revenue Growth', fund.revenue_growth != null ? (fund.revenue_growth * 100).toFixed(1) + '%' : 'N/A'],
            ['Earnings Growth', fund.earnings_growth != null ? (fund.earnings_growth * 100).toFixed(1) + '%' : 'N/A'],
            ['Promoter Holding', fund.promoter_holding != null ? (fund.promoter_holding * 100).toFixed(1) + '%' : 'N/A'],
            ['EPS', fund.eps != null ? '₹' + fund.eps.toFixed(2) : 'N/A'],
            ['Book Value', fund.book_value != null ? '₹' + fund.book_value.toFixed(2) : 'N/A'],
        ];
        if (m) {
            items.push(['RSI (14-day)', m.rsi_14]);
            items.push(['Volatility (Ann.)', m.volatility_annual_pct + '%']);
            items.push(['20-Day MA', '₹' + m.ma_20]);
            items.push(['50-Day MA', '₹' + m.ma_50]);
            items.push(['Volume Surge', (m.volume_surge_pct > 0 ? '+' : '') + m.volume_surge_pct + '%']);
            items.push(['Green Months (of 6)', m.green_months_of_6 + '/6']);
            items.push(['Max Drawdown (6M)', m.max_drawdown_pct + '%']);
        }
        const metricsGrid = document.createElement('div');
        metricsGrid.className = 'metrics-grid';
        items.forEach(([label, value]) => {
            const item = document.createElement('div');
            item.className = 'metric-item';
            const lbl = document.createElement('span');
            lbl.className = 'metric-label';
            lbl.textContent = label;
            const val = document.createElement('span');
            val.className = 'metric-value';
            val.textContent = value;
            item.appendChild(lbl);
            item.appendChild(val);
            metricsGrid.appendChild(item);
        });
        el.appendChild(metricsGrid);
    }));

    // --- Section 3: SWOT ---
    const swot = stock.swot || {};
    const swotSummary = (swot.strengths ? swot.strengths.length : 0) + 'S / ' +
        (swot.weaknesses ? swot.weaknesses.length : 0) + 'W / ' +
        (swot.opportunities ? swot.opportunities.length : 0) + 'O / ' +
        (swot.threats ? swot.threats.length : 0) + 'T';
    grid.appendChild(createCollapsible('SWOT Analysis', swotSummary, el => {
        const swotGrid = document.createElement('div');
        swotGrid.className = 'swot-grid';
        ['strengths', 'weaknesses', 'opportunities', 'threats'].forEach(key => {
            const box = document.createElement('div');
            box.className = 'swot-box swot-' + key;
            const h4 = document.createElement('h4');
            h4.textContent = key.charAt(0).toUpperCase() + key.slice(1);
            box.appendChild(h4);
            (swot[key] || []).forEach(item => {
                const p = document.createElement('p');
                p.textContent = item;
                box.appendChild(p);
            });
            swotGrid.appendChild(box);
        });
        el.appendChild(swotGrid);
    }));

    // --- Section 4: Market Intelligence (Insider + Bulk Deals + Retail Interest + Breakout) ---
    const insider = stock.insider_activity || {};
    const institutional = stock.institutional_activity || {};
    const retail = stock.retail_interest || {};
    const breakoutSignals = stock.breakout_signals || [];
    const mktSummary = [
        breakoutSignals.length ? 'Breakout: ' + breakoutSignals.length + ' signal(s)' : '',
        insider.signal && insider.signal !== 'NO_DATA' ? 'Insider: ' + insider.signal : '',
        institutional.signal && institutional.signal !== 'NO_DEALS' ? 'Institutional: ' + institutional.signal : '',
        retail.signal && retail.signal !== 'NO_DATA' ? 'Retail: ' + retail.signal : '',
    ].filter(Boolean).join(' | ') || 'No market intelligence data';
    grid.appendChild(createCollapsible('Market Intelligence (NSE + Trends)', mktSummary, el => {
        // Breakout signals
        if (breakoutSignals.length) {
            const h = document.createElement('p');
            h.style.fontWeight = '600';
            h.style.fontSize = '0.6875rem';
            h.textContent = 'Breakout Signals (Independent Scanner):';
            el.appendChild(h);
            breakoutSignals.forEach(s => {
                const chip = document.createElement('span');
                chip.className = 'signal-chip';
                chip.textContent = s;
                el.appendChild(chip);
            });
        }
        // Insider trades
        if (insider.signal && insider.signal !== 'NO_DATA') {
            const h = document.createElement('p');
            h.style.fontWeight = '600';
            h.style.fontSize = '0.6875rem';
            h.textContent = 'Insider Trading (SEBI PIT Disclosures):';
            el.appendChild(h);
            const sig = document.createElement('span');
            sig.className = 'badge badge-' + (insider.signal === 'STRONG_BUY' || insider.signal === 'BUY' ? 'high' : insider.signal === 'SELL_WARNING' || insider.signal === 'SELL' ? 'rejected' : 'low');
            sig.textContent = insider.signal;
            el.appendChild(sig);
            const sum = document.createElement('p');
            sum.style.fontSize = '0.625rem';
            sum.style.color = 'var(--text-secondary)';
            sum.textContent = insider.summary || '';
            el.appendChild(sum);
            (insider.details || []).forEach(d => {
                const p = document.createElement('p');
                p.style.fontSize = '0.625rem';
                p.textContent = d;
                el.appendChild(p);
            });
        }
        // Institutional
        if (institutional.signal && institutional.signal !== 'NO_DEALS') {
            const h = document.createElement('p');
            h.style.fontWeight = '600';
            h.style.fontSize = '0.6875rem';
            h.style.marginTop = '0.5rem';
            h.textContent = 'Bulk/Block Deals (NSE):';
            el.appendChild(h);
            const sig = document.createElement('span');
            sig.className = 'badge badge-' + (institutional.signal === 'ACCUMULATION' || institutional.signal === 'NET_BUY' ? 'high' : institutional.signal === 'DISTRIBUTION' || institutional.signal === 'NET_SELL' ? 'rejected' : 'low');
            sig.textContent = institutional.signal;
            el.appendChild(sig);
            const sum = document.createElement('p');
            sum.style.fontSize = '0.625rem';
            sum.style.color = 'var(--text-secondary)';
            sum.textContent = institutional.summary || '';
            el.appendChild(sum);
        }
        // Retail interest
        if (retail.signal && retail.signal !== 'NO_DATA') {
            const h = document.createElement('p');
            h.style.fontWeight = '600';
            h.style.fontSize = '0.6875rem';
            h.style.marginTop = '0.5rem';
            h.textContent = 'Google Trends (Retail Interest):';
            el.appendChild(h);
            const sum = document.createElement('p');
            sum.style.fontSize = '0.625rem';
            sum.style.color = 'var(--text-secondary)';
            sum.textContent = retail.summary || '';
            el.appendChild(sum);
            (retail.details || []).forEach(d => {
                const p = document.createElement('p');
                p.style.fontSize = '0.625rem';
                p.textContent = d;
                el.appendChild(p);
            });
        }
        if ((!insider.signal || insider.signal === 'NO_DATA') && (!institutional.signal || institutional.signal === 'NO_DEALS') && (!retail.signal || retail.signal === 'NO_DATA')) {
            el.textContent = 'No market intelligence data available for this stock.';
            el.style.color = 'var(--text-secondary)';
        }
    }));

    // --- Section 5: Critic Agent ---
    const criticSummary = criticVerdict
        ? criticVerdict.verdict.replace('_', ' ') + ' (Score: ' + criticVerdict.critic_score + '/100, Confidence: ' + (criticVerdict.confidence * 100).toFixed(0) + '%)'
        : 'Not evaluated';
    grid.appendChild(createCollapsible('Critic Agent — Independent Verdict', criticSummary, el => {
        if (!criticVerdict) {
            el.textContent = 'Critic agent has not evaluated this stock yet.';
            return;
        }
        const vClass = criticVerdict.verdict === 'AGREE' ? 'agree' : (criticVerdict.verdict === 'PARTIALLY_AGREE' ? 'partial' : 'disagree');
        const badge = document.createElement('span');
        badge.className = 'critic-verdict-badge ' + vClass;
        badge.textContent = criticVerdict.verdict.replace('_', ' ');
        el.appendChild(badge);

        if (criticVerdict.risk_flags && criticVerdict.risk_flags.length) {
            const flags = document.createElement('div');
            flags.style.marginTop = '0.5rem';
            criticVerdict.risk_flags.forEach(f => {
                const chip = document.createElement('span');
                chip.className = 'critic-risk-flag';
                chip.textContent = f;
                flags.appendChild(chip);
            });
            el.appendChild(flags);
        }

        if (criticVerdict.challenges && criticVerdict.challenges.length) {
            const h = document.createElement('p');
            h.style.fontWeight = '600';
            h.style.fontSize = '0.6875rem';
            h.style.margin = '0.5rem 0 0.25rem';
            h.textContent = 'Challenges:';
            el.appendChild(h);
            criticVerdict.challenges.forEach(c => {
                const p = document.createElement('p');
                p.style.fontSize = '0.6875rem';
                p.style.color = 'var(--warning)';
                p.style.marginBottom = '0.25rem';
                p.textContent = c;
                el.appendChild(p);
            });
        }
        if (criticVerdict.evidence_for && criticVerdict.evidence_for.length) {
            criticVerdict.evidence_for.forEach(e => {
                const p = document.createElement('p');
                p.style.fontSize = '0.625rem';
                p.style.color = 'var(--success)';
                p.textContent = '+ ' + e;
                el.appendChild(p);
            });
        }
        if (criticVerdict.evidence_against && criticVerdict.evidence_against.length) {
            criticVerdict.evidence_against.forEach(e => {
                const p = document.createElement('p');
                p.style.fontSize = '0.625rem';
                p.style.color = 'var(--error)';
                p.textContent = '- ' + e;
                el.appendChild(p);
            });
        }
    }));

    // --- Section 6: Risks & Bear Case ---
    const risks = [...(stock.red_flags || []), ...(stock.bear_case || []), ...(swot.threats || [])];
    const riskSummary = risks.length ? risks.length + ' risk factors identified' : 'Low risk profile';
    grid.appendChild(createCollapsible('Risks & Bear Case', riskSummary, el => {
        if (!risks.length) {
            el.textContent = 'Low risk profile — no major flags.';
            el.style.color = 'var(--success)';
            return;
        }
        risks.forEach(r => {
            const p = document.createElement('p');
            p.style.fontSize = '0.6875rem';
            p.style.color = 'var(--error)';
            p.style.marginBottom = '0.25rem';
            p.textContent = '• ' + r;
            el.appendChild(p);
        });
        // Penalties
        const ch = stock.challenge_detail || {};
        if (stock.penalty) {
            const pen = document.createElement('p');
            pen.style.fontSize = '0.625rem';
            pen.style.marginTop = '0.5rem';
            pen.style.color = 'var(--text-secondary)';
            pen.textContent = 'Penalties — Valuation: ' + (ch.valuation_penalty || 0) + ', Debt: ' + (ch.debt_penalty || 0) + ', Promoter: ' + (ch.promoter_penalty || 0) + ', Sector: ' + (ch.sector_penalty || 0) + ', Total: ' + (stock.penalty || 0);
            el.appendChild(pen);
        }
    }));

    // --- Section 7: References & Expert Views (all links) ---
    const refCount = (expertData ? expertData.insights.length : 0);
    const refSummary = refCount ? refCount + ' expert references' + (expertData.sentiment ? ' | Sentiment: ' + expertData.sentiment : '') : 'No references yet';
    grid.appendChild(createCollapsible('References & Expert Views', refSummary, el => {
        // Yahoo Finance link
        const yahooLink = document.createElement('a');
        yahooLink.href = 'https://finance.yahoo.com/quote/' + stock.symbol + '.NS/';
        yahooLink.target = '_blank';
        yahooLink.rel = 'noopener noreferrer';
        yahooLink.textContent = 'Yahoo Finance — ' + stock.symbol;
        yahooLink.className = 'ref-link';
        el.appendChild(yahooLink);

        // Screener.in link
        const screenerLink = document.createElement('a');
        screenerLink.href = 'https://www.screener.in/company/' + stock.symbol + '/';
        screenerLink.target = '_blank';
        screenerLink.rel = 'noopener noreferrer';
        screenerLink.textContent = 'Screener.in — ' + stock.symbol;
        screenerLink.className = 'ref-link';
        el.appendChild(screenerLink);

        // MoneyControl link
        const mcLink = document.createElement('a');
        mcLink.href = 'https://www.moneycontrol.com/india/stockpricequote/' + stock.symbol.toLowerCase();
        mcLink.target = '_blank';
        mcLink.rel = 'noopener noreferrer';
        mcLink.textContent = 'MoneyControl — ' + stock.symbol;
        mcLink.className = 'ref-link';
        el.appendChild(mcLink);

        // Expert YouTube videos
        if (expertData && expertData.insights && expertData.insights.length) {
            const h = document.createElement('p');
            h.style.fontWeight = '600';
            h.style.fontSize = '0.6875rem';
            h.style.margin = '0.75rem 0 0.25rem';
            h.textContent = 'Expert Analysis (YouTube & Social):';
            el.appendChild(h);
            if (expertData.sentiment) {
                const badge = document.createElement('span');
                badge.className = 'expert-sentiment expert-sentiment-' + expertData.sentiment.toLowerCase();
                badge.textContent = 'Sentiment: ' + expertData.sentiment;
                el.appendChild(badge);
            }
            expertData.insights.forEach(ins => {
                const row = document.createElement('div');
                row.style.marginTop = '0.375rem';
                const a = document.createElement('a');
                a.href = ins.url;
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.textContent = ins.title;
                a.className = 'ref-link';
                row.appendChild(a);
                if (ins.channel || ins.views) {
                    const meta = document.createElement('span');
                    meta.style.fontSize = '0.5625rem';
                    meta.style.color = 'var(--text-secondary)';
                    meta.style.marginLeft = '0.5rem';
                    meta.textContent = (ins.channel || '') + (ins.views ? ' • ' + ins.views + ' views' : '') + (ins.published ? ' • ' + ins.published : '');
                    row.appendChild(meta);
                }
                el.appendChild(row);
            });
        }
    }));

    panel.scrollIntoView({ behavior: 'smooth' });
}

function createCollapsible(title, summary, renderContent) {
    const section = document.createElement('div');
    section.className = 'detail-collapsible';

    const header = document.createElement('div');
    header.className = 'collapsible-header';

    const titleEl = document.createElement('span');
    titleEl.className = 'collapsible-title';
    titleEl.textContent = title;
    header.appendChild(titleEl);

    const summaryEl = document.createElement('span');
    summaryEl.className = 'collapsible-summary';
    summaryEl.textContent = summary;
    header.appendChild(summaryEl);

    const arrow = document.createElement('span');
    arrow.className = 'collapsible-arrow';
    arrow.textContent = '+';
    header.appendChild(arrow);

    const content = document.createElement('div');
    content.className = 'collapsible-content';
    content.style.display = 'none';

    header.addEventListener('click', () => {
        const isOpen = content.style.display !== 'none';
        content.style.display = isOpen ? 'none' : 'block';
        arrow.textContent = isOpen ? '+' : '−';
        section.classList.toggle('open', !isOpen);
        if (!isOpen && !content.dataset.rendered) {
            renderContent(content);
            content.dataset.rendered = 'true';
        }
    });

    section.appendChild(header);
    section.appendChild(content);
    return section;
}

function closeDetail() {
    document.getElementById('detail-panel').style.display = 'none';
}

function renderPerfRow(stock) {
    let perfRow = document.getElementById('detail-perf-row');
    if (!perfRow) {
        perfRow = document.createElement('div');
        perfRow.id = 'detail-perf-row';
        perfRow.className = 'detail-perf-row';
        const grid = document.querySelector('.detail-grid');
        grid.parentNode.insertBefore(perfRow, grid);
    }
    perfRow.textContent = '';

    const m = stock.metrics;
    const periods = [
        { label: '1 Day', value: m ? m.return_1d_pct : null, suffix: '%' },
        { label: '1 Week', value: m ? m.return_1w_pct : null, suffix: '%' },
        { label: '1 Month', value: m ? m.return_1m_pct : null, suffix: '%' },
        { label: '3 Months', value: m ? m.return_3m_pct : null, suffix: '%' },
        { label: '6 Months', value: m ? m.return_6m_pct : null, suffix: '%' },
        { label: 'YTD', value: m ? m.return_ytd_pct : null, suffix: '%' },
        { label: '1 Year', value: m ? m.return_1y_pct : null, suffix: '%' },
        { label: 'Trend', value: m ? m.trend : 'N/A', suffix: '' },
    ];

    periods.forEach(p => {
        const pill = document.createElement('div');
        pill.className = 'perf-pill';
        const val = document.createElement('div');
        val.className = 'perf-pill-value';
        if (p.value === null) {
            val.textContent = 'N/A';
        } else {
            val.textContent = (typeof p.value === 'number' ? (p.value > 0 ? '+' : '') + p.value.toFixed(1) : p.value) + p.suffix;
            if (typeof p.value === 'number') {
                val.classList.add(p.value >= 0 ? 'positive' : 'negative');
            }
        }
        const lbl = document.createElement('div');
        lbl.className = 'perf-pill-label';
        lbl.textContent = p.label;
        pill.appendChild(val);
        pill.appendChild(lbl);
        perfRow.appendChild(pill);
    });
}


loadAnalysis();
