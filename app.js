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
  let allPondFeatures = [];

  // Leaflet의 레이어 컨트롤은 내부적으로 addLayer()/removeLayer()를 사용한다.
  // 체크하면 레이어를 지도에 추가하고, 해제하면 지도에서 제거한다.
  L.control.layers(
    null,
    {
      '의성군 행정경계': boundaryLayer,
      '못 위치': pondLayer,
      '농경지·농업진흥지역': agricultureLayer,
      '읍면별 시설 밀도': regionLayer,
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
        <div class="bar-row" title="${escapeHtml(`${item[labelKey]}: ${formatter(value)}`)}">
          <span>${escapeHtml(item[labelKey])}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span class="bar-value">${formatter(value)}</span>
        </div>
      `;
    }).join('');
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
        <div class="bar-row" title="${escapeHtml(title)}">
          <span>${escapeHtml(item.address || '시설')}</span>
          <div class="bar-track"><div class="bar-fill bar-fill-accent" style="width:${width}%"></div></div>
          <span class="bar-value">${formatNumber(value)}</span>
        </div>
      `;
    }).join('');
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
          <div class="dotplot-row" title="${escapeHtml(title)}">
            <span class="dotplot-rank">${String(index + 1).padStart(2, '0')}</span>
            <span class="dotplot-label">${escapeHtml(item.region)}</span>
            <div class="dotplot-track"><i class="dotplot-line" style="width:${position}%"></i><i class="dotplot-dot" style="left:${position}%"></i></div>
            <span class="dotplot-value">${formatNumber(value)}</span>
          </div>
        `;
      }).join('')}
    `;
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
          ${slices.map((slice) => `<path class="pie-slice" d="${slice.path}" fill="${slice.color}"><title>${escapeHtml(slice.title)}</title></path>`).join('')}
          <circle cx="100" cy="100" r="40" fill="var(--panel)" />
          <text x="100" y="96" text-anchor="middle" class="pie-total-label">${formatNumber(total)}</text>
          <text x="100" y="112" text-anchor="middle" class="pie-total-sub">시설</text>
        </svg>
        <div class="pie-legend">
          ${slices.map((slice) => `<div class="pie-legend-item" title="${escapeHtml(slice.title)}"><i style="background:${slice.color}"></i><span>${escapeHtml(slice.item.management)}</span><strong>${formatNumber(slice.item.facility_count)}개</strong></div>`).join('')}
        </div>
      </div>
    `;
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

      // 분석 C와 농업환경 분석에 사용한 농경지 Polygon을 지도에 올린다.
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

    const revealTargets = document.querySelectorAll(
      '.section > .container, .career-card, .learning-card, .outcome-card, .analysis-block'
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

      const navLinks = [...document.querySelectorAll('nav a[href^="#"]')];
      const navSections = navLinks
        .map((link) => document.querySelector(link.getAttribute('href')))
        .filter(Boolean);
      const navObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          navLinks.forEach((link) => link.classList.toggle(
            'is-active', link.getAttribute('href') === `#${entry.target.id}`
          ));
        });
      }, { threshold: 0.2, rootMargin: '-20% 0px -65% 0px' });
      navSections.forEach((section) => navObserver.observe(section));
    }
  }

  // 2. Leaflet 지도는 위에서 생성했고, 데이터는 경계부터 순서대로 불러온다.
  initializeScrollExperience();
  initializeMap();
  initializeAnalysis();
});
