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

    const insightsSection = document.getElementById('insights-section');
    const tableSection = document.querySelector('.stock-table-container');
    const filtersSection = document.querySelector('.filters');

    if (tab === 'insights') {
        insightsSection.style.display = 'block';
        tableSection.style.display = 'none';
        filtersSection.style.display = 'none';
        loadInsights();
    } else {
        insightsSection.style.display = 'none';
        tableSection.style.display = 'block';
        filtersSection.style.display = 'flex';
        applyFilters();
    }
}

function switchTabFilters(tab) {
    applyFilters();
}

function applyFilters() {
    if (!analysisData || activeTab === 'insights') return;
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
        scoreTd.title = 'Pulse.AI composite score from fundamental + technical + momentum analysis';
        tr.appendChild(scoreTd);

        const adjTd = document.createElement('td');
        const adjStrong = document.createElement('strong');
        adjStrong.textContent = s.adjusted_score;
        adjTd.title = 'Devil\'s Advocate Score = Pulse.AI Score ' + (s.penalty || 0) + ' penalty (Valuation: ' + ((s.challenge_detail || {}).valuation_penalty || 0) + ', Debt: ' + ((s.challenge_detail || {}).debt_penalty || 0) + ', Promoter: ' + ((s.challenge_detail || {}).promoter_penalty || 0) + ', Sector: ' + ((s.challenge_detail || {}).sector_penalty || 0) + ', P&D: ' + ((s.challenge_detail || {}).pump_dump_penalty || 0) + ')';
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
            if (criticData.verdict !== 'AGREE') {
                const tip = (criticData.challenges && criticData.challenges[0]) || (criticData.evidence_against && criticData.evidence_against[0]) || '';
                if (tip) {
                    const tipEl = document.createElement('div');
                    tipEl.className = 'critic-tip';
                    tipEl.textContent = tip.length > 80 ? tip.slice(0, 77) + '...' : tip;
                    tipEl.title = tip;
                    verdictTd.appendChild(tipEl);
                }
            }
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

    document.querySelectorAll('.stock-table tbody tr').forEach(tr => tr.classList.remove('row-selected'));
    document.querySelectorAll('.stock-table tbody tr').forEach(tr => {
        const sym = tr.querySelector('td:nth-child(2) strong');
        if (sym && sym.textContent === symbol) tr.classList.add('row-selected');
    });

    const overlay = document.getElementById('modal-overlay');
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    document.getElementById('detail-name').textContent =
        stock.symbol + ' — ' + stock.name + ' (₹' + (stock.price || 0).toFixed(2) + ' | ' + (stock.conviction_level || 'N/A') + ')';

    renderPerfRow(stock);

    const tabs = [
        { id: 'thesis', label: 'Thesis' },
        { id: 'fundamentals', label: 'Fundamentals' },
        { id: 'swot', label: 'SWOT' },
        { id: 'intelligence', label: 'Market Intel' },
        { id: 'critic', label: 'Critic Agent' },
        { id: 'risks', label: 'Risks' },
        { id: 'references', label: 'References' },
    ];

    const tabsContainer = document.getElementById('modal-tabs');
    tabsContainer.textContent = '';
    tabs.forEach((t, i) => {
        const btn = document.createElement('button');
        btn.className = 'modal-tab' + (i === 0 ? ' active' : '');
        btn.textContent = t.label;
        btn.addEventListener('click', () => switchModalTab(t.id, stock));
        tabsContainer.appendChild(btn);
    });

    switchModalTab('thesis', stock);
}

function switchModalTab(tabId, stock) {
    document.querySelectorAll('.modal-tab').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === getTabLabel(tabId));
    });

    const body = document.getElementById('modal-body');
    body.textContent = '';

    const fund = stock.fundamentals || {};
    const m = stock.metrics;
    const criticReport = analysisData.critic_report;
    const criticVerdict = criticReport ? (criticReport.verdicts || []).find(v => v.symbol === stock.symbol) : null;
    const expertData = (analysisData.expert_analysis || []).find(e => e.symbol === stock.symbol);

    switch (tabId) {
        case 'thesis':
            renderThesisTab(body, stock);
            break;
        case 'fundamentals':
            renderFundamentalsTab(body, stock, fund, m);
            break;
        case 'swot':
            renderSwotTab(body, stock);
            break;
        case 'intelligence':
            renderIntelTab(body, stock);
            break;
        case 'critic':
            renderCriticTab(body, stock, criticVerdict);
            break;
        case 'risks':
            renderRisksTab(body, stock);
            break;
        case 'references':
            renderReferencesTab(body, stock, expertData);
            break;
    }
}

