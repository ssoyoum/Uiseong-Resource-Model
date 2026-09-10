// Run with SGIS_DOM_RUNTIME pointing at a directory with linkedom installed.
// DOM integration only: Leaflet rendering and browser layout are not simulated.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {readFile} from 'node:fs/promises';

const root = fileURLToPath(new URL('../', import.meta.url));
const runtime = process.env.SGIS_DOM_RUNTIME;
if (!runtime) throw new Error('Set SGIS_DOM_RUNTIME to the temporary npm prefix containing linkedom.');
const {parseHTML} = await import(pathToFileURL(path.join(runtime, 'node_modules/linkedom/esm/index.js')));
const {document, window} = parseHTML(await readFile(path.join(root, 'index.html'), 'utf8'));

// linkedom exposes select.value as a getter; browsers also provide its setter.
const selectPrototype = Object.getPrototypeOf(document.querySelector('select'));
const selectGetter = Object.getOwnPropertyDescriptor(selectPrototype, 'value').get;
Object.defineProperty(selectPrototype, 'value', {get: selectGetter, set(value) {
  [...this.options].forEach(option => { option.selected = option.value === value; });
}});
Object.assign(globalThis, {document, window, CustomEvent: window.CustomEvent,
  requestAnimationFrame: () => 0, location: {reload() {}},
  fetch: async relative => {
    try {
      const body = await readFile(path.join(root, relative), 'utf8');
      return {ok: true, json: async () => JSON.parse(body), text: async () => body};
    } catch { return {ok: false, status: 404}; }
  },
});
const layer = () => ({addTo() {return this;}, addData() {}, bindPopup() {}, clearLayers() {}, addLayer() {},
  getBounds() {return {isValid: () => true, pad() {return this;}};}});
globalThis.L = {map: () => ({fitBounds() {}, setMaxBounds() {}}), tileLayer: layer,
  geoJSON: layer, layerGroup: layer, circleMarker: layer, control: {layers: layer}};
const selectedValue = selector => {
  const select = document.querySelector(selector);
  return select?.options?.find?.(option => option.selected)?.value
    || [...(select?.options || [])].find(option => option.selected)?.value;
};
const click = selector => {
  const element = document.querySelector(selector);
  assert.ok(element, `Missing element ${selector}`);
  element.dispatchEvent(new window.Event('click', {bubbles: true}));
};
const changeSelect = (selector, value) => {
  const select = document.querySelector(selector);
  assert.ok(select, `Missing select ${selector}`);
  select.value = value;
  select.dispatchEvent(new window.Event('change', {bubbles: true}));
};
const until = async predicate => {
  const deadline = Date.now() + 5000;
  while (!predicate()) {
    assert.ok(Date.now() < deadline, 'DOM initialization timed out');
    await new Promise(resolve => setTimeout(resolve, 10));
  }
};

test('D/E/F controls select, reset, and synchronize with actual map filter results', async () => {
  const source = await readFile(path.join(root, 'app.js'), 'utf8');
  new vm.Script(source, {filename: path.join(root, 'app.js'),
    importModuleDynamically: vm.constants.USE_MAIN_CONTEXT_DEFAULT_LOADER}).runInThisContext();
  document.dispatchEvent(new window.Event('DOMContentLoaded'));
  await until(() => document.querySelectorAll('.def-point').length === 175
    && document.querySelector('#filtered-count')?.textContent === '427'
    && document.querySelectorAll('[data-emd]').length === 18
    && document.querySelectorAll('.map-legend-row [data-policy-filter]').length === 7);

  click('[data-sgis-filter="both"]');
  assert.equal(document.querySelectorAll('.def-point').length, 42);
  click('[data-sgis-filter="all"]');
  assert.equal(document.querySelectorAll('.def-point').length, 175);
  changeSelect('#sgis-map-filter', 'both');
  assert.equal(document.querySelector('#filtered-count').textContent, '42');
  assert.equal(document.querySelector('[data-sgis-filter="both"]').getAttribute('aria-pressed'), 'true');
  changeSelect('#sgis-map-filter', 'all');
  assert.equal(document.querySelector('#filtered-count').textContent, '427');
  click('.def-point');
  assert.match(document.querySelector('#def-point-detail').textContent, /5분.*10분.*증가/);

  click('#analysis-e [data-policy-code="YOUTH_PARTICIPATION_REVIEW"]');
  assert.equal(document.querySelector('#filtered-count').textContent, '43');
  assert.equal(document.querySelector('.map-legend-row [data-policy-filter="YOUTH_PARTICIPATION_REVIEW"]').getAttribute('aria-pressed'), 'true');
  assert.match(document.querySelector('#def-policy-detail').textContent, /청년참여 검토/);

  click('.map-legend-row [data-policy-filter="COMMUNITY_SUPPORT_REVIEW"]');
  assert.equal(document.querySelector('#filtered-count').textContent, '53');
  assert.equal(document.querySelector('#analysis-e [data-policy-code="COMMUNITY_SUPPORT_REVIEW"]').getAttribute('aria-pressed'), 'true');
  click('.map-legend-row [data-policy-filter="COMMUNITY_SUPPORT_REVIEW"]');
  assert.equal(document.querySelector('#filtered-count').textContent, '427');

  changeSelect('#road-map-filter', '3');
  assert.equal(document.querySelector('#filtered-count').textContent, '230');
  assert.equal(document.querySelector('[data-road-bin="3"]').getAttribute('aria-pressed'), 'true');
  changeSelect('#road-map-filter', 'all');
  assert.equal(document.querySelector('#filtered-count').textContent, '427');

  const addressSearch = document.querySelector('#pond-search-input');
  addressSearch.value = '의성읍 중리리 82유';
  addressSearch.dispatchEvent(new window.Event('input', {bubbles: true}));
  assert.equal(document.querySelector('#filtered-count').textContent, '1');
  addressSearch.value = '시설명으로는찾지않음';
  addressSearch.dispatchEvent(new window.Event('input', {bubbles: true}));
  assert.equal(document.querySelector('#filtered-count').textContent, '0');
  click('#pond-search-reset');
  assert.equal(document.querySelector('#filtered-count').textContent, '427');

  click('[data-road-bin="3"]');
  assert.match(document.querySelector('#def-road-detail').textContent, /230개/);
  click('[data-emd="안계면"]');
  assert.match(document.querySelector('#def-emd-detail').textContent, /안계면/);
  assert.ok(Number(document.querySelector('#filtered-count').textContent) > 0);
  assert.ok(Number(document.querySelector('#filtered-count').textContent) < 427);
  click('#pond-search-reset');
  assert.equal(document.querySelector('#filtered-count').textContent, '427');
  assert.equal(document.querySelectorAll('[data-emd][aria-pressed="true"]').length, 0);

  const sort = document.querySelector('#def-population-sort');
  const elderlyOption = [...sort.options].find(option => option.value === 'elderly');
  elderlyOption.selected = true;
  sort.dispatchEvent(new window.Event('change', {bubbles: true}));
  const population = JSON.parse(await readFile(path.join(root, 'data/analysis/population_summary.json'), 'utf8'));
  const expected = [...population.data].sort((a,b) => b.elderly_ratio-a.elderly_ratio)[0].emd_name;
  assert.equal(document.querySelector('[data-emd]').dataset.emd, expected);
});
