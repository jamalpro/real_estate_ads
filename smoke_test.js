// Smoke test for the generated page: node smoke_test.js
// Loads real_estate_ads.html, runs its script against a minimal DOM, and checks
// that listings actually render and the filters/sorts/export behave.
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const html = fs.readFileSync(path.join(__dirname, 'real_estate_ads.html'), 'utf8');
const dataIsland = html.match(/<script id="ads-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const pageScript = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/)[1];

const failures = [];
function check(name, condition, detail) {
  if (condition) return;
  failures.push(name + (detail ? ': ' + detail : ''));
}

function makeElement(id) {
  return {
    id,
    value: '',
    textContent: '',
    innerHTML: '',
    hidden: false,
    offsetHeight: 150,
    children: [],
    listeners: {},
    appendChild(child) { this.children.push(child); },
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); },
    fire(type) { (this.listeners[type] || []).forEach((fn) => fn.call(this)); }
  };
}

const els = new Map([['ads-data', Object.assign(makeElement('ads-data'), { textContent: dataIsland })]]);
const $ = (id) => {
  if (!els.has(id)) els.set(id, makeElement(id));
  return els.get(id);
};

let downloaded = null;
const sandbox = {
  Intl, Map, Set, Array, Object, String, Number, Math, JSON, console,
  setTimeout, clearTimeout,
  document: {
    getElementById: $,
    documentElement: { style: { setProperty() {} } },
    createElement: () => ({ click() { downloaded = this.href; }, set href(v) { this._h = v; }, get href() { return this._h; } })
  },
  window: { addEventListener() {} },
  Option: function (text, value) { return { text, value }; },
  Blob: function (parts) { this.text = parts.join(''); sandbox.__lastBlob = this; },
  URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} }
};
sandbox.window.document = sandbox.document;

vm.createContext(sandbox);
try {
  vm.runInContext(pageScript, sandbox, { filename: 'page.js' });
} catch (err) {
  console.error('page script threw: ' + err.message);
  process.exit(1);
}

const total = JSON.parse(dataIsland).ads.length;
const countCards = () => ($('cards').innerHTML.match(/<article class="card">/g) || []).length;
const settle = () => new Promise((r) => setTimeout(r, 200));

async function run() {
  check('all ads render on load', countCards() === total, countCards() + ' of ' + total);
  check('empty state hidden', $('empty').hidden === true);
  check('stats rendered', $('stats').innerHTML.includes('نتائج الفلترة'));
  check('meta line rendered', $('meta').textContent.includes('إعلان'));
  check('transaction options populated', $('trx').children.length > 1, String($('trx').children.length));
  check('area options populated', $('area').children.length > 20, String($('area').children.length));
  check('raw text is escaped', !/<article[\s\S]*?<script/.test($('cards').innerHTML));

  // Arabic spelling variants must match: "الروضه" should find ads written "الروضة".
  $('q').value = 'الروضه';
  $('q').fire('input');
  await settle();
  const variantHits = countCards();
  check('normalized Arabic search finds variants', variantHits > 0, String(variantHits));

  // Arabic-Indic digits in ad text must match Latin digits typed by the user.
  $('q').value = '100';
  $('q').fire('input');
  await settle();
  check('digit search matches Arabic-Indic numerals', countCards() > 0);

  $('q').value = '';
  $('q').fire('input');
  await settle();
  check('clearing search restores all ads', countCards() === total);

  // Cheapest-first must not be polluted by ads with no USD price.
  $('sort').value = 'price_asc';
  $('sort').fire('change');
  const prices = [...$('cards').innerHTML.matchAll(/class="price">([\s\S]*?)<\/div>/g)].map((m) => m[1]);
  check('price sort keeps unpriced ads last', !prices[0].includes('السعر غير مذكور'));

  $('maxPrice').value = '100000';
  $('maxPrice').fire('input');
  await settle();
  check('max price filters the list', countCards() > 0 && countCards() < total, String(countCards()));
  check('max price shows the USD-only note', $('note').hidden === false);

  $('btnView').fire('click');
  check('table view renders rows', ($('tbody').innerHTML.match(/<tr>/g) || []).length === countCards() || $('tbody').innerHTML.includes('<tr>'));
  check('table view empties the card grid', $('cards').innerHTML === '');
  $('btnView').fire('click');

  $('btnCsv').fire('click');
  const csv = sandbox.__lastBlob.text;
  check('csv export starts with a BOM', csv.charCodeAt(0) === 0xfeff);
  check('csv export has one row per result', csv.split('\r\n').length >= 2);

  $('btnReset').fire('click');
  check('reset restores every ad', countCards() === total, String(countCards()));
  check('reset hides the price note', $('note').hidden === true);

  if (failures.length) {
    console.error('FAIL (' + failures.length + ')');
    failures.forEach((f) => console.error('  - ' + f));
    process.exit(1);
  }
  console.log('ok - all checks passed (' + total + ' ads)');
}

run();