function getTabLabel(id) {
    const map = { thesis: 'Thesis', fundamentals: 'Fundamentals', swot: 'SWOT', intelligence: 'Market Intel', critic: 'Critic Agent', risks: 'Risks', references: 'References' };
    return map[id] || id;
}

function renderThesisTab(el, stock) {
    const thesis = stock.multibagger_thesis;
    if (thesis && thesis.target_multiple) {
        const target = document.createElement('div');
        target.className = 'modal-highlight';
        target.textContent = 'Target: ' + thesis.target_multiple;
        el.appendChild(target);
    }
    if (thesis && thesis.thesis && thesis.thesis.length) {
        thesis.thesis.forEach(point => {
            const div = document.createElement('div');
            div.className = 'thesis-point';
            div.textContent = point;
            el.appendChild(div);
        });
    } else {
        el.textContent = 'Insufficient data for multi-bagger thesis.';
        el.style.color = 'var(--text-secondary)';
    }
}

function getMetricColor(label, rawValue) {
    if (rawValue == null || rawValue === 'N/A') return 'neutral';
    const v = typeof rawValue === 'string' ? parseFloat(rawValue) : rawValue;
    if (isNaN(v)) return 'neutral';
    switch (label) {
        case 'PE Ratio': return v < 25 ? 'green' : v < 50 ? 'yellow' : 'red';
        case 'PB Ratio': return v < 3 ? 'green' : v < 6 ? 'yellow' : 'red';
        case 'ROE': return v > 15 ? 'green' : v > 8 ? 'yellow' : 'red';
        case 'Debt/Equity': return v < 50 ? 'green' : v < 100 ? 'yellow' : 'red';
        case 'Revenue Growth': return v > 15 ? 'green' : v > 5 ? 'yellow' : 'red';
        case 'Earnings Growth': return v > 15 ? 'green' : v > 0 ? 'yellow' : 'red';
        case 'Promoter Holding': return v > 50 ? 'green' : v > 35 ? 'yellow' : 'red';
        case 'RSI (14-day)': return v >= 30 && v <= 70 ? 'green' : (v < 30 ? 'yellow' : 'red');
        case 'Volume Surge': return v > 50 ? 'green' : v > 0 ? 'yellow' : 'neutral';
        case 'Green Months (of 6)': return v >= 4 ? 'green' : v >= 2 ? 'yellow' : 'red';
        case 'Max Drawdown (6M)': return v > -10 ? 'green' : v > -25 ? 'yellow' : 'red';
        case 'Volatility (Ann.)': return v < 30 ? 'green' : v < 50 ? 'yellow' : 'red';
        default: return 'neutral';
    }
}

