const $ = s => document.querySelector(s);
const C = { dc: '#2f5fe0', cache: '#d8453b', ep: '#17916a', video: '#7c55d8', ink: '#131b2c', ink2: '#39445a', muted: '#6d778a', flag: '#f4b400', amber: '#d48a1a' };
const K = { good: '#17916a', fix: '#e39a22', fix2: '#f3cf86', none: '#d5dbe4' };
const S = { instances: [], codes: [], inst: null, code: null, charts: {}, sol: null, frame: 0, timer: null, editor: null, dirty: false, small: null };
const fmt = n => Number(n).toLocaleString('en-US');
const enc = o => Object.entries(o).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');
const esc = t => String(t).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const pc = (a, b) => b ? 100 * a / b : 0;
const pct = x => (x >= 99.95 && x < 100 ? x.toFixed(2) : x > 0 && x < 10 ? x.toFixed(1) : Math.round(x)) + '%';
const plural = (n, w) => `${fmt(n)} ${w}${n === 1 ? '' : 's'}`;
const GROUPS = { statement: 'Example from the problem', official: 'Official', generated: 'Made by you' };
const BEST = 'The best possible score is the score you would get if every cache were big enough for all videos. No solution can beat it.';

const TYPES = {
  random: 'All values are random.',
  zipf: 'A few videos are very popular. Most videos are rarely watched.',
  regional: 'Endpoints are split into regions. Each region has its own caches and its own popular videos.',
  dejavu: 'The students\u2019 DejaVu generator, with its bug fixed. Each endpoint watches the same few videos again and again.',
  giant: 'Videos are about as big as a cache, or bigger.',
  knapsack_trap: 'A trap for greedy code: the video that looks best for each MB is not the best choice.',
  edge: 'Very small or extreme cases, to check that your code does not crash.'
};
const VARIANTS = {
  single: 'One video, one endpoint, one cache, one request.',
  no_cache: 'No endpoint is connected to a cache. The best score is 0.',
  too_big: 'Every video is bigger than a cache.',
  exact_fit: 'Four videos that fill one cache exactly.',
  maximum: 'The biggest numbers the rules allow.'
};
const SECTION_NAMES = ['Videos and space', 'Network', 'Requests'];
const SECTION_COLORS = [C.video, C.cache, C.ep];
const ROWS = {
  'videos': ['Videos', 'Number of different videos.'],
  'video size (MB)': ['Video size (MB)', 'From the smallest to the biggest video.'],
  'videos never requested': ['Videos nobody asks for', 'Never put these in a cache.'],
  'videos bigger than X (can never be cached)': ['Videos too big for a cache', 'They can only come from the datacenter.'],
  'caches': ['Total cache space', 'Number of caches times the size of one cache.'],
  'total size of requested videos': ['Size of requested videos', 'Space needed to store one copy of each video people ask for.'],
  'cache space / requested size': ['Caches can hold', 'How much of the requested videos fits in all caches together. Under 100%, you must choose which videos to keep.'],
  'videos per cache on average (X / mean size)': ['Videos in one cache', 'About how many videos of average size fit in one cache.'],
  'endpoints': ['Endpoints', 'Groups of users in one place.'],
  'endpoint-cache links': ['Endpoint–cache connections', 'All connections between endpoints and caches.'],
  'caches per endpoint': ['Caches per endpoint', 'How many caches each endpoint can use.'],
  'endpoints with no cache': ['Endpoints with no cache', 'These endpoints always wait for the datacenter.'],
  'endpoints per cache': ['Endpoints per cache', 'How many endpoints use each cache.'],
  'caches linked to no endpoint': ['Caches nobody uses', 'No endpoint is connected to them. A video there helps nobody.'],
  'datacenter latency Ld (ms)': ['Wait from the datacenter (ms)', 'How long a request waits when the video comes from the datacenter.'],
  'cache latency Lc (ms)': ['Wait from a cache (ms)', 'How long a request waits when the video comes from a cache. Always less than the datacenter.'],
  'time saved per link Ld - Lc (ms)': ['Time a cache saves (ms)', 'Datacenter wait minus cache wait, for one request.'],
  'request lines R': ['Request lines', 'Lines in the file. Each line says: this endpoint asks for this video this many times.'],
  'total requests (sum of Rn)': ['Total requests', 'All requests added together.'],
  'requests per endpoint': ['Requests per endpoint', 'How many requests each endpoint sends.'],
  'share taken by the top 10 % videos': ['Views on the top 10% of videos', 'If this is high, caching a few popular videos is enough for a good score.'],
  'requests that can never be sped up': ['Requests no cache can help', 'The endpoint has no cache, or the video is too big for a cache.'],
  'score upper bound': ['Best possible score', BEST]
};

const tip = $('#tip');
function showTip(text, x, y) {
  if (!text) return hideTip();
  tip.innerHTML = text;
  tip.classList.add('on');
  placeTip(x, y);
}
function placeTip(x, y) {
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let left = x + 14, top = y + 16;
  if (left + w > innerWidth - 8) left = x - w - 14;
  if (top + h > innerHeight - 8) top = y - h - 12;
  tip.style.left = Math.max(8, left) + 'px';
  tip.style.top = Math.max(8, top) + 'px';
}
function hideTip() { tip.classList.remove('on'); }
document.addEventListener('mouseover', e => {
  const t = e.target.closest('[data-tip]');
  t ? showTip(t.dataset.tip, e.clientX, e.clientY) : hideTip();
});
document.addEventListener('mousemove', e => { if (tip.classList.contains('on')) placeTip(e.clientX, e.clientY); });
document.addEventListener('focusin', e => {
  const t = e.target.closest('[data-tip]');
  if (!t) return;
  const r = t.getBoundingClientRect();
  showTip(t.dataset.tip, r.left, r.bottom);
});
document.addEventListener('focusout', hideTip);
document.addEventListener('scroll', hideTip, true);

