// Analysis D/E/F: saved-data views. No API collection or policy scores.
export const POLICY = {
  FIELD_REVIEW_REQUIRED: {label: '현장 확인 필요', color: '#dc2626', rule: '대표점·인근좌표·중복좌표 등 좌표 품질 조건을 통과하지 못했습니다.', next: '공식 좌표나 현장 위치를 확인한 뒤 생활권을 다시 조회합니다.'},
  INSUFFICIENT_SGIS_10MIN: {label: 'SGIS 10분 인구 미확보', color: '#9ca3af', rule: '좌표 조건은 통과했으나 10분 생활권 인구가 제공되지 않았습니다.', next: '위치 인식과 통계 응답을 재확인합니다. 미확보를 0명이나 낮은 수요로 해석하지 않습니다.'},
  COMMUNITY_SUPPORT_REVIEW: {label: '공동체 지원 검토', color: '#d97706', rule: '읍·면 고령비율 상위 맥락이고, 확보한 VWorld 레이어의 1km 내 시설 수가 0개입니다.', next: '실제 주민 이용 수요, 누락된 시설, 운영·관리상태를 확인합니다.'},
  YOUTH_PARTICIPATION_REVIEW: {label: '청년참여 검토', color: '#059669', rule: '고령비율 상위 맥락에 해당하지 않고, 읍·면 청년비율이 상위이며 10분 인구 응답이 있습니다.', next: '청년 참여 의향과 기록·교육 활동 여건을 확인합니다. 청년 방문 수요가 입증된 것은 아닙니다.'},
  ACCESS_AND_REACH_REVIEW: {label: '접근·도달 검토', color: '#2563eb', rule: '앞선 검토 그룹에 속하지 않으며, 10분 인구 또는 5→10분 증가폭이 상위 사분위에 해당합니다.', next: '실제 진입로·이동 여건과 시설 이용 가능성을 확인합니다.'},
  CONTEXT_ONLY: {label: '맥락 참고', color: '#7c3aed', rule: '10분 인구 응답은 있으나 앞선 정책 검토 조건에 해당하지 않습니다.', next: '기존 지역·공간 맥락을 참고하고 시설 상태와 활용 근거를 추가 확인합니다.'},
};

const html = (value) => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
export function number(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
const fmt = value => number(value) === null ? '미확보' : number(value).toLocaleString('ko-KR', {maximumFractionDigits: 1});
const pct = (count, total) => total ? `${fmt(count / total * 100)}%` : '미확보';
const bool = value => value === true || String(value).toLowerCase() === 'true';

export function parseCsv(text) {
  const records = [];
  let record = [], cell = '', quoted = false;
  const source = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    if (char === '"') {
      if (quoted && source[i + 1] === '"') { cell += '"'; i += 1; }
      else quoted = !quoted;
    } else if (char === ',' && !quoted) { record.push(cell); cell = ''; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && source[i + 1] === '\n') i += 1;
      record.push(cell);
      if (record.some(value => value !== '')) records.push(record);
      record = []; cell = '';
    } else cell += char;
  }
  if (quoted) throw new Error('CSV 따옴표가 닫히지 않았습니다.');
  if (cell !== '' || record.length) { record.push(cell); records.push(record); }
  const headers = records.shift() || [];
  return records.map(values => {
    if (values.length !== headers.length) throw new Error('CSV 열 수가 일치하지 않습니다.');
    return Object.fromEntries(headers.map((header, i) => [header, values[i]]));
  });
}

function uniqueIds(rows) {
  const ids = rows.map(row => String(row.pond_id));
  if (new Set(ids).size !== rows.length) throw new Error('중복 시설 ID가 있습니다.');
}