function renderFundamentalsTab(el, stock, fund, m) {
    const items = [
        ['PE Ratio', fund.pe_ratio != null ? fund.pe_ratio.toFixed(1) : 'N/A', fund.pe_ratio],
        ['PB Ratio', fund.pb_ratio != null ? fund.pb_ratio.toFixed(2) : 'N/A', fund.pb_ratio],
        ['ROE', fund.roe != null ? (fund.roe * 100).toFixed(1) + '%' : 'N/A', fund.roe != null ? fund.roe * 100 : null],
        ['Debt/Equity', fund.debt_to_equity != null ? fund.debt_to_equity.toFixed(0) : 'N/A', fund.debt_to_equity],
        ['Revenue Growth', fund.revenue_growth != null ? (fund.revenue_growth * 100).toFixed(1) + '%' : 'N/A', fund.revenue_growth != null ? fund.revenue_growth * 100 : null],
        ['Earnings Growth', fund.earnings_growth != null ? (fund.earnings_growth * 100).toFixed(1) + '%' : 'N/A', fund.earnings_growth != null ? fund.earnings_growth * 100 : null],
        ['Promoter Holding', fund.promoter_holding != null ? (fund.promoter_holding * 100).toFixed(1) + '%' : 'N/A', fund.promoter_holding != null ? fund.promoter_holding * 100 : null],
        ['EPS', fund.eps != null ? '₹' + fund.eps.toFixed(2) : 'N/A', null],
        ['Book Value', fund.book_value != null ? '₹' + fund.book_value.toFixed(2) : 'N/A', null],
    ];
    if (m) {
        items.push(['RSI (14-day)', m.rsi_14, m.rsi_14]);
        items.push(['Volatility (Ann.)', m.volatility_annual_pct + '%', m.volatility_annual_pct]);
        items.push(['20-Day MA', '₹' + m.ma_20, null]);
        items.push(['50-Day MA', '₹' + m.ma_50, null]);
        items.push(['Volume Surge', (m.volume_surge_pct > 0 ? '+' : '') + m.volume_surge_pct + '%', m.volume_surge_pct]);
        items.push(['Green Months (of 6)', m.green_months_of_6 + '/6', m.green_months_of_6]);
        items.push(['Max Drawdown (6M)', m.max_drawdown_pct + '%', m.max_drawdown_pct]);
    }
    const grid = document.createElement('div');
    grid.className = 'metrics-grid';
    items.forEach(([label, display, raw]) => {
        const item = document.createElement('div');
        const color = getMetricColor(label, raw);
        item.className = 'metric-item metric-' + color;
        const lbl = document.createElement('span');
        lbl.className = 'metric-label';
        lbl.textContent = label;
        const val = document.createElement('span');
        val.className = 'metric-value';
        val.textContent = display;
        item.appendChild(lbl);
        item.appendChild(val);
        grid.appendChild(item);
    });
    el.appendChild(grid);
}

function renderSwotTab(el, stock) {
    const swot = stock.swot || {};
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
}

function renderIntelTab(el, stock) {
    const insider = stock.insider_activity || {};
    const institutional = stock.institutional_activity || {};
    const retail = stock.retail_interest || {};
    const breakoutSignals = stock.breakout_signals || [];

    if (breakoutSignals.length) {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Breakout Signals (Independent Scanner)';
        el.appendChild(h);
        breakoutSignals.forEach(s => {
            const chip = document.createElement('span');
            chip.className = 'signal-chip';
            chip.textContent = s;
            el.appendChild(chip);
        });
    }

    if (insider.signal && insider.signal !== 'NO_DATA') {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Insider Trading (SEBI PIT Disclosures)';
        el.appendChild(h);
        const sig = document.createElement('span');
        sig.className = 'badge badge-' + (insider.signal === 'STRONG_BUY' || insider.signal === 'BUY' ? 'high' : insider.signal === 'SELL_WARNING' || insider.signal === 'SELL' ? 'rejected' : 'low');
        sig.textContent = insider.signal;
        el.appendChild(sig);
        if (insider.summary) {
            const sum = document.createElement('p');
            sum.className = 'intel-detail';
            sum.textContent = insider.summary;
            el.appendChild(sum);
        }
        (insider.details || []).forEach(d => {
            const p = document.createElement('p');
            p.className = 'intel-detail';
            p.textContent = d;
            el.appendChild(p);
        });
    }

    if (institutional.signal && institutional.signal !== 'NO_DEALS') {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Bulk/Block Deals (NSE)';
        el.appendChild(h);
        const sig = document.createElement('span');
        sig.className = 'badge badge-' + (institutional.signal === 'ACCUMULATION' || institutional.signal === 'NET_BUY' ? 'high' : institutional.signal === 'DISTRIBUTION' || institutional.signal === 'NET_SELL' ? 'rejected' : 'low');
        sig.textContent = institutional.signal;
        el.appendChild(sig);
        if (institutional.summary) {
            const sum = document.createElement('p');
            sum.className = 'intel-detail';
            sum.textContent = institutional.summary;
            el.appendChild(sum);
        }
    }

    if (retail.signal && retail.signal !== 'NO_DATA') {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Google Trends (Retail Interest)';
        el.appendChild(h);
        if (retail.summary) {
            const sum = document.createElement('p');
            sum.className = 'intel-detail';
            sum.textContent = retail.summary;
            el.appendChild(sum);
        }
        (retail.details || []).forEach(d => {
            const p = document.createElement('p');
            p.className = 'intel-detail';
            p.textContent = d;
            el.appendChild(p);
        });
    }

    if (!breakoutSignals.length && (!insider.signal || insider.signal === 'NO_DATA') && (!institutional.signal || institutional.signal === 'NO_DEALS') && (!retail.signal || retail.signal === 'NO_DATA')) {
        el.textContent = 'No market intelligence data available for this stock.';
        el.style.color = 'var(--text-secondary)';
    }
}

