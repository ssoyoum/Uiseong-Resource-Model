import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {parseCsv, number, sgisModel, policyModel, roadModel} from '../def-dashboard.mjs';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const csv = async path => parseCsv(await read(path));

test('CSV preserves BOM, commas, quoted newlines and empty missing values', () => {
  assert.deepEqual(parseCsv('\uFEFFid,address,value\r\n1,"가음면, \"\"못\"\"\n주소",\r\n'),
    [{id: '1', address: '가음면, "못"\n주소', value: ''}]);
  assert.equal(number(''), null);
  assert.equal(number('DATA_NOT_AVAILABLE'), null);
  assert.equal(number(null), null);
  assert.equal(number('0'), 0);
});

test('SGIS scatter uses the eligible paired IDs and excludes representative coordinates', async () => {
  const rows = await csv('data/analysis/sgis_catchment_analysis.csv');
  const policies = await csv('data/analysis/sgis_policy_evidence.csv');
  const summary = JSON.parse(await read('data/analysis/sgis_catchment_analysis.json'));
  const model = sgisModel(rows, summary, policies);
  assert.equal(model.eligible.length, 380);
  assert.equal(model.paired.length, 175);
  assert.equal(model.paired.some(row => String(row.pond_id) === '1'), false);
  assert.equal(Math.max(...model.paired.map(row => row.p5)), 2298);
  assert.equal(Math.max(...model.paired.map(row => row.p10)), 3877);
  assert.equal(model.paired.filter(row => row.flags.includes('HIGH_10MIN_REACH') && row.flags.includes('HIGH_5_TO_10_EXPANSION')).length, 42);
});

test('missing SGIS values stay missing, while actual zero values remain eligible', () => {
  const base = {sgis_analysis_eligible: 'True', sgis_population_5min: '0', sgis_population_10min: '0'};
  const rows = [{...base, pond_id: '1', coordinate_group_id: 'a'}, {...base, pond_id: '2', coordinate_group_id: 'b', sgis_population_5min: ''}];
  const model = sgisModel(rows, {facility_count: 2, coverage: {available_both: 1}}, []);
  assert.deepEqual(model.paired.map(row => row.pond_id), ['1']);
});

test('all policy categories are computed from actual rows and contain 427 distinct IDs', async () => {
  const groups = policyModel(await csv('data/analysis/sgis_policy_evidence.csv'));
  assert.deepEqual(groups.map(group => group.rows.length), [47, 190, 53, 43, 20, 74]);
  assert.equal(new Set(groups.flatMap(group => group.rows.map(row => row.pond_id))).size, 427);
  assert.throws(() => policyModel([{pond_id: '1', policy_review_context: 'UNKNOWN'}]));
});

test('road histogram matches actual distances instead of the former hardcoded 228/125/46/28', async () => {
  const model = roadModel(await csv('data/analysis/pond_accessibility.csv'));
  assert.deepEqual(model.bins.map(bin => bin.rows.length), [78, 56, 63, 230]);
  assert.equal(model.total, 427);
  assert.equal(model.missing, 0);
});

test('distance boundaries are mutually exclusive and missing distance is not zero', () => {
  const values = ['', 0, 100, 100.1, 300, 300.1, 500, 500.1];
  const model = roadModel(values.map((distance, id) => ({pond_id: String(id), distance_to_road_m: distance})));
  assert.deepEqual(model.bins.map(bin => bin.rows.length), [2, 2, 2, 1]);
  assert.equal(model.missing, 1);
});
