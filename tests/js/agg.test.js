// Checks docs/agg.js filtering against totals computed by pandas (tests/fixtures/filters.json).
const test = require('node:test');
const assert = require('node:assert');
const Agg = require('../../docs/agg.js');
const data = require('../../docs/data.json');
const cases = require('../fixtures/filters.json');

for (const c of cases) {
  test(`filter ${JSON.stringify([c.year, c.region, c.category])}`, () => {
    const r = Agg.filter(data, { year: c.year, region: c.region, category: c.category });
    assert.strictEqual(r.orders, c.orders);
    assert.ok(Math.abs(r.revenue - c.revenue) < 0.5, `${r.revenue} vs ${c.revenue}`);
  });
}
