const $ = s => document.querySelector(s);
const meanings = {
  safe: 'The mail server accepted this exact mailbox. It exists and can receive mail.',
  risky: 'The address probably works but cannot be fully confirmed (catch-all, full inbox, disposable or role account).',
  invalid: 'The mailbox or domain does not accept mail. Spoofed or invented sender.',
  unknown: 'The mail server did not give a clear answer, or port 25 is blocked from here.'
};
function fact(label, value) {
  const d = document.createElement('div'); d.className = 'fact';
  const b = document.createElement('b'); b.textContent = label;
  d.append(b, document.createTextNode(value === undefined || value === null ? '—' : String(value)));
  return d;
}
async function run() {
  const email = $('#email').value.trim();
  if (!email) { $('#email').focus(); return; }
  $('#go').disabled = true; $('#result').hidden = true;
  $('#state').textContent = `Checking ${email}…`;
  try {
    const r = await fetch('/api/email-check', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email}), signal: AbortSignal.timeout(160000)});
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
    const v = data.is_reachable || 'unknown';
    $('#verdict').className = `verdict ${v}`; $('#verdict').textContent = `${email} — ${v.toUpperCase()}`;
    $('#meaning').textContent = meanings[v] || '';
    const f = $('#facts'); f.replaceChildren(
      fact('Valid syntax', data.syntax?.is_valid_syntax),
      fact('Domain accepts mail (MX)', data.mx?.accepts_mail),
      fact('SMTP reachable', data.smtp?.can_connect_smtp),
      fact('Mailbox deliverable', data.smtp?.is_deliverable),
      fact('Catch-all domain', data.smtp?.is_catch_all),
      fact('Mailbox disabled', data.smtp?.is_disabled),
      fact('Inbox full', data.smtp?.has_full_inbox),
      fact('Disposable provider', data.misc?.is_disposable),
      fact('Role account', data.misc?.is_role_account),
      fact('MX records', (data.mx?.records || []).join(', ') || '—')
    );
    $('#raw').textContent = JSON.stringify(data, null, 2);
    $('#result').hidden = false; $('#state').textContent = 'Done.';
  } catch (e) {
    $('#state').textContent = `Check failed: ${e.message}`;
  } finally { $('#go').disabled = false; }
}
$('#go').addEventListener('click', run);
$('#email').addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
