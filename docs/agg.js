/* Filtering over the exported cube. tests/js/agg.test.js checks it against pandas totals. */
(function (root) {
  // cube row: [monthIndex, regionIndex, categoryIndex, paymentIndex, revenue, orders]
  function filter(data, f) {
    const R = f.region ? data.dims.region.indexOf(f.region) : -1;
    const C = f.category ? data.dims.category.indexOf(f.category) : -1;
    const P = f.payment ? data.dims.payment.indexOf(f.payment) : -1;
    const perMonth = data.months.map(() => ({ revenue: 0, orders: 0 }));
    let revenue = 0, orders = 0;
    for (const [m, r, c, p, rev, n] of data.cube) {
      if (f.year && !data.months[m].startsWith(String(f.year))) continue;
      if (R >= 0 && r !== R) continue;
      if (C >= 0 && c !== C) continue;
      if (P >= 0 && p !== P) continue;
      perMonth[m].revenue += rev; perMonth[m].orders += n; revenue += rev; orders += n;
    }
    return { revenue: Math.round(revenue * 100) / 100, orders, perMonth };
  }
  const api = { filter };
  if (typeof module !== 'undefined') module.exports = api; else root.Agg = api;
})(this);
