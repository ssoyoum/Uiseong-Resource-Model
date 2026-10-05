// 자료–분석 연결도. 연결 관계는 index.html의 data-flow-to 속성에 있고, 여기서는 선만 그린다.
// 선이 없어도(좁은 화면·스크립트 실패) 각 자료 칸의 '쓰인 분석' 글자로 같은 내용을 읽을 수 있다.
const SVG_NS = 'http://www.w3.org/2000/svg';

export function initDataFlow() {
  const map = document.querySelector('[data-flow-map]');
  const svg = map?.querySelector('.flow-lines');
  if (!map || !svg) return;
  const sources = [...map.querySelectorAll('.flow-source')];
  const targets = new Map([...map.querySelectorAll('.flow-target')].map((node) => [node.dataset.flowTarget, node]));
  const links = sources.flatMap((source) => source.dataset.flowTo.split(/\s+/).filter((key) => targets.has(key)).map((key) => ({source, key})));

  const draw = () => {
    svg.replaceChildren();
    // 두 열이 세로로 쌓이는 좁은 화면에서는 선을 그리지 않는다.
    const box = map.getBoundingClientRect();
    const firstTarget = targets.values().next().value;
    if (!firstTarget || firstTarget.getBoundingClientRect().left <= sources[0].getBoundingClientRect().right) return;
    svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
    links.forEach((link) => {
      const from = link.source.getBoundingClientRect();
      const to = targets.get(link.key).getBoundingClientRect();
      const x1 = from.right - box.left;
      const y1 = from.top + from.height / 2 - box.top;
      const x2 = to.left - box.left;
      const y2 = to.top + to.height / 2 - box.top;
      const bend = (x2 - x1) * 0.5;
      const path = document.createElementNS(SVG_NS, 'path');
      path.setAttribute('d', `M${x1.toFixed(1)},${y1.toFixed(1)} C${(x1 + bend).toFixed(1)},${y1.toFixed(1)} ${(x2 - bend).toFixed(1)},${y2.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`);
      path.setAttribute('pathLength', '1');
      path.dataset.from = link.source.dataset.flowKey;
      path.dataset.to = link.key;
      svg.append(path);
    });
    applyFocus();
  };

  // 선택한 자료(또는 분석)와 이어진 선·칸만 강조한다.
  let active = null;
  const applyFocus = () => {
    map.classList.toggle('has-focus', Boolean(active));
    const related = (sourceKey, targetKey) => !active || (active.type === 'source' ? sourceKey === active.key : targetKey === active.key);
    svg.querySelectorAll('path').forEach((path) => path.classList.toggle('is-on', Boolean(active) && related(path.dataset.from, path.dataset.to)));
    sources.forEach((source) => {
      const on = !active || (active.type === 'source' ? source.dataset.flowKey === active.key : source.dataset.flowTo.split(/\s+/).includes(active.key));
      source.classList.toggle('is-on', Boolean(active) && on);
      source.setAttribute('aria-pressed', String(Boolean(active) && active.type === 'source' && source.dataset.flowKey === active.key));
    });
    targets.forEach((target, key) => {
      const on = !active || (active.type === 'target' ? key === active.key : links.some((link) => link.key === key && link.source.dataset.flowKey === active.key));
      target.classList.toggle('is-on', Boolean(active) && on);
    });
  };
  const setActive = (next) => { active = next; applyFocus(); };

  let pinned = null;
  sources.forEach((source) => {
    const value = {type: 'source', key: source.dataset.flowKey};
    source.addEventListener('pointerenter', () => { if (!pinned) setActive(value); });
    source.addEventListener('pointerleave', () => { if (!pinned) setActive(null); });
    source.addEventListener('focus', () => { if (!pinned) setActive(value); });
    source.addEventListener('blur', () => { if (!pinned) setActive(null); });
    // 누르면 고정하고, 같은 칸을 다시 누르면 해제한다(터치 화면 대응).
    source.addEventListener('click', () => {
      pinned = pinned?.key === value.key ? null : value;
      setActive(pinned || value);
    });
  });
  targets.forEach((target, key) => {
    const value = {type: 'target', key};
    target.addEventListener('pointerenter', () => { if (!pinned) setActive(value); });
    target.addEventListener('pointerleave', () => { if (!pinned) setActive(null); });
  });
  document.addEventListener('click', (event) => {
    if (pinned && !map.contains(event.target)) { pinned = null; setActive(null); }
  });

  draw();
  let frame = 0;
  const redraw = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(draw); };
  window.addEventListener('resize', redraw);
  if ('ResizeObserver' in window) new ResizeObserver(redraw).observe(map);
  // 글꼴이 늦게 적용되면 칸 높이가 바뀌므로 한 번 더 그린다.
  document.fonts?.ready.then(redraw);

  // 화면에 들어오면 선이 왼쪽에서 오른쪽으로 그려진다(움직임 설정을 따름).
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      map.classList.add('is-drawn');
      observer.disconnect();
    }, {threshold: 0.3});
    observer.observe(map);
  } else {
    map.classList.add('is-drawn');
  }
}
