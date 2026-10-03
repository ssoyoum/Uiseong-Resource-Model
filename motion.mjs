// Section-specific scroll interactions. Plain DOM APIs only.
// Motion is opt-in: without this module (or with reduced motion) every element stays visible.
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const wide = window.matchMedia('(min-width: 901px)');
const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));

function revealOnView(elements, {threshold = 0.15, repeat = false} = {}) {
  const items = [...elements].filter(Boolean);
  if (!items.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      // 화면보다 긴 블록은 비율 기준을 넘지 못하므로 위쪽이 들어오면 보여 준다.
      const tallEnough = entry.boundingClientRect.top < window.innerHeight * 0.85;
      if (entry.isIntersecting && (entry.intersectionRatio >= threshold || tallEnough)) {
        entry.target.classList.add('m-in');
        if (!repeat) observer.unobserve(entry.target);
      } else if (repeat && !entry.isIntersecting) {
        entry.target.classList.remove('m-in');
      }
    });
  }, {threshold: [0, threshold], rootMargin: '0px 0px -8% 0px'});
  items.forEach((item) => observer.observe(item));
}

function mark(elements, kind, {stagger = true} = {}) {
  [...elements].forEach((element, index) => {
    element.dataset.m = kind;
    if (stagger) element.style.setProperty('--i', String(index));
  });
  return [...elements];
}

// HERO: 제목을 글자 단위로 나눠 차례로 떠오르게 한다(<br>·<em> 구조 유지).
function splitHeadline(heading) {
  if (!heading || heading.dataset.split) return;
  heading.dataset.split = 'true';
  heading.setAttribute('aria-label', heading.textContent.replace(/\s+/g, ' ').trim());
  let index = 0;
  const walk = (node) => {
    [...node.childNodes].forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        const fragment = document.createDocumentFragment();
        [...child.textContent].forEach((char) => {
          if (/\s/.test(char)) { fragment.append(char); return; }
          const span = document.createElement('span');
          span.className = 'm-char';
          span.setAttribute('aria-hidden', 'true');
          span.style.setProperty('--i', String(index++));
          span.textContent = char;
          fragment.append(span);
        });
        child.replaceWith(fragment);
      } else if (child.nodeType === Node.ELEMENT_NODE && child.tagName !== 'BR') {
        walk(child);
      }
    });
  };
  walk(heading);
}

// 숫자를 0에서 실제 값까지 올린다. 첫 텍스트 노드의 숫자만 바꿔 단위 <span>은 그대로 둔다.
function countUp(elements) {
  const targets = [...elements].map((element) => {
    const node = [...element.childNodes].find((child) => child.nodeType === Node.TEXT_NODE && /\d/.test(child.textContent));
    // 'EPSG:5174'처럼 숫자가 코드의 일부인 값은 세지 않는다.
    if (!node || !/^[\d,.\s]+$/.test(node.textContent.trim())) return null;
    const match = node.textContent.match(/[\d,]+(\.\d+)?/);
    const value = Number(match[0].replace(/,/g, ''));
    return Number.isFinite(value) ? {element, node, value, original: node.textContent, token: match[0]} : null;
  }).filter(Boolean);
  if (!targets.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      const target = targets.find((item) => item.element === entry.target);
      const start = performance.now();
      const step = (now) => {
        const t = clamp((now - start) / 1200);
        const eased = 1 - (1 - t) ** 3;
        const current = Math.round(target.value * eased).toLocaleString('ko-KR');
        target.node.textContent = target.original.replace(target.token, current);
        if (t < 1) requestAnimationFrame(step);
        else target.node.textContent = target.original;
      };
      requestAnimationFrame(step);
    });
  }, {threshold: 0.6});
  targets.forEach((item) => observer.observe(item.element));
}