export function sgisModel(rows, summary, policyRows) {
  uniqueIds(rows);
  const seen = new Set();
  const eligible = rows.filter(row => {
    if (!bool(row.sgis_analysis_eligible) || seen.has(row.coordinate_group_id)) return false;
    seen.add(row.coordinate_group_id); return true;
  });
  const policies = new Map(policyRows.map(row => [String(row.pond_id), row]));
  const paired = eligible.filter(row => number(row.sgis_population_5min) !== null && number(row.sgis_population_10min) !== null)
    .map(row => ({...row, p5: number(row.sgis_population_5min), p10: number(row.sgis_population_10min),
      flags: policies.get(String(row.pond_id))?.policy_evidence_flags || ''}));
  if (paired.length !== summary.coverage.available_both || rows.length !== summary.facility_count) {
    throw new Error('SGIS 요약과 시설별 표본 수가 다릅니다.');
  }
  return {rows, eligible, paired, summary};
}

export function policyModel(rows) {
  uniqueIds(rows);
  if (rows.some(row => !POLICY[row.policy_review_context])) throw new Error('정의되지 않은 정책 검토 맥락입니다.');
  return Object.entries(POLICY).map(([code, config]) => ({...config, code,
    rows: rows.filter(row => row.policy_review_context === code)}));
}

export function roadModel(rows) {
  uniqueIds(rows);
  const bins = [
    {label: '100m 이하', max: 100}, {label: '100m 초과–300m 이하', max: 300},
    {label: '300m 초과–500m 이하', max: 500}, {label: '500m 초과', max: Infinity},
  ].map(bin => ({...bin, rows: []}));
  let missing = 0;
  rows.forEach(row => {
    const distance = number(row.distance_to_road_m ?? row.nearest_road_m);
    if (distance === null || distance < 0) { missing += 1; return; }
    bins.find(bin => distance <= bin.max).rows.push(row);
  });
  return {bins, missing, total: rows.length};
}

