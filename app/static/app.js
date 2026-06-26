const API = '/api';

// ─── Tab Switching ───────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.remove('active');
      c.style.animation = 'none';
      void c.offsetWidth;
    });
    tab.classList.add('active');
    const content = document.getElementById('tab-' + tab.dataset.tab);
    content.classList.add('active');
    content.style.animation = 'fadeIn 0.45s cubic-bezier(0.34, 1.56, 0.64, 1)';
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    document.querySelector(`.nav-links a[href="#${tab.dataset.tab}"]`)?.classList.add('active');
  });
});

document.querySelectorAll('.nav-links a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    const tab = document.querySelector(`.tab[data-tab="${a.getAttribute('href').slice(1)}"]`);
    if (tab) tab.click();
  });
});

// ─── Dropzone Setup ──────────────────────────────────────────
function setupDropzone(dzId, inputId) {
  const dz = document.getElementById(dzId);
  const input = document.getElementById(inputId);
  if (!dz || !input) return;
  dz.addEventListener('click', () => input.click());
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event('change'));
    }
  });
  dz.addEventListener('mousemove', e => {
    const rect = dz.getBoundingClientRect();
    dz.style.setProperty('--mouse-x', ((e.clientX - rect.left) / rect.width * 100) + '%');
    dz.style.setProperty('--mouse-y', ((e.clientY - rect.top) / rect.height * 100) + '%');
  });
}

setupDropzone('dropzone-analyze', 'file-input-analyze');
setupDropzone('dropzone-match', 'file-input-match');
setupDropzone('dropzone-batch', 'file-input-batch');

// ─── File Helpers ────────────────────────────────────────────
function getFile(inputId) {
  const input = document.getElementById(inputId);
  return input?.files?.[0] || null;
}

function validFile(file) {
  if (!file) return false;
  if (!file.name.match(/\.(pdf|docx|txt)$/i)) { alert('Please upload a PDF, DOCX, or TXT file.'); return false; }
  if (file.size > 10 * 1024 * 1024) { alert('File size exceeds 10MB limit.'); return false; }
  return true;
}

// ─── Spinner ─────────────────────────────────────────────────
function showSpinner(msg) {
  document.querySelector('#spinner p').textContent = msg || 'Working...';
  document.getElementById('spinner').hidden = false;
}
function hideSpinner() {
  document.getElementById('spinner').hidden = true;
}

// ─── Analyze Tab ─────────────────────────────────────────────
document.getElementById('file-input-analyze')?.addEventListener('change', async () => {
  const file = getFile('file-input-analyze');
  if (!validFile(file)) return;
  const fd = new FormData();
  fd.append('resume', file);
  showSpinner('Uploading resume...');
  try {
    const up = await fetch(API + '/upload', { method: 'POST', body: fd });
    const ud = await up.json();
    if (!ud.text) throw new Error(ud.error || 'Upload failed');
    showSpinner('Running AI analysis...');
    const ar = await fetch(API + '/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resumeText: ud.text, resumeName: file.name })
    });
    const ad = await ar.json();
    if (ad.ats_score === undefined) throw new Error(ad.error || 'Analysis failed');
    showResults(ad, file.name);
    saveToHistory(ad);
  } catch (err) {
    alert('Error: ' + err.message);
  }
  hideSpinner();
});