// 스크롤 위치를 0~1 진행률(--p)로 바꿔 CSS가 단계별로 그리게 한다.
const progressItems = [];
function trackProgress(element, compute) {
  if (element) progressItems.push({element, compute});
}
const viewportProgress = (element) => {
  const rect = element.getBoundingClientRect();
  const height = window.innerHeight;
  return clamp((height * 0.82 - rect.top) / (rect.height + height * 0.25));
};
const pinnedProgress = (track) => {
  const rect = track.getBoundingClientRect();
  const distance = track.offsetHeight - window.innerHeight;
  return distance > 0 ? clamp(-rect.top / (distance * 0.85)) : 1;
};
let ticking = false;
function updateProgress() {
  ticking = false;
  progressItems.forEach(({element, compute}) => element.style.setProperty('--p', compute(element).toFixed(3)));
}
function requestProgress() {
  if (!ticking) { ticking = true; requestAnimationFrame(updateProgress); }
}

// MODEL: 세 단계를 화면에 고정해 두고 스크롤에 따라 하나씩 연결한다.
function pinModelSteps() {
  const section = document.getElementById('project');
  const heading = section?.querySelector('.policy-section-heading');
  const grid = section?.querySelector('.model-stage-grid');
  if (!heading || !grid) return;
  const track = document.createElement('div');
  track.className = 'm-pin-track';
  const stage = document.createElement('div');
  stage.className = 'm-pin-stage';
  const line = document.createElement('div');
  line.className = 'm-model-line';
  line.setAttribute('aria-hidden', 'true');
  heading.before(track);
  track.append(stage);
  stage.append(heading, line, grid);
  [...grid.children].forEach((card, index) => card.style.setProperty('--k', String(0.12 + index * 0.3)));
  trackProgress(track, pinnedProgress);
}

// WHY: 화면에 고정해 두고 스크롤에 따라 문장 속 단어를 하나씩 켠다.
function scrubWords() {
  const section = document.getElementById('why');
  if (!section) return;
  const words = [];
  section.querySelectorAll('p').forEach((paragraph) => {
    const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const fragment = document.createDocumentFragment();
      node.textContent.split(/(\s+)/).forEach((part) => {
        if (!part) return;
        if (/^\s+$/.test(part)) { fragment.append(part); return; }
        const span = document.createElement('span');
        span.className = 'm-word';
        span.textContent = part;
        words.push(span);
        fragment.append(span);
      });
      node.replaceWith(fragment);
    });
  });
  section.classList.add('m-scrub');
  trackProgress(section, (element) => {
    const progress = pinnedProgress(element);
    const lit = Math.round(progress * 1.15 * words.length);
    words.forEach((word, index) => word.classList.toggle('on', index < lit));
    return progress;
  });
}

// RESEARCH: 타임라인을 가로로 펼쳐 세로 스크롤만큼 옆으로 흘려보낸다.
function horizontalTimeline() {
  const section = document.getElementById('research');
  const container = section?.querySelector('.container');
  const timeline = section?.querySelector('.timeline');
  if (!container || !timeline) return;
  const items = [...timeline.querySelectorAll('.timeline-item')];
  items.forEach((item, index) => item.style.setProperty('--k', (index / (items.length + 1)).toFixed(3)));
  section.classList.add('m-hscroll');
  let shift = 0;
  const measure = () => {
    timeline.style.transform = '';
    shift = Math.max(0, timeline.scrollWidth - container.clientWidth + 48);
    section.style.height = `${window.innerHeight + shift * 1.1}px`;
  };
  measure();
  window.addEventListener('resize', measure);
  trackProgress(section, (element) => {
    const progress = pinnedProgress(element);
    timeline.style.transform = `translate3d(${(-progress * shift).toFixed(1)}px, 0, 0)`;
    return progress;
  });
}

// DATA: 처리 단계가 왼쪽부터 순서대로 점등된다.
function lightPipeline() {
  const pipeline = document.querySelector('#data .data-pipeline');
  if (!pipeline) return;
  const parts = [...pipeline.children];
  parts.forEach((part, index) => part.style.setProperty('--k', (index / (parts.length + 1)).toFixed(3)));
  pipeline.classList.add('m-pipeline');
  trackProgress(pipeline, viewportProgress);
}

// WEBGIS: 지도 창이 스크롤에 따라 넓어진다.
function growMap() {
  const stage = document.querySelector('#webgis .map-stage');
  if (!stage) return;
  delete stage.dataset.m;
  stage.classList.add('m-map-grow');
  trackProgress(stage, viewportProgress);
}

