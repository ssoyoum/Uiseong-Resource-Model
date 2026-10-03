// Analysis G–J: data quality, source manifest, coordinate candidates and sensitivity.
// Shows saved pipeline outputs only. No API calls, no recalculation of results.
import {number} from './def-dashboard.mjs?v=20261001-d-hover';

const html = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fmt = (value, digits = 1) => number(value) === null ? '미확인' : number(value).toLocaleString('ko-KR', {maximumFractionDigits: digits});
const NA = 'DATA_NOT_AVAILABLE';

const card = (label, value, note) => `<div class="def-stat"><span>${html(label)}</span><strong>${html(value)}</strong><small>${html(note)}</small></div>`;
const heading = (letter, title, note) => `<div class="def-heading"><span class="def-letter">${letter}</span><div><h3>분석 ${letter}. ${title}</h3><p class="analysis-note">${note}</p></div></div>`;
const table = (headers, rows) => `<div class="def-table-wrap"><table class="def-table"><thead><tr>${headers.map(t => `<th scope="col">${html(t)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
const source = (text, links) => `<p class="def-source">${html(text)} · ${links.map(([label, path]) => `<a href="${path}" target="_blank" rel="noopener">${html(label)} ↗</a>`).join(' · ')}</p>`;
const badge = status => {
  const kind = {PASS: 'pass', WARN: 'warn', FAIL: 'fail', INFO: 'info'}[status] || 'na';
  const label = {PASS: '통과', WARN: '주의', FAIL: '실패', INFO: '참고'}[status] || (status === NA ? '미확인' : status);
  return `<span class="quality-badge quality-badge-${kind}">${html(label)}</span>`;
};
const valueCell = value => {
  if (value === 'NOT_APPLICABLE') return '<span class="def-muted">해당 없음</span>';
  return (!value || value === NA) ? '<span class="quality-badge quality-badge-na">미확인</span>' : html(value);
};
// 긴 API 경로는 '/'·'+' 뒤에서 줄바꿈되게 한다(값이 있는 경우에만).
const layerCell = value => (!value || value === NA || value === 'NOT_APPLICABLE') ? valueCell(value) : html(value).replace(/([/+])/g, '$1<wbr>');

const CHECK_LABELS = {
  population_emd_count_18: ['인구', '읍·면 18개, 코드 중복 없음'],
  population_subgroups_within_total: ['인구', '청년+고령 ≤ 총인구'],
  population_ratio_recompute: ['인구', '청년·고령 비율 재계산 일치'],
  population_emd_sum_equals_county_total: ['인구', '읍·면 합계 = 원자료 의성군 총계'],
  sgis_rows_unique_427x2: ['SGIS', '427개 × 5·10분 요청, 중복 없음'],
  sgis_available_population_present: ['SGIS', '확보 응답에 인구값 존재'],
  sgis_population_non_negative: ['SGIS', '인구값 음수 없음'],
  sgis_missing_not_zero_filled: ['SGIS', '미확보 응답을 0명으로 채우지 않음'],
  sgis_5min_not_greater_than_10min: ['SGIS', '5분 인구·면적 ≤ 10분'],
  sgis_displayed_vs_api_total: ['SGIS', '화면 표시값과 API 합계 차이'],
  context_rows_427_unique: ['공간', '주변여건 427개, 중복 없음'],
  facility_count_500m_le_1km: ['공간', '시설 수 500m ≤ 1km'],
  road_length_500m_le_1km: ['공간', '도로 길이 500m ≤ 1km'],
  agricultural_area_500m_le_1km: ['공간', '농업면적 500m ≤ 1km'],
  agricultural_ratio_500m_in_0_100: ['공간', '500m 농업비율 0~100%'],
  agricultural_ratio_1000m_in_0_100: ['공간', '1km 농업비율 0~100%'],
  official_population_fields_empty_without_grid: ['혼용 방지', '공식 인구격자 미확보 → official_* 비어 있음'],
  worldpop_500m_le_1km: ['공간', 'WorldPop 참고인구 500m ≤ 1km'],
  road_distance_complete_non_negative: ['도로', '427개 도로거리 산출, 음수 없음'],
  road_source_year_recorded: ['도로', 'UQ151 기준연도 기록'],
  classification_complete_with_reason: ['분류', '427개 유형과 판단 사유 기록'],
  coordinate_corrections_not_applied: ['좌표', '보정 후보 미반영 상태 유지'],
  submission_numbers_frozen: ['재현성', '핵심 수치(427·380·190 등) 고정'],
  raw_checksums_unchanged: ['재현성', '원자료 SHA-256 변화 없음'],
};

function checkEvidence(item) {
  const d = item.details || {};
  switch (item.name) {
    case 'population_emd_sum_equals_county_total': return `${d.year}년 ${fmt(d.emd_sum, 0)}명 = ${fmt(d.county_total_in_raw, 0)}명`;
    case 'sgis_rows_unique_427x2': return `${fmt(d.rows, 0)}건 · 중복 ${fmt(d.duplicate_keys, 0)}건`;
    case 'sgis_missing_not_zero_filled': return `미확보 ${fmt(d.missing_rows, 0)}건 모두 빈 값`;
    case 'sgis_5min_not_greater_than_10min': return `양쪽 확보 ${fmt(d.ponds_with_both, 0)}개 · 위반 ${(d.population_violations || []).length + (d.service_area_violations || []).length}건`;
    case 'sgis_displayed_vs_api_total': return `${fmt(d.compared, 0)}건 중 5% 초과 ${fmt(d.over_5_percent, 0)}건 · 분석은 표시값 사용`;
    case 'road_distance_complete_non_negative': return `${fmt(d.min_m, 0)}–${fmt(d.max_m, 0)}m · 결측 ${fmt(d.missing, 0)}개`;
    case 'road_source_year_recorded': return '원자료에 기준연도 명시 없음 → 추정하지 않음';
    case 'classification_complete_with_reason': return `사유 누락 ${fmt(d.missing_reason, 0)}개`;
    case 'coordinate_corrections_not_applied': return `검토 대상 ${fmt(d.template_rows, 0)}개 · 반영 ${fmt(d.rows_with_correction, 0)}개`;
    case 'submission_numbers_frozen': return `${(d.checked || []).length}개 수치 · 변경 ${Object.keys(d.changed || {}).length}개`;
    case 'raw_checksums_unchanged': return `변경 ${(d.changed || []).length}개 · 로컬 누락 ${(d.missing_local || []).length}개`;
    default: {
      if ('violations' in d) return `위반 ${fmt(d.violations, 0)}건`;
      if ('rows' in d) return `${fmt(d.rows, 0)}행`;
      if ('max_abs_error' in d) return `최대 오차 ${Number(d.max_abs_error).toExponential(1)}`;
      if ('min' in d && 'max' in d) return `${fmt(d.min)}–${fmt(d.max)}%`;
      return '';
    }
  }
}

function renderQuality(block, audit, validation) {
  const counts = audit.status_counts || {};
  const total = audit.checks.length;
  const raw = audit.checks.find(item => item.name === 'raw_checksums_unchanged');
  const frozen = audit.checks.find(item => item.name === 'submission_numbers_frozen');
  block.innerHTML = heading('G', '데이터 품질 자동 점검', '분석 결과를 다시 만들 때마다 인구 합계, SGIS 응답, Buffer 값, 원자료 변화를 자동으로 대조합니다. 점검은 결과를 고치지 않고 이상 여부만 기록합니다.') + `
    <div class="def-stat-grid">${card('품질 점검 통과', `${counts.PASS || 0} / ${total}`, `주의 ${counts.WARN || 0} · 실패 ${counts.FAIL || 0} · 참고 ${counts.INFO || 0}`)}${card('공간 검증', `${validation.pass_count} PASS`, `실패 ${validation.fail_count}건 · CRS·경계·geometry`)}${card('재현성 고정', `${(frozen?.details?.checked || []).length}개 수치`, `원자료 SHA-256 ${raw?.status === 'PASS' ? '변화 없음' : '확인 필요'} · 변경 시 실패 처리`)}</div>
    <div class="def-panel">${table(['영역', '점검 내용', '결과', '근거'], audit.checks.map(item => {
      const [area, label] = CHECK_LABELS[item.name] || ['기타', item.name];
      return `<tr><td>${html(area)}</td><th scope="row">${html(label)}</th><td>${badge(item.status)}</td><td>${html(checkEvidence(item))}</td></tr>`;
    }))}
    <p class="def-muted">‘주의’는 오류가 아니라 확인되지 않은 정보를 숨기지 않고 표시한 것입니다. ‘참고’는 SGIS 비밀보호 처리로 화면 표시값과 API 합계가 다를 수 있음을 기록한 항목입니다.</p></div>` +
    source('자동 품질 점검 · 파이프라인 실행마다 갱신', [['품질 점검 JSON', 'data/analysis/data_quality_audit.json'], ['공간 검증 JSON', 'data/analysis/validation_report.json']]);
}

function renderSources(block, rows) {
  const confirmedYear = rows.filter(row => row.reference_year && row.reference_year !== NA).length;
  const notRedistributed = rows.filter(row => String(row.redistribution_status).startsWith('RAW_NOT_REDISTRIBUTED')).length;
  block.innerHTML = heading('H', '데이터 출처와 기준연도', '분석에 쓴 자료를 같은 12개 항목으로 정리했습니다. 원본에서 확인되지 않은 값은 추정하지 않고 ‘미확인’으로 표시합니다.') + `
    <div class="def-stat-grid">${card('정리한 자료', `${rows.length}건`, 'VWorld·행정안전부·SGIS·교통문화지수·WorldPop')}${card('기준연도 확인', `${confirmedYear}건`, `미확인 ${rows.length - confirmedYear}건`)}${card('원자료 미공개', `${notRedistributed}건`, '이용조건 확인 전 저장소에 올리지 않음')}</div>
    <div class="def-panel">${table(['자료', '제공', '레이어·API', '기준연도', '좌표계', '분석 산출물'], rows.map(row => `<tr><th scope="row">${html(row.dataset_name)}</th><td>${valueCell(row.provider)}</td><td>${layerCell(row.layer_id)}</td><td>${valueCell(row.reference_year)}</td><td>${valueCell(row.crs === 'NOT_SPATIAL_TABLE' ? '표 자료' : row.crs)}</td><td><code>${html(String(row.processed_output).split('/').pop())}</code></td></tr>`))}
    <p class="def-muted">VWorld UQ164·UO601의 기준연도는 내려받은 파일명의 데이터 버전(202608)에서 읽었습니다. UQ151 도로는 파일 작성일만 확인되어 기준연도를 비워 두었습니다. 행정경계·농업지역은 기존 프로젝트 자료로 원 출처를 추가로 확인하고 있습니다.</p></div>` +
    source('표준 출처 목록 · 원본 목록에서 자동 생성', [['출처 목록 CSV', 'data/manifests/source_manifest.csv']]);
}

function renderCoordinates(block, summary) {
  const exact = summary.status_counts?.EXACT_PARCEL_MATCH || 0;
  const noResult = summary.status_counts?.NO_RESULT || 0;
  const shift = summary.shift_from_current_m || {};
  block.innerHTML = heading('I', '좌표 품질 보완 후보', '시군구 대표점·인근좌표·중복좌표로 기록된 못은 생활권 분석에서 제외했습니다. 이 못들의 지번주소를 통계청 SGIS 주소 지오코딩으로 다시 조회해 보완 후보를 만들었습니다.') + `
    <div class="def-stat-grid">${card('좌표 검토 대상', `${summary.record_count}개`, '분석 D·E에서 제외한 시설')}${card('지번 완전 일치', `${exact}개`, `리·본번·부번 일치 · 미조회 ${noResult}개`)}${card('현재 분석 반영', '0개', '현장·공식자료 확인 후 반영 예정')}</div>
    <div class="def-chart-layout"><div class="def-panel"><h4>후보 좌표와 기존 좌표의 거리</h4>
      ${table(['구분', '값'], [
        ['비교 가능한 후보', `${fmt(shift.count, 0)}개`],
        ['이동거리 중앙값', `${fmt(shift['50%'], 0)}m`],
        ['이동거리 범위', `${fmt(shift.min, 0)}–${fmt(shift.max, 0)}m`],
        ['주소의 읍·면과 다른 후보', `${(summary.emd_mismatch_ponds || []).length}개`],
        ['같은 지번을 공유하는 못', (summary.shared_candidate_ponds || []).join(', ') || '없음'],
      ].map(([label, value]) => `<tr><th scope="row">${html(label)}</th><td>${html(value)}</td></tr>`))}
    </div><aside class="def-panel def-reading"><h4>읽는 방법</h4>
      <p>기존 좌표가 군 대표점으로 기록된 시설은 실제 위치와 수 km 차이가 날 수 있습니다. 후보는 필지의 대표 좌표이므로 못 수면의 위치와 다를 수 있습니다.</p>
      <div class="analysis-insight"><strong>현재 결과에 반영하지 않은 이유</strong>후보를 반영하면 SGIS 생활권을 다시 조회해야 합니다. 공개 화면의 수치(380개·190개)는 검증을 마친 현재 좌표를 기준으로 유지합니다.</div>
      <button type="button" class="def-map-link" data-show-candidates>지도에서 후보 위치 보기 ↑</button>
    </aside></div>` +
    source('SGIS 주소 지오코딩 API · 검토용 후보', [['후보 요약 JSON', 'data/analysis/coordinate_geocode_candidates.json'], ['시설별 후보 CSV', 'data/analysis/coordinate_geocode_candidates.csv']]);
  block.querySelector('[data-show-candidates]')?.addEventListener('click', () => document.dispatchEvent(new CustomEvent('quality:show-candidates')));
}

function renderSensitivity(block, scenarios, worldpop, policyRows) {
  const s = scenarios.sensitivity || {};
  const labels = {access_emphasis: '접근성 강조', preservation_emphasis: '보전 강조', youth_activity_emphasis: '청년활동 강조'};
  const overlapKey = Object.keys(s).find(key => /^top\d+_overlap_with_base$/.test(key));
  const topK = overlapKey ? overlapKey.match(/\d+/)[0] : '';
  const stable = s.stable_candidates_frequency_ge_0_8 || [];
  const contexts = new Map(policyRows.map(row => [String(row.pond_id), row.policy_review_context]));
  const contextLabels = {COMMUNITY_SUPPORT_REVIEW: '공동체 지원 검토', YOUTH_PARTICIPATION_REVIEW: '청년참여 검토', ACCESS_AND_REACH_REVIEW: '접근·도달 검토', CONTEXT_ONLY: '맥락 참고'};
  const stableByContext = stable.reduce((acc, id) => { const key = contextLabels[contexts.get(String(id))] || '기타'; acc[key] = (acc[key] || 0) + 1; return acc; }, {});
  const spearmanValues = Object.values(s.spearman_vs_base || {});
  const wp = worldpop.summary || {};
  block.innerHTML = heading('J', '가정에 대한 민감도와 참고 인구', '지표의 가중치를 바꿔도 같은 시설이 반복해서 검토 대상으로 나타나는지 확인한 실험입니다. 확정 순위나 사업 대상 선정이 아닙니다.') + `
    <div class="def-stat-grid">${card('비교한 시설', `${scenarios.eligible_count}개`, `SGIS 10분 인구 확보 · 결측 대체 없음`)}${card('순위상관(기본 대비)', `${fmt(Math.min(...spearmanValues), 2)} 이상`, '3개 강조 시나리오 Spearman')}${card(`무작위 가중치 상위 ${topK}`, `${stable.length}개`, `${fmt(s.random_weight_draws, 0)}회 중 80% 이상 반복`)}</div>
    <div class="def-chart-layout"><div class="def-panel"><h4>시나리오별 비교 (기본: 5개 지표군 균등가중)</h4>
      ${table(['시나리오', '순위상관', `상위 ${topK} 겹침`], Object.entries(s.spearman_vs_base || {}).map(([key, value]) => `<tr><th scope="row">${html(labels[key] || key)}</th><td>${fmt(value, 3)}</td><td>${fmt(s[overlapKey]?.[key], 0)} / ${topK}</td></tr>`))}
      <p class="def-muted">지표군: 생활권 수요(SGIS 10분), 도로접근, 주변시설, 읍·면 청년비율, 자원(저수용량·농업비율). 백분위 정규화 · 무작위 가중치는 Dirichlet 분포, seed ${html(scenarios.random_seed)}. 정규화를 Min-Max로 바꿔도 순위상관 ${fmt(s.spearman_base_percentile_vs_minmax, 2)}.</p>
      <p class="def-muted">반복 상위 ${stable.length}개의 검토 맥락(분석 E): ${Object.entries(stableByContext).map(([key, value]) => `${html(key)} ${value}개`).join(' · ') || '없음'}</p>
    </div><aside class="def-panel def-reading"><h4>WorldPop 참고 인구 (2020)</h4>
      ${table(['반경', '중앙값', '0명인 못'], [['500m', wp['500m']], ['1km', wp['1km']]].map(([label, values]) => `<tr><th scope="row">${label}</th><td>${fmt(values?.median, 0)}명</td><td>${fmt(values?.zero_population_ponds, 0)}개</td></tr>`))}
      <div class="analysis-insight"><strong>공식 인구가 아닙니다</strong>WorldPop 100m 추정격자로 계산한 비교용 값입니다. 국내 공식 인구격자의 500m·1km 인구는 계속 미확보로 표시합니다.</div>
    </aside></div>` +
    source('정책 가정 실험 · 참고자료', [['민감도 JSON', 'data/analysis/policy_priority_scenarios.json'], ['WorldPop 참고 JSON', 'data/analysis/worldpop_reference_buffer.json']]);
}

export async function initQualityDashboard({loadJson, loadCsv}) {
  const blocks = ['quality-g', 'quality-h', 'quality-i', 'quality-j'].map(id => document.getElementById(id));
  const fail = (block, letter, error) => {
    if (!block) return;
    block.innerHTML = heading(letter, '자료를 확인할 수 없습니다', 'DATA_NOT_AVAILABLE · 저장된 점검 자료를 불러오지 못했습니다.');
    console.error(`분석 ${letter} 로드 실패`, error);
  };
  const [g, h, i, j] = blocks;
  await Promise.all([
    Promise.all([loadJson('data/analysis/data_quality_audit.json'), loadJson('data/analysis/validation_report.json')])
      .then(([audit, validation]) => g && renderQuality(g, audit, validation)).catch(error => fail(g, 'G', error)),
    loadCsv('data/manifests/source_manifest.csv').then(rows => h && renderSources(h, rows)).catch(error => fail(h, 'H', error)),
    loadJson('data/analysis/coordinate_geocode_candidates.json').then(summary => i && renderCoordinates(i, summary)).catch(error => fail(i, 'I', error)),
    Promise.all([loadJson('data/analysis/policy_priority_scenarios.json'), loadJson('data/analysis/worldpop_reference_buffer.json'), loadCsv('data/analysis/sgis_policy_evidence.csv')])
      .then(([scenarios, worldpop, policies]) => j && renderSensitivity(j, scenarios, worldpop, policies)).catch(error => fail(j, 'J', error)),
  ]);
}
