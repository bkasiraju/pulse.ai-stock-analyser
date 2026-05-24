let analysisData = null;
let currentSort = { key: 'adjusted_score', dir: 'desc' };

async function loadAnalysis() {
    try {
        const resp = await fetch('/api/analysis');
        const data = await resp.json();
        if (data.error) return;
        analysisData = data;
        renderDashboard();
    } catch (e) {
        console.error('Failed to load analysis:', e);
    }
}

async function runAnalysis(type) {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    overlay.style.display = 'flex';

    const endpoint = type === 'quick' ? '/api/run-quick' : '/api/run-full';
    loadingText.textContent = type === 'quick'
        ? 'Running quick analysis (10 stocks)...'
        : 'Running full analysis (50 stocks)... This may take 2-3 minutes';

    try {
        const resp = await fetch(endpoint, { method: 'POST' });
        const result = await resp.json();
        if (result.status === 'success') {
            await loadAnalysis();
        } else {
            alert('Analysis failed: ' + (result.message || 'Unknown error'));
        }
    } catch (e) {
        alert('Error running analysis: ' + e.message);
    } finally {
        overlay.style.display = 'none';
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
    document.getElementById('last-updated').textContent = `Last run: ${dt.toLocaleString('en-IN')}`;
    document.getElementById('footer-time').textContent = dt.toLocaleString('en-IN');

    populateSectorFilter();
    renderTable(analysisData.top_picks);
    renderForumSentiment();
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

function applyFilters() {
    if (!analysisData) return;
    let stocks = analysisData.top_picks;

    const cat = document.getElementById('filter-category').value;
    const conv = document.getElementById('filter-conviction').value;
    const sector = document.getElementById('filter-sector').value;
    const search = document.getElementById('filter-search').value.toLowerCase();

    if (cat !== 'all') stocks = stocks.filter(s => s.classification === cat);
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
            `₹${(s.price || 0).toFixed(2)}`,
            `₹${(s.market_cap_cr || 0).toLocaleString('en-IN')}Cr`,
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

        // Category badge
        const catTd = document.createElement('td');
        const catBadge = document.createElement('span');
        catBadge.className = `badge badge-${s.classification === 'penny' ? 'penny' : s.classification === 'small_cap' ? 'small' : 'mid'}`;
        catBadge.textContent = s.classification;
        catTd.appendChild(catBadge);
        tr.appendChild(catTd);

        // Score
        const scoreTd = document.createElement('td');
        scoreTd.textContent = s.score;
        tr.appendChild(scoreTd);

        // Adjusted Score
        const adjTd = document.createElement('td');
        const adjStrong = document.createElement('strong');
        adjStrong.textContent = s.adjusted_score;
        adjTd.appendChild(adjStrong);
        tr.appendChild(adjTd);

        // Conviction badge
        const convTd = document.createElement('td');
        const convBadge = document.createElement('span');
        convBadge.className = `badge badge-${convictionClass(s.conviction_level)}`;
        convBadge.textContent = s.conviction_level;
        convTd.appendChild(convBadge);
        tr.appendChild(convTd);

        // Red flags
        const flagTd = document.createElement('td');
        (s.red_flags || []).forEach(f => {
            const chip = document.createElement('span');
            chip.className = 'red-flag-chip';
            chip.textContent = f;
            flagTd.appendChild(chip);
        });
        tr.appendChild(flagTd);

        // Action button
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
        `${stock.symbol} — ${stock.name} (₹${stock.price?.toFixed(2)} | ${stock.conviction_level})`;

    // Fundamentals
    const fund = stock.fundamentals;
    const fundEl = document.getElementById('detail-fundamentals');
    fundEl.textContent = '';
    const fundList = document.createElement('ul');
    const fundItems = [
        `PE Ratio: ${fund.pe_ratio?.toFixed(1) ?? 'N/A'}`,
        `PB Ratio: ${fund.pb_ratio?.toFixed(2) ?? 'N/A'}`,
        `ROE: ${fund.roe ? (fund.roe * 100).toFixed(1) + '%' : 'N/A'}`,
        `Debt/Equity: ${fund.debt_to_equity?.toFixed(0) ?? 'N/A'}`,
        `Revenue Growth: ${fund.revenue_growth ? (fund.revenue_growth * 100).toFixed(1) + '%' : 'N/A'}`,
        `Earnings Growth: ${fund.earnings_growth ? (fund.earnings_growth * 100).toFixed(1) + '%' : 'N/A'}`,
        `Promoter Holding: ${fund.promoter_holding ? (fund.promoter_holding * 100).toFixed(1) + '%' : 'N/A'}`,
        `EPS: ${fund.eps?.toFixed(2) ?? 'N/A'}`,
        `Book Value: ₹${fund.book_value?.toFixed(2) ?? 'N/A'}`,
    ];
    fundItems.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        fundList.appendChild(li);
    });
    fundEl.appendChild(fundList);

    // SWOT
    const swot = stock.swot;
    const swotEl = document.getElementById('detail-swot');
    swotEl.textContent = '';
    const swotGrid = document.createElement('div');
    swotGrid.className = 'swot-grid';

    ['strengths', 'weaknesses', 'opportunities', 'threats'].forEach(key => {
        const box = document.createElement('div');
        box.className = `swot-box swot-${key}`;
        const h4 = document.createElement('h4');
        h4.textContent = key.charAt(0).toUpperCase() + key.slice(1);
        box.appendChild(h4);
        (swot[key] || []).forEach(item => {
            const p = document.createElement('p');
            p.textContent = `• ${item}`;
            box.appendChild(p);
        });
        swotGrid.appendChild(box);
    });
    swotEl.appendChild(swotGrid);

    // Bear Case
    const bearEl = document.getElementById('detail-bear-case');
    bearEl.textContent = '';
    if (stock.bear_case?.length) {
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

    // Penalties
    const ch = stock.challenge_detail || {};
    const penEl = document.getElementById('detail-penalties');
    penEl.textContent = '';
    const penList = document.createElement('ul');
    [`Valuation: ${ch.valuation_penalty ?? 0}`,
     `Debt Trap: ${ch.debt_penalty ?? 0}`,
     `Promoter: ${ch.promoter_penalty ?? 0}`,
     `Sector: ${ch.sector_penalty ?? 0}`,
     `Pump/Dump: ${ch.pump_dump_penalty ?? 0}`,
     `Total Penalty: ${stock.penalty ?? 0}`
    ].forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        if (text.startsWith('Total')) {
            const strong = document.createElement('strong');
            strong.textContent = text;
            li.textContent = '';
            li.appendChild(strong);
        }
        penList.appendChild(li);
    });
    penEl.appendChild(penList);

    // Score Reasons
    const reasonEl = document.getElementById('detail-reasons');
    reasonEl.textContent = '';
    if (stock.score_reasons?.length) {
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

    // Risks
    const riskEl = document.getElementById('detail-risks');
    riskEl.textContent = '';
    const risks = [...(stock.red_flags || []), ...(stock.swot?.threats || [])];
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

    panel.scrollIntoView({ behavior: 'smooth' });
}

function closeDetail() {
    document.getElementById('detail-panel').style.display = 'none';
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
        title.textContent = m.title;
        title.style.color = 'var(--text)';
        title.style.textDecoration = 'none';
        title.style.display = 'block';
        title.style.marginTop = '0.25rem';
        div.appendChild(title);
        container.appendChild(div);
    });
}

// Init
loadAnalysis();
