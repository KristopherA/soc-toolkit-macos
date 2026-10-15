const icons = {
  graph: '<circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" r="2.5"/><circle cx="12" cy="19" r="2.5"/><path d="M7.3 7.2 10.6 17M16.7 7.2 13.4 17M7.5 6h9"/>',
  phone: '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>',
  radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12 19 5"/>',
  hook: '<path d="M14 3v11a4 4 0 0 1-8 0v-2l3 2"/><path d="M14 3h4"/>',
  mailcheck: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/><path d="m15 17 2 2 4-4"/>',
  memory: '<rect x="3" y="7" width="18" height="10" rx="1"/><path d="M7 7V4M11 7V4M15 7V4M19 7V4M7 20v-3M11 20v-3M15 20v-3M7 11h4v2H7z"/>',
  binary: '<path d="M6 4v6M9 4h1v6M14 4h3v6h-3zM6 14h3v6H6zM14 14v6M17 14h1v6"/>',
  lookup: '<circle cx="11" cy="11" r="7"/><path d="m21 21-5-5M8 11h6M11 8v6"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  dns: '<rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 7h.01M7 17h.01"/>',
  bug: '<rect x="8" y="7" width="8" height="13" rx="4"/><path d="M12 7V4M9 4l1 3M15 4l-1 3M8 11H4M8 16H4M16 11h4M16 16h4"/>',
  list: '<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>',
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
  book: '<path d="M4 4h6a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4zM20 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z"/>',
  home: '<path d="M3 11 12 4l9 7M5 10v10h14V10"/>'
};
let services = [], category = 'All', states = {}, lastCheck = null, fetching = false;
let recent = null;
try { recent = localStorage.getItem('soc.lastOpened'); } catch (_) {}
const $ = selector => document.querySelector(selector);
const kind = s => s.cli ? 'CLI' : s.external ? 'External' : 'Web';
const statusText = s => ({ready:'Responding', attention:'Needs attention', unavailable:'Unavailable'})[s?.state] || 'Checking';

async function copyText(text, button, label) {
  try { await navigator.clipboard.writeText(text); button.firstChild.textContent = 'Copied'; }
  catch (_) { button.firstChild.textContent = 'Select the command to copy'; }
  setTimeout(() => { button.firstChild.textContent = label; }, 2200);
}

function matches(s, query) {
  const inCategory = category === 'All' || s.category === category || kind(s) === category;
  return inCategory && `${s.name} ${s.description} ${s.category} ${s.command || ''}`.toLowerCase().includes(query);
}

function render() {
  const query = $('#search').value.trim().toLowerCase();
  const visible = services.filter(s => matches(s, query));
  const container = $('#tools');
  container.replaceChildren();
  for (const service of visible) {
    const card = document.createElement('article');
    card.className = `card${service.external ? ' external' : ''}${service.cli ? ' cli' : ''}${recent === service.id ? ' recent' : ''}`;
    card.dataset.service = service.id;
    const top = document.createElement('div'); top.className = 'card-top';
    const icon = document.createElement('span'); icon.className = 'tool-icon'; icon.setAttribute('aria-hidden','true');
    icon.innerHTML = `<svg viewBox="0 0 24 24">${icons[service.icon] || icons.list}</svg>`;
    const number = document.createElement('span'); number.className = 'tool-number'; number.textContent = String(services.indexOf(service) + 1).padStart(2, '0');
    top.append(icon, number);
    const heading = document.createElement('h3'); heading.textContent = service.name;
    const description = document.createElement('p'); description.textContent = service.description;
    const meta = document.createElement('div'); meta.className = 'card-meta';
    const label = document.createElement('span'); label.className = 'category-label'; label.textContent = service.category;
    const status = document.createElement('span');
    if (service.external) { status.className = 'status external'; status.textContent = 'External site'; status.title = 'Third-party website; not monitored.'; }
    else if (service.cli) { status.className = 'status ondemand'; status.textContent = 'On demand'; status.title = 'Runs in a throwaway container with ./soc'; }
    else { status.className = `status ${states[service.id]?.state || ''}`; status.textContent = statusText(states[service.id]); }
    meta.append(label, status);
    card.append(top, heading, description);
    if (service.cli) {
      const example = document.createElement('code'); example.className = 'example'; example.textContent = service.command;
      const button = document.createElement('button'); button.type = 'button'; button.className = 'card-cmd';
      const text = document.createElement('span'); text.textContent = 'Copy command';
      const small = document.createElement('small'); small.textContent = './soc'; text.append(small);
      const glyph = document.createElement('span'); glyph.textContent = '⧉'; glyph.setAttribute('aria-hidden', 'true');
      button.append(text, glyph);
      button.setAttribute('aria-label', `Copy the ${service.name} example command`);
      button.addEventListener('click', () => copyText(service.command, text, 'Copy command'));
      card.append(example, meta, button);
    } else {
      const link = document.createElement('a'); link.className = 'card-link'; link.href = service.url;
      link.target = service.external ? '_blank' : 'soc-service';
      if (service.external) link.rel = 'noopener noreferrer';
      link.setAttribute('aria-label', service.external ? `Open ${service.name} website in a new tab` : `Open ${service.name} in service tab`);
      const linkText = document.createElement('span'); linkText.textContent = service.external ? 'Open site' : 'Open tool';
      const port = document.createElement('small'); port.textContent = service.external ? new URL(service.url).host.replace(/^(www|app|viz)\./, '') : `:${service.port}`; linkText.append(port);
      const arrow = document.createElement('span'); arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true'); link.append(linkText, arrow);
      link.addEventListener('click', () => {
        recent = service.id;
        try { localStorage.setItem('soc.lastOpened', recent); } catch (_) {}
        document.querySelectorAll('.card.recent').forEach(c => c.classList.remove('recent'));
        card.classList.add('recent');
      });
      card.append(meta, link);
    }
    container.append(card);
  }
  $('#empty').hidden = visible.length > 0;
  $('#result-count').textContent = `${visible.length} ${visible.length === 1 ? 'tool' : 'tools'}`;
  const active = document.querySelector('[data-category].active span');
  $('#category-title').textContent = active ? active.textContent : 'All tools';
  $('#tools').setAttribute('aria-busy','false');
  updateAvailability();
}

