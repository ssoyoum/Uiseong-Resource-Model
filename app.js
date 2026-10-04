/**
 * 의성군 중심 Web GIS
 *
 * 현재 단계의 목표는 단순하다.
 * 1) 의성군 행정경계를 읽는다.
 * 2) 경계의 실제 bounds로 지도를 맞춘다.
 * 3) 의성군 안의 못 위치를 표시하고 Popup을 연다.
 *
 * 농업진흥지역과 읍면별 총용량 레이어는 분석 결과를 확인할 때
 * 레이어 컨트롤에서 ON/OFF할 수 있다.
 */

document.addEventListener('DOMContentLoaded', () => {
  // L.map(): id가 "map"인 HTML 요소를 Leaflet 지도 객체로 만든다.
  // 중심 좌표를 임의로 넣지 않는다. 경계를 읽은 뒤 fitBounds()로 위치를 정한다.
  const map = L.map('map', {
    minZoom: 9,
    maxZoom: 15,
    zoomControl: true,
  });

  // L.tileLayer(): 배경 타일(도로·지명 등)을 지도에 추가한다.
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  // 레이어를 따로 관리하면 나중에 ON/OFF와 필터를 단순하게 만들 수 있다.
  const boundaryLayer = L.geoJSON(null, {
    style: {
      color: '#176b4d',
      weight: 2.5,
      opacity: 0.95,
      fillColor: '#8bc9a8',
      fillOpacity: 0.12,
    },
  }).addTo(map);

  const pondLayer = L.layerGroup().addTo(map);
  const agricultureLayer = L.geoJSON(null, {
    style: {
      color: '#c77d1a',
      weight: 0.6,
      opacity: 0.65,
      fillColor: '#f2c66d',
      fillOpacity: 0.28,
    },
    onEachFeature: (feature, layer) => {
      const area = Number(feature.properties?.area_ha || 0);
      layer.bindPopup(`농경지·농업진흥지역<br>면적: ${formatNumber(area)} ha`);
    },
  }).addTo(map);
  const regionLayer = L.geoJSON(null, {
    style: (feature) => {
      const density = Number(feature.properties?.facilities_per_km2 || 0);
      const fillOpacity = density > 0 ? Math.min(0.65, 0.12 + density / 2) : 0.04;
      return {
        color: '#6d8272',
        weight: 1,
        fillColor: '#4c956c',
        fillOpacity,
      };
    },
    onEachFeature: (feature, layer) => {
      const properties = feature.properties || {};
      layer.bindPopup(
        `${properties.spatial_region || '읍면'}<br>` +
        `시설: ${formatNumber(properties.facility_count)}개<br>` +
        `면적: ${formatNumber(properties.area_km2)}km²<br>` +
        `면적당 시설: ${formatNumber(properties.facilities_per_km2)}개/km²`
      );
    },
  });
  // 분석 I의 좌표 보완 후보. 분석 결과에는 반영하지 않은 검토용 레이어라 기본은 꺼 둔다.
  const coordinateCandidateLayer = L.layerGroup();
  const coordinateCandidates = new Map();
  let allPondFeatures = [];
  let policyEvidenceMap = {};
  let activePolicyFilter = 'all';
  let activeRegionFilter = 'all';
  let activeCapacityFilter = 'all';
  let activeClassificationFilter = 'all';
  let activeSearch = '';
  let activeSgisMapFilter = 'all';
  let activeRoadMapFilter = 'all';
  let policyConfig = {};
  let mapReady = false;
  const selectedIds = { sgis: null, road: null };
  const dashboardModule = import('./def-dashboard.mjs?v=20261001-d-hover');
  const markerById = new Map();
  const pondId = feature => String(feature.properties?.pond_id || feature.properties?.id || '');
  const sgisMapLabels = {
    all: 'D 전체 시설',
    reach: 'D 10분 인구 상위',
    gain: 'D 증가폭 상위',
    both: 'D 두 조건 동시 충족',
  };
  const roadMapLabels = {
    all: 'F 전체 거리',
    0: 'F 100m 이하',
    1: 'F 100m 초과–300m 이하',
    2: 'F 300m 초과–500m 이하',
    3: 'F 500m 초과',
  };

  // Leaflet의 레이어 컨트롤은 내부적으로 addLayer()/removeLayer()를 사용한다.
  // 체크하면 레이어를 지도에 추가하고, 해제하면 지도에서 제거한다.
  L.control.layers(
    null,
    {
      '의성군 행정경계': boundaryLayer,
      '못 위치': pondLayer,
      '농경지·농업진흥지역': agricultureLayer,
      '읍면별 시설 밀도': regionLayer,
      'I. 좌표 보완 후보(미반영)': coordinateCandidateLayer,
    },
    { collapsed: false }
  ).addTo(map);

  async function loadCoordinateCandidates() {
    const rows = await loadCsv('data/analysis/coordinate_geocode_candidates.csv');
    const current = new Map(allPondFeatures.map((feature) => [pondId(feature), feature.geometry?.coordinates]));
    rows.filter((row) => row.geocode_status === 'EXACT_PARCEL_MATCH').forEach((row) => {
      const lat = Number(row.candidate_lat_wgs84);
      const lng = Number(row.candidate_lng_wgs84);
      const from = current.get(String(row.pond_id));
      if (!Number.isFinite(lat) || !Number.isFinite(lng) || !from) return;
      coordinateCandidates.set(String(row.pond_id), row);
      const popup = `<strong>못 ${escapeHtml(row.pond_id)} · 좌표 보완 후보</strong><br>${escapeHtml(row.address)}<br>` +
        `SGIS 지번 일치: ${escapeHtml(row.returned_lot)}<br>현재 좌표와 ${formatNumber(Math.round(Number(row.shift_from_current_m)))}m 차이<br>` +
        '<small>분석 D·E에는 반영하지 않은 검토용 후보</small>';
      L.polyline([[from[1], from[0]], [lat, lng]], { color: '#8a5a00', weight: 1.4, dashArray: '4 4', opacity: 0.75 }).addTo(coordinateCandidateLayer);
      L.circleMarker([lat, lng], { radius: 5, color: '#8a5a00', weight: 2, fillColor: '#fdf1d8', fillOpacity: 1 }).bindPopup(popup).addTo(coordinateCandidateLayer);
    });
  }

  document.addEventListener('quality:show-candidates', () => {
    if (!map.hasLayer(coordinateCandidateLayer)) coordinateCandidateLayer.addTo(map);
    const bounds = L.featureGroup(coordinateCandidateLayer.getLayers()).getBounds();
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [30, 30] });
    document.getElementById('map')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });

  function escapeHtml(value) {
    return String(value ?? '-').replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;',
    }[character]));
  }

  function formatNumber(value) {
    return Number(value).toLocaleString('ko-KR', {
      maximumFractionDigits: 1,
    });
  }

  function enableFastTooltips(container) {
    if (!container) return;
    let tooltip = document.querySelector('.fast-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.className = 'fast-tooltip';
      document.body.appendChild(tooltip);
    }

    const moveTooltip = (event) => {
      const left = Math.min(event.clientX + 12, window.innerWidth - tooltip.offsetWidth - 12);
      const top = Math.min(event.clientY + 12, window.innerHeight - tooltip.offsetHeight - 12);
      tooltip.style.left = `${Math.max(8, left)}px`;
      tooltip.style.top = `${Math.max(8, top)}px`;
    };

    container.querySelectorAll('[data-tooltip]').forEach((target) => {
      target.addEventListener('mouseenter', (event) => {
        tooltip.textContent = target.dataset.tooltip;
        tooltip.classList.add('is-visible');
        moveTooltip(event);
      });
      target.addEventListener('mousemove', moveTooltip);
      target.addEventListener('mouseleave', () => tooltip.classList.remove('is-visible'));
    });
  }

  function pondColor(capacity) {
    if (capacity >= 10) return '#176b4d';
    if (capacity >= 5) return '#d39a24';
    return '#397bb8';
  }

  const coordinateLabels = {
    RELIABLE_POINT: ['ok', '단일 좌표 확인'],
    UNVERIFIED_ADMIN_POINT: ['warn', '군 대표점 좌표 · 생활권 분석 제외'],
    UNVERIFIED_NEARBY_POINT: ['warn', '인근 좌표 · 생활권 분석 제외'],
    DUPLICATED_COORDINATE: ['warn', '다른 못과 같은 좌표 · 생활권 분석 제외'],
  };

  // 분석 G·I와 같은 기준으로 시설별 데이터 상태를 보여준다.
  function qualityHtml(evidence) {
    const hasValue = (v) => v !== null && v !== undefined && String(v).trim() !== '' && Number.isFinite(Number(v));
    const [coordinateKind, coordinateText] = coordinateLabels[evidence.coordinate_validation] || ['na', '좌표 검증 자료 미확보'];
    const sgisCount = [evidence.sgis_population_5min, evidence.sgis_population_10min].filter(hasValue).length;
    const reliable = coordinateKind === 'ok';
    let sgisKind = sgisCount === 2 ? 'ok' : sgisCount === 1 ? 'warn' : 'na';
    let sgisText = sgisCount === 2 ? '5분·10분 응답 확보' : sgisCount === 1 ? '한 시간대만 응답' : '응답 미확보 (0명으로 해석하지 않음)';
    // 대표점·중복좌표의 응답은 실제 위치가 아닌 좌표 기준이므로 분석에 쓰지 않는다.
    if (!reliable && sgisCount) { sgisKind = 'warn'; sgisText = '응답은 있으나 좌표 확인 전이라 분석 제외'; }
    const candidate = coordinateCandidates.get(pondId({ properties: evidence }));
    const rows = [
      ['좌표', coordinateKind, coordinateText],
      ['SGIS', sgisKind, sgisText],
    ];
    if (candidate) rows.push(['보완 후보', 'info', `SGIS 지번 일치 · ${formatNumber(Math.round(Number(candidate.shift_from_current_m)))}m 차이 · 미반영`]);
    return `<div class="popup-quality"><strong>데이터 상태 · 분석 G·I</strong>${rows.map(([label, kind, text]) => `<p><span>${label}</span><i class="popup-quality-${kind}">${escapeHtml(text)}</i></p>`).join('')}</div>`;
  }

  function popupHtml(feature) {
    const properties = feature.properties || {};
    const [lng, lat] = feature.geometry.coordinates;
    const evidence = policyEvidenceMap[pondId(feature)] || {};
    const context = policyConfig[evidence.policy_review_context];
    const value = (v, unit = '') => v !== null && v !== undefined && String(v).trim() !== '' && Number.isFinite(Number(v)) ? `${formatNumber(v)}${unit}` : '미확보';

    return `
      <div class="popup-card">
        <h4>${escapeHtml(properties.address || '못')}</h4>
        <p class="map-context-label" style="--context-color:${context?.color || '#9ca3af'}">${escapeHtml(context?.label || '정책 자료 미확보')} · ID ${escapeHtml(pondId(feature))}</p>
        <table style="width:100%; border-collapse:collapse;">
          <tr><th>SGIS 5분 인구</th><td>${value(evidence.sgis_population_5min, '명')}</td></tr>
          <tr><th>SGIS 10분 인구</th><td>${value(evidence.sgis_population_10min, '명')}</td></tr>
          <tr><th>도로 직선거리</th><td>${value(properties.distance_to_road_m, 'm')}</td></tr>
          <tr><th>1km 주변시설</th><td>${value(properties.facility_count_1000m, '개')}</td></tr>
          <tr><th>규칙기반 활용유형</th><td>${escapeHtml(properties.classification_label)}</td></tr>
          <tr><th>활용유형 판정 근거</th><td>${escapeHtml(properties.classification_reason || '미확보')}</td></tr>
          <tr>
            <td style="padding:2px; color:#666;">지역</td>
            <td style="padding:2px; font-weight:bold;">${escapeHtml(properties.region)}</td>
          </tr>
          <tr>
            <td style="padding:2px; color:#666;">저수량</td>
            <td style="padding:2px; font-weight:bold;">${formatNumber(properties.capacity)} 천톤</td>
          </tr>
          <tr>
            <td style="padding:2px; color:#666;">좌표</td>
            <td style="padding:2px;">${lat.toFixed(5)}, ${lng.toFixed(5)}</td>
          </tr>
        </table>
        ${qualityHtml(evidence)}
        <div class="popup-review-note"><strong>정책 검토 근거</strong><p>${escapeHtml(context?.rule || '정책 검토 자료 미확보')}</p><strong>다음 확인</strong><p>${escapeHtml(context?.next || '원자료와 현장 상태를 추가 확인합니다.')}</p></div>
        <small>출처: SGIS 2024년 기준 응답 · VWorld 저장 공간자료 · 읍·면 인구 ${escapeHtml(properties.emd_year || '2025')}년. 생활권 인구는 실제 방문객 수가 아닙니다.</small>
      </div>
    `;
  }

  function createPondGeoJson(features) {
    // L.geoJSON(): GeoJSON FeatureCollection을 Leaflet 레이어로 변환한다.
    return L.geoJSON({ type: 'FeatureCollection', features }, {
      pointToLayer: (feature, latlng) => {
        const capacity = Number(feature.properties?.capacity || 0);

        return L.circleMarker(latlng, {
          radius: Math.max(5, Math.min(11, capacity * 0.55)),
          color: '#ffffff',
          weight: 1.5,
          fillColor: policyConfig[policyEvidenceMap[pondId(feature)]?.policy_review_context]?.color || '#9ca3af',
          fillOpacity: 0.9,
        });
      },
      onEachFeature: (feature, layer) => {
        // bindPopup(): 해당 못을 클릭했을 때 상세 정보를 보여준다.
        // 함수로 넘겨 열 때마다 최신 상태(늦게 불러오는 좌표 후보 포함)로 만든다.
        layer.bindPopup(() => popupHtml(feature));
        markerById.set(pondId(feature), layer);
      },
    });
  }

  function renderPonds(features) {
    // clearLayers(): 현재 표시된 못 레이어를 비운다.
    pondLayer.clearLayers();
    markerById.clear();

    // addLayer(): 새로 만든 GeoJSON 못 레이어를 그룹에 추가한다.
    pondLayer.addLayer(createPondGeoJson(features));
  }

  function parseCsv(text) {
    const rows = [];
    let row = [], cell = '', quoted = false;
    const source = String(text || '').replace(/^\uFEFF/, '');
    for (let i = 0; i < source.length; i += 1) {
      const ch = source[i];
      if (ch === '"') {
        if (quoted && source[i + 1] === '"') { cell += '"'; i += 1; }
        else quoted = !quoted;
      } else if (ch === ',' && !quoted) { row.push(cell); cell = ''; }
      else if ((ch === '\n' || ch === '\r') && !quoted) {
        if (ch === '\r' && source[i + 1] === '\n') i += 1;
        row.push(cell); if (row.some((v) => v !== '')) rows.push(row); row = []; cell = '';
      } else cell += ch;
    }
    row.push(cell); if (row.some((v) => v !== '')) rows.push(row);
    const headers = rows.shift() || [];
    return rows.map((values) => Object.fromEntries(headers.map((key, i) => [key, values[i] ?? ''])));
  }

  async function loadCsv(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${path} fetch failed: ${response.status}`);
    return parseCsv(await response.text());
  }

  function applyMapFilters() {
    if (!mapReady) return;
    const filtered = allPondFeatures.filter((feature) => {
      const props = feature.properties || {};
      const id = String(props.pond_id || props.id || '');
      const evidence = policyEvidenceMap[id] || {};
      if (Object.values(selectedIds).some(ids => ids && !ids.has(id))) return false;
      if (activeClassificationFilter !== 'all' && props.classification_label !== activeClassificationFilter) return false;
      if (activeSearch && !String(props.address || props.address_context || '').toLocaleLowerCase('ko').includes(activeSearch)) return false;
      if (activePolicyFilter !== 'all' && evidence.policy_review_context !== activePolicyFilter) return false;
      if (activeRegionFilter !== 'all' && (props.region || props.emd_name) !== activeRegionFilter) return false;
      if (activeCapacityFilter !== 'all') {
        const capacity = Number(props.capacity || 0);
        if (activeCapacityFilter === 'small' && capacity >= 5) return false;
        if (activeCapacityFilter === 'medium' && (capacity < 5 || capacity >= 10)) return false;
        if (activeCapacityFilter === 'large' && capacity < 10) return false;
      }
      return true;
    });
    renderPonds(filtered);
    const count = document.getElementById('filtered-count');
    if (count) count.textContent = String(filtered.length);
    document.querySelectorAll('[data-policy-filter]').forEach(item => item.setAttribute('aria-pressed', String(item.dataset.policyFilter === activePolicyFilter)));
    for (const [id, value] of [['policy-context-filter', activePolicyFilter], ['map-policy-filter', activePolicyFilter], ['region-filter', activeRegionFilter], ['classification-filter', activeClassificationFilter], ['capacity-filter', activeCapacityFilter]]) {
      const select = document.getElementById(id);
      if (select) [...select.options].forEach(option => { option.selected = option.value === value; });
    }
    const status = document.getElementById('map-analysis-status');
    const policyLabel = policyConfig[activePolicyFilter]?.label || '전체 정책 맥락';
    if (status) status.textContent = `${sgisMapLabels[activeSgisMapFilter]} · E ${policyLabel} · ${roadMapLabels[activeRoadMapFilter]} · ${activeRegionFilter === 'all' ? '전체 읍·면' : activeRegionFilter} · ${filtered.length}개 표시${filtered.length ? '' : ' — 조건을 해제하거나 초기화하세요.'}`;
  }

  function sgisIdsFor(code) {
    if (code === 'all') return null;
    return Object.values(policyEvidenceMap).filter((row) => {
      const flags = String(row.policy_evidence_flags || '');
      if (code === 'reach') return flags.includes('HIGH_10MIN_REACH');
      if (code === 'gain') return flags.includes('HIGH_5_TO_10_EXPANSION');
      return flags.includes('HIGH_10MIN_REACH') && flags.includes('HIGH_5_TO_10_EXPANSION');
    }).map((row) => String(row.pond_id));
  }

  function roadIdsFor(code) {
    if (code === 'all') return null;
    return allPondFeatures.filter((feature) => {
      const distance = Number(feature.properties?.distance_to_road_m ?? feature.properties?.nearest_road_m);
      if (!Number.isFinite(distance) || distance < 0) return false;
      if (code === '0') return distance <= 100;
      if (code === '1') return distance > 100 && distance <= 300;
      if (code === '2') return distance > 300 && distance <= 500;
      return distance > 500;
    }).map(pondId);
  }

  function setSgisMapFilter(code, notifyDashboard = true) {
    activeSgisMapFilter = sgisMapLabels[code] ? code : 'all';
    const ids = sgisIdsFor(activeSgisMapFilter);
    selectedIds.sgis = ids === null ? null : new Set(ids);
    const select = document.getElementById('sgis-map-filter');
    if (select) select.value = activeSgisMapFilter;
    applyMapFilters();
    if (notifyDashboard) document.dispatchEvent(new CustomEvent('sgis:map-sgis-filter', {detail: activeSgisMapFilter}));
  }

  function setRoadMapFilter(code, notifyDashboard = true) {
    activeRoadMapFilter = roadMapLabels[code] ? code : 'all';
    const ids = roadIdsFor(activeRoadMapFilter);
    selectedIds.road = ids === null ? null : new Set(ids);
    const select = document.getElementById('road-map-filter');
    if (select) select.value = activeRoadMapFilter;
    applyMapFilters();
    if (notifyDashboard) document.dispatchEvent(new CustomEvent('sgis:map-road-filter', {detail: activeRoadMapFilter}));
  }

  document.addEventListener('sgis:policy-filter', (event) => {
    activePolicyFilter = event.detail || 'all';
    document.querySelectorAll('[data-policy-filter]').forEach((item) => item.setAttribute('aria-pressed', String(item.dataset.policyFilter === activePolicyFilter)));
    applyMapFilters();
  });
  document.addEventListener('sgis:region-filter', (event) => {
    activeRegionFilter = event.detail || 'all';
    applyMapFilters();
  });

  async function loadJson(path) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`${path} 불러오기 실패: ${response.status}`);
    }
    return response.json();
  }

  function renderBarChart(containerId, items, labelKey, valueKey, formatter) {
    const container = document.getElementById(containerId);
    if (!container || !items.length) return;

    const maximum = Math.max(...items.map((item) => Number(item[valueKey]) || 0), 1);
    container.innerHTML = items.map((item) => {
      const value = Number(item[valueKey]) || 0;
      const width = Math.max(1, (value / maximum) * 100);
      return `
        <div class="bar-row" data-tooltip="${escapeHtml(`${item[labelKey]}: ${formatter(value)}`)}">
          <span>${escapeHtml(item[labelKey])}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span class="bar-value">${formatter(value)}</span>
        </div>
      `;
    }).join('');
    enableFastTooltips(container);
  }

  function renderTopFacilitiesChart(items) {
    const container = document.getElementById('top-facilities');
    if (!container || !items?.length) return;

    const topItems = items.slice(0, 5);
    const maximum = Math.max(...topItems.map((item) => Number(item.capacity) || 0), 1);
    container.innerHTML = topItems.map((item) => {
      const value = Number(item.capacity) || 0;
      // 극단적인 용량 값이 작은 시설의 차트를 숨기지 않도록 로그 스케일로 폭을 계산한다.
      const width = Math.max(4, (Math.log10(value + 1) / Math.log10(maximum + 1)) * 100);
      const title = `${item.address || '시설'} · ${item.region || '-'} · ${formatNumber(value)} 천톤`;
      return `
        <div class="bar-row" data-tooltip="${escapeHtml(title)}">
          <span>${escapeHtml(item.address || '시설')}</span>
          <div class="bar-track"><div class="bar-fill bar-fill-accent" style="width:${width}%"></div></div>
          <span class="bar-value">${formatNumber(value)}</span>
        </div>
      `;
    }).join('');
    enableFastTooltips(container);
  }

  function renderDensityDotPlot(items) {
    const container = document.getElementById('region-density-dotplot');
    if (!container || !items?.length) return;

    const ranked = [...items]
      .filter((item) => Number(item.facilities_per_km2) >= 0)
      .sort((a, b) => Number(b.facilities_per_km2) - Number(a.facilities_per_km2));
    const maximum = Math.max(...ranked.map((item) => Number(item.facilities_per_km2) || 0), 1);

    container.innerHTML = `
      <div class="dotplot-scale"><span>0개/km²</span><span>${formatNumber(maximum)}개/km²</span></div>
      ${ranked.map((item, index) => {
        const value = Number(item.facilities_per_km2) || 0;
        const position = Math.max(2, (value / maximum) * 100);
        const title = `${item.region}: ${formatNumber(value)}개/km² · 시설 ${formatNumber(item.facility_count)}개 · 면적 ${formatNumber(item.area_km2)}km²`;
        return `
          <div class="dotplot-row" data-tooltip="${escapeHtml(title)}">
            <span class="dotplot-rank">${String(index + 1).padStart(2, '0')}</span>
            <span class="dotplot-label">${escapeHtml(item.region)}</span>
            <div class="dotplot-track"><i class="dotplot-line" style="--dot-end:${position}%"></i><i class="dotplot-dot" style="--dot-end:${position}%"></i></div>
            <span class="dotplot-value" data-target="${value}">0</span>
          </div>
        `;
      }).join('')}
    `;
    enableFastTooltips(container);

    const startAnimation = () => {
      container.classList.add('is-visible');
      container.querySelectorAll('.dotplot-value').forEach((valueElement, index) => {
        const target = Number(valueElement.dataset.target || 0);
        const startedAt = performance.now() + index * 45;
        const duration = 720;
        const tick = (now) => {
          const progress = Math.min(1, Math.max(0, (now - startedAt) / duration));
          const eased = 1 - Math.pow(1 - progress, 3);
          valueElement.textContent = formatNumber(target * eased);
          if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    };
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries, currentObserver) => {
        if (!entries[0].isIntersecting) return;
        startAnimation();
        currentObserver.disconnect();
      }, { threshold: 0.25 });
      observer.observe(container);
    } else {
      startAnimation();
    }
  }

  function renderManagementPie(items) {
    const container = document.getElementById('management-pie');
    if (!container || !items?.length) return;

    const total = items.reduce((sum, item) => sum + (Number(item.facility_count) || 0), 0);
    const colors = ['#2d6a4f', '#d59d2d', '#397bb8', '#9b5de5'];
    const center = 100;
    const radius = 72;
    let angle = -Math.PI / 2;
    const slices = items.map((item, index) => {
      const value = Number(item.facility_count) || 0;
      const share = total ? value / total : 0;
      const nextAngle = angle + share * Math.PI * 2;
      const start = [center + radius * Math.cos(angle), center + radius * Math.sin(angle)];
      const end = [center + radius * Math.cos(nextAngle), center + radius * Math.sin(nextAngle)];
      const largeArc = share > 0.5 ? 1 : 0;
      const path = `M ${center} ${center} L ${start[0].toFixed(2)} ${start[1].toFixed(2)} A ${radius} ${radius} 0 ${largeArc} 1 ${end[0].toFixed(2)} ${end[1].toFixed(2)} Z`;
      angle = nextAngle;
      const percentage = total ? (share * 100).toFixed(1) : '0.0';
      return {
        item,
        path,
        color: colors[index % colors.length],
        percentage,
        title: `${item.management}: ${formatNumber(value)}개 (${percentage}%) · 총용량 ${formatNumber(item.total_capacity)}천톤 · 평균 ${formatNumber(item.mean_capacity)}천톤`,
      };
    });

    container.innerHTML = `
      <div class="pie-layout">
        <svg class="pie-chart" viewBox="0 0 200 200" role="img" aria-label="관리주체별 시설 수 원그래프">
          ${slices.map((slice) => `<path class="pie-slice" d="${slice.path}" fill="${slice.color}" data-tooltip="${escapeHtml(slice.title)}"></path>`).join('')}
          <circle cx="100" cy="100" r="40" fill="var(--panel)" />
          <text x="100" y="96" text-anchor="middle" class="pie-total-label">${formatNumber(total)}</text>
          <text x="100" y="112" text-anchor="middle" class="pie-total-sub">시설</text>
        </svg>
        <div class="pie-legend">
          ${slices.map((slice) => `<div class="pie-legend-item" data-tooltip="${escapeHtml(slice.title)}"><i style="background:${slice.color}"></i><span>${escapeHtml(slice.item.management)}</span><strong>${formatNumber(slice.item.facility_count)}개</strong></div>`).join('')}
        </div>
      </div>
    `;
    enableFastTooltips(container);

    const pieChart = container.querySelector('.pie-chart');
    const revealPie = () => pieChart?.classList.add('is-visible');
    if (pieChart && 'IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries, currentObserver) => {
        if (!entries[0].isIntersecting) return;
        revealPie();
        currentObserver.disconnect();
      }, { threshold: 0.35 });
      observer.observe(pieChart);
    } else {
      revealPie();
    }
  }

  function renderScatterPlot(containerId, points) {
    const container = document.getElementById(containerId);
    if (!container || !points.length) return;

    const width = 640;
    const height = 320;
    const padding = { top: 18, right: 20, bottom: 42, left: 58 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const maxX = Math.max(...points.map((point) => Number(point.capacity) || 0), 1);
    const maxY = Math.max(...points.map((point) => Number(point.agricultural_area_ha) || 0), 1);
    const xDomain = 10 ** Math.ceil(Math.log10(maxX + 1));
    const yDomain = 10 ** Math.ceil(Math.log10(maxY + 1));
    const logPosition = (value, domain) => Math.log10(1 + Math.max(0, Number(value) || 0)) / Math.log10(1 + domain);
    const ticksFor = (domain) => [0, 1, 10, 100, 1000, domain].filter((value, index, values) => value <= domain && values.indexOf(value) === index);
    const xTicks = ticksFor(xDomain);
    const yTicks = ticksFor(yDomain);
    const circles = points.map((point) => {
      const x = padding.left + logPosition(point.capacity, xDomain) * plotWidth;
      const y = padding.top + plotHeight - logPosition(point.agricultural_area_ha, yDomain) * plotHeight;
      const title = `${point.address || '시설'} · ${point.region || '-'} · 용량 ${formatNumber(point.capacity)}천톤 · 주변 농업지역 ${formatNumber(point.agricultural_area_ha)}ha`;
      return `<circle class="scatter-point" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.5" fill="#176b4d" fill-opacity="0.48"><title>${escapeHtml(title)}</title></circle>`;
    }).join('');
    const xGuides = xTicks.map((value) => {
      const x = padding.left + logPosition(value, xDomain) * plotWidth;
      return `<line x1="${x.toFixed(1)}" y1="${padding.top}" x2="${x.toFixed(1)}" y2="${padding.top + plotHeight}" class="scatter-grid" /><text x="${x.toFixed(1)}" y="${height - 22}" class="scatter-tick">${formatNumber(value)}</text>`;
    }).join('');
    const yGuides = yTicks.map((value) => {
      const y = padding.top + plotHeight - logPosition(value, yDomain) * plotHeight;
      return `<line x1="${padding.left}" y1="${y.toFixed(1)}" x2="${width - padding.right}" y2="${y.toFixed(1)}" class="scatter-grid" /><text x="${padding.left - 8}" y="${(y + 4).toFixed(1)}" class="scatter-tick scatter-y-tick">${formatNumber(value)}</text>`;
    }).join('');

    container.innerHTML = `
      <svg class="scatter-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="로그축 못 용량과 주변 농업지역 면적 산점도">
        ${xGuides}${yGuides}
        <line x1="${padding.left}" y1="${padding.top + plotHeight}" x2="${width - padding.right}" y2="${padding.top + plotHeight}" class="scatter-axis" />
        <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${padding.top + plotHeight}" class="scatter-axis" />
        ${circles}
        <text x="${width / 2}" y="${height - 6}" class="scatter-label">시설 용량 (천톤, log scale)</text>
        <text x="16" y="${height / 2}" class="scatter-label" transform="rotate(-90 16 ${height / 2})">주변 농업지역 (ha, log scale)</text>
      </svg>
    `;
  }

  function animateBasicStats(values) {
    const container = document.getElementById('basic-stats');
    if (!container) return;

    const targets = [
      { id: 'total-facilities', value: values.facilities, format: (value) => formatNumber(value) },
      { id: 'total-capacity', value: values.totalCapacity, format: (value) => `${formatNumber(value)} 천톤` },
      { id: 'average-capacity', value: values.averageCapacity, format: (value) => `${formatNumber(value)} 천톤` },
      { id: 'max-capacity', value: values.maximumCapacity, format: (value) => `${formatNumber(value)} 천톤` },
    ];

    const play = () => {
      targets.forEach((target, index) => {
        const element = document.getElementById(target.id);
        if (!element) return;
        const startedAt = performance.now() + index * 90;
        const duration = 850;
        const tick = (now) => {
          const progress = Math.min(1, Math.max(0, (now - startedAt) / duration));
          const eased = 1 - Math.pow(1 - progress, 3);
          element.textContent = target.format(target.value * eased);
          if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    };

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries, currentObserver) => {
        if (!entries[0].isIntersecting) return;
        play();
        currentObserver.disconnect();
      }, { threshold: 0.35 });
      observer.observe(container);
    } else {
      play();
    }
  }

  function renderAnalysis(analysis) {
    const regions = analysis.e.csv_region_summary || [];
    const facilityStats = analysis.c;
    const centroid = analysis.d;
    const agriculture = analysis.agriculture;
    const totalCapacity = regions.reduce((sum, item) => sum + Number(item.total_capacity || 0), 0);
    const averageCapacity = facilityStats.facility_count ? totalCapacity / facilityStats.facility_count : 0;
    const maximumCapacity = centroid.top_facilities?.[0]?.capacity || 0;

    animateBasicStats({
      facilities: facilityStats.facility_count,
      totalCapacity,
      averageCapacity,
      maximumCapacity,
    });

    document.getElementById('centroid-summary').innerHTML = [
      ['전체 용량 가중 중심', centroid.weighted_centroid],
      ['전체 단순 중심', centroid.unweighted_centroid],
      ['상위 10개 용량 가중 중심', centroid.top_10_centroid],
    ].map(([label, point]) => `
      <div class="centroid-card">
        <strong>${label}</strong>
        <span>위도 ${point.lat.toFixed(5)}</span>
        <span>경도 ${point.lng.toFixed(5)}</span>
      </div>
    `).join('');

    const weighted = centroid.weighted_centroid;
    const unweighted = centroid.unweighted_centroid;
    const centerShiftKm = Math.sqrt(
      Math.pow((weighted.lat - unweighted.lat) * 111, 2) +
      Math.pow((weighted.lng - unweighted.lng) * 89, 2)
    );
    document.getElementById('analysis-a-insight').innerHTML =
      `<strong>핵심 결과</strong> 용량 가중 중심은 ${weighted.lat.toFixed(3)}°N, ${weighted.lng.toFixed(3)}°E로 계산되었고, 단순 중심과 약 ${formatNumber(centerShiftKm)}km 차이가 나타났습니다. 시설의 개수뿐 아니라 규모까지 함께 보았을 때의 공간적 차이를 확인한 결과입니다.`;

    const management = analysis.e.xlsx_management_summary || [];
    renderTopFacilitiesChart(centroid.top_facilities);
    renderDensityDotPlot(regions);
    renderManagementPie(management);
    const managementInsight = document.getElementById('management-insight');
    if (managementInsight && management.length) {
      const totalManaged = management.reduce((sum, item) => sum + Number(item.facility_count || 0), 0);
      const largestManagement = [...management].sort((a, b) => Number(b.facility_count || 0) - Number(a.facility_count || 0))[0];
      const share = totalManaged ? (Number(largestManagement.facility_count) / totalManaged) * 100 : 0;
      managementInsight.innerHTML = `<strong>관리 구조</strong> ${escapeHtml(largestManagement.management)}가 ${formatNumber(largestManagement.facility_count)}개(${formatNumber(share)}%)로 가장 큰 비중을 차지합니다.`;
    }

    const densest = [...regions].sort((a, b) => Number(b.facilities_per_km2 || 0) - Number(a.facilities_per_km2 || 0))[0];
    document.getElementById('region-insight').innerHTML = densest
      ? `<strong>대표 insight</strong> ${escapeHtml(densest.region)}의 토지 면적당 시설 수가 가장 높습니다(${formatNumber(densest.facilities_per_km2)}개/km²). 읍면별 시설 수를 면적으로 표준화해 지역 규모의 영향을 줄였습니다.`
      : '';
    const largestManagement = [...management].sort((a, b) => Number(b.facility_count || 0) - Number(a.facility_count || 0))[0];
    document.getElementById('analysis-b-insight').innerHTML = densest && largestManagement
      ? `<strong>비교 기준</strong> 읍면 비교는 토지 면적당 시설 밀도, 관리주체 비교는 시설 수 비중으로 나누어 해석했습니다. 서로 다른 공간 단위와 관리 단위를 한 지표로 섞지 않았습니다.`
      : '';

    const buffer500 = agriculture.buffers['500'];
    const buffer1000 = agriculture.buffers['1000'];
    document.getElementById('agriculture-summary').innerHTML = [buffer500, buffer1000].map((item) => `
      <div class="centroid-card">
        <strong>못 주변 ${item.radius_m}m</strong>
        <span>평균 농업지역: ${formatNumber(item.mean_agricultural_area_m2 / 10000)} ha</span>
        <span>평균 비율: ${formatNumber(item.mean_agricultural_ratio)}%</span>
      </div>
    `).join('');
    document.getElementById('agriculture-correlation').innerHTML =
      `<strong>보조 검토 결과:</strong> 1km 기준 Pearson r=${formatNumber(buffer1000.pearson_r)}, ` +
      `Spearman ρ=${formatNumber(buffer1000.spearman_r)}로 상관관계는 약했습니다. 따라서 이 분석은 인과관계 주장이 아니라, 시설별 주변 환경지표를 만드는 GIS 처리 사례로 해석합니다.`;
    renderScatterPlot('agriculture-scatter', buffer1000.scatter);
  }

  async function initializeAnalysis() {
    try {
      const analysis = await loadJson('data/analysis/advanced_analysis.json');
      renderAnalysis(analysis);
    } catch (error) {
      console.error('분석 결과를 불러오지 못했습니다.', error);
    }
  }

  // 지도 영역이 화면에 가까워지면 한 번만 실행한다. 관찰을 못 쓰는 환경에서는 바로 실행한다.
  function whenNearMap(callback) {
    const target = document.getElementById('map');
    if (!target || !('IntersectionObserver' in window)) { callback(); return; }
    const observer = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      observer.disconnect();
      callback();
    }, { rootMargin: '1200px 0px' });
    observer.observe(target);
  }

  async function loadSupportLayers() {
    try {
      // 분석 C와 농업환경 분석에 사용한 농경지 Polygon을 지도에 올린다.
      const agricultureGeoJson = await loadJson('data/geojson/agricultural_areas_web.geojson');
      agricultureLayer.addData(agricultureGeoJson);
      const regionGeoJson = await loadJson('data/geojson/uiseong_emd_web.geojson');
      regionLayer.addData(regionGeoJson);
    } catch (error) {
      console.error('보조 지도 레이어를 불러오지 못했습니다.', error);
    }
  }

  async function initializeMap() {
    try {
      // 1. 의성군 행정경계 GeoJSON을 먼저 읽는다.
      const boundaryGeoJson = await loadJson('data/geojson/uiseong_boundary.geojson');
      boundaryLayer.addData(boundaryGeoJson);

      // 3. 경계 레이어에서 실제 bounds를 계산한다.
      const bounds = boundaryLayer.getBounds();
      if (!bounds.isValid()) {
        throw new Error('의성군 경계 bounds가 유효하지 않습니다.');
      }

      // 4. 경계의 실제 bounds로 의성군 전체가 보이도록 자동 확대한다.
      // setView()로 임의의 중심 좌표를 지정하지 않는다.
      map.fitBounds(bounds, { padding: [24, 24], animate: false });
      map.setMaxBounds(bounds.pad(0.06));

      // 5. 변환·검증이 끝난 못 GeoJSON을 읽는다.
      const pondsGeoJson = await loadJson('data/geojson/ponds_classified.geojson');
      allPondFeatures = Array.isArray(pondsGeoJson.features)
        ? pondsGeoJson.features
        : [];
      const filter = document.getElementById('capacity-filter');
      try {
        const evidenceRows = await loadCsv('data/analysis/sgis_policy_evidence.csv');
        policyEvidenceMap = Object.fromEntries(evidenceRows.map((row) => [String(row.pond_id || row.id || ''), row]));
      } catch (error) {
        console.warn('SGIS policy evidence unavailable', error);
      }
      policyConfig = (await dashboardModule).POLICY;
      // 핵심 시설·정책 데이터가 준비되는 즉시 필터를 활성화한다.
      // 부가 레이어를 읽는 동안 사용자가 조작해도 선택 상태가 유실되지 않는다.
      mapReady = true;
      document.getElementById('map')?.setAttribute('data-ready', 'true');
      const policyCodes = [['all', {label: '전체', color: '#475569'}], ...Object.entries(policyConfig)];
      const shortPolicyLabels = {
        all: '전체',
        FIELD_REVIEW_REQUIRED: '현장',
        INSUFFICIENT_SGIS_10MIN: '미확보',
        COMMUNITY_SUPPORT_REVIEW: '공동체',
        YOUTH_PARTICIPATION_REVIEW: '청년',
        ACCESS_AND_REACH_REVIEW: '접근',
        CONTEXT_ONLY: '맥락',
      };
      const contextCounts = Object.values(policyEvidenceMap).reduce((counts, row) => {
        counts[row.policy_review_context] = (counts[row.policy_review_context] || 0) + 1;
        return counts;
      }, {});
      for (const id of ['policy-context-filter', 'map-policy-filter']) {
        const policySelect = document.getElementById(id);
        if (!policySelect) continue;
        policySelect.innerHTML = policyCodes.map(([code, config]) => `<option value="${code}">${escapeHtml(config.label)} (${code === 'all' ? allPondFeatures.length : contextCounts[code] || 0}개)</option>`).join('');
        policySelect.addEventListener('change', event => document.dispatchEvent(new CustomEvent('sgis:policy-filter', {detail: event.target.value})));
      }
      document.getElementById('classification-filter')?.addEventListener('change', event => { activeClassificationFilter = event.target.value; applyMapFilters(); });
      document.getElementById('pond-search-input')?.addEventListener('input', event => { activeSearch = event.target.value.trim().toLocaleLowerCase('ko'); applyMapFilters(); });
      document.getElementById('sgis-map-filter')?.addEventListener('change', event => setSgisMapFilter(event.target.value));
      document.getElementById('road-map-filter')?.addEventListener('change', event => setRoadMapFilter(event.target.value));
      const legend = document.querySelector('.map-legend-row');
      if (legend) {
        legend.setAttribute('role', 'group');
        legend.setAttribute('aria-label', '정책 검토 맥락 지도 범례');
        legend.innerHTML = `<div class="map-legend-heading"><strong>마커 색상 · 분석 E</strong><span>정책 맥락 선택</span></div><div class="map-legend-items">${policyCodes.map(([code, config]) => { const count = code === 'all' ? allPondFeatures.length : contextCounts[code] || 0; return `<button type="button" class="legend-badge-item" data-policy-filter="${code}" style="--context-color:${config.color}" aria-label="${escapeHtml(config.label)} ${count}개" title="${escapeHtml(config.label)} ${count}개" aria-pressed="${code === activePolicyFilter}"><i class="dot" style="background:${config.color}" aria-hidden="true"></i><span class="legend-label-full">${escapeHtml(config.label)}</span><span class="legend-label-short" aria-hidden="true">${escapeHtml(shortPolicyLabels[code] || config.label)}</span><strong aria-hidden="true">${count}개</strong></button>`; }).join('')}</div>`;
        legend.addEventListener('click', (event) => {
          const button = event.target.closest('[data-policy-filter]');
          if (!button) return;
          activePolicyFilter = activePolicyFilter === button.dataset.policyFilter ? 'all' : button.dataset.policyFilter;
          legend.querySelectorAll('[data-policy-filter]').forEach((item) => item.setAttribute('aria-pressed', String(item.dataset.policyFilter === activePolicyFilter)));
          applyMapFilters();
          document.dispatchEvent(new CustomEvent('sgis:policy-filter', { detail: activePolicyFilter }));
        });
      }
      const regionFilter = document.getElementById('region-filter');
      if (regionFilter) {
        const regions = [...new Set(allPondFeatures.map((feature) => feature.properties?.region || feature.properties?.emd_name).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'ko'));
        regionFilter.innerHTML = '<option value="all">전체 읍·면</option>' + regions.map((region) => `<option value="${escapeHtml(region)}">${escapeHtml(region)}</option>`).join('');
        regionFilter.addEventListener('change', (event) => { activeRegionFilter = event.target.value; applyMapFilters(); document.dispatchEvent(new CustomEvent('sgis:region-filter', { detail: activeRegionFilter })); });
      }
      document.getElementById('pond-search-reset')?.addEventListener('click', () => {
        activePolicyFilter = 'all'; activeRegionFilter = 'all'; activeCapacityFilter = 'all';
        activeClassificationFilter = 'all'; activeSearch = '';
        activeSgisMapFilter = 'all'; activeRoadMapFilter = 'all';
        selectedIds.sgis = null; selectedIds.road = null;
        const search = document.getElementById('pond-search-input');
        if (search) search.value = '';
        if (regionFilter) regionFilter.value = 'all';
        if (filter) filter.value = 'all';
        const sgisMapFilter = document.getElementById('sgis-map-filter');
        const roadMapFilter = document.getElementById('road-map-filter');
        if (sgisMapFilter) sgisMapFilter.value = 'all';
        if (roadMapFilter) roadMapFilter.value = 'all';
        legend?.querySelectorAll('[data-policy-filter]').forEach((item) => item.setAttribute('aria-pressed', String(item.dataset.policyFilter === 'all')));
        applyMapFilters();
        document.dispatchEvent(new CustomEvent('sgis:policy-filter', { detail: 'all' }));
        document.dispatchEvent(new CustomEvent('sgis:region-filter', { detail: 'all' }));
        document.dispatchEvent(new CustomEvent('sgis:reset'));
      });

      // 농경지·읍면 밀도는 보조 레이어라 지도에 가까워질 때 불러온다(첫 화면 속도).
      // 좌표 후보는 분석 D에서 시설을 고를 때 팝업에 쓰이므로 바로 불러온다.
      whenNearMap(loadSupportLayers);
      loadCoordinateCandidates().catch((error) => console.warn('Coordinate candidates unavailable', error));

      const allOption = filter?.querySelector('option[value="all"]');
      if (allOption) {
        allOption.textContent = `의성군 내 전체 (${allPondFeatures.length}개)`;
      }

      // 기존 용량 필터는 핵심 지도 확인 뒤에도 동작하는 가장 단순한 필터다.
      filter?.addEventListener('change', (event) => {
        activeCapacityFilter = event.target.value;
        applyMapFilters();
      });

      applyMapFilters();

      console.info(`의성군 지도 준비 완료: 경계 1개, 못 ${allPondFeatures.length}개`);
    } catch (error) {
      console.error('지도 데이터를 불러오지 못했습니다.', error);
    }
  }

  function initializeScrollExperience() {
    const progressBar = document.getElementById('scroll-progress-bar');
    const updateProgress = () => {
      if (!progressBar) return;
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      const progress = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
      progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    };
    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', updateProgress);
    updateProgress();

    // Tall sections may never reach an intersection threshold on narrow screens.
    // Keep analysis and map content visible; reveal only compact cards.
    const revealTargets = document.querySelectorAll(
      '.career-card, .learning-card, .outcome-card'
    );
    revealTargets.forEach((target, index) => {
      target.classList.add('scroll-reveal');
      target.style.setProperty('--reveal-delay', `${Math.min(index % 4, 3) * 80}ms`);
    });

    if (!('IntersectionObserver' in window)) {
      revealTargets.forEach((target) => target.classList.add('is-visible'));
    } else {
      const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -7% 0px' });
      revealTargets.forEach((target) => revealObserver.observe(target));

      const header = document.querySelector('.site-header');
      const navLinks = [...document.querySelectorAll('nav a[href^="#"]')];
      const navSections = navLinks
        .map((link) => document.querySelector(link.getAttribute('href')))
        .filter(Boolean);
      const updateActiveNavigation = () => {
        const headerOffset = (header?.offsetHeight || 72) + 36;
        const currentPosition = window.scrollY + headerOffset;
        let activeSection = navSections[0]?.id || 'about';
        navSections.forEach((section) => {
          if (section.offsetTop <= currentPosition) activeSection = section.id;
        });
        navLinks.forEach((link) => link.classList.toggle(
          'is-active', link.getAttribute('href') === `#${activeSection}`
        ));
        header?.setAttribute('data-section', activeSection);
      };
      window.addEventListener('scroll', updateActiveNavigation, { passive: true });
      window.addEventListener('resize', updateActiveNavigation);
      updateActiveNavigation();
    }
  }

  // 2. Leaflet 지도는 위에서 생성했고, 데이터는 경계부터 순서대로 불러온다.
  initializeScrollExperience();
  import('./motion.mjs?v=20261004-lazy')
    .then(({ initMotion }) => initMotion())
    .catch((error) => console.warn('Section motion unavailable', error));
  initializeMap();
  initializeAnalysis();
  dashboardModule.then(({ initDefDashboard }) => initDefDashboard({
    loadJson,
    loadCsv,
    onPolicySelect: (value) => {
      activePolicyFilter = value || 'all';
      document.dispatchEvent(new CustomEvent('sgis:policy-filter', { detail: activePolicyFilter }));
    },
    onRegionSelect: (value) => {
      activeRegionFilter = value || 'all';
      document.dispatchEvent(new CustomEvent('sgis:region-filter', { detail: activeRegionFilter }));
    },
    onSgisSelect: (ids, code = 'all') => {
      activeSgisMapFilter = code;
      selectedIds.sgis = ids === null ? null : new Set(ids.map(String));
      const select = document.getElementById('sgis-map-filter');
      if (select) select.value = code;
      applyMapFilters();
    },
    onRoadSelect: (ids, code = 'all') => {
      activeRoadMapFilter = code;
      selectedIds.road = ids === null ? null : new Set(ids.map(String));
      const select = document.getElementById('road-map-filter');
      if (select) select.value = code;
      applyMapFilters();
    },
    onFacilitySelect: id => {
      const feature = allPondFeatures.find(item => pondId(item) === String(id));
      if (!feature) return;
      const marker = markerById.get(String(id));
      if (marker) {
        map.setView?.([feature.geometry.coordinates[1], feature.geometry.coordinates[0]], 13);
        marker.openPopup?.();
        document.getElementById('map')?.scrollIntoView?.({behavior: 'smooth', block: 'center'});
      } else {
        const status = document.getElementById('map-analysis-status');
        if (status) status.textContent = `못 ${id}는 다른 지도 조건에서 제외되어 있습니다. 초기화 후 선택하세요.`;
      }
    },
  })).catch((error) => console.error('D/E/F dashboard load failed', error));
  import('./quality-dashboard.mjs?v=20261004-lazy')
    .then(({ initQualityDashboard }) => initQualityDashboard({ loadJson, loadCsv }))
    .catch((error) => console.error('G–J quality dashboard load failed', error));
});
