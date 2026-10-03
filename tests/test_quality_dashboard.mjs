import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {parseCsv} from '../def-dashboard.mjs';
import {initQualityDashboard} from '../quality-dashboard.mjs';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const loaders = {
  loadJson: async path => JSON.parse((await read(path)).replace(/^﻿/, '')),
  loadCsv: async path => parseCsv(await read(path)),
};
const text = html => html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

async function render() {
  const blocks = {};
  globalThis.document = {getElementById: id => (blocks[id] ??= {id, innerHTML: '', querySelector: () => null})};
  await initQualityDashboard(loaders);
  return Object.fromEntries(Object.entries(blocks).map(([id, block]) => [id, block.innerHTML]));
}

test('G–J render saved outputs without load errors or broken values', async () => {
  const blocks = await render();
  assert.deepEqual(Object.keys(blocks), ['quality-g', 'quality-h', 'quality-i', 'quality-j']);
  for (const [id, html] of Object.entries(blocks)) {
    assert.doesNotMatch(text(html), /자료를 확인할 수 없습니다|undefined|NaN|Infinity|\[object Object\]/, id);
  }
});

test('quality audit counts on the page match the saved audit', async () => {
  const audit = JSON.parse(await read('data/analysis/data_quality_audit.json'));
  const page = text((await render())['quality-g']);
  assert.match(page, new RegExp(`${audit.status_counts.PASS} / ${audit.checks.length}`));
  assert.equal(audit.status_counts.FAIL ?? 0, 0);
});

test('source table shows every manifest row and marks unknown values instead of guessing', async () => {
  const rows = parseCsv(await read('data/manifests/source_manifest.csv'));
  const html = (await render())['quality-h'];
  for (const row of rows) assert.ok(html.includes(row.dataset_name.replace(/&/g, '&amp;')), row.dataset_name);
  assert.ok(html.includes('미확인'));
  assert.ok(!html.includes('DATA_NOT_AVAILABLE'));
  // 레이어 개념이 없는 자료는 '미확인'이 아니라 '해당 없음'으로 표시한다.
  assert.ok(html.includes('해당 없음'));
});

test('coordinate candidates are reported as not applied and match the saved summary', async () => {
  const summary = JSON.parse(await read('data/analysis/coordinate_geocode_candidates.json'));
  const page = text((await render())['quality-i']);
  assert.match(page, new RegExp(`좌표 검토 대상 ${summary.record_count}개`));
  assert.match(page, new RegExp(`지번 완전 일치 ${summary.status_counts.EXACT_PARCEL_MATCH}개`));
  assert.match(page, /현재 분석 반영 0개/);
});

test('sensitivity block labels the experiment and keeps WorldPop separate from official population', async () => {
  const page = text((await render())['quality-j']);
  assert.match(page, /확정 순위나 사업 대상 선정이 아닙니다/);
  assert.match(page, /공식 인구가 아닙니다/);
});