// ─── Render Results ──────────────────────────────────────────
function showResults(data, filename) {
  const el = document.getElementById('results-analyze');
  el.hidden = false;
  document.getElementById('result-filename').textContent = filename || data.resume_name || 'Analysis Result';

  const sc = Math.round(data.ats_score);
  const circumference = 339.292;
  const offset = circumference - (circumference * sc / 100);

  const ring = document.getElementById('score-ring');
  const text = document.getElementById('score-text');
  if (ring) {
    const grad = document.querySelector('#score-ring use') ? null : null;
    const svg = ring.closest('svg');
    const stops = svg?.querySelectorAll('stop');
    if (stops) {
      if (sc >= 70) { stops[0].setAttribute('stop-color', '#00cec9'); stops[1].setAttribute('stop-color', '#55efc4'); }
      else if (sc >= 40) { stops[0].setAttribute('stop-color', '#fdcb6e'); stops[1].setAttribute('stop-color', '#ffeaa7'); }
      else { stops[0].setAttribute('stop-color', '#e17055'); stops[1].setAttribute('stop-color', '#fab1a0'); }
    }
    ring.style.stroke = sc >= 70 ? 'var(--green)' : sc >= 40 ? 'var(--yellow)' : 'var(--red)';
    setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
  }
  if (text) text.textContent = sc;

  // Breakdown
  const bd = document.getElementById('breakdown');
  if (bd && data.breakdown) {
    bd.innerHTML = Object.entries(data.breakdown).map(([k, v]) => {
      const pct = Math.round(v);
      const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)';
      return `<div class="breakdown-item">
        <div class="value" style="color:${color}">${pct}%</div>
        <div class="label">${k.replace(/_/g, ' ')}</div>
      </div>`;
    }).join('');
  }

  // Suggestions
  const sg = document.getElementById('suggestions');
  if (sg && data.suggestions?.length) {
    sg.innerHTML = `<h4>Suggestions</h4><ul>${data.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>`;
    sg.hidden = false;
  } else if (sg) {
    sg.hidden = true;
  }

  // Skills
  const sl = document.getElementById('skills-list');
  if (sl && data.skills?.length) {
    sl.innerHTML = data.skills.map(s => {
      const prof = s.proficiency ? `<span class="prof">${s.proficiency}</span>` : '';
      return `<span class="tag">${s.name}${prof}</span>`;
    }).join('');
    document.getElementById('section-skills').hidden = false;
  } else if (sl) {
    document.getElementById('section-skills').hidden = true;
  }

  // Experience
  const el2 = document.getElementById('experience-list');
  if (el2 && data.experience?.length) {
    el2.innerHTML = data.experience.map(e => `
      <div class="exp-item">
        <h4>${e.role} at ${e.company}</h4>
        <div class="meta">${e.duration || ''}</div>
        ${e.description?.length ? `<ul>${e.description.map(d => `<li>${d}</li>`).join('')}</ul>` : ''}
      </div>
    `).join('');
    document.getElementById('section-experience').hidden = false;
  } else if (el2) {
    document.getElementById('section-experience').hidden = true;
  }

  // Education
  const ed = document.getElementById('education-list');
  if (ed && data.education?.length) {
    ed.innerHTML = data.education.map(e => `
      <div class="edu-item">
        <h4>${e.institution}</h4>
        <p>${e.degree}${e.field ? ' in ' + e.field : ''}${e.year ? ' — ' + e.year : ''}</p>
      </div>
    `).join('');
    document.getElementById('section-education').hidden = false;
  } else if (ed) {
    document.getElementById('section-education').hidden = true;
  }

  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── Match Tab ───────────────────────────────────────────────
