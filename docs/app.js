(async () => {
  const D = await (await fetch('data.json')).json(), $ = id => document.getElementById(id);
  const fmt = n => Math.round(n).toLocaleString('en-US');
  const short = n => n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e3 ? Math.round(n / 1e3) + 'K' : String(Math.round(n));
  const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x !== undefined) e.textContent = x; return e; };
  const NS = 'http://www.w3.org/2000/svg';
  const svgEl = (svg, tag, a, txt) => { const e = document.createElementNS(NS, tag); for (const k in a) e.setAttribute(k, a[k]); if (txt !== undefined) e.textContent = txt; svg.append(e); return e; };
  const M = D.meta;
  $('note').textContent = 'Synthetic data (fixed seed): ' + fmt(M.orders) + ' orders, ' + fmt(M.customers) + ' customers, ' + M.first + ' to ' + M.last + '. Revenue is in EGP. Nothing here is real company data.';
  [['fr', 'region', 'All regions'], ['fc', 'category', 'All categories'], ['fp', 'payment', 'All payments']].forEach(([id, k, all]) => {
    const s = $(id); s.append(new Option(all, '')); D.dims[k].forEach(v => s.append(new Option(v, v)));
  });
  const state = () => ({ year: $('fy').value, region: $('fr').value, category: $('fc').value, payment: $('fp').value });
  const total = Agg.filter(D, {});

  function line(box, labels, series, opts) {
    const W = 760, H = 250, p = { l: 52, r: 12, t: 12, b: 26 };
    const all = series.flatMap(s => s.values.filter(v => v != null)), mx = Math.max(...all, 1) * 1.08;
    const n = labels.length, x = i => p.l + i / Math.max(n - 1, 1) * (W - p.l - p.r), y = v => H - p.b - v / mx * (H - p.t - p.b);
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    [0, .5, 1].forEach(f => { svgEl(svg, 'line', { x1: p.l, x2: W - p.r, y1: y(mx * f), y2: y(mx * f), stroke: 'rgba(255,255,255,.08)' }); svgEl(svg, 'text', { x: p.l - 6, y: y(mx * f) + 4, 'text-anchor': 'end', fill: '#8fb0ac', 'font-size': 11 }, short(mx * f)); });
    [0, Math.floor(n / 2), n - 1].forEach(i => svgEl(svg, 'text', { x: x(i), y: H - 7, 'text-anchor': i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle', fill: '#8fb0ac', 'font-size': 11 }, labels[i]));
    series.forEach(s => {
      const pts = s.values.map((v, i) => v == null ? null : `${x(i)},${y(v)}`).filter(Boolean);
      if (s.area) { const first = s.values.findIndex(v => v != null), last = s.values.length - 1 - [...s.values].reverse().findIndex(v => v != null); svgEl(svg, 'polygon', { points: `${x(first)},${y(0)} ${pts.join(' ')} ${x(last)},${y(0)}`, fill: 'rgba(45,212,191,.12)' }); }
      svgEl(svg, 'polyline', { points: pts.join(' '), fill: 'none', stroke: s.color, 'stroke-width': 2.2, 'stroke-dasharray': s.dash || '' });
      if (s.dots) s.values.forEach((v, i) => v != null && svgEl(svg, 'circle', { cx: x(i), cy: y(v), r: 3.5, fill: s.color }));
    });
    const dot = svgEl(svg, 'circle', { r: 4.5, fill: '#fff', cx: -10, cy: -10 });
    svg.addEventListener('pointermove', e => { const r = svg.getBoundingClientRect(); const i = Math.max(0, Math.min(n - 1, Math.round(((e.clientX - r.left) / r.width * W - p.l) / (W - p.l - p.r) * (n - 1))));
      const s = series.find(q => q.values[i] != null); if (!s) return; dot.setAttribute('cx', x(i)); dot.setAttribute('cy', y(s.values[i])); opts.onHover && opts.onHover(i, series); });
    box.replaceChildren(svg);
  }

  function drawTrend() {
    const f = state(), r = Agg.filter(D, f);
    [[fmt(r.revenue), 'revenue (EGP)'], [fmt(r.orders), 'orders'], [r.orders ? fmt(r.revenue / r.orders) : '0', 'average order value'],
     [(r.revenue / total.revenue * 100).toFixed(1) + '%', 'of all revenue']].forEach((k, i) => { const t = $('kpis').children[i] || $('kpis').appendChild(el('div', 'kpi')); t.replaceChildren(el('b', '', k[0]), el('span', '', k[1])); });
    const idx = D.months.map((m, i) => i).filter(i => !f.year || D.months[i].startsWith(f.year));
    $('trendSub').textContent = [f.year || 'both years', f.region, f.category, f.payment].filter(Boolean).join(' · ');
    line($('trend'), idx.map(i => D.months[i]), [{ values: idx.map(i => r.perMonth[i].revenue), color: '#2dd4bf', area: true }],
      { onHover: (k) => { const i = idx[k]; $('tip').textContent = D.months[i] + ': ' + fmt(r.perMonth[i].revenue) + ' EGP, ' + r.perMonth[i].orders + ' orders'; } });
  }
  ['fy', 'fr', 'fc', 'fp'].forEach(i => $(i).addEventListener('change', drawTrend));
  $('reset').onclick = () => { ['fy', 'fr', 'fc', 'fp'].forEach(i => $(i).value = ''); drawTrend(); };
  drawTrend();

  // forecast
  const F = D.forecast, act = F.actual, nA = act.length;
  line($('fc1'), D.months.concat(F.future_months), [
    { values: act.concat(F.future.map(() => null)), color: '#2dd4bf', area: true },
    { values: act.map((v, i) => i === nA - 1 ? v : null).concat(F.future), color: '#fbbf24', dash: '6 5', dots: true }], {});
  const name = { naive: 'naive (last month)', mean_3: 'mean of last 3', seasonal_naive: 'seasonal naive (same month last year)', trend_seasonal: 'trend + month effects' };
  const tbl = (box, head, rows) => { const h = el('tr'); head.forEach((x, i) => h.append(el('th', i ? 'r' : '', x))); box.append(h);
    rows.forEach((r, k) => { const tr = el('tr', k === 0 ? 'best' : ''); r.forEach((c, i) => tr.append(el('td', i ? 'r' : '', c))); box.append(tr); }); };
  tbl($('rolling'), ['Rolling origin (10 origins, 3 months ahead)', 'MAPE'], F.rolling.map(r => [name[r.model], r.mape + '%']));
  tbl($('holdout'), ['Single hold-out (last 6 months)', 'MAPE'], F.backtest.map(r => [name[r.model], r.mape + '%']));
  $('fcNote').textContent = 'The rolling test favours ' + name[F.rolling[0].model] + ' (' + F.rolling[0].mape + '% error). The single hold-out favours ' + name[F.backtest[0].model] + ' (' + F.backtest[0].mape + '%). With 24 months the two disagree, so treat the dashed line (' + name[F.best] + ') as a baseline, not a prediction. MAPE is the mean absolute percentage error.';

  // cohort heatmap
  const C = D.cohort, cols = C.values[0].length, hm = el('div', 'heat'); hm.style.gridTemplateColumns = `62px 34px repeat(${cols - 1},minmax(0,1fr))`;
  hm.append(el('div', 'h', 'cohort'), el('div', 'h', 'size')); for (let a = 1; a < cols; a++) hm.append(el('div', 'h', '+' + a));
  C.cohorts.forEach((c, i) => { hm.append(el('div', 'l', c), el('div', 'l', C.sizes[i]));
    for (let a = 1; a < cols; a++) { const v = C.values[i][a], d = el('div', '', v == null ? '' : v.toFixed(0)); d.style.background = v == null ? 'rgba(255,255,255,.04)' : `rgba(45,212,191,${Math.min(.12 + v / 14 * .8, .95)})`; d.style.color = v != null && v > 8 ? '#04100f' : '#bfe9e3'; d.title = v == null ? 'not observable yet' : c + ', month +' + a + ': ' + v + '%'; hm.append(d); } });
  $('cohort').append(hm);

  // rfm
  const totC = D.rfm.reduce((s, r) => s + r[1], 0), totR = D.rfm.reduce((s, r) => s + r[2], 0);
  const bar = (box, label, pct, text, cls) => { const row = el('div', 'hb'), t = el('div', 't'), f = el('div', 'f ' + (cls || '')); f.style.width = Math.min(pct, 100) + '%'; t.append(f); row.append(el('div', 'n', label), t, el('div', 'v', text)); box.append(row); };
  D.rfm.forEach(r => { bar($('rfm'), r[0] + ' customers', r[1] / totC * 100, (r[1] / totC * 100).toFixed(0) + '%'); bar($('rfm'), r[0] + ' revenue', r[2] / totR * 100, (r[2] / totR * 100).toFixed(0) + '%', 'w'); });
  const leg = el('p', '', 'Teal is share of customers, amber is share of revenue, per segment.'); leg.style.cssText = 'color:#8fb0ac;font-size:12px;margin-top:8px'; $('rfm').append(leg);

  // pareto
  { const W = 420, H = 300, p = { l: 40, r: 10, t: 10, b: 28 }, svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const x = v => p.l + v / 100 * (W - p.l - p.r), y = v => H - p.b - v / 100 * (H - p.t - p.b);
    [0, 50, 100].forEach(v => { svgEl(svg, 'line', { x1: p.l, x2: W - p.r, y1: y(v), y2: y(v), stroke: 'rgba(255,255,255,.08)' }); svgEl(svg, 'text', { x: p.l - 6, y: y(v) + 4, 'text-anchor': 'end', fill: '#8fb0ac', 'font-size': 11 }, v + '%'); svgEl(svg, 'text', { x: x(v), y: H - 8, 'text-anchor': 'middle', fill: '#8fb0ac', 'font-size': 11 }, v + '%'); });
    svgEl(svg, 'line', { x1: x(0), y1: y(0), x2: x(100), y2: y(100), stroke: '#8fb0ac', 'stroke-dasharray': '4 4' });
    svgEl(svg, 'polyline', { points: D.pareto.map(q => x(q[0]) + ',' + y(q[1])).join(' '), fill: 'none', stroke: '#2dd4bf', 'stroke-width': 2.4 });
    svgEl(svg, 'circle', { cx: x(20), cy: y(D.pareto_top20), r: 5, fill: '#fbbf24' }); $('pareto').append(svg);
    $('parNote').textContent = 'The top 20% of customers bring ' + D.pareto_top20 + '% of revenue. Dashed line is perfect equality.'; }

  // yoy
  const mxY = Math.max(...D.yoy.flatMap(r => [r[1], r[2]]));
  D.yoy.forEach(r => { const row = el('div', 'hb'); row.style.gridTemplateColumns = '120px 1fr 130px'; const t = el('div'); [[r[1], '#0d9488'], [r[2], '#2dd4bf']].forEach(([v, c]) => { const tr = el('div', 't'); tr.style.margin = '3px 0'; const f = el('div', 'f'); f.style.cssText = `width:${v / mxY * 100}%;background:${c}`; tr.append(f); t.append(tr); });
    row.append(el('div', 'n', r[0]), t, el('div', 'v', (r[3] > 0 ? '+' : '') + r[3] + '% YoY')); $('yoy').append(row); });
})();
