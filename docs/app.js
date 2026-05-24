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
    renderProactivePicks();
    renderForumSentiment();
    renderExpertAnalysis();
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

function renderTable(stocks) {
    const tbody = document.getElementById('stock-tbody');
    tbody.textContent = '';

    if (!stocks.length) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 11;
        td.className = 'empty-state';
        td.textContent = 'No stocks match filters';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    stocks.sort((a, b) => {
        let va = a[currentSort.key] ?? '';
        let vb = b[currentSort.key] ?? '';
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
            } else {
                td.textContent = val;
            }
            tr.appendChild(td);
        });

        const catTd = document.createElement('td');
        const catBadge = document.createElement('span');
        catBadge.className = 'badge badge-' + (s.classification === 'penny' ? 'penny' : s.classification === 'small_cap' ? 'small' : 'mid');
        catBadge.textContent = s.classification;
        catTd.appendChild(catBadge);
        tr.appendChild(catTd);

        const scoreTd = document.createElement('td');
        scoreTd.textContent = s.score;
        tr.appendChild(scoreTd);

        const adjTd = document.createElement('td');
        const adjStrong = document.createElement('strong');
        adjStrong.textContent = s.adjusted_score;
        adjTd.appendChild(adjStrong);
        tr.appendChild(adjTd);

        const convTd = document.createElement('td');
        const convBadge = document.createElement('span');
        convBadge.className = 'badge badge-' + convictionClass(s.conviction_level);
        convBadge.textContent = s.conviction_level;
        convTd.appendChild(convBadge);
        tr.appendChild(convTd);

        const flagTd = document.createElement('td');
        (s.red_flags || []).forEach(f => {
            const chip = document.createElement('span');
            chip.className = 'red-flag-chip';
            chip.textContent = f;
            flagTd.appendChild(chip);
        });
        tr.appendChild(flagTd);

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

    // 6-Month Metrics
    renderMetrics(stock);

    // Multi-Bagger Thesis
    renderThesis(stock);

    const fund = stock.fundamentals;
    const fundEl = document.getElementById('detail-fundamentals');
    fundEl.textContent = '';
    const fundList = document.createElement('ul');
    const fundItems = [
        'PE Ratio: ' + (fund.pe_ratio != null ? fund.pe_ratio.toFixed(1) : 'N/A'),
        'PB Ratio: ' + (fund.pb_ratio != null ? fund.pb_ratio.toFixed(2) : 'N/A'),
        'ROE: ' + (fund.roe != null ? (fund.roe * 100).toFixed(1) + '%' : 'N/A'),
        'Debt/Equity: ' + (fund.debt_to_equity != null ? fund.debt_to_equity.toFixed(0) : 'N/A'),
        'Revenue Growth: ' + (fund.revenue_growth != null ? (fund.revenue_growth * 100).toFixed(1) + '%' : 'N/A'),
        'Earnings Growth: ' + (fund.earnings_growth != null ? (fund.earnings_growth * 100).toFixed(1) + '%' : 'N/A'),
        'Promoter Holding: ' + (fund.promoter_holding != null ? (fund.promoter_holding * 100).toFixed(1) + '%' : 'N/A'),
        'EPS: ' + (fund.eps != null ? fund.eps.toFixed(2) : 'N/A'),
        'Book Value: ₹' + (fund.book_value != null ? fund.book_value.toFixed(2) : 'N/A'),
    ];
    fundItems.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        fundList.appendChild(li);
    });
    fundEl.appendChild(fundList);

    const swot = stock.swot;
    const swotEl = document.getElementById('detail-swot');
    swotEl.textContent = '';
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
            p.textContent = '• ' + item;
            box.appendChild(p);
        });
        swotGrid.appendChild(box);
    });
    swotEl.appendChild(swotGrid);

    const bearEl = document.getElementById('detail-bear-case');
    bearEl.textContent = '';
    if (stock.bear_case && stock.bear_case.length) {
        const ul = document.createElement('ul');
        stock.bear_case.forEach(b => {
            const li = document.createElement('li');
            li.textContent = b;
            li.style.color = 'var(--red)';
            ul.appendChild(li);
        });
        bearEl.appendChild(ul);
    } else {
        const p = document.createElement('p');
        p.textContent = 'No significant bear case identified — strong pick.';
        p.style.color = 'var(--green)';
        bearEl.appendChild(p);
    }

    const ch = stock.challenge_detail || {};
    const penEl = document.getElementById('detail-penalties');
    penEl.textContent = '';
    const penList = document.createElement('ul');
    [
        'Valuation: ' + (ch.valuation_penalty || 0),
        'Debt Trap: ' + (ch.debt_penalty || 0),
        'Promoter: ' + (ch.promoter_penalty || 0),
        'Sector: ' + (ch.sector_penalty || 0),
        'Pump/Dump: ' + (ch.pump_dump_penalty || 0),
        'Total Penalty: ' + (stock.penalty || 0),
    ].forEach((text, idx) => {
        const li = document.createElement('li');
        if (idx === 5) {
            const strong = document.createElement('strong');
            strong.textContent = text;
            li.appendChild(strong);
        } else {
            li.textContent = text;
        }
        penList.appendChild(li);
    });
    penEl.appendChild(penList);

    const reasonEl = document.getElementById('detail-reasons');
    reasonEl.textContent = '';
    if (stock.score_reasons && stock.score_reasons.length) {
        const ul = document.createElement('ul');
        stock.score_reasons.forEach(r => {
            const li = document.createElement('li');
            li.textContent = r;
            ul.appendChild(li);
        });
        reasonEl.appendChild(ul);
    } else {
        const p = document.createElement('p');
        p.textContent = 'No specific reasons captured.';
        reasonEl.appendChild(p);
    }

    const riskEl = document.getElementById('detail-risks');
    riskEl.textContent = '';
    const risks = [...(stock.red_flags || []), ...(stock.swot ? stock.swot.threats || [] : [])];
    if (risks.length) {
        const ul = document.createElement('ul');
        risks.forEach(r => {
            const li = document.createElement('li');
            li.textContent = r;
            li.style.color = 'var(--orange)';
            ul.appendChild(li);
        });
        riskEl.appendChild(ul);
    } else {
        const p = document.createElement('p');
        p.textContent = 'Low risk profile.';
        riskEl.appendChild(p);
    }

    // Expert views for this stock
    const expertEl = document.getElementById('detail-expert');
    expertEl.textContent = '';
    const expertData = (analysisData.expert_analysis || []).find(e => e.symbol === stock.symbol);
    if (expertData && expertData.insights && expertData.insights.length) {
        if (expertData.sentiment) {
            const badge = document.createElement('span');
            badge.className = 'expert-sentiment expert-sentiment-' + expertData.sentiment.toLowerCase();
            badge.textContent = 'Sentiment: ' + expertData.sentiment;
            expertEl.appendChild(badge);
        }
        const ul = document.createElement('ul');
        ul.style.marginTop = '0.5rem';
        expertData.insights.forEach(ins => {
            const li = document.createElement('li');
            li.style.marginBottom = '0.25rem';
            const a = document.createElement('a');
            a.href = ins.url;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.textContent = ins.title;
            a.style.color = 'var(--primary)';
            a.style.fontSize = '0.75rem';
            li.appendChild(a);
            if (ins.channel) {
                const meta = document.createElement('span');
                meta.style.fontSize = '0.625rem';
                meta.style.color = 'var(--text-secondary)';
                meta.style.marginLeft = '0.5rem';
                meta.textContent = ins.channel + (ins.views ? ' • ' + ins.views + ' views' : '');
                li.appendChild(meta);
            }
            ul.appendChild(li);
        });
        expertEl.appendChild(ul);
    } else {
        const p = document.createElement('p');
        p.textContent = 'No expert analysis available for this stock yet.';
        p.style.color = 'var(--text-secondary)';
        p.style.fontSize = '0.75rem';
        expertEl.appendChild(p);
    }

    panel.scrollIntoView({ behavior: 'smooth' });
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