document.getElementById('btn-match')?.addEventListener('click', async () => {
  const file = getFile('file-input-match');
  if (!file) { alert('Please select a resume file first.'); return; }
  const jd = document.getElementById('jd-input')?.value?.trim();
  if (!jd) { alert('Please enter a job description.'); return; }

  const fd = new FormData();
  fd.append('resume', file);
  showSpinner('Processing...');
  try {
    const up = await fetch(API + '/upload', { method: 'POST', body: fd });
    const ud = await up.json();
    if (!ud.text) throw new Error(ud.error || 'Upload failed');
    showSpinner('Matching resume vs job description...');
    const ar = await fetch(API + '/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resumeText: ud.text, jobDescription: jd, resumeName: file.name })
    });
    const ad = await ar.json();
    if (ad.ats_score === undefined) throw new Error(ad.error || 'Match failed');

    const el = document.getElementById('results-match');
    el.hidden = false;

    const sc = Math.round(ad.ats_score);
    const circumference = 339.292;
    const offset = circumference - (circumference * sc / 100);
    const ring = document.getElementById('match-ring');
    if (ring) {
      ring.style.stroke = sc >= 70 ? 'var(--green)' : sc >= 40 ? 'var(--yellow)' : 'var(--red)';
      setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
    }
    const mt = document.getElementById('match-score-text');
    if (mt) mt.textContent = sc;

    const mb = document.getElementById('match-breakdown');
    if (mb && ad.breakdown) {
      mb.innerHTML = Object.entries(ad.breakdown).map(([k, v]) => {
        const pct = Math.round(v);
        const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)';
        return `<div class="breakdown-item">
          <div class="value" style="color:${color}">${pct}%</div>
          <div class="label">${k.replace(/_/g, ' ')}</div>
        </div>`;
      }).join('');
    }

    const ms = document.getElementById('match-suggestions');
    if (ms && ad.suggestions?.length) {
      ms.innerHTML = `<h4>Suggestions</h4><ul>${ad.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>`;
      ms.hidden = false;
    } else if (ms) {
      ms.hidden = true;
    }

    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) {
    alert('Error: ' + err.message);
  }
  hideSpinner();
});

// ─── Batch Tab ───────────────────────────────────────────────
document.getElementById('btn-batch')?.addEventListener('click', async () => {
  const input = document.getElementById('file-input-batch');
  const files = input?.files;
  if (!files?.length) { alert('Please select at least one resume file.'); return; }

  const jd = document.getElementById('jd-batch')?.value?.trim() || '';
  const list = document.getElementById('batch-results-list');
  const errs = document.getElementById('batch-errors');
  const results = document.getElementById('results-batch');
  results.hidden = false;
  list.innerHTML = '';
  errs.innerHTML = '';
  if (errs) errs.hidden = true;

  showSpinner(`Analyzing ${files.length} resume(s)...`);
  let completed = 0;

  for (const file of files) {
    if (!validFile(file)) continue;
    const fd = new FormData();
    fd.append('resume', file);
    try {
      const up = await fetch(API + '/upload', { method: 'POST', body: fd });
      const ud = await up.json();
      if (!ud.text) throw new Error(ud.error || 'Upload failed');
      const ar = await fetch(API + '/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resumeText: ud.text, jobDescription: jd || 'general software engineering role', resumeName: file.name })
      });
      const ad = await ar.json();
      if (ad.ats_score === undefined) throw new Error(ad.error || 'Analysis failed');
      const sc = Math.round(ad.ats_score);
      const color = sc >= 70 ? 'var(--green)' : sc >= 40 ? 'var(--yellow)' : 'var(--red)';
      list.innerHTML += `<div class="breakdown-item" style="margin-bottom:8px; text-align:left; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:500">${file.name}</span>
        <span style="font-weight:700; color:${color}; font-family: 'Space Grotesk', sans-serif;">${sc}%</span>
      </div>`;
    } catch (err) {
      errs.innerHTML += `<p style="font-size:13px; color:var(--red); margin:4px 0">${file.name}: ${err.message}</p>`;
      if (errs) errs.hidden = false;
    }
    completed++;
    showSpinner(`Analyzing ${completed}/${files.length} resume(s)...`);
  }
  hideSpinner();
});