function renderCriticTab(el, stock, criticVerdict) {
    if (!criticVerdict) {
        el.textContent = 'Critic agent has not evaluated this stock yet.';
        el.style.color = 'var(--text-secondary)';
        return;
    }

    const scoreRow = document.createElement('div');
    scoreRow.className = 'modal-highlight';
    scoreRow.textContent = 'Critic Score: ' + criticVerdict.critic_score + '/100 | Confidence: ' + (criticVerdict.confidence * 100).toFixed(0) + '%';
    el.appendChild(scoreRow);

    const vClass = criticVerdict.verdict === 'AGREE' ? 'agree' : (criticVerdict.verdict === 'PARTIALLY_AGREE' ? 'partial' : 'disagree');
    const badge = document.createElement('span');
    badge.className = 'critic-verdict-badge ' + vClass;
    badge.textContent = criticVerdict.verdict.replace('_', ' ');
    badge.style.marginBottom = '0.75rem';
    badge.style.display = 'inline-block';
    el.appendChild(badge);

    if (criticVerdict.risk_flags && criticVerdict.risk_flags.length) {
        const flags = document.createElement('div');
        flags.style.marginBottom = '0.75rem';
        criticVerdict.risk_flags.forEach(f => {
            const chip = document.createElement('span');
            chip.className = 'critic-risk-flag';
            chip.textContent = f;
            flags.appendChild(chip);
        });
        el.appendChild(flags);
    }

    if (criticVerdict.challenges && criticVerdict.challenges.length) {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Challenges';
        el.appendChild(h);
        criticVerdict.challenges.forEach(c => {
            const p = document.createElement('p');
            p.style.fontSize = '0.75rem';
            p.style.color = 'var(--warning)';
            p.style.marginBottom = '0.25rem';
            p.textContent = c;
            el.appendChild(p);
        });
    }
    if (criticVerdict.evidence_for && criticVerdict.evidence_for.length) {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Evidence For';
        el.appendChild(h);
        criticVerdict.evidence_for.forEach(e => {
            const p = document.createElement('p');
            p.style.fontSize = '0.75rem';
            p.style.color = 'var(--success)';
            p.textContent = '+ ' + e;
            el.appendChild(p);
        });
    }
    if (criticVerdict.evidence_against && criticVerdict.evidence_against.length) {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Evidence Against';
        el.appendChild(h);
        criticVerdict.evidence_against.forEach(e => {
            const p = document.createElement('p');
            p.style.fontSize = '0.75rem';
            p.style.color = 'var(--error)';
            p.textContent = '- ' + e;
            el.appendChild(p);
        });
    }
}

function renderRisksTab(el, stock) {
    const swot = stock.swot || {};
    const risks = [...(stock.red_flags || []), ...(stock.bear_case || []), ...(swot.threats || [])];

    if (!risks.length) {
        el.textContent = 'Low risk profile — no major flags identified.';
        el.style.color = 'var(--success)';
        return;
    }

    risks.forEach(r => {
        const p = document.createElement('p');
        p.style.fontSize = '0.75rem';
        p.style.color = 'var(--error)';
        p.style.marginBottom = '0.375rem';
        p.textContent = '• ' + r;
        el.appendChild(p);
    });

    const ch = stock.challenge_detail || {};
    if (stock.penalty) {
        const pen = document.createElement('div');
        pen.className = 'modal-highlight';
        pen.style.marginTop = '0.75rem';
        pen.textContent = 'Penalty Breakdown — Valuation: ' + (ch.valuation_penalty || 0) + ' | Debt: ' + (ch.debt_penalty || 0) + ' | Promoter: ' + (ch.promoter_penalty || 0) + ' | Sector: ' + (ch.sector_penalty || 0) + ' | Pump/Dump: ' + (ch.pump_dump_penalty || 0) + ' | Total: ' + stock.penalty;
        el.appendChild(pen);
    }
}