function renderMetrics(stock) {
    const el = document.getElementById('detail-metrics');
    el.textContent = '';
    const m = stock.metrics;

    if (!m) {
        const p = document.createElement('p');
        p.textContent = 'Historical metrics not available for this stock.';
        p.style.color = 'var(--text-secondary)';
        p.style.fontSize = '0.75rem';
        el.appendChild(p);
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'metrics-grid';

    const items = [
        ['RSI (14-day)', m.rsi_14],
        ['Volatility (Ann.)', m.volatility_annual_pct + '%'],
        ['20-Day MA', '₹' + m.ma_20],
        ['50-Day MA', '₹' + m.ma_50],
        ['Above 20MA', m.above_20ma ? 'Yes' : 'No'],
        ['Above 50MA', m.above_50ma ? 'Yes' : 'No'],
        ['Volume Surge (20d vs 50d)', (m.volume_surge_pct > 0 ? '+' : '') + m.volume_surge_pct + '%'],
        ['Avg Volume (20d)', (m.avg_volume_20d || 0).toLocaleString('en-IN')],
        ['Green Months (of 6)', m.green_months_of_6 + ' / 6'],
        ['Max Drawdown (6M)', m.max_drawdown_pct + '%'],
    ];

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
        grid.appendChild(item);
    });

    el.appendChild(grid);
}