// A–F, G–K 목차: 지금 읽는 분석을 강조한다.
function followChapters() {
  document.querySelectorAll('[data-toc]').forEach((toc) => {
    const links = [...toc.querySelectorAll('a[href^="#"]')];
    const targets = links.map((link) => document.querySelector(link.getAttribute('href'))).filter(Boolean);
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((link) => link.classList.toggle('is-current', link.getAttribute('href') === `#${entry.target.id}`));
      });
    }, {rootMargin: '-40% 0px -55% 0px'});
    targets.forEach((target) => observer.observe(target));
  });
}

// OUTCOME: 카드가 마우스 방향으로 살짝 기운다.
function tiltCards(cards) {
  cards.forEach((card) => {
    card.classList.add('m-tilt');
    card.addEventListener('pointermove', (event) => {
      const rect = card.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      card.style.setProperty('--rx', `${(-y * 8).toFixed(2)}deg`);
      card.style.setProperty('--ry', `${(x * 10).toFixed(2)}deg`);
    });
    card.addEventListener('pointerleave', () => { card.style.setProperty('--rx', '0deg'); card.style.setProperty('--ry', '0deg'); });
  });
}

// QUALITY: 표가 나중에 채워져도 행이 순서대로 들어오게 한다.
function staggerRows(blocks) {
  const number = (block) => block.querySelectorAll('.def-table tbody tr').forEach((row, index) => row.style.setProperty('--i', String(Math.min(index, 24))));
  blocks.forEach((block) => {
    number(block);
    new MutationObserver(() => number(block)).observe(block, {childList: true, subtree: true});
  });
}

export function initMotion() {
  if (reduceMotion || !('IntersectionObserver' in window)) return;
  document.documentElement.classList.add('motion');
  const header = document.querySelector('.site-header');
  document.documentElement.style.setProperty('--header-h', `${header?.offsetHeight || 64}px`);

  splitHeadline(document.querySelector('#about h1'));
  countUp(document.querySelectorAll('.public-metrics strong, #result .stat-number'));
  revealOnView(mark(document.querySelectorAll('.policy-hero-card, .public-metrics'), 'rise'));
  revealOnView(mark(document.querySelectorAll('main section:not(#about) h2'), 'wipe', {stagger: false}), {threshold: 0.6});

  const why = document.querySelectorAll('#why .two-col > div');
  if (why[0]) why[0].dataset.m = 'left';
  if (why[1]) why[1].dataset.m = 'right';
  revealOnView(why, {threshold: 0.3});

  revealOnView(mark(document.querySelectorAll('#project .model-evidence-note, #project .model-quicklinks'), 'up'));
  revealOnView(mark(document.querySelectorAll('#data .data-structure-card'), 'flip'));
  revealOnView(mark(document.querySelectorAll('.analysis-part'), 'slide', {stagger: false}), {threshold: 0.4});
  revealOnView(mark(document.querySelectorAll('#analysis .analysis-block'), 'zoom', {stagger: false}), {threshold: 0.08});
  revealOnView(mark(document.querySelectorAll('#result .result-stat'), 'pop'), {threshold: 0.4});
  revealOnView(mark(document.querySelectorAll('#webgis .map-stage'), 'open', {stagger: false}), {threshold: 0.25});
  const qualityBlocks = mark(document.querySelectorAll('#quality .analysis-block'), 'rows', {stagger: false});
  staggerRows(qualityBlocks);
  revealOnView(qualityBlocks, {threshold: 0.08});
  revealOnView(mark(document.querySelectorAll('#archive .public-source-card'), 'fan'));
  tiltCards([...document.querySelectorAll('.outcome-card')]);
  followChapters();

  // 고정·진행률 연출은 넓은 화면에서만 쓴다. 좁은 화면은 위의 등장 효과만 남긴다.
  if (wide.matches) {
    document.documentElement.classList.add('motion-wide');
    scrubWords();
    pinModelSteps();
    horizontalTimeline();
    lightPipeline();
    growMap();
    window.addEventListener('scroll', requestProgress, {passive: true});
    window.addEventListener('resize', requestProgress);
    updateProgress();
  }
}