function updateAvailability() {
  document.querySelectorAll('.card:not(.external):not(.cli)').forEach(card => {
    const state = states[card.dataset.service];
    const status = card.querySelector('.status');
    status.className = `status ${state?.state || ''}`;
    status.textContent = statusText(state);
    status.title = state?.httpCode ? `HTTP ${state.httpCode} · ${state.latencyMs} ms` : 'Waiting for an HTTP response';
  });
  const web = services.filter(s => kind(s) === 'Web');
  const count = web.filter(s => states[s.id]?.state === 'ready').length;
  $('#ready-count').replaceChildren(document.createTextNode(lastCheck ? String(count) : '—'));
  const total = document.createElement('span'); total.textContent = ` / ${web.length || 5}`; $('#ready-count').append(total);
  $('#summary-label').textContent = lastCheck ? 'Web tools responding' : 'Checking availability';
  $('#last-check').textContent = lastCheck ? `CHECKED ${new Date(lastCheck * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'})}` : 'Waiting for first check';
}

async function refresh() {
  if (fetching) return;
  fetching = true; $('#refresh').disabled = true;
  try {
    const response = await fetch('/api/status', {cache:'no-store', signal:AbortSignal.timeout(6000)});
    if (!response.ok) throw new Error('Status unavailable');
    const data = await response.json(); states = data.services; lastCheck = data.checkedAt;
    $('#notice').hidden = true; updateAvailability();
  } catch (_) {
    states = {}; lastCheck = null; updateAvailability();
    $('#notice').textContent = 'Availability checks are temporarily unreachable. You can still open your tools.'; $('#notice').hidden = false;
  } finally { fetching = false; $('#refresh').disabled = false; }
}

function updateCounts() {
  document.querySelectorAll('[data-category]').forEach(button => {
    const name = button.dataset.category;
    const count = name === 'All' ? services.length : services.filter(s => s.category === name || kind(s) === name).length;
    const badge = button.querySelector('.nav-count');
    if (badge) badge.textContent = String(count);
    button.hidden = count === 0;
  });
  const counts = {Web: 0, CLI: 0, External: 0};
  services.forEach(s => counts[kind(s)]++);
  $('.subtitle').textContent = `${counts.Web} web tools, ${counts.CLI} command-line tools and ${counts.External} lookups. One place to start.`;
}

$('#categories').addEventListener('click', event => {
  const button = event.target.closest('[data-category]'); if (!button) return;
  category = button.dataset.category;
  document.querySelectorAll('[data-category]').forEach(b => { const on = b === button; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
  render();
});
$('#search').addEventListener('input', render);
$('#refresh').addEventListener('click', refresh);
document.addEventListener('keydown', event => {
  if (event.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) { event.preventDefault(); $('#search').focus(); }
  if (event.key === 'Escape' && document.activeElement === $('#search')) { $('#search').value = ''; render(); }
});
$('#copy-command').addEventListener('click', async () => {
  const b = $('#copy-command');
  try { await navigator.clipboard.writeText('docker compose --profile cli --profile ghidra build'); b.textContent = 'Copied'; }
  catch (_) { b.textContent = 'Select command to copy'; }
  setTimeout(() => { b.textContent = 'Copy'; }, 2500);
});

async function init() {
  try {
    const response = await fetch('/api/services', {signal:AbortSignal.timeout(6000)});
    if (!response.ok) throw new Error('Catalog unavailable');
    services = await response.json(); updateCounts(); render(); await refresh();
    setInterval(() => { if (!document.hidden) refresh(); }, 15000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  } catch (_) {
    $('#tools').setAttribute('aria-busy','false');
    $('#notice').textContent = 'The tool list could not load. Refresh this page after the dashboard has started.'; $('#notice').hidden = false;
  }
}
init();