// ─── History Tab ─────────────────────────────────────────────
function loadHistory() {
  const list = document.getElementById('history-list');
  if (!list) return;
  const history = JSON.parse(localStorage.getItem('resume_history') || '[]');
  if (!history.length) {
    list.innerHTML = '<p class="dropzone-hint">No analyses yet. Upload a resume to get started.</p>';
    return;
  }
  list.innerHTML = history.reverse().map((item, i) => {
    const idx = history.length - 1 - i;
    const sc = Math.round(item.ats_score);
    const color = sc >= 70 ? 'var(--green)' : sc >= 40 ? 'var(--yellow)' : 'var(--red)';
    const date = item.date ? new Date(item.date).toLocaleDateString() : '';
    return `<div class="breakdown-item" style="cursor:pointer; margin-bottom:8px; text-align:left; display:flex; justify-content:space-between; align-items:center; transition:all 0.2s"
      onclick="loadAnalysisFromHistory(${idx})" onmouseover="this.style.background='rgba(108,92,231,0.1)'" onmouseout="this.style.background=''">
      <div><span style="font-weight:500">${item.resume_name || 'Resume ' + (idx + 1)}</span>
      ${date ? `<br><span style="font-size:11px; color:var(--text2); opacity:0.6">${date}</span>` : ''}</div>
      <span style="font-weight:700; color:${color}; font-family: 'Space Grotesk', sans-serif; font-size:20px">${sc}%</span>
    </div>`;
  }).join('');
}

function saveToHistory(data) {
  const history = JSON.parse(localStorage.getItem('resume_history') || '[]');
  history.push({ ...data, date: new Date().toISOString() });
  localStorage.setItem('resume_history', JSON.stringify(history.slice(-50)));
}

window.loadAnalysisFromHistory = function(idx) {
  const history = JSON.parse(localStorage.getItem('resume_history') || '[]');
  const item = history[idx];
  if (!item) return;
  document.querySelector('.tab[data-tab="analyze"]')?.click();
  showResults(item, item.resume_name);
};

document.querySelector('.tab[data-tab="history"]')?.addEventListener('click', loadHistory);

// ─── Compare Tab ─────────────────────────────────────────────
document.getElementById('btn-compare')?.addEventListener('click', () => {
  const input = document.getElementById('compare-ids');
  const ids = input?.value?.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
  if (!ids || ids.length < 2) { alert('Please enter at least 2 valid analysis IDs.'); return; }

  const history = JSON.parse(localStorage.getItem('resume_history') || '[]');
  const items = ids.map(id => history[id]).filter(Boolean);
  if (items.length < 2) { alert('Could not find those analyses in history.'); return; }

  const el = document.getElementById('results-compare');
  el.hidden = false;
  const wrap = document.getElementById('compare-table-wrapper');

  const headers = ['Resume', 'Score', ...Object.keys(items[0]?.breakdown || {}), 'Suggestions'];
  const rows = items.map(item => {
    const sc = Math.round(item.ats_score);
    const color = sc >= 70 ? 'var(--green)' : sc >= 40 ? 'var(--yellow)' : 'var(--red)';
    const breakdowns = Object.values(item.breakdown || {}).map(v => Math.round(v) + '%');
    return `<tr>
      <td style="font-weight:500">${item.resume_name || 'Resume'}</td>
      <td style="font-weight:700; color:${color}">${sc}%</td>
      ${breakdowns.map(v => `<td>${v}</td>`).join('')}
      <td style="font-size:12px; color:var(--text2)">${item.suggestions?.length || 0} suggestions</td>
    </tr>`;
  }).join('');

  wrap.innerHTML = `<div style="overflow-x:auto">
    <table style="width:100%; border-collapse:collapse; font-size:14px">
      <thead><tr>${headers.map(h => `<th style="text-align:left; padding:10px 12px; border-bottom:1px solid rgba(108,92,231,0.1); color:var(--text2); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.04em">${h}</th>`).join('')}</tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`;
  el.scrollIntoView({ behavior: 'smooth' });
});

// ─── Export PDF ──────────────────────────────────────────────
document.getElementById('export-pdf')?.addEventListener('click', () => {
  const el = document.getElementById('results-analyze');
  if (!el || el.hidden) return;
  window.print();
});

// ─── Check API Health ───────────────────────────────────────
(async function() {
  try {
    await fetch(API + '/health');
  } catch (e) {
    // silently fail if backend not running
  }
})();