function renderReferencesTab(el, stock, expertData) {
    const linksDiv = document.createElement('div');
    linksDiv.className = 'ref-links-grid';

    const yahooLink = document.createElement('a');
    yahooLink.href = 'https://finance.yahoo.com/quote/' + stock.symbol + '.NS/';
    yahooLink.target = '_blank';
    yahooLink.rel = 'noopener noreferrer';
    yahooLink.textContent = 'Yahoo Finance';
    yahooLink.className = 'ref-link-card';
    linksDiv.appendChild(yahooLink);

    const screenerLink = document.createElement('a');
    screenerLink.href = 'https://www.screener.in/company/' + stock.symbol + '/';
    screenerLink.target = '_blank';
    screenerLink.rel = 'noopener noreferrer';
    screenerLink.textContent = 'Screener.in';
    screenerLink.className = 'ref-link-card';
    linksDiv.appendChild(screenerLink);

    const mcLink = document.createElement('a');
    mcLink.href = 'https://www.moneycontrol.com/india/stockpricequote/' + stock.symbol.toLowerCase();
    mcLink.target = '_blank';
    mcLink.rel = 'noopener noreferrer';
    mcLink.textContent = 'MoneyControl';
    mcLink.className = 'ref-link-card';
    linksDiv.appendChild(mcLink);

    const trendLink = document.createElement('a');
    trendLink.href = 'https://www.google.com/finance/quote/' + stock.symbol + ':NSE';
    trendLink.target = '_blank';
    trendLink.rel = 'noopener noreferrer';
    trendLink.textContent = 'Google Finance';
    trendLink.className = 'ref-link-card';
    linksDiv.appendChild(trendLink);

    const growwLink = document.createElement('a');
    growwLink.href = 'https://groww.in/search?q=' + encodeURIComponent(stock.symbol) + '&searchType=stocks';
    growwLink.target = '_blank';
    growwLink.rel = 'noopener noreferrer';
    growwLink.textContent = 'Groww (Trade)';
    growwLink.className = 'ref-link-card ref-link-trade';
    linksDiv.appendChild(growwLink);

    const zerodhaLink = document.createElement('a');
    zerodhaLink.href = 'https://www.nseindia.com/get-quotes/equity?symbol=' + encodeURIComponent(stock.symbol);
    zerodhaLink.target = '_blank';
    zerodhaLink.rel = 'noopener noreferrer';
    zerodhaLink.textContent = 'NSE India';
    zerodhaLink.className = 'ref-link-card ref-link-trade';
    linksDiv.appendChild(zerodhaLink);

    const tvLink = document.createElement('a');
    tvLink.href = 'https://www.tradingview.com/chart/?symbol=NSE%3A' + encodeURIComponent(stock.symbol);
    tvLink.target = '_blank';
    tvLink.rel = 'noopener noreferrer';
    tvLink.textContent = 'TradingView (Chart)';
    tvLink.className = 'ref-link-card ref-link-trade';
    linksDiv.appendChild(tvLink);

    el.appendChild(linksDiv);

    if (expertData && expertData.insights && expertData.insights.length) {
        const h = document.createElement('h4');
        h.className = 'intel-heading';
        h.textContent = 'Expert Analysis (YouTube & Social)';
        el.appendChild(h);
        if (expertData.sentiment) {
            const badge = document.createElement('span');
            badge.className = 'expert-sentiment expert-sentiment-' + expertData.sentiment.toLowerCase();
            badge.textContent = 'Sentiment: ' + expertData.sentiment;
            el.appendChild(badge);
        }
        expertData.insights.forEach(ins => {
            const row = document.createElement('div');
            row.style.marginTop = '0.5rem';
            const a = document.createElement('a');
            a.href = ins.url;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.textContent = ins.title;
            a.className = 'ref-link';
            row.appendChild(a);
            if (ins.channel || ins.views) {
                const meta = document.createElement('span');
                meta.style.fontSize = '0.625rem';
                meta.style.color = 'var(--text-secondary)';
                meta.style.marginLeft = '0.5rem';
                meta.textContent = (ins.channel || '') + (ins.views ? ' • ' + ins.views + ' views' : '') + (ins.published ? ' • ' + ins.published : '');
                row.appendChild(meta);
            }
            el.appendChild(row);
        });
    }
}

