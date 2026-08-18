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
      layer.bindPopup(`농업진흥지역<br>면적: ${formatNumber(area)} ha`);
    },
  }).addTo(map);
  const regionLayer = L.geoJSON(null, {
    style: (feature) => {
      const capacity = Number(feature.properties?.total_capacity || 0);
      const fillOpacity = capacity > 0 ? Math.min(0.65, 0.12 + capacity / 30000) : 0.04;
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
        `총용량: ${formatNumber(properties.total_capacity)} 천톤`
      );
    },
  });
  let allPondFeatures = [];

  // Leaflet의 레이어 컨트롤은 내부적으로 addLayer()/removeLayer()를 사용한다.
  // 체크하면 레이어를 지도에 추가하고, 해제하면 지도에서 제거한다.
  L.control.layers(
    null,
    {
      '의성군 행정경계': boundaryLayer,
      '못 위치': pondLayer,
      '농업진흥지역': agricultureLayer,
      '읍면별 총용량': regionLayer,
    },
    { collapsed: false }
  ).addTo(map);

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

  function pondColor(capacity) {
    if (capacity >= 10) return '#176b4d';
    if (capacity >= 5) return '#d39a24';
    return '#397bb8';
  }

  function popupHtml(feature) {
    const properties = feature.properties || {};
    const [lng, lat] = feature.geometry.coordinates;

    return `
      <div class="popup-card">
        <h4>${escapeHtml(properties.address || '못')}</h4>
        <table style="width:100%; border-collapse:collapse;">
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
          fillColor: pondColor(capacity),
          fillOpacity: 0.9,
        });
      },
      onEachFeature: (feature, layer) => {
        // bindPopup(): 해당 못을 클릭했을 때 상세 정보를 보여준다.
        layer.bindPopup(popupHtml(feature));
      },
    });
  }

  function renderPonds(features) {
    // clearLayers(): 현재 표시된 못 레이어를 비운다.
    pondLayer.clearLayers();

    // addLayer(): 새로 만든 GeoJSON 못 레이어를 그룹에 추가한다.
    pondLayer.addLayer(createPondGeoJson(features));
  }

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
        <div class="bar-row">
          <span>${escapeHtml(item[labelKey])}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span class="bar-value">${formatter(value)}</span>
        </div>
      `;
    }).join('');
  }

  function renderScatterPlot(containerId, points) {
    const container = document.getElementById(containerId);
    if (!container || !points.length) return;

    const width = 640;
    const height = 320;
    const padding = { top: 18, right: 20, bottom: 42, left: 58 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const maxX = Math.max(...points.map((point) => Number(point.capacity)), 1);
    const maxY = Math.max(...points.map((point) => Number(point.agricultural_area_ha)), 1);
    const circles = points.map((point) => {
      const x = padding.left + (Number(point.capacity) / maxX) * plotWidth;
      const y = padding.top + plotHeight - (Number(point.agricultural_area_ha) / maxY) * plotHeight;
      return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="#176b4d" fill-opacity="0.45"><title>${escapeHtml(point.address)}: ${formatNumber(point.capacity)}천톤 / ${formatNumber(point.agricultural_area_ha)}ha</title></circle>`;
    }).join('');

    container.innerHTML = `
      <svg class="scatter-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="못 용량과 주변 농업지역 면적 산점도">
        <line x1="${padding.left}" y1="${padding.top + plotHeight}" x2="${width - padding.right}" y2="${padding.top + plotHeight}" class="scatter-axis" />
        <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${padding.top + plotHeight}" class="scatter-axis" />
        ${circles}
        <text x="${width / 2}" y="${height - 8}" class="scatter-label">시설 용량 (천톤)</text>
        <text x="16" y="${height / 2}" class="scatter-label" transform="rotate(-90 16 ${height / 2})">주변 농업지역 (ha)</text>
      </svg>
    `;
  }

  function renderAnalysis(analysis) {
    const regions = analysis.e.csv_region_summary || [];
    const facilityStats = analysis.c;
    const centroid = analysis.d;
    const agriculture = analysis.agriculture;
    const totalCapacity = regions.reduce((sum, item) => sum + Number(item.total_capacity || 0), 0);
    const averageCapacity = facilityStats.facility_count ? totalCapacity / facilityStats.facility_count : 0;
    const maximumCapacity = centroid.top_facilities?.[0]?.capacity || 0;

    document.getElementById('total-facilities').textContent = formatNumber(facilityStats.facility_count);
    document.getElementById('total-capacity').textContent = `${formatNumber(totalCapacity)} 천톤`;
    document.getElementById('average-capacity').textContent = `${formatNumber(averageCapacity)} 천톤`;
    document.getElementById('max-capacity').textContent = `${formatNumber(maximumCapacity)} 천톤`;

    const regionSummary = document.getElementById('region-summary');
    regionSummary.innerHTML = regions.map((item) => `
      <div class="region-card">
        <strong>${escapeHtml(item.region)}</strong>
        <span>시설: ${formatNumber(item.facility_count)}개</span>
        <span>총용량: ${formatNumber(item.total_capacity)} 천톤</span>
      </div>
    `).join('');

    document.getElementById('c-research-note').textContent =
      '시설 간 최근린거리 및 공간적 군집성을 추가적으로 검토했으나, ' +
      '통계적 유의성이 낮아 강한 군집 패턴은 확인되지 않았다.';

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

    document.getElementById('top-facilities').innerHTML = `
      <table class="analysis-table">
        <thead><tr><th>주소</th><th>지역</th><th>용량(천톤)</th></tr></thead>
        <tbody>${centroid.top_facilities.map((item) => `
          <tr><td>${escapeHtml(item.address)}</td><td>${escapeHtml(item.region)}</td><td>${formatNumber(item.capacity)}</td></tr>
        `).join('')}</tbody>
      </table>
    `;

    document.getElementById('regional-centroids').innerHTML = `
      <table class="analysis-table">
        <thead><tr><th>지역</th><th>시설</th><th>가중 중심</th></tr></thead>
        <tbody>${centroid.regional_weighted_centroids.map((item) => `
          <tr><td>${escapeHtml(item.region)}</td><td>${item.facility_count}개</td><td>${item.weighted_lat.toFixed(3)}, ${item.weighted_lng.toFixed(3)}</td></tr>
        `).join('')}</tbody>
      </table>
    `;

    renderBarChart('region-capacity-chart', regions.slice(0, 13), 'region', 'total_capacity', (value) => `${formatNumber(value)} 천톤`);

    const boxplot = document.getElementById('region-boxplot');
    const boxplotMaximum = Math.max(...regions.map((item) => item.max_capacity), 1);
    boxplot.innerHTML = regions.map((item) => {
      const range = Math.max(item.max_capacity - item.min_capacity, 1);
      const left = (item.min_capacity / boxplotMaximum) * 100;
      const whiskerWidth = ((item.max_capacity - item.min_capacity) / boxplotMaximum) * 100;
      const boxLeft = (item.q1 / boxplotMaximum) * 100;
      const boxWidth = Math.max(0.5, ((item.q3 - item.q1) / boxplotMaximum) * 100);
      const medianLeft = (item.median_capacity / boxplotMaximum) * 100;
      return `
        <div class="boxplot-row" title="최소 ${item.min_capacity} / Q1 ${item.q1} / 중앙 ${item.median_capacity} / Q3 ${item.q3} / 최대 ${item.max_capacity}">
          <span>${escapeHtml(item.region)}</span>
          <div class="boxplot-track">
            <i class="boxplot-whisker" style="left:${left}%;width:${Math.max(0.5, whiskerWidth)}%"></i>
            <i class="boxplot-box" style="left:${boxLeft}%;width:${boxWidth}%"></i>
            <i class="boxplot-median" style="left:${medianLeft}%"></i>
          </div>
        </div>
      `;
    }).join('');

    const management = analysis.e.xlsx_management_summary || [];
    document.getElementById('management-summary').innerHTML = `
      <table class="analysis-table">
        <thead><tr><th>관리주체</th><th>시설</th><th>총용량</th><th>평균용량</th></tr></thead>
        <tbody>${management.map((item) => `
          <tr><td>${escapeHtml(item.management)}</td><td>${item.facility_count}개</td><td>${formatNumber(item.total_capacity)} 천톤</td><td>${formatNumber(item.mean_capacity)} 천톤</td></tr>
        `).join('')}</tbody>
      </table>
    `;

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
      `<strong>용량 × 주변 농업환경:</strong> 1km 기준 Pearson r=${formatNumber(buffer1000.pearson_r)}, ` +
      `Spearman ρ=${formatNumber(buffer1000.spearman_r)}. ${escapeHtml(buffer1000.correlation_interpretation)}.`;
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
      const pondsGeoJson = await loadJson('data/geojson/ponds.geojson');
      allPondFeatures = Array.isArray(pondsGeoJson.features)
        ? pondsGeoJson.features
        : [];

      // E와 농업환경 분석에 사용한 농업진흥지역 Polygon을 지도에 올린다.
      const agricultureGeoJson = await loadJson('data/geojson/agricultural_areas.geojson');
      agricultureLayer.addData(agricultureGeoJson);
      const regionGeoJson = await loadJson('data/geojson/uiseong_emd.geojson');
      regionLayer.addData(regionGeoJson);

      // 6~7. 의성군 지도 위에 못을 표시하고 클릭 Popup을 연결한다.
      renderPonds(allPondFeatures);

      const filter = document.getElementById('capacity-filter');
      const allOption = filter?.querySelector('option[value="all"]');
      if (allOption) {
        allOption.textContent = `의성군 내 전체 (${allPondFeatures.length}개)`;
      }

      // 기존 용량 필터는 핵심 지도 확인 뒤에도 동작하는 가장 단순한 필터다.
      filter?.addEventListener('change', (event) => {
        const value = event.target.value;
        const filtered = value === 'all'
          ? allPondFeatures
          : allPondFeatures.filter((feature) => {
              const capacity = Number(feature.properties?.capacity || 0);
              if (value === 'small') return capacity < 5;
              if (value === 'medium') return capacity >= 5 && capacity < 10;
              if (value === 'large') return capacity >= 10;
              return true;
            });
        renderPonds(filtered);
      });

      console.info(`의성군 지도 준비 완료: 경계 1개, 못 ${allPondFeatures.length}개`);
    } catch (error) {
      console.error('지도 데이터를 불러오지 못했습니다.', error);
    }
  }

  // 2. Leaflet 지도는 위에서 생성했고, 데이터는 경계부터 순서대로 불러온다.
  initializeMap();
  initializeAnalysis();
});