if (window.Chart) {
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.font.size = 11;
  Chart.defaults.color = C.muted;
  Chart.defaults.borderColor = '#edf0f5';
  Chart.defaults.elements.bar.borderRadius = 2;
  Chart.defaults.plugins.tooltip.backgroundColor = C.ink;
  Chart.defaults.plugins.tooltip.padding = 9;
  Chart.defaults.plugins.tooltip.cornerRadius = 6;
  Chart.defaults.plugins.tooltip.displayColors = false;
}

async function api(url, opts) { return (await fetch(url, opts)).json(); }
const post = (url, data) => api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });

const rng = l => l.includes('\u2013') ? 'between ' + l.replace('\u2013', ' and ') : 'exactly ' + l;
const s1 = (n, verb) => n === 1 ? verb + 's' : verb;
const axis = text => ({ display: true, text, color: C.ink2, font: { weight: '600', size: 12 } });
function chart(id, config) {
  if (S.charts[id]) S.charts[id].destroy();
  if (!window.Chart) return null;
  config.options = Object.assign({ animation: false, maintainAspectRatio: false }, config.options || {});
  config.options.plugins = Object.assign({ legend: { display: false } }, config.options.plugins || {});
  S.charts[id] = new Chart(document.getElementById(id), config);
  return S.charts[id];
}
function hist(id, h, color, xName, yName, sentence) {
  return chart(id, {
    type: 'bar',
    data: { labels: h.labels, datasets: [{ data: h.counts, backgroundColor: color, borderWidth: 0, barPercentage: 1, categoryPercentage: 0.9 }] },
    options: {
      scales: {
        x: { title: axis(xName), grid: { display: false }, ticks: { maxTicksLimit: 8, maxRotation: 0 } },
        y: { title: axis(yName), beginAtZero: true, ticks: { maxTicksLimit: 5, precision: 0 } }
      },
      plugins: { tooltip: { callbacks: { title: () => '', label: c => sentence(c.raw, rng(c.label)) } } }
    }
  });
}

const activeTab = () => document.querySelector('.tabs .on').dataset.tab;
function setTab(name) {
  document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === name));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('on', v.id === name));
  if (name === 'code') setTimeout(() => S.editor.refresh(), 0);
  refresh();
}
function refresh() {
  const t = activeTab();
  if (t === 'instances') loadInstance();
  if (t === 'demo') loadDemo();
  if (t === 'stats') loadStats();
}

async function loadLists() {
  S.instances = await api('/api/instances');
  S.codes = await api('/api/codes');
  const si = $('#selInstance');
  si.innerHTML = '';
  for (const g of Object.keys(GROUPS)) {
    const og = document.createElement('optgroup');
    og.label = GROUPS[g];
    S.instances.filter(i => i.groupe === g).forEach(i => og.append(new Option(i.nom, i.id)));
    if (og.children.length) si.append(og);
  }
  $('#selCode').innerHTML = S.codes.map(c => `<option>${c}</option>`).join('');
  if (!S.instances.some(i => i.id === S.inst)) S.inst = (S.instances.find(i => i.groupe === 'statement') || S.instances[0] || {}).id;
  if (!S.codes.includes(S.code)) S.code = S.codes.find(c => c === 'my_solution.cpp') || S.codes[0];
  si.value = S.inst;
  $('#selCode').value = S.code;
  drawList();
}

const short = n => n >= 1000 ? (n / 1000).toFixed(n % 1000 ? 1 : 0) + 'k' : String(n);
function drawList() {
  const box = $('#instList');
  box.innerHTML = '';
  for (const g of Object.keys(GROUPS)) {
    const list = S.instances.filter(i => i.groupe === g);
    if (!list.length) continue;
    box.insertAdjacentHTML('beforeend', `<div class="group">${GROUPS[g]}</div>`);
    for (const i of list) {
      const [V, E, R, Cn, X] = i.VERCX.map(Number);
      const b = document.createElement('button');
      b.className = 'inst' + (i.id === S.inst ? ' on' : '');
      b.dataset.tip = `<b>${esc(i.nom)}</b>${plural(V, 'video')}, ${plural(E, 'endpoint')}, ${plural(R, 'request line')}, ${plural(Cn, 'cache')} of ${fmt(X)} MB.`;
      b.innerHTML = `<span>${esc(i.nom)}</span><small>${short(V)} ${V === 1 ? 'video' : 'videos'}</small>`;
      b.onclick = () => pickInstance(i.id);
      box.append(b);
    }
  }
}

function pickInstance(id) {
  S.inst = id;
  $('#selInstance').value = id;
  drawList();
  stop();
  refresh();
}