function closeDetail() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.body.style.overflow = '';
    document.querySelectorAll('.stock-table tbody tr').forEach(tr => tr.classList.remove('row-selected'));
}

function renderPerfRow(stock) {
    const perfRow = document.getElementById('detail-perf-row');
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


document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeDetail();
});

/* ═══════════════════════════════════════════════════════════
   PULSE.AI INSIGHTS — Performance Tracking & Validation
   ═══════════════════════════════════════════════════════════ */
let insightsData = null;
let insightsChart = null;
let insightsPeriod = 30;

async function loadInsights() {
    if (insightsData) {
        populateInsightsDropdown();
        return;
    }
    try {
        const resp = await fetch('insights.json');
        insightsData = await resp.json();
        populateInsightsDropdown();
        renderInsightsGrid();
    } catch (e) {
        const grid = document.getElementById('insights-grid');
        grid.textContent = 'Insights data not yet available. Run the pipeline to generate.';
        grid.style.color = 'var(--text-secondary)';
        grid.style.padding = '2rem';
        grid.style.textAlign = 'center';
    }
}

function populateInsightsDropdown() {
    const select = document.getElementById('insights-stock');
    select.textContent = '';
    const defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = 'Select stock to view chart...';
    select.appendChild(defaultOpt);

    (insightsData.stocks || []).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.symbol;
        opt.textContent = s.symbol + ' — ' + s.name + ' (' + s.assessment.verdict + ')';
        select.appendChild(opt);
    });

    if (insightsData.stocks && insightsData.stocks.length) {
        select.value = insightsData.stocks[0].symbol;
        renderInsightsChart();
    }
}

function setInsightsPeriod(days) {
    insightsPeriod = days;
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.period) === days);
    });
    renderInsightsChart();
}