function renderThesis(stock) {
    const el = document.getElementById('detail-thesis');
    el.textContent = '';
    const thesis = stock.multibagger_thesis;

    if (!thesis || !thesis.thesis || !thesis.thesis.length) {
        const p = document.createElement('p');
        p.textContent = 'Insufficient data for multi-bagger thesis.';
        p.style.color = 'var(--text-secondary)';
        p.style.fontSize = '0.75rem';
        el.appendChild(p);
        return;
    }

    thesis.thesis.forEach(point => {
        const div = document.createElement('div');
        div.className = 'thesis-point';
        div.textContent = point;
        el.appendChild(div);
    });

    if (thesis.target_multiple) {
        const target = document.createElement('span');
        target.className = 'thesis-target';
        target.textContent = 'Target: ' + thesis.target_multiple;
        el.appendChild(target);
    }
}

function renderProactivePicks() {
    const section = document.getElementById('proactive-section');
    const container = document.getElementById('proactive-picks');
    const picks = analysisData.proactive_breakouts || [];

    if (!picks.length) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    container.textContent = '';

    picks.forEach(p => {
        const card = document.createElement('div');
        card.className = 'proactive-card';

        const left = document.createElement('div');
        const sym = document.createElement('div');
        sym.className = 'proactive-symbol';
        sym.textContent = p.symbol;
        const name = document.createElement('div');
        name.className = 'proactive-name';
        name.textContent = p.name;
        left.appendChild(sym);
        left.appendChild(name);

        const middle = document.createElement('div');
        middle.className = 'proactive-signals';
        (p.signals || []).forEach(s => {
            const chip = document.createElement('span');
            chip.className = 'signal-chip';
            chip.textContent = s;
            middle.appendChild(chip);
        });

        const right = document.createElement('div');
        right.className = 'proactive-meta';
        right.textContent = '₹' + p.price + ' | ₹' + p.market_cap_cr + 'Cr';

        card.appendChild(left);
        card.appendChild(middle);
        card.appendChild(right);
        container.appendChild(card);
    });
}

function renderForumSentiment() {
    const section = document.getElementById('forum-section');
    const container = document.getElementById('forum-mentions');
    const mentions = analysisData.forum_sentiment || [];

    if (!mentions.length) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    container.textContent = '';
    mentions.forEach(m => {
        const div = document.createElement('div');
        div.className = 'forum-mention';
        const source = document.createElement('span');
        source.className = 'source';
        source.textContent = m.source;
        div.appendChild(source);
        const title = document.createElement('a');
        title.className = 'title';
        title.href = m.url;
        title.target = '_blank';
        title.rel = 'noopener noreferrer';
        title.textContent = m.title;
        title.style.color = 'var(--text)';
        title.style.textDecoration = 'none';
        title.style.display = 'block';
        title.style.marginTop = '0.25rem';
        div.appendChild(title);
        container.appendChild(div);
    });
}

function renderExpertAnalysis() {
    const section = document.getElementById('expert-section');
    const container = document.getElementById('expert-picks');
    const experts = analysisData.expert_analysis || [];

    if (!experts.length) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    container.textContent = '';

    experts.forEach(item => {
        const card = document.createElement('div');
        card.className = 'expert-card';

        const header = document.createElement('div');
        header.className = 'expert-header';

        const sym = document.createElement('span');
        sym.className = 'expert-symbol';
        sym.textContent = item.symbol;
        header.appendChild(sym);

        const source = document.createElement('span');
        source.className = 'expert-source';
        source.textContent = item.source;
        header.appendChild(source);

        card.appendChild(header);

        (item.insights || []).forEach(insight => {
            const row = document.createElement('div');
            row.className = 'expert-insight';

            const title = document.createElement('a');
            title.href = insight.url;
            title.target = '_blank';
            title.rel = 'noopener noreferrer';
            title.className = 'expert-title';
            title.textContent = insight.title;
            row.appendChild(title);

            const meta = document.createElement('div');
            meta.className = 'expert-meta';
            meta.textContent = insight.channel + (insight.views ? ' • ' + insight.views + ' views' : '') + (insight.published ? ' • ' + insight.published : '');
            row.appendChild(meta);

            card.appendChild(row);
        });

        if (item.sentiment) {
            const sentiment = document.createElement('div');
            sentiment.className = 'expert-sentiment expert-sentiment-' + item.sentiment.toLowerCase();
            sentiment.textContent = 'Expert Sentiment: ' + item.sentiment;
            card.appendChild(sentiment);
        }

        container.appendChild(card);
    });
}

loadAnalysis();