function drawNet(svg, g, opt) {
  opt = opt || {};
  const W = 1000, H = 430, M = 60;
  const xs = (n, k) => n === 1 ? W / 2 : M + k * (W - 2 * M) / (n - 1);
  const xc = {}, xe = {}, ld = {}, deg = {};
  g.caches.forEach((c, k) => xc[c] = xs(g.caches.length, k));
  g.endpoints.forEach((e, k) => { xe[e.id] = xs(g.endpoints.length, k); ld[e.id] = e.ld; });
  g.liens.forEach(l => deg[l.c] = (deg[l.c] || 0) + 1);
  const yd = 50, yc = 200, ye = 360;
  const top = Math.max(1, ...Object.values(opt.servi || {}), ...Object.values(opt.dc || {}));
  let h = '';
  for (const e of g.endpoints) {
    const n = (opt.dc || {})[e.id] || 0;
    const w = opt.dc ? 1 + 6 * n / top : 1.2;
    const op = opt.dc ? (n ? 0.75 : 0.12) : 0.3;
    h += `<line x1="${W / 2}" y1="${yd}" x2="${xe[e.id]}" y2="${ye}" stroke="${C.dc}" stroke-width="${w}" stroke-opacity="${op}"/>`;
  }
  for (const l of g.liens) {
    if (xc[l.c] === undefined || xe[l.e] === undefined) continue;
    const n = (opt.servi || {})[l.e + '-' + l.c] || 0;
    const x1 = xc[l.c], y1 = yc + 16, x2 = xe[l.e], y2 = ye - 13;
    h += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${C.cache}" stroke-width="${n ? 1.5 + 6 * n / top : 1.2}" stroke-opacity="${n ? 0.9 : 0.45}" ${n ? '' : 'stroke-dasharray="4 4"'}/>`;
    h += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="transparent" stroke-width="12" data-tip="<b>Endpoint ${l.e} and cache ${l.c}</b>From this cache, a request waits ${l.lc} ms instead of ${ld[l.e]} ms. It saves ${ld[l.e] - l.lc} ms.${n ? ` Right now this cache serves ${fmt(n)} requests of this endpoint.` : ''}"/>`;
    if (g.endpoints.length <= 6) {
      const x = x1 + 0.6 * (x2 - x1), y = y1 + 0.6 * (y2 - y1);
      h += `<text x="${x}" y="${y}" font-size="11" fill="${C.cache}" text-anchor="middle" paint-order="stroke" stroke="#fff" stroke-width="4" pointer-events="none">${l.lc} ms</text>`;
    }
  }
  h += `<g data-tip="<b>Datacenter</b>It has every video, but it is the slowest place to get one."><rect x="${W / 2 - 22}" y="${yd - 22}" width="44" height="44" rx="10" fill="${C.dc}"/>`
    + `<text x="${W / 2}" y="${yd + 5}" font-size="13" font-weight="700" fill="#fff" text-anchor="middle">DC</text></g>`;
  for (const c of g.caches) {
    const x = xc[c];
    const p = opt.plein ? Math.min(1, opt.plein[c] / opt.X) : 0;
    const vids = (opt.contenu || {})[c] || [];
    const flash = opt.flash === c;
    const t = `<b>Cache ${c}</b>Used by ${plural(deg[c] || 0, 'endpoint')}.${opt.plein ? ` ${fmt(opt.plein[c])} of ${fmt(opt.X)} MB used.` : ''}${vids.length ? ' It holds ' + vids.map(v => 'v' + v).join(', ') + '.' : ''}`;
    h += `<g data-tip="${t}"><rect x="${x - 27}" y="${yc - 16}" width="54" height="32" rx="5" fill="#fff" stroke="${flash ? C.flag : C.cache}" stroke-width="${flash ? 4 : 2}"/>`;
    if (p) h += `<rect x="${x - 25}" y="${yc + 14 - 28 * p}" width="50" height="${28 * p}" fill="${C.cache}" fill-opacity="0.22"/>`;
    h += `<text x="${x}" y="${yc + 5}" font-size="13" font-weight="700" text-anchor="middle">c${c}</text></g>`;
    for (let k = 0; k * 3 < vids.length && k < 3; k++) {
      h += `<text x="${x}" y="${yc - 24 - 14 * k}" font-size="12" font-weight="700" fill="${C.video}" text-anchor="middle" paint-order="stroke" stroke="#fff" stroke-width="4" pointer-events="none">${vids.slice(k * 3, k * 3 + 3).map(v => 'v' + v).join(' ')}</text>`;
    }
  }
  for (const e of g.endpoints) {
    const k = g.liens.filter(l => l.e === e.id).length;
    h += `<g data-tip="<b>Endpoint ${e.id}</b>Waits ${e.ld} ms when a video comes from the datacenter. Connected to ${plural(k, 'cache')}."><circle cx="${xe[e.id]}" cy="${ye}" r="13" fill="${C.ep}"/>`
      + `<text x="${xe[e.id]}" y="${ye + 32}" font-size="12" font-weight="700" text-anchor="middle">e${e.id}</text>`
      + `<text x="${xe[e.id]}" y="${ye + 46}" font-size="11" fill="${C.dc}" text-anchor="middle">${e.ld} ms</text></g>`;
  }
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = h;
}

function row(key, value) {
  const [label, t] = ROWS[key] || [key, ''];
  const m = /^min (\S+) \| mean (\S+) \| median (\S+) \| max (\S+)$/.exec(value);
  let shown = /^\d+$/.test(value) ? fmt(value) : esc(value);
  let more = '';
  if (m) {
    shown = m[1] === m[4] ? fmt(m[1]) : `${fmt(m[1])} to ${fmt(m[4])} <small>avg ${fmt(Math.round(m[2]))}</small>`;
    more = `<br>Smallest ${fmt(m[1])}, average ${m[2]}, middle ${m[3]}, biggest ${fmt(m[4])}.`;
  }
  if (key === 'cache space / requested size') shown = fmt(Math.round(100 * parseFloat(value))) + '%';
  if (key === 'caches') shown = esc(value.replace(' x ', ' × '));
  return `<div data-tip="${esc('<b>' + label + '</b>' + t + more)}"><dt>${label}</dt><dd>${shown}</dd></div>`;
}

async function loadInstance() {
  if (!S.inst) return;
  const id = S.inst;
  $('#instName').textContent = id.split('/').pop().replace(/\.in$/, '');
  $('#checkMsg').textContent = '';
  const d = await api('/api/instance?' + enc({ id }));
  if (id !== S.inst) return;
  $('#instName').textContent = d.nom;
  $('#strip').innerHTML = [
    ['', d.V, 'videos', 'Number of different videos.'],
    ['', d.E, 'endpoints', 'Groups of users in one place.'],
    ['', d.R, 'request lines', 'Each line says: this endpoint asks for this video this many times.'],
    ['', d.C, 'caches', 'Number of cache servers.'],
    ['', d.X, 'MB in one cache', 'How much one cache can hold.'],
    ['bound', d.borne, 'best possible score', BEST]
  ].map(([k, v, l, t]) => `<div class="${k}" data-tip="${t}"><b>${fmt(v)}</b><span>${l}</span></div>`).join('');
  drawNet($('#svgNet'), d.graphe);
  $('#sections').innerHTML = d.sections.map((s, k) =>
    `<div><h3><i style="background:${SECTION_COLORS[k]}"></i>${SECTION_NAMES[k] || s.titre}</h3><dl>${s.lignes.map(([a, b]) => row(a, b)).join('')}</dl></div>`).join('');
  hist('chSizes', d.tailles, C.video, 'Video size (MB)', 'Number of videos', (n, l) => `${plural(n, 'video')} ${n === 1 ? 'is' : 'are'} ${l} MB`);
  chart('chSpace', {
    type: 'bar',
    data: { labels: ['Requested videos', 'All caches'], datasets: [{ data: [d.capacite.demandee, d.capacite.totale], backgroundColor: [C.video, C.cache], barPercentage: 0.7 }] },
    options: {
      indexAxis: 'y',
      scales: { x: { title: axis('Size (MB)'), beginAtZero: true, ticks: { maxTicksLimit: 5 } }, y: { grid: { display: false }, ticks: { color: C.ink2, font: { weight: '600' } } } },
      plugins: { tooltip: { callbacks: { title: () => '', label: c => c.dataIndex ? `All caches together hold ${fmt(c.raw)} MB` : `One copy of every requested video needs ${fmt(c.raw)} MB` } } }
    }
  });
  hist('chCpe', d.caches_par_endpoint, C.ep, 'Caches connected to the endpoint', 'Number of endpoints', (n, l) => `${plural(n, 'endpoint')} ${n === 1 ? 'is' : 'are'} connected to ${l} caches`);
  hist('chEpc', d.endpoints_par_cache, C.cache, 'Endpoints connected to the cache', 'Number of caches', (n, l) => `${plural(n, 'cache')} ${n === 1 ? 'is' : 'are'} used by ${l} endpoints`);
  hist('chLd', d.ld, C.dc, 'Wait from the datacenter (ms)', 'Number of endpoints', (n, l) => `${plural(n, 'endpoint')} ${s1(n, 'wait')} ${l} ms for the datacenter`);
  hist('chGain', d.gains, C.amber, 'Time saved by the cache (ms)', 'Number of connections', (n, l) => `${plural(n, 'connection')} ${s1(n, 'save')} ${l} ms per request`);
  chart('chPop', {
    type: 'scatter',
    data: { datasets: [{ data: d.popularite.map(([x, y]) => ({ x, y })), showLine: true, pointRadius: 0, pointHitRadius: 6, borderColor: C.video, borderWidth: 2 }] },
    options: {
      scales: { x: { type: 'logarithmic', title: axis('Video rank, 1 = most watched (log scale)') }, y: { type: 'logarithmic', title: axis('Requests (log scale)') } },
      plugins: { tooltip: { callbacks: { label: c => `Video number ${fmt(c.raw.x)} in the ranking gets ${fmt(c.raw.y)} requests` } } }
    }
  });
  hist('chPe', d.par_endpoint, C.ep, 'Requests sent by the endpoint', 'Number of endpoints', (n, l) => `${plural(n, 'endpoint')} ${s1(n, 'send')} ${l} requests`);
}

async function solution() {
  if (!S.inst || !S.code) return null;
  return api('/api/solution?' + enc({ code: S.code, id: S.inst }));
}
function emptyState(el, text) {
  el.innerHTML = `<p>${text}</p><button class="primary">Run it now</button>`;
  el.querySelector('button').onclick = () => run([S.inst]);
}
const NOT_RUN = 'This program has not been run on this instance yet.';

async function loadDemo() {
  stop();
  $('#demoBody').style.display = 'none';
  $('#demoEmpty').innerHTML = '<p>Loading…</p>';
  const d = await solution();
  if (!d) return;
  if (d.absent) return emptyState($('#demoEmpty'), NOT_RUN);
  if (d.erreur) return emptyState($('#demoEmpty'), 'The output file has a problem: ' + esc(d.erreur));
  $('#demoEmpty').innerHTML = '';
  $('#demoBody').style.display = '';
  S.sol = d;
  const r = d.replay, n = r.images.length;
  $('#slider').max = n - 1;
  chart('chReplay', {
    type: 'line',
    data: {
      labels: r.images.map(i => i.etape),
      datasets: [
        { label: 'Your score', data: r.images.map(i => i.score), borderColor: C.ep, backgroundColor: C.ep + '1f', fill: true, borderWidth: 2, pointRadius: 0, tension: 0.15 },
        { label: 'Now', data: new Array(n).fill(null), pointRadius: 6, pointBackgroundColor: C.ink, pointBorderColor: '#fff', pointBorderWidth: 2, showLine: false },
        { label: 'Best possible score', data: new Array(n).fill(d.borne), borderColor: C.muted, borderDash: [5, 5], borderWidth: 1.2, pointRadius: 0 }
      ]
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      scales: { x: { title: axis('Videos placed'), grid: { display: false }, ticks: { maxTicksLimit: 8 } }, y: { title: axis('Score'), beginAtZero: true, ticks: { maxTicksLimit: 5 } } },
      plugins: {
        legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 12, boxHeight: 2, filter: x => x.text !== 'Now' } },
        tooltip: { filter: c => c.datasetIndex === 0, callbacks: { title: c => `After ${fmt(c[0].label)} videos placed`, label: c => `Score: ${fmt(c.raw)}` } }
      }
    }
  });
  const rack = $('#rack');
  rack.style.setProperty('--cell', r.C > 300 ? '13px' : r.C > 100 ? '20px' : '38px');
  rack.innerHTML = Array.from({ length: r.C }, (_, c) => `<div>${r.C <= 100 ? `<span>${c}</span>` : ''}<i></i></div>`).join('');
  S.small = null;
  $('#demoSmall').style.display = 'none';
  if (r.petit) {
    const p = r.petit;
    S.small = { ...p, graph: { endpoints: p.ld.map((ld, id) => ({ id, ld })), caches: Array.from({ length: r.C }, (_, c) => c), liens: p.liens } };
    $('#demoSmall').style.display = '';
  }
  showFrame(0);
}

function showFrame(k) {
  const r = S.sol.replay, f = r.images[k];
  S.frame = k;
  $('#slider').value = k;
  $('#stepCount').textContent = `${fmt(f.etape)} of ${fmt(r.total)} videos placed`;
  $('#rScore').textContent = fmt(f.score);
  $('#rWait').textContent = fmt(Math.round(r.lat_moyenne_dc - f.score / 1000));
  $('#rPct').textContent = S.sol.borne ? pct(pc(f.score, S.sol.borne)) : '–';
  const ch = S.charts.chReplay;
  if (ch) { ch.data.datasets[1].data = r.images.map((x, j) => j === k ? x.score : null); ch.update('none'); }
  const cells = $('#rack').children;
  for (let c = 0; c < cells.length; c++) {
    const p = Math.min(1, f.plein[c] / r.X);
    const bar = cells[c].querySelector('i');
    bar.style.height = (100 * p) + '%';
    bar.style.opacity = 0.35 + 0.65 * p;
    cells[c].classList.toggle('flash', !!f.evt && f.evt.cache === c);
    cells[c].dataset.tip = `<b>Cache ${c}</b>${fmt(f.plein[c])} of ${fmt(r.X)} MB used (${Math.round(100 * p)}% full).`;
  }
  const evts = r.images.slice(1, k + 1).filter(x => x.evt).slice(-6).reverse();
  $('#journal').innerHTML = evts.length ? evts.map(x =>
    `<li>Put <b class="v">v${x.evt.video}</b> (${x.evt.taille} MB) in <b class="c">cache ${x.evt.cache}</b>: ${x.evt.gain ? 'users save ' + fmt(x.evt.gain) + ' ms in total' : 'nobody uses this copy'}</li>`).join('')
    : '<li>No video placed yet. Every request comes from the datacenter.</li>';
  if (S.small) smallFrame(f);
}

function smallFrame(f) {
  const p = S.small, content = {};
  p.ordre.slice(0, f.etape).forEach(([c, v]) => (content[c] = content[c] || []).push(v));
  const servi = {}, dc = {};
  const rows = p.requetes.map(([v, e, n]) => {
    let best = p.ld[e], src = null;
    for (const l of p.liens) if (l.e === e && (content[l.c] || []).includes(v) && l.lc < best) { best = l.lc; src = l.c; }
    if (src === null) dc[e] = (dc[e] || 0) + n; else servi[e + '-' + src] = (servi[e + '-' + src] || 0) + n;
    return { v, e, n, src, best, gain: p.ld[e] - best };
  });
  drawNet($('#svgDemo'), p.graph, { contenu: content, servi, dc, plein: f.plein, X: S.sol.replay.X, flash: f.evt ? f.evt.cache : null });
  $('#reqTable').innerHTML = '<thead><tr><th>Video</th><th>Endpoint</th><th class="n">Requests</th><th>Comes from</th><th class="n">Wait</th><th class="n">Time saved per request</th></tr></thead><tbody>' +
    rows.map(l => `<tr><td>v${l.v} <span style="color:${C.muted}">${p.taille[l.v]} MB</span></td><td>e${l.e}</td><td class="n">${fmt(l.n)}</td>
      <td style="color:${l.src === null ? C.dc : C.cache}">${l.src === null ? 'datacenter' : 'cache ' + l.src}</td><td class="n">${l.best} ms</td><td class="n">${l.gain} ms</td></tr>`).join('') + '</tbody>';
}

function stop() {
  clearInterval(S.timer);
  S.timer = null;
  $('#btnPlay').textContent = 'Play';
}
function play() {
  if (S.timer) return stop();
  const r = S.sol.replay;
  if (S.frame >= r.images.length - 1) showFrame(0);
  $('#btnPlay').textContent = 'Pause';
  S.timer = setInterval(() => {
    if (S.frame >= r.images.length - 1) return stop();
    showFrame(S.frame + 1);
  }, 1000 / Number($('#selSpeed').value));
}

function stack(parts, cls) {
  const tot = parts.reduce((t, p) => t + p.v, 0) || 1;
  return `<div class="stack ${cls || ''}">${parts.map(p => p.v ? `<span style="width:${100 * p.v / tot}%;background:${p.c}" data-tip="<b>${p.l}</b>${p.t}"></span>` : '').join('')}</div>`;
}
function legend(parts) {
  const tot = parts.reduce((t, p) => t + p.v, 0) || 1;
  return `<div class="legend">${parts.filter(p => p.v).map(p => `<div data-tip="${p.t}"><i style="background:${p.c}"></i><b>${p.f ? p.f(p.v) : pct(100 * p.v / tot)}</b><span>${p.l}</span></div>`).join('')}</div>`;
}
function verdict(p) {
  if (p >= 99) return ['l5', 'Solved'];
  if (p >= 85) return ['l4', 'Very good'];
  if (p >= 60) return ['l3', 'Good'];
  if (p >= 30) return ['l2', 'Weak'];
  return ['l1', 'Very weak'];
}

async function loadStats() {
  loadCompare();
  $('#statsBody').style.display = 'none';
  $('#statsEmpty').innerHTML = '<p>Reading the solution…</p>';
  const inst = S.inst, code = S.code;
  const d = await solution();
  if (!d || inst !== S.inst || code !== S.code) return;
  if (d.absent) return emptyState($('#statsEmpty'), NOT_RUN);
  if (d.erreur) return emptyState($('#statsEmpty'), 'The output file has a problem: ' + esc(d.erreur));
  $('#statsEmpty').innerHTML = '';
  $('#statsBody').style.display = '';
  const B = d.bilan;
  const share = pc(d.score, d.borne);
  $('#repTitle').textContent = d.nom;
  $('#repSub').textContent = d.valide ? `Result of ${S.code}` : 'This solution breaks the rules: ' + d.erreurs.join('; ');
  const [lvl, word] = d.borne ? verdict(share) : ['l5', 'Nothing to gain'];
  $('#repChip').className = 'chip ' + lvl;
  $('#repChip').textContent = word;
  $('#repChip').dataset.tip = d.borne ? `You have ${pct(share)} of the best possible score.` : 'No cache can help on this instance, so every solution scores 0.';

  const lost = B.perdu.absent + B.perdu.lent;
  const why = B.perdu.absent >= B.perdu.lent
    ? 'Most points are lost because many videos are not in any cache near the users who watch them.'
    : 'Most points are lost because many videos are in a cache, but not in the fastest one.';
  const scoreParts = [
    { v: d.score, c: K.good, l: 'your score', t: 'Points you already have.', f: fmt },
    { v: B.perdu.absent, c: K.fix, l: 'lost: video in no nearby cache', t: 'The user has caches, but none of them holds the video, so it comes from the datacenter.', f: fmt },
    { v: B.perdu.lent, c: K.fix2, l: 'lost: video in a slower cache', t: 'The video is in a cache near the user, but a faster cache near the user does not have it.', f: fmt }
  ];
  $('#qScore').innerHTML = `
    <div><h2>How good is your score?</h2>
    <p>${d.borne ? `Your score is <b>${fmt(d.score)}</b>. The best possible score is <b>${fmt(d.borne)}</b>. You have <b>${pct(share)}</b> of it.
      ${lost ? why : 'You lose no points.'}` : 'No cache can help on this instance. Every solution scores 0.'}</p></div>
    <div class="vis">${stack(scoreParts)}<div class="ends"><span>0</span><span data-tip="${BEST}">best possible: ${fmt(d.borne)}</span></div>${legend(scoreParts)}</div>`;

  const E = B.espace, totalSpace = E.utile + E.inutile + E.vide;
  const spaceParts = [
    { v: E.utile, c: K.good, l: 'useful videos', t: 'Videos that some users get from this cache.' },
    { v: E.inutile, c: K.fix, l: 'wasted copies', t: 'Nobody gets the video from this copy, because a faster cache near them has the same video.' },
    { v: E.vide, c: K.none, l: 'empty', t: 'Free space. It is usually too small for any video that is still missing.' }
  ];
  const wasteP = pc(E.inutile, totalSpace), emptyP = pc(E.vide, totalSpace);
  const spaceText = wasteP >= 5
    ? `<b>${pct(wasteP)}</b> of the cache space is wasted. It holds copies that no user needs. Remove them and put other videos there.`
    : emptyP >= 10 ? `<b>${pct(emptyP)}</b> of the cache space is empty. You may be able to add more videos.`
    : `The caches are well used. <b>${pct(pc(E.utile, totalSpace))}</b> of the space holds videos that users need.`;
  const cell = d.C > 300 ? '9px' : d.C > 100 ? '13px' : '22px';
  const cells = E.par_cache.map(([u, w], c) => `<div data-tip="<b>Cache ${c}</b>${fmt(u)} MB useful, ${fmt(w)} MB wasted, ${fmt(d.X - u - w)} MB empty."><i style="height:${pc(u, d.X)}%;background:${K.good}"></i><i style="height:${pc(w, d.X)}%;background:${K.fix}"></i></div>`).join('');
  $('#qSpace').innerHTML = `
    <div><h2>How are the caches used?</h2><p>${spaceText}</p></div>
    <div class="vis">${stack(spaceParts)}${legend(spaceParts)}<p class="cells-title">Each cache, one square:</p><div class="cells${d.C > 100 ? ' many' : ''}" style="--cell:${cell}">${cells}</div></div>`;

  const Q = B.requetes, totalReq = Q.cache + Q.dc_possible + Q.dc_impossible;
  const reqParts = [
    { v: Q.cache, c: K.good, l: 'served by a cache', t: 'These requests get the video from a cache.' },
    { v: Q.dc_possible, c: K.fix, l: 'served by the datacenter, but a cache could do it', t: 'The user has a cache and the video fits in it, but the video was not put there.' },
    { v: Q.dc_impossible, c: K.none, l: 'served by the datacenter, no cache can help', t: 'The user has no cache, or the video is too big for a cache.' }
  ];
  const faster = pc(d.lat_avant - d.lat_apres, d.lat_avant);
  $('#qWait').innerHTML = `
    <div><h2>How long do users wait?</h2>
    <p>Without caches, a request waits <b>${fmt(Math.round(d.lat_avant))}&nbsp;ms</b> on average. With your caches, it waits <b>${fmt(Math.round(d.lat_apres))}&nbsp;ms</b>. That is <b>${pct(faster)}</b> faster.</p></div>
    <div class="vis">
      <div class="rows">
        <div class="hrow big" data-tip="Average wait if every video came from the datacenter."><span class="name">Without caches</span><div class="track"><i style="width:100%;background:${C.dc}"></i></div><span class="val">${fmt(Math.round(d.lat_avant))} ms</span></div>
        <div class="hrow big" data-tip="Average wait with your solution."><span class="name">With your caches</span><div class="track"><i style="width:${pc(d.lat_apres, d.lat_avant)}%;background:${K.good}"></i></div><span class="val">${fmt(Math.round(d.lat_apres))} ms</span></div>
      </div>
      <p class="cells-title">Where the requests are served from:</p>
      ${stack(reqParts, 'thin')}${legend(reqParts)}
    </div>`;

  const worst = B.pires;
  $('#qFix').innerHTML = `
    <div><h2>What should you fix first?</h2>
    <p>${worst.length ? 'These videos lose the most points. Put each one in the cache shown. If the cache is full, remove a wasted copy first.' : 'Nothing. Every request already gets its video from the fastest place it can.'}</p></div>
    <div class="vis"><div class="fixes">${worst.map(w => `
      <div class="fixrow">
        <div class="what">Put <span class="tag-v">v${w.v}</span> in <span class="tag-c">cache ${w.cache}</span>
          <small>Endpoint ${w.e} asks for it ${fmt(w.n)} times. Now it waits ${fmt(w.obtenu)} ms. From cache ${w.cache} it would wait ${fmt(w.possible)} ms.</small></div>
        <div class="cost"><b>+${fmt(w.perte)}</b><span>points</span></div>
      </div>`).join('')}</div></div>`;

  const maxG = Math.max(1, ...B.top.map(t => t.gain));
  $('#qTop').innerHTML = `
    <div><h2>Which videos give you the most points?</h2>
    <p>${B.top.length ? `These ${B.top.length} copies give <b>${pct(B.part_top)}</b> of your score.` : 'No video in your caches saves any time yet.'}</p></div>
    <div class="vis"><div class="rows">${B.top.map(t => `
      <div class="hrow" data-tip="Video ${t.v} (${t.taille} MB) in cache ${t.c} gives you ${fmt(t.gain)} points.">
        <span class="name"><span class="tag-v">v${t.v}</span> in <span class="tag-c">cache ${t.c}</span></span>
        <div class="track"><i style="width:${pc(t.gain, maxG)}%;background:${K.good}"></i></div><span class="val">${fmt(t.gain)} pts</span></div>`).join('')}</div></div>`;
}

async function loadCompare() {
  const scores = await api('/api/scores');
  const last = {}, best = {};
  for (const s of scores) {
    if (s.code === S.code) last[s.instance] = s;
    if (s.valide && (!best[s.instance] || s.score > best[s.instance].score)) best[s.instance] = s;
  }
  const rows = S.instances.filter(i => last[i.id]);
  if (!rows.length) {
    $('#compareTable').innerHTML = `<tbody><tr><td>${esc(S.code)} has not been run yet. Click "Run on all instances" in the Code tab.</td></tr></tbody>`;
    return;
  }
  let total = 0;
  $('#compareTable').innerHTML = '<thead><tr><th>Instance</th><th class="n">Your score</th><th class="n">Best possible</th><th>How close</th><th data-tip="The best score any of your programs got on this instance.">Your best ever</th><th class="n">Run time</th></tr></thead><tbody>' +
    rows.map(i => {
      const s = last[i.id], b = best[i.id];
      total += s.valide ? s.score : 0;
      const p = pc(s.score, s.borne);
      const col = p >= 90 ? C.ep : p >= 50 ? C.amber : C.cache;
      return `<tr><td>${esc(i.nom)}</td><td class="n">${s.valide ? fmt(s.score) : 'breaks the rules'}</td><td class="n">${fmt(s.borne)}</td>
        <td><div class="pct"><div class="bar"><i style="width:${Math.min(100, p)}%;background:${col}"></i></div>${s.borne ? pct(p) : '–'}</div></td>
        <td data-tip="${b ? 'Got by ' + esc(b.code) + ' on ' + esc(b.date) : ''}">${b ? fmt(b.score) : ''}</td><td class="n">${s.temps} s</td></tr>`;
    }).join('') + `</tbody><tfoot><tr><td>Total</td><td class="n">${fmt(total)}</td><td colspan="4"></td></tr></tfoot>`;
}

function initEditor() {
  const ta = $('#codeArea');
  if (window.CodeMirror) {
    S.editor = CodeMirror.fromTextArea(ta, { lineNumbers: true, indentUnit: 4, mode: 'text/x-c++src' });
    S.editor.on('change', () => S.dirty = true);
  } else {
    S.editor = { getValue: () => ta.value, setValue: v => ta.value = v, setOption: () => 0, refresh: () => 0 };
    ta.addEventListener('input', () => S.dirty = true);
  }
}
async function loadCode() {
  if (!S.code) return;
  const d = await api('/api/code?' + enc({ chemin: S.code }));
  S.editor.setOption('mode', S.code.endsWith('.py') ? 'python' : 'text/x-c++src');
  S.editor.setValue(d.contenu);
  S.dirty = false;
  $('#codeName').textContent = S.code;
  setTimeout(() => S.editor.refresh(), 0);
}
function say(sel, text, ok) {
  const el = $(sel);
  el.textContent = text;
  el.className = 'msg ' + (ok ? 'ok' : 'ko');
}
async function save() {
  const d = await post('/api/code', { chemin: S.code, contenu: S.editor.getValue() });
  if (d.erreur) return say('#codeMsg', d.erreur, false);
  S.dirty = false;
  say('#codeMsg', 'Saved.', true);
}
async function saveAs() {
  const name = prompt('Name of the new version, without .cpp or .py');
  if (!name) return;
  const ext = S.code.endsWith('.py') ? '.py' : '.cpp';
  const d = await post('/api/code', { chemin: 'versions/' + name + ext, contenu: S.editor.getValue(), nouveau: true });
  if (d.erreur) return say('#codeMsg', d.erreur, false);
  S.code = d.chemin;
  await loadLists();
  S.dirty = false;
  $('#codeName').textContent = S.code;
  say('#codeMsg', 'Saved as ' + d.chemin, true);
}

async function run(list) {
  if (S.dirty) await save();
  const before = {};
  (await api('/api/scores')).filter(s => s.code === S.code && s.valide).forEach(s => before[s.instance] = Math.max(before[s.instance] || 0, s.score));
  const buttons = document.querySelectorAll('#btnRun, #btnRunOne, #btnRunAll');
  buttons.forEach(b => b.disabled = true);
  const code = S.code;
  const { job } = await post('/api/lancer', { code, instances: list });
  $('#console').textContent = '';
  const poll = async () => {
    const j = await api('/api/job/' + job);
    const out = $('#console');
    const atEnd = out.scrollTop + out.clientHeight >= out.scrollHeight - 20;
    out.textContent = j.log;
    if (atEnd) out.scrollTop = out.scrollHeight;
    $('#jobState').textContent = j.statut === 'running' ? `Running: ${j.resultats.length} of ${j.total} done` : j.statut === 'done' ? 'Finished' : 'Error: see the Code tab';
    $('#runTitle').hidden = !j.resultats.length;
    $('#resultsTable').innerHTML = j.resultats.length ? '<thead><tr><th>Instance</th><th class="n">Score</th><th class="n">Best possible</th><th class="n">How close</th><th class="n">Run time</th><th class="n">Compared with your best</th></tr></thead><tbody>' +
      j.resultats.map(r => {
        const a = before[r.instance], diff = a === undefined ? null : r.score - a;
        return `<tr><td>${esc(r.nom)}</td><td class="n" ${r.valide ? '' : `data-tip="${esc(r.erreurs.join('; '))}"`}>${r.valide ? fmt(r.score) : 'breaks the rules'}</td><td class="n">${fmt(r.borne)}</td>
          <td class="n">${r.borne ? pct(pc(r.score, r.borne)) : '–'}</td><td class="n">${r.temps} s</td>
          <td class="n ${diff > 0 ? 'up' : diff < 0 ? 'down' : ''}">${diff === null ? 'first run' : diff === 0 ? 'same' : (diff > 0 ? '+' : '') + fmt(diff)}</td></tr>`;
      }).join('') + '</tbody>' : '';
    if (j.statut === 'running') return setTimeout(poll, 700);
    buttons.forEach(b => b.disabled = false);
    setTimeout(() => { if ($('#jobState').textContent === 'Finished') $('#jobState').textContent = ''; }, 4000);
    refresh();
  };
  poll();
}

async function generate(ev) {
  ev.preventDefault();
  const data = Object.fromEntries(new FormData(ev.target));
  say('#genMsg', 'Making the file…', true);
  try {
    const d = await post('/api/generer', data);
    if (d.erreur) return say('#genMsg', d.erreur, false);
    await loadLists();
    pickInstance(d.id);
    say('#genMsg', 'Saved as ' + d.id.split('/').pop(), true);
  } catch (e) {
    say('#genMsg', 'It did not work. Check the numbers.', false);
  }
}
async function check() {
  const d = await api('/api/valider?' + enc({ id: S.inst }));
  const lines = [d.erreurs.length ? 'This file breaks the rules:' : 'This file follows all the rules.'].concat(d.erreurs, d.avertissements.map(a => 'Note: ' + a + '.'));
  say('#checkMsg', lines.join('\n'), !d.erreurs.length);
}
function updateForm() {
  const t = $('#genType').value;
  $('#typeText').textContent = TYPES[t];
  document.querySelectorAll('#genForm [data-for]').forEach(l => l.hidden = !l.dataset.for.split(' ').includes(t));
  $('#genVariant').closest('label').dataset.tip = VARIANTS[$('#genVariant').value];
}

document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => setTab(b.dataset.tab));
$('#selInstance').onchange = e => pickInstance(e.target.value);
$('#selCode').onchange = e => { S.code = e.target.value; loadCode(); refresh(); };
$('#btnRun').onclick = () => run([S.inst]);
$('#btnRunOne').onclick = () => run([S.inst]);
$('#btnRunAll').onclick = () => run('all');
$('#btnSave').onclick = save;
$('#btnSaveAs').onclick = saveAs;
$('#btnCheck').onclick = check;
$('#genForm').onsubmit = generate;
$('#genType').onchange = updateForm;
$('#genVariant').onchange = updateForm;
$('#btnPlay').onclick = play;
$('#btnStart').onclick = () => { stop(); showFrame(0); };
$('#slider').oninput = e => { stop(); showFrame(Number(e.target.value)); };

(async () => {
  initEditor();
  updateForm();
  await loadLists();
  await loadCode();
  refresh();
})();