function renderInsightsChart() {
    const symbol = document.getElementById('insights-stock').value;
    if (!symbol || !insightsData) return;

    const stockData = insightsData.stocks.find(s => s.symbol === symbol);
    if (!stockData) return;

    const assessment = document.getElementById('insights-assessment');
    assessment.textContent = '';

    const a = stockData.assessment;
    const verdictColors = {
        STRONG_MULTIBAGGER: '#166534', ON_TRACK: '#2e844a',
        MODERATE_GROWTH: '#854d0e', FLAT: '#706e6b', UNDERPERFORMING: '#991b1b',
        INSUFFICIENT_DATA: '#706e6b'
    };

    const row = document.createElement('div');
    row.className = 'insights-assessment-row';

    const items = [
        ['Verdict', a.verdict.replace(/_/g, ' '), verdictColors[a.verdict] || '#706e6b'],
        ['Total Return', (a.total_return_pct || 0) + '%', a.total_return_pct >= 0 ? '#166534' : '#991b1b'],
        ['Annualized', (a.annualized_return_pct || 0) + '%', a.annualized_return_pct >= 50 ? '#166534' : a.annualized_return_pct >= 0 ? '#854d0e' : '#991b1b'],
        ['Drawdown', (a.drawdown_from_peak_pct || 0) + '%', a.drawdown_from_peak_pct > -10 ? '#166534' : '#991b1b'],
        ['DA Score', stockData.da_score || 'N/A', ''],
        ['Conviction', stockData.conviction_level || 'N/A', ''],
    ];

    items.forEach(([label, value, color]) => {
        const chip = document.createElement('div');
        chip.className = 'insights-chip';
        const lbl = document.createElement('div');
        lbl.className = 'insights-chip-label';
        lbl.textContent = label;
        const val = document.createElement('div');
        val.className = 'insights-chip-value';
        val.textContent = value;
        if (color) val.style.color = color;
        chip.appendChild(lbl);
        chip.appendChild(val);
        row.appendChild(chip);
    });
    assessment.appendChild(row);

    // Chart
    let ts = stockData.timeseries || [];
    if (insightsPeriod < ts.length) {
        ts = ts.slice(-insightsPeriod);
    }

    const labels = ts.map(p => p.date);
    const prices = ts.map(p => p.close);
    const cumReturns = ts.map(p => p.cumulative_return_pct);

    const ctx = document.getElementById('insights-chart').getContext('2d');
    if (insightsChart) insightsChart.destroy();

    const isPositive = cumReturns.length && cumReturns[cumReturns.length - 1] >= 0;

    insightsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Price (₹)',
                    data: prices,
                    borderColor: '#0176d3',
                    backgroundColor: 'rgba(1,118,211,0.05)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    yAxisID: 'y',
                },
                {
                    label: 'Cumulative Return (%)',
                    data: cumReturns,
                    borderColor: isPositive ? '#2e844a' : '#b91c1c',
                    backgroundColor: isPositive ? 'rgba(46,132,74,0.05)' : 'rgba(185,28,28,0.05)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderDash: [4, 2],
                    yAxisID: 'y1',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        title: ctx => ctx[0].label,
                        label: ctx => ctx.dataset.label + ': ' + (ctx.datasetIndex === 0 ? '₹' : '') + ctx.parsed.y.toFixed(2) + (ctx.datasetIndex === 1 ? '%' : ''),
                    }
                }
            },
            scales: {
                x: {
                    ticks: { maxTicksLimit: 10, font: { size: 10 } },
                    grid: { display: false },
                },
                y: {
                    position: 'left',
                    title: { display: true, text: 'Price (₹)', font: { size: 10 } },
                    ticks: { font: { size: 10 } },
                    grid: { color: 'rgba(0,0,0,0.04)' },
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Return (%)', font: { size: 10 } },
                    ticks: { font: { size: 10 }, callback: v => v + '%' },
                    grid: { display: false },
                }
            }
        }
    });
}

function renderInsightsGrid() {
    const grid = document.getElementById('insights-grid');
    grid.textContent = '';

    if (!insightsData || !insightsData.stocks.length) {
        grid.textContent = 'No insights data available.';
        return;
    }

    const sorted = [...insightsData.stocks].sort((a, b) => (b.assessment.total_return_pct || 0) - (a.assessment.total_return_pct || 0));

    sorted.forEach(s => {
        const card = document.createElement('div');
        card.className = 'insights-stock-card';
        card.addEventListener('click', () => {
            document.getElementById('insights-stock').value = s.symbol;
            renderInsightsChart();
            document.getElementById('insights-chart').scrollIntoView({ behavior: 'smooth' });
        });

        const a = s.assessment;
        const verdictClass = a.verdict === 'STRONG_MULTIBAGGER' || a.verdict === 'ON_TRACK' ? 'green' :
            a.verdict === 'MODERATE_GROWTH' ? 'yellow' : 'red';

        card.innerHTML = '';
        const top = document.createElement('div');
        top.className = 'insights-card-top';
        const sym = document.createElement('strong');
        sym.textContent = s.symbol;
        const badge = document.createElement('span');
        badge.className = 'badge badge-' + verdictClass;
        badge.textContent = a.verdict.replace(/_/g, ' ');
        top.appendChild(sym);
        top.appendChild(badge);
        card.appendChild(top);

        const metrics = document.createElement('div');
        metrics.className = 'insights-card-metrics';
        metrics.textContent = 'Return: ' + (a.total_return_pct || 0) + '% | Ann: ' + (a.annualized_return_pct || 0) + '% | ' + s.conviction_level;
        card.appendChild(metrics);

        grid.appendChild(card);
    });
}

loadAnalysis();