const card = (label, value, note) => `<div class="def-stat"><span>${html(label)}</span><strong>${html(value)}</strong><small>${html(note)}</small></div>`;
const source = (text, path) => `<p class="def-source">${html(text)} · <a href="${path}" target="_blank" rel="noopener">분석 자료 보기 ↗</a></p>`;
function blockFor(id, letter) {
  const block = document.getElementById(id)?.closest('.analysis-block');
  if (block) { block.classList.add('analysis-def-block'); block.id = `analysis-${letter}`; }
  return block;
}
const heading = (letter, title, note) => `<div class="def-heading"><span class="def-letter">${letter.toUpperCase()}</span><div><h3>분석 ${letter.toUpperCase()}. ${title}</h3><p class="analysis-note">${note}</p></div></div>`;
const table = (headers, rows) => `<div class="def-table-wrap"><table class="def-table"><thead><tr>${headers.map(t => `<th scope="col">${html(t)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;

function renderD(block, model, evidence, onSgisSelect, onFacilitySelect) {
  const {summary, paired, eligible} = model;
  const coverage = summary.coverage;
  const flags = evidence.evidence_flag_counts;
  const overlap = paired.filter(row => row.flags.includes('HIGH_10MIN_REACH') && row.flags.includes('HIGH_5_TO_10_EXPANSION')).length;
  const filters = [
    {code: 'all', label: '전체 비교', count: paired.length, test: () => true},
    {code: 'reach', label: '10분 인구 상위', count: flags.HIGH_10MIN_REACH, test: row => row.flags.includes('HIGH_10MIN_REACH')},
    {code: 'gain', label: '증가폭 상위', count: flags.HIGH_5_TO_10_EXPANSION, test: row => row.flags.includes('HIGH_5_TO_10_EXPANSION')},
    {code: 'both', label: '두 조건 동시 충족', count: overlap, test: row => row.flags.includes('HIGH_10MIN_REACH') && row.flags.includes('HIGH_5_TO_10_EXPANSION')},
  ];
  filters.forEach(filter => { filter.count = paired.filter(filter.test).length; });
  block.innerHTML = heading('d', 'SGIS 생활권역 인구 비교', '못의 위치에서 5분·10분 주행생활권으로 범위를 넓히면 인구 규모가 어떻게 달라질까요? 저장된 SGIS 응답을 비교합니다.') + `
    <div class="def-stat-grid">${card('좌표 조건 통과', `${eligible.length}개`, `전체 ${model.rows.length}개 중 ${model.rows.length - eligible.length}개 제외`)}${card('10분 인구 확보', `${coverage.available_10min}개`, `${summary.year}년 기준 요청`)}${card('5분·10분 비교', `${paired.length}개`, '두 시간대 모두 인구값 확보')}</div>
    <div class="def-workflow"><span>시설 ID 연결</span><b>→</b><span>좌표 품질 제외</span><b>→</b><span>시간대별 응답 확인</span><b>→</b><span>인구 규모·증가폭 비교</span></div>
    <div class="def-chart-layout"><div class="def-panel">
      <div class="def-panel-title"><h4>[그림 D-1. 5분·10분 주행생활권 인구 비교]</h4><span>단위: 명</span></div>
      <div class="def-controls" role="group" aria-label="SGIS 비교 대상">${filters.map(filter => `<button type="button" data-sgis-filter="${filter.code}" aria-pressed="${filter.code === 'all'}">${filter.label}<strong>${filter.count}</strong></button>`).join('')}</div>
      <p class="def-chart-status" id="def-sgis-count" aria-live="polite"></p><div id="sgis-scatter-plot"></div>
      <p class="def-muted">두 축은 log10(인구+1) 척도이며 눈금은 실제 인구입니다. 조건을 누르면 지도도 필터링됩니다. 점 선택 후 ‘지도에서 보기’를 누르면 해당 못을 확인할 수 있습니다.</p>
      <p class="def-muted">최대값 ID 474: 5분 2,298명·10분 3,877명. 저장 응답과 일치하고 단일 좌표이므로 유지했습니다. 대표·인근·중복좌표 47개는 비교에서 제외했습니다.</p>
      <div class="def-selected" id="def-point-detail" aria-live="polite">점 하나를 선택해 5분·10분 인구와 증가폭을 확인하세요.</div>
    </div><aside class="def-panel def-reading"><h4>비교 기준과 읽는 방법</h4>
      ${table(['지표', '중앙값', '표본'], [
        ['5분 인구', summary.distributions.sgis_population_5min, '명'],
        ['10분 인구', summary.distributions.sgis_population_10min, '명'],
        ['5→10분 증가폭', summary.distributions.sgis_population_gain_5_to_10, '명'],
      ].map(([label, values, unit]) => `<tr><th scope="row">${label}</th><td>${fmt(values.median)}${unit}</td><td>${values.count}개</td></tr>`))}
      <p><strong>10분 인구 상위 기준</strong><br>${fmt(evidence.thresholds_q25_q75.sgis_population_10min.q75)}명 이상 · 인구 확보 ${coverage.available_10min}개 기준</p>
      <p><strong>증가폭 상위 기준</strong><br>${fmt(evidence.thresholds_q25_q75.sgis_population_gain_5_to_10.q75)}명 이상 · 양쪽 확보 ${paired.length}개 기준</p>
      <div class="analysis-insight"><strong>이 결과로 말할 수 있는 것</strong>같은 이동시간 조건에서 생활권 인구를 비교할 수 있습니다. 상위 조건은 확정 사업대상이나 실제 방문 수요를 뜻하지 않습니다.</div>
      <p class="def-muted">버튼 수치는 그래프에서 비교 가능한 표본 수입니다. 미확보값은 0명으로 바꾸지 않으며 시설별 생활권 인구를 합산하지 않습니다. [표 D-1. 생활권 인구 요약]</p>
    </aside></div>` + source(`SGIS 생활권역 · ${summary.year}년 인구 · 저장된 응답`, 'data/analysis/sgis_catchment_analysis.json');
  let selected = 'all';
  const draw = () => {
    const filter = filters.find(item => item.code === selected);
    const points = paired.filter(filter.test);
    block.querySelectorAll('[data-sgis-filter]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.sgisFilter === selected)));
    block.querySelector('#def-sgis-count').textContent = `${filter.label}: 비교 가능한 ${points.length}개 표시 / 전체 비교 ${paired.length}개`;
    const width = 680, height = 400, left = 64, top = 22, bottom = 345, right = 650;
    const max = Math.max(1, ...paired.map(row => Math.max(row.p5, row.p10)));
    const domain = 10 ** Math.ceil(Math.log10(max + 1));
    const scale = value => Math.log10(value + 1) / Math.log10(domain + 1);
    const x = value => left + scale(value) * (right - left);
    const y = value => bottom - scale(value) * (bottom - top);
    const ticks = [0, 10, 100, 1000, 10000, 100000].filter(value => value <= domain);
    const guides = ticks.map(value => `<line x1="${x(value)}" x2="${x(value)}" y1="${top}" y2="${bottom}" class="def-grid"/><line x1="${left}" x2="${right}" y1="${y(value)}" y2="${y(value)}" class="def-grid"/><text x="${x(value)}" y="${bottom + 22}" text-anchor="middle">${fmt(value)}</text><text x="${left - 10}" y="${y(value) + 4}" text-anchor="end">${fmt(value)}</text>`).join('');
    block.querySelector('#sgis-scatter-plot').innerHTML = `<svg class="def-scatter" viewBox="0 0 ${width} ${height}" aria-label="SGIS 인구 산점도 ${points.length}개">
      ${guides}<line x1="${x(0)}" x2="${x(domain)}" y1="${y(0)}" y2="${y(domain)}" class="def-diagonal"/>
      ${points.map(row => `<circle cx="${x(row.p5)}" cy="${y(row.p10)}" r="5" class="def-point" tabindex="0" role="button" data-pond-point="${html(row.pond_id)}" aria-label="못 ${html(row.pond_id)}, 5분 ${fmt(row.p5)}명, 10분 ${fmt(row.p10)}명"><title>못 ${html(row.pond_id)} · ${html(row.address)} · 5분 ${fmt(row.p5)}명 / 10분 ${fmt(row.p10)}명</title></circle>`).join('')}
      <text x="${(left + right) / 2}" y="390" text-anchor="middle">5분 생활권 인구 (명)</text><text transform="translate(17 180) rotate(-90)" text-anchor="middle">10분 생활권 인구 (명)</text></svg>`;
    block.querySelector('#def-point-detail').textContent = '점 하나를 선택해 5분·10분 인구와 증가폭을 확인하세요.';
  };
  const selectPoint = target => {
    const row = paired.find(item => String(item.pond_id) === target.dataset.pondPoint);
    if (!row) return;
    block.querySelectorAll('.def-point').forEach(point => point.classList.toggle('is-selected', point === target));
    block.querySelector('#def-point-detail').innerHTML = `<strong>못 ${html(row.pond_id)} · ${html(row.address)}</strong><span>5분 ${fmt(row.p5)}명 → 10분 ${fmt(row.p10)}명 · 증가 ${fmt(row.p10 - row.p5)}명</span><button type="button" class="def-map-link" data-locate-pond="${html(row.pond_id)}">지도에서 이 못 보기 ↑</button>`;
  };
  block.addEventListener('click', event => {
    const filter = event.target.closest('[data-sgis-filter]');
    if (filter) { selected = filter.dataset.sgisFilter; draw(); onSgisSelect(selected === 'all' ? null : paired.filter(filters.find(item => item.code === selected).test).map(row => row.pond_id), selected); }
    const point = event.target.closest('[data-pond-point]');
    if (point) selectPoint(point);
    const locate = event.target.closest('[data-locate-pond]');
    if (locate) onFacilitySelect(locate.dataset.locatePond);
  });
  document.addEventListener('sgis:reset', () => { selected = 'all'; draw(); });
  document.addEventListener('sgis:map-sgis-filter', event => { selected = filters.some(item => item.code === event.detail) ? event.detail : 'all'; draw(); });
  block.addEventListener('keydown', event => {
    if (event.target.matches('[data-pond-point]') && ['Enter', ' '].includes(event.key)) { event.preventDefault(); selectPoint(event.target); }
  });
  draw();
}

function renderE(block, rows, onPolicySelect) {
  const groups = policyModel(rows);
  const total = rows.length;
  block.innerHTML = heading('e', '정책 검토 맥락을 시설별로 확인', '좌표 품질과 인구 응답을 먼저 확인하고, 지역의 연령구조·주변시설·생활권 인구를 순서대로 검토합니다. 각 시설은 하나의 그룹에 속합니다.') + `
    <div class="def-policy-layout"><div class="def-panel"><div class="def-panel-title"><h4>전체 ${total}개의 검토 맥락</h4><span>범례를 눌러 상세 확인</span></div>
      <div class="def-policy-overview"><div id="policy-donut-chart"></div><div class="def-policy-legend" role="group" aria-label="정책 검토 맥락 선택"><button type="button" data-policy-code="all" aria-pressed="true">전체 보기<strong>${total}개</strong></button>
      ${groups.map(group => `<button type="button" data-policy-code="${group.code}" aria-pressed="false" style="--context-color:${group.color}"><i></i><span>${html(group.label)}</span><strong>${group.rows.length}개</strong><small>${pct(group.rows.length, total)}</small></button>`).join('')}</div></div>
      <p class="def-muted">선택 상태는 위 지도에 있는 정책 필터와 동기화됩니다. 다른 지도 필터를 사용 중이면 결과는 교집합으로 표시됩니다.</p>
    </div><div class="def-panel" id="def-policy-detail" aria-live="polite"></div></div>
    <details class="def-method-detail"><summary>어떤 순서와 근거로 분류했나요?</summary><ol class="def-rule-list">${groups.map(group => `<li><strong>${html(group.label)} · ${group.rows.length}개</strong><p>${html(group.rule)}</p></li>`).join('')}</ol><p class="def-muted">청년·고령 비율의 상위 기준은 좌표 조건을 통과한 시설에 연결된 읍·면 비율의 제3사분위수입니다. 이전 조건을 먼저 적용하며, 분류는 사업 우선순위 점수가 아닙니다.</p></details>
    ` + source('SGIS 정책 근거표 · 모든 그룹은 현장 확인 전 검토 맥락', 'data/analysis/sgis_policy_evidence.csv');
  let active = 'all';
  const draw = () => {
    const group = groups.find(item => item.code === active);
    const selectedRows = group?.rows || rows;
    block.querySelectorAll('[data-policy-code]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.policyCode === active)));
    let offset = 0;
    const segments = groups.map(item => {
      const share = item.rows.length / total * 100;
      const segment = `<circle cx="100" cy="100" r="70" pathLength="100" fill="none" stroke="${item.color}" stroke-width="26" stroke-dasharray="${share} ${100 - share}" stroke-dashoffset="${-offset}" transform="rotate(-90 100 100)" opacity="${active === 'all' || active === item.code ? 1 : .16}"/>`;
      offset += share; return segment;
    }).join('');
    block.querySelector('#policy-donut-chart').innerHTML = `<svg viewBox="0 0 200 200" role="img" aria-label="${html(group?.label || '전체')} ${selectedRows.length}개" class="def-donut">${segments}<text x="100" y="100" text-anchor="middle" class="def-donut-total">${selectedRows.length}</text><text x="100" y="121" text-anchor="middle">${active === 'all' ? '전체 못' : '선택한 못'}</text></svg>`;
    block.querySelector('#def-policy-detail').innerHTML = `<span class="def-eyebrow">${group ? 'SELECTED CONTEXT' : 'READING GUIDE'}</span><h4>${html(group?.label || '검토 근거에서 현장 확인으로')}</h4>
      <p class="def-detail-count">${selectedRows.length}<small>개 · 전체의 ${pct(selectedRows.length, total)}</small></p>
      <p>${html(group?.rule || '왼쪽 범례에서 하나를 선택하면 해당 그룹의 판정 근거와 실제 시설 목록을 확인할 수 있습니다.')}</p>
      <div class="analysis-insight"><strong>다음에 확인할 사항</strong>${html(group?.next || '인구 통계와 공간조건으로 현장 검토 질문을 정리합니다. 시설의 관리상태·보존가치·실제 수요가 확인되기 전에는 정책 후보를 확정하지 않습니다.')}</div>
      ${group ? table(['시설 ID', '읍·면', '10분 인구'], selectedRows.slice(0, 5).map(row => `<tr><td>${html(row.pond_id)}</td><td>${html(row.emd_name)}</td><td>${fmt(row.sgis_population_10min)}${number(row.sgis_population_10min) === null ? '' : '명'}</td></tr>`)) + `<p class="def-muted">원자료 순서의 앞 ${Math.min(5, selectedRows.length)}개 예시 · 우선순위가 아닙니다.</p><button class="def-map-link" type="button" data-show-map>지도에서 선택 결과 보기 ↑</button>` : '<p class="def-muted">SGIS 미확보와 좌표 품질 제외는 별도로 관리합니다. 일부 레이어에 시설이 없다는 이유만으로 실제 서비스 부족을 단정하지 않습니다.</p>'}`;
  };
  block.addEventListener('click', event => {
    const button = event.target.closest('[data-policy-code]');
    if (button) { active = active === button.dataset.policyCode ? 'all' : button.dataset.policyCode; draw(); onPolicySelect(active); }
    if (event.target.closest('[data-show-map]')) document.getElementById('map')?.scrollIntoView({behavior: 'smooth', block: 'center'});
  });
  document.addEventListener('sgis:policy-filter', event => { active = POLICY[event.detail] ? event.detail : 'all'; draw(); });
  draw();
}

function renderF(block, roads, population, onRegionSelect, onRoadSelect) {
  const model = roadModel(roads);
  const emds = population.data;
  if (!Array.isArray(emds) || !emds.length) throw new Error('읍·면 인구자료가 없습니다.');
  const total = emds.reduce((sum, row) => sum + (number(row.total_population) ?? 0), 0);
  const near = model.bins[0].rows.length + model.bins[1].rows.length;
  block.innerHTML = heading('f', '도로거리와 읍·면 인구구조', '도로에 가까운 정도와 지역의 연령구조를 함께 살펴봅니다. UQ151 도로 객체까지의 직선거리이며 네트워크 이동거리나 SGIS 주행시간과는 다릅니다.') + `
    <div class="def-stat-grid">${card('도로 300m 이내', `${near}개`, `${pct(near, model.total)} · 전체 ${model.total}개`)}${card('도로 500m 초과', `${model.bins[3].rows.length}개`, '진입로·현장 이동 여건 추가 확인')}${card(`${population.year.join('·')}년 주민등록인구`, `${fmt(total)}명`, `${emds.length}개 읍·면 · 행정안전부`)}</div>
    <div class="def-road-layout"><div class="def-panel"><h4>최근접 도로거리 구간</h4><div id="road-distance-chart"></div><div id="def-road-detail" class="def-selected" aria-live="polite">거리 구간을 눌러 해당 시설 ID를 확인하세요.</div><p class="def-muted">거리 계산: EPSG:5174 · 단위 m · 거리 미확보 ${model.missing}개. 도로 원자료 기준시점은 추가 확인이 필요합니다.</p><div class="analysis-insight"><strong>해석의 범위</strong>도로와 가깝더라도 실제 진입로·통행 가능 여부를 확인해야 합니다. 도로거리만으로 접근 여건의 우수성을 확정하지 않습니다.</div></div>
    <div class="def-panel"><div class="def-panel-title"><h4>읍·면별 연령 비율</h4><label class="def-sort-label">정렬 <select id="def-population-sort"><option value="youth">청년 비율순</option><option value="elderly">고령 비율순</option><option value="name">읍·면 이름순</option></select></label></div>
      <p class="def-muted"><i class="def-key def-key-elderly"></i>고령 만 65세 이상 <i class="def-key def-key-youth"></i>청년 만 19~39세 · 양쪽 동일한 0–100% 척도</p><div id="bilateral-population-chart"></div><div class="def-selected" id="def-emd-detail" aria-live="polite">읍·면을 선택하면 인구와 비율을 확인하고 지도 읍·면 필터를 적용합니다.</div>
      <p class="def-muted">읍·면 집계는 지역 배경지표입니다. 못 주변의 청년·고령 인구나 시설 이용수요를 뜻하지 않습니다.</p></div></div>` + source(`VWorld UQ151 최근접거리 · 행정안전부 ${population.year.join('·')}년 인구`, 'data/analysis/population_summary.json');
  const maxCount = Math.max(1, ...model.bins.map(bin => bin.rows.length));
  block.querySelector('#road-distance-chart').innerHTML = model.bins.map((bin, index) => `<button type="button" class="def-road-row" data-road-bin="${index}" aria-pressed="false"><span>${bin.label}</span><strong>${bin.rows.length}개 <small>${pct(bin.rows.length, model.total)}</small></strong><i><b style="width:${bin.rows.length / maxCount * 100}%"></b></i></button>`).join('');
  let sort = 'youth', selectedEmd = '', selectedRoad = null;
  const describeEmd = () => {
    const row = emds.find(item => item.emd_name === selectedEmd);
    block.querySelector('#def-emd-detail').innerHTML = row ? `<strong>${html(row.emd_name)} · ${fmt(row.total_population)}명</strong><span>고령 ${fmt(row.elderly_population)}명 (${fmt(row.elderly_ratio)}%) · 청년 ${fmt(row.youth_population)}명 (${fmt(row.youth_ratio)}%)</span>` : '읍·면 전체 선택으로 돌아왔습니다.';
  };
  const draw = () => {
    const sorted = [...emds].sort((a, b) => sort === 'name' ? a.emd_name.localeCompare(b.emd_name, 'ko') : b[`${sort}_ratio`] - a[`${sort}_ratio`]);
    block.querySelector('#bilateral-population-chart').innerHTML = `<div class="def-pop-axis"><span>100% ← 고령</span><span>읍·면</span><span>청년 → 100%</span></div>` + sorted.map(row => `<button type="button" class="def-pop-row" data-emd="${html(row.emd_name)}" aria-pressed="${selectedEmd === row.emd_name}" aria-label="${html(row.emd_name)}, 고령 ${fmt(row.elderly_ratio)}%, 청년 ${fmt(row.youth_ratio)}%"><span class="def-pop-side def-pop-left"><small>${fmt(row.elderly_ratio)}%</small><i><b style="width:${row.elderly_ratio}%"></b></i></span><strong>${html(row.emd_name)}</strong><span class="def-pop-side def-pop-right"><i><b style="width:${row.youth_ratio}%"></b></i><small>${fmt(row.youth_ratio)}%</small></span></button>`).join('');
  };
  block.querySelector('#def-population-sort').addEventListener('change', event => {sort = event.target.value; draw();});
  block.addEventListener('click', event => {
    const roadButton = event.target.closest('[data-road-bin]');
    if (roadButton) {
      const index = Number(roadButton.dataset.roadBin);
      selectedRoad = selectedRoad === index ? null : index;
      const bin = selectedRoad === null ? null : model.bins[selectedRoad];
      block.querySelectorAll('[data-road-bin]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.roadBin) === selectedRoad)));
      block.querySelector('#def-road-detail').innerHTML = bin ? `<strong>${bin.label} · ${bin.rows.length}개</strong><span>지도에 같은 거리 조건을 적용했습니다. 다시 누르면 해제됩니다.</span><span>시설 ID 예시: ${bin.rows.slice(0, 8).map(row => html(row.pond_id)).join(', ') || '해당 시설 없음'}</span>` : '도로거리 조건을 해제했습니다.';
      onRoadSelect(bin ? bin.rows.map(row => row.pond_id) : null, bin ? String(selectedRoad) : 'all');
    }
    const emdButton = event.target.closest('[data-emd]');
    if (emdButton) {
      selectedEmd = selectedEmd === emdButton.dataset.emd ? '' : emdButton.dataset.emd;
      draw(); onRegionSelect(selectedEmd || 'all');
      describeEmd();
      [...block.querySelectorAll('[data-emd]')].find(button => button.dataset.emd === emdButton.dataset.emd)?.focus();
    }
  });
  document.addEventListener('sgis:reset', () => {
    selectedRoad = null; selectedEmd = '';
    block.querySelectorAll('[data-road-bin]').forEach(button => button.setAttribute('aria-pressed', 'false'));
    block.querySelector('#def-road-detail').textContent = '도로거리 조건을 해제했습니다.';
    draw(); describeEmd();
  });
  document.addEventListener('sgis:region-filter', event => {
    const region = event.detail === 'all' ? '' : event.detail;
    if (region === selectedEmd) return;
    selectedEmd = region; draw(); describeEmd();
  });
  document.addEventListener('sgis:map-road-filter', event => {
    selectedRoad = event.detail === 'all' ? null : Number(event.detail);
    block.querySelectorAll('[data-road-bin]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.roadBin) === selectedRoad)));
    const bin = selectedRoad === null ? null : model.bins[selectedRoad];
    block.querySelector('#def-road-detail').innerHTML = bin ? `<strong>${bin.label} · ${bin.rows.length}개</strong><span>지도에서 선택한 거리 조건입니다.</span>` : '도로거리 조건을 해제했습니다.';
  });
  draw();
}

export async function initDefDashboard({loadJson, loadCsv, onPolicySelect, onRegionSelect, onSgisSelect = () => {}, onRoadSelect = () => {}, onFacilitySelect = () => {}}) {
  const d = blockFor('sgis-scatter-plot', 'd');
  const e = blockFor('policy-donut-chart', 'e');
  const f = blockFor('road-distance-chart', 'f');
  for (const [block, letter] of [[d, 'd'], [e, 'e'], [f, 'f']]) {
    if (block) block.innerHTML = heading(letter, '분석 자료를 불러오는 중', '저장된 분석 결과를 확인하고 있습니다.');
  }
  const policyPromise = loadCsv('data/analysis/sgis_policy_evidence.csv');
  const unavailable = (block, letter, error) => {
    if (!block) return;
    block.innerHTML = heading(letter, '분석 자료를 확인할 수 없습니다', 'DATA_NOT_AVAILABLE · 저장된 분석 자료를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.');
    const button = document.createElement('button'); button.type = 'button'; button.className = 'def-map-link'; button.textContent = '다시 불러오기';
    button.addEventListener('click', () => location.reload()); block.appendChild(button);
    console.error(`분석 ${letter.toUpperCase()} 로드 실패`, error);
  };
  await Promise.all([
    Promise.all([loadCsv('data/analysis/sgis_catchment_analysis.csv'), loadJson('data/analysis/sgis_catchment_analysis.json'), policyPromise, loadJson('data/analysis/sgis_policy_evidence.json')])
      .then(([rows, summary, policies, evidence]) => {if (d) renderD(d, sgisModel(rows, summary, policies), evidence, onSgisSelect, onFacilitySelect);}).catch(error => unavailable(d, 'd', error)),
    policyPromise.then(rows => {if (e) renderE(e, rows, onPolicySelect);}).catch(error => unavailable(e, 'e', error)),
    Promise.all([loadCsv('data/analysis/pond_accessibility.csv'), loadJson('data/analysis/population_summary.json')])
      .then(([roads, population]) => {if (f) renderF(f, roads, population, onRegionSelect, onRoadSelect);}).catch(error => unavailable(f, 'f', error)),
  ]);
}
