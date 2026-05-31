"""
[P3] Deck de swipe type Tinder — version pro.

Rend une pile de dossiers dans une seule iframe. Toute l'interaction (drag,
clavier, undo, fin de file) est gérée côté client en JS vanilla, ce qui donne
un swipe fluide sans rerun Streamlit par carte.

Gestes :
    ← / A   classer fraude     (voile bleu)
    → / D   marquer légitime   (voile vert)
    ↑ / E   escalader          (voile jaune)
    Z       annuler la dernière décision

Les décisions sont accumulées côté client et exportables en CSV depuis l'écran
de fin. Le pont vers le backend Python (audit.py / feedback.py) viendra ensuite.
"""
from __future__ import annotations

from src.ui.case_card import CARD_CSS, render_card_inner, render_controls
from src.ui.mock_data import CaseFile


def _risk_key(label: str) -> str:
    """Normalise un risk_label ("ÉLEVÉ"/"MOYEN"/"FAIBLE") en clé ascii."""
    lab = (label or "").upper()
    if "LEV" in lab:   # ÉLEVÉ / ELEVE
        return "eleve"
    if "MOY" in lab:   # MOYEN
        return "moyen"
    return "faible"


DECK_CSS = """
body { padding: 18px 16px 28px; }
.deck-wrap {
  width: min(560px, 100%); margin: 0 auto;
  opacity: 0; transition: opacity 350ms ease;
}
.deck-wrap.ready { opacity: 1; }

.stage { position: relative; }   /* hauteur fixée par JS */

.swipe-card {
  position: absolute; top: 0; left: 0; right: 0;
  transition: transform 360ms cubic-bezier(.2,.7,.2,1), opacity 300ms ease;
  will-change: transform, opacity;
  touch-action: none;
}
.swipe-card.dragging { transition: none; }
.swipe-card.gone { display: none; }
.swipe-card .card { user-select: none; -webkit-user-select: none; }
.swipe-card.top { cursor: grab; }
.swipe-card.top:active { cursor: grabbing; }

.tint {
  position: absolute; inset: 0; border-radius: 16px;
  opacity: 0; pointer-events: none; transition: opacity 120ms ease;
}
.decision-label {
  position: absolute; top: 28px; left: 50%;
  transform: translateX(-50%) rotate(-5deg);
  padding: 8px 20px; border: 3px solid; border-radius: 12px;
  font-family: var(--font-sans); font-weight: 700; font-size: 22px;
  letter-spacing: 0.1em; text-transform: uppercase;
  opacity: 0; pointer-events: none; transition: opacity 120ms ease;
  background: rgba(255,255,255,0.86);
}

/* Panneau de contrôles sous la pile */
.deck-controls {
  width: 100%;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 14px;
  padding: 16px 18px 18px;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 8px 16px -8px rgba(16,24,40,0.08);
}
.deck-progress { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.deck-progress .label { font-size: 12px; font-weight: 600; color: var(--c-text-2); }
.deck-progress .count { font-family: var(--font-mono); font-size: 12px; color: var(--c-text-3); }
.progress-track { height: 6px; border-radius: 999px; background: #EAECF0; overflow: hidden; margin-bottom: 16px; }
.progress-fill { height: 100%; width: 0%; background: #1E40AF; border-radius: 999px; transition: width 280ms ease; }

/* Bouton Annuler (ghost, pleine largeur) */
.btn-undo { width: 100%; margin-top: 10px; color: var(--c-text-2); }
.btn:disabled { opacity: 0.45; cursor: default; box-shadow: none; }
.btn:disabled:hover { box-shadow: none; background: var(--c-surface); }

/* Écran de fin */
.deck-done {
  width: 100%;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 16px;
  padding: 28px 24px;
  text-align: center;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 20px 32px -12px rgba(16,24,40,0.10);
}
.deck-done h2 { font-size: 18px; font-weight: 600; color: var(--c-text); margin-bottom: 6px; }
.deck-done p { font-size: 13px; color: var(--c-text-3); margin-bottom: 20px; }
.done-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 22px; }
.done-stat { border: 1px solid var(--c-border); border-radius: 10px; padding: 14px 8px; }
.done-stat .n { font-family: var(--font-mono); font-size: 24px; font-weight: 600; }
.done-stat .k { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--c-text-3); margin-top: 4px; }
.done-actions { display: flex; gap: 10px; justify-content: center; }

/* Sélecteur de vue (segmented control) */
.view-toggle {
  display: inline-flex; background: #EAECF0; border-radius: 10px;
  padding: 3px; margin-bottom: 14px;
}
.seg {
  border: none; background: transparent; cursor: pointer;
  font-family: var(--font-sans); font-size: 13px; font-weight: 600;
  color: var(--c-text-2); padding: 7px 16px; border-radius: 8px;
  transition: background-color 140ms ease, color 140ms ease;
}
.seg.active {
  background: var(--c-surface); color: var(--c-text);
  box-shadow: 0 1px 2px rgba(16,24,40,0.08);
}

/* Tableau de bord */
.dashboard {
  width: 100%; background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: 16px; padding: 22px 24px;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 20px 32px -12px rgba(16,24,40,0.10);
}
.dash-progress { margin-bottom: 24px; }
.dash-progress-head { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 10px; }
.dash-progress-head .t { font-weight: 600; color: var(--c-text-2); }
.dash-progress-head .c { font-family: var(--font-mono); color: var(--c-text-3); }

/* KPI */
.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 18px; }
.kpi { border: 1px solid var(--c-border); border-radius: 10px; padding: 14px 10px; background: #FCFCFD; text-align: center; }
.kpi-val { font-family: var(--font-mono); font-size: 22px; font-weight: 600; color: var(--c-text); font-variant-numeric: tabular-nums; }
.kpi-lbl { font-size: 10px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--c-text-3); margin-top: 5px; }
.dash-section { margin-bottom: 24px; }
.dash-section:last-child { margin-bottom: 0; }
.dash-title {
  font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--c-text-3); margin-bottom: 16px;
}
.dash-row {
  display: grid; grid-template-columns: 12px 80px 1fr 32px; gap: 12px;
  align-items: center; margin-bottom: 14px;
}
.dash-row:last-child { margin-bottom: 0; }
.dash-dot { width: 10px; height: 10px; border-radius: 50%; }
.dash-label { font-size: 13px; color: var(--c-text); }
.dash-bar-track { display: block; width: 100%; height: 8px; border-radius: 999px; background: #EAECF0; overflow: hidden; }
.dash-bar-fill { display: block; height: 8px; border-radius: 999px; width: 0%; transition: width 280ms ease; }
.dash-count { font-family: var(--font-mono); font-size: 14px; font-weight: 600; text-align: right; color: var(--c-text); }

/* Bannière d'apprentissage (feedback loop) */
.learn-banner {
  display: flex; align-items: center; gap: 10px;
  background: #ECFDF3; border: 1px solid #ABEFC6; border-radius: 10px;
  padding: 10px 14px; margin-bottom: 12px;
  font-size: 13px; color: #067647; font-weight: 500;
  animation: learn-in 280ms ease;
}
.learn-banner .lb-icon { flex-shrink: 0; width: 16px; height: 16px; }
@keyframes learn-in { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: none; } }

/* Drapeau "appris" sur une carte dépriorisée */
.learned-flag {
  display: none;
  position: absolute; top: 0; left: 0; right: 0; z-index: 5;
  background: #ECFDF3; border-bottom: 1px solid #ABEFC6;
  color: #067647; font-size: 11px; font-weight: 600;
  text-align: center; padding: 6px 10px;
  border-radius: 16px 16px 0 0;
}
.swipe-card.learned-legit .learned-flag { display: block; }
.swipe-card.learned-legit .card { opacity: 0.82; }

/* Ligne d'apprentissage dans le dashboard */
.dash-learn {
  background: #ECFDF3; border: 1px solid #ABEFC6; border-radius: 10px;
  padding: 10px 14px; margin-bottom: 22px;
  font-size: 12px; color: #067647; font-weight: 500;
}
"""


# JS vanilla — chaîne brute (les accolades internes ne sont pas du f-string).
DECK_JS = r"""
(function () {
  const DIRS = {
    fraud:    { dx: -1, dy: 0,  text: 'Fraude',   color: '#1E40AF', tint: 'rgba(30,64,175,0.16)' },
    legit:    { dx: 1,  dy: 0,  text: 'Légitime', color: '#17B26A', tint: 'rgba(23,178,106,0.16)' },
    escalate: { dx: 0,  dy: -1, text: 'Escalader',color: '#CA8A04', tint: 'rgba(202,138,4,0.16)' },
  };
  const THRESHOLD = 110;

  // Feedback loop : seuil d'innocentements pour juger une catégorie "fiable"
  const TRUST_LEGIT = 2;
  const CAT_LABELS = {
    online_retail: 'Achat en ligne', electronics: 'Électronique',
    gift_card: 'Carte-cadeau', travel: 'Voyage', restaurant: 'Restaurant',
    grocery: 'Épicerie', gas: 'Essence', subscription: 'Abonnement',
    utilities: 'Services', entertainment: 'Divertissement', atm: 'Retrait ATM',
  };
  const prettyCat = c => CAT_LABELS[c] || (c || 'inconnue');

  const stage = document.getElementById('stage');
  const cards = Array.from(document.querySelectorAll('.swipe-card'));
  const total = cards.length;
  const fill = document.getElementById('progressFill');
  const countEl = document.getElementById('progressCount');
  const labelEl = document.getElementById('progressLabel');
  const doneEl = document.getElementById('deckDone');
  const controlsEl = document.getElementById('deckControls');

  let cur = 0;
  const decisions = new Array(total).fill(null);
  const lastDir = new Array(total).fill(null);
  const history = [];
  let lastActionTime = Date.now();
  const times = [];   // durée (ms) entre décisions, pour le temps moyen

  // Hauteur de la scène = carte la plus haute (+ marge pour la pile derrière)
  function sizeStage() {
    let maxH = 0;
    cards.forEach(c => { maxH = Math.max(maxH, c.offsetHeight); });
    stage.style.height = (maxH + 30) + 'px';
  }

  function restack() {
    cards.forEach((card, i) => {
      card.classList.remove('top', 'gone');
      const tint = card.querySelector('.tint');
      const label = card.querySelector('.decision-label');
      tint.style.opacity = 0;
      label.style.opacity = 0;

      if (i < cur) {
        card.classList.add('gone');
      } else if (i === cur) {
        card.classList.add('top');
        card.style.zIndex = 100;
        card.style.transform = 'translate(0,0) rotate(0deg)';
        card.style.opacity = 1;
      } else {
        const depth = i - cur;
        if (depth <= 2) {
          card.style.zIndex = 100 - depth;
          card.style.transform = 'translateY(' + (depth * 14) + 'px) scale(' + (1 - depth * 0.04) + ')';
          card.style.opacity = 1;
        } else {
          card.style.zIndex = 100 - depth;
          card.style.transform = 'translateY(28px) scale(0.92)';
          card.style.opacity = 0;
        }
      }
    });
    updateProgress();
  }

  function updateProgress() {
    const done = cur;
    fill.style.width = (total ? (done / total) * 100 : 0) + '%';
    countEl.textContent = done + ' / ' + total;
    if (cur < total) {
      labelEl.textContent = 'Dossier ' + (cur + 1) + ' sur ' + total;
    } else {
      labelEl.textContent = 'File terminée';
    }
    const undoBtn = document.getElementById('undoBtn');
    if (undoBtn) undoBtn.disabled = history.length === 0;
    recomputeLearning();
    renderDashboard();
  }

  // --- Feedback loop : apprentissage en session ---
  // Recalculé entièrement depuis l'état (decisions + cur) à chaque changement,
  // donc automatiquement cohérent avec l'undo.
  function recomputeLearning() {
    const legitByCat = {};
    for (let i = 0; i < cur; i++) {
      if (decisions[i] === 'legit') {
        const c = cards[i].getAttribute('data-category') || '';
        if (c) legitByCat[c] = (legitByCat[c] || 0) + 1;
      }
    }
    const trusted = Object.keys(legitByCat).filter(c => legitByCat[c] >= TRUST_LEGIT);

    // réinitialise puis tague les dossiers à venir (i > cur) des catégories fiables
    let demoted = 0;
    for (let i = 0; i < total; i++) cards[i].classList.remove('learned-legit');
    for (let i = cur + 1; i < total; i++) {
      const c = cards[i].getAttribute('data-category') || '';
      if (trusted.indexOf(c) !== -1) {
        cards[i].classList.add('learned-legit');
        demoted += 1;
      }
    }

    const checkIcon = '<svg class="lb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>';
    const names = trusted.map(prettyCat).join(', ');

    const banner = document.getElementById('learnBanner');
    if (banner) {
      if (trusted.length) {
        banner.innerHTML = checkIcon + 'Appris : ' + names + ' jugée(s) fiable(s) — '
          + demoted + ' flag(s) similaire(s) dépriorisé(s).';
        banner.hidden = false;
      } else {
        banner.hidden = true;
      }
    }
    const dl = document.getElementById('dashLearn');
    if (dl) {
      if (trusted.length) {
        dl.textContent = 'Apprentissage actif : ' + names
          + ' jugée(s) fiable(s) — ' + demoted + ' flag(s) restant(s) dépriorisé(s).';
        dl.hidden = false;
      } else {
        dl.hidden = true;
      }
    }
  }

  // --- Tableau de bord ---
  let currentView = 'deck';

  function renderDashboard() {
    const rem = { eleve: 0, moyen: 0, faible: 0 };
    for (let i = cur; i < total; i++) {
      const k = cards[i].getAttribute('data-risk') || 'faible';
      if (rem[k] != null) rem[k] += 1;
    }
    const res = { fraud: 0, escalate: 0, legit: 0 };
    const resImp = { eleve: 0, moyen: 0, faible: 0 };
    for (let i = 0; i < cur; i++) {
      const d = decisions[i];
      if (res[d] != null) res[d] += 1;
      const k = cards[i].getAttribute('data-risk') || 'faible';
      if (resImp[k] != null) resImp[k] += 1;
    }
    const setRow = (cntId, barId, n) => {
      const c = document.getElementById(cntId);
      const b = document.getElementById(barId);
      if (c) c.textContent = n;
      if (b) b.style.width = (total ? (n / total * 100) : 0) + '%';
    };
    setRow('cntRemEleve', 'barRemEleve', rem.eleve);
    setRow('cntRemMoyen', 'barRemMoyen', rem.moyen);
    setRow('cntRemFaible', 'barRemFaible', rem.faible);
    setRow('cntResFraud', 'barResFraud', res.fraud);
    setRow('cntResEscalate', 'barResEscalate', res.escalate);
    setRow('cntResLegit', 'barResLegit', res.legit);
    setRow('cntResImpEleve', 'barResImpEleve', resImp.eleve);
    setRow('cntResImpMoyen', 'barResImpMoyen', resImp.moyen);
    setRow('cntResImpFaible', 'barResImpFaible', resImp.faible);

    const df = document.getElementById('dashFill');
    if (df) df.style.width = (total ? (cur / total * 100) : 0) + '%';

    // KPI
    const setText = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
    setText('kpiProgress', cur + ' / ' + total);
    setText('kpiFraudRate', cur ? Math.round(res.fraud / cur * 100) + ' %' : '—');
    if (times.length) {
      const avg = times.reduce((a, b) => a + b, 0) / times.length / 1000;
      setText('kpiAvgTime', avg.toFixed(1) + ' s');
    } else {
      setText('kpiAvgTime', '—');
    }
  }

  function setView(v) {
    currentView = v;
    const deckView = document.getElementById('deckView');
    const dash = document.getElementById('dashboard');
    if (v === 'dashboard') {
      if (deckView) deckView.style.display = 'none';
      if (dash) dash.hidden = false;
      renderDashboard();
    } else {
      if (deckView) deckView.style.display = '';
      if (dash) dash.hidden = true;
    }
    document.querySelectorAll('.seg').forEach(s => {
      s.classList.toggle('active', s.getAttribute('data-view') === v);
    });
  }

  document.querySelectorAll('.seg').forEach(s => {
    s.addEventListener('click', () => setView(s.getAttribute('data-view')));
  });

  function applyDrag(card, dx, dy) {
    const rot = dx * 0.04;
    card.style.transform = 'translate(' + dx + 'px,' + dy + 'px) rotate(' + rot + 'deg)';
    const dir = dirFromDelta(dx, dy);
    const tint = card.querySelector('.tint');
    const label = card.querySelector('.decision-label');
    if (!dir) { tint.style.opacity = 0; label.style.opacity = 0; return; }
    const d = DIRS[dir];
    const mag = Math.min(Math.max(Math.abs(dx), Math.abs(dy)) / THRESHOLD, 1);
    tint.style.background = d.tint;
    tint.style.opacity = mag * 0.9;
    label.textContent = d.text;
    label.style.color = d.color;
    label.style.borderColor = d.color;
    label.style.opacity = Math.min(mag * 1.4, 1);
  }

  function dirFromDelta(dx, dy) {
    if (dy < -60 && Math.abs(dy) > Math.abs(dx)) return 'escalate';
    if (Math.abs(dx) < 24 && Math.abs(dy) < 24) return null;
    return dx < 0 ? 'fraud' : 'legit';
  }

  function flyOff(dir) {
    if (cur >= total) return;
    const card = cards[cur];
    const d = DIRS[dir];
    const tint = card.querySelector('.tint');
    const label = card.querySelector('.decision-label');

    // Voile + label pleins pendant la sortie
    tint.style.background = d.tint;
    tint.style.opacity = 0.9;
    label.textContent = d.text;
    label.style.color = d.color;
    label.style.borderColor = d.color;
    label.style.opacity = 1;

    card.classList.remove('dragging');
    const offX = d.dx * 140;
    const offY = d.dy * 140;
    const rot = d.dx * 12;
    card.style.transform = 'translate(' + offX + 'vw,' + offY + 'vh) rotate(' + rot + 'deg)';
    card.style.opacity = 0;

    decisions[cur] = dir;
    lastDir[cur] = dir;
    history.push(cur);
    const nowT = Date.now();
    times.push(nowT - lastActionTime);
    lastActionTime = nowT;
    cur += 1;

    setTimeout(() => {
      restack();
      if (cur >= total) showDone();
    }, 340);
  }

  function undo() {
    if (history.length === 0) return;
    if (cur >= total) hideDone();
    const idx = history.pop();
    decisions[idx] = null;
    if (times.length) times.pop();
    lastActionTime = Date.now();
    cur = idx;

    const card = cards[idx];
    const d = DIRS[lastDir[idx]] || DIRS.legit;
    // place la carte hors-champ du côté de sa sortie, puis on la ramène
    card.classList.remove('gone', 'dragging');
    card.style.transition = 'none';
    card.style.transform = 'translate(' + (d.dx * 140) + 'vw,' + (d.dy * 140) + 'vh) rotate(' + (d.dx * 12) + 'deg)';
    card.style.opacity = 0;
    // force reflow puis anime le retour
    void card.offsetWidth;
    card.style.transition = '';
    restack();
  }

  // --- Drag (pointer events) sur la carte du dessus ---
  let dragging = null, startX = 0, startY = 0;

  stage.addEventListener('pointerdown', (e) => {
    if (cur >= total) return;
    const card = cards[cur];
    if (!card.contains(e.target)) return;
    if (e.target.closest('button')) return;  // ne pas drag depuis un bouton
    dragging = card;
    startX = e.clientX; startY = e.clientY;
    card.classList.add('dragging');
    card.setPointerCapture(e.pointerId);
  });

  stage.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    applyDrag(dragging, e.clientX - startX, e.clientY - startY);
  });

  function endDrag(e) {
    if (!dragging) return;
    const dx = e.clientX - startX, dy = e.clientY - startY;
    const card = dragging;
    dragging = null;
    card.classList.remove('dragging');
    const dir = dirFromDelta(dx, dy);
    const passed = Math.max(Math.abs(dx), Math.abs(dy)) >= THRESHOLD;
    if (dir && passed) {
      flyOff(dir);
    } else {
      // retour à la place
      card.style.transform = 'translate(0,0) rotate(0deg)';
      card.querySelector('.tint').style.opacity = 0;
      card.querySelector('.decision-label').style.opacity = 0;
    }
  }
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);

  // --- Boutons ---
  document.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const map = { fraud: 'fraud', legit: 'legit', escalate: 'escalate' };
      const dir = map[btn.getAttribute('data-action')];
      if (dir) flyOff(dir);
    });
  });
  const undoBtn = document.getElementById('undoBtn');
  if (undoBtn) undoBtn.addEventListener('click', undo);

  // --- Clavier ---
  document.addEventListener('keydown', (e) => {
    if (currentView !== 'deck') return;  // pas de décision depuis le dashboard
    const k = e.key.toLowerCase();
    if (k === 'a' || e.key === 'ArrowLeft') { e.preventDefault(); flyOff('fraud'); }
    else if (k === 'd' || e.key === 'ArrowRight') { e.preventDefault(); flyOff('legit'); }
    else if (k === 'e' || e.key === 'ArrowUp') { e.preventDefault(); flyOff('escalate'); }
    else if (k === 'z') { e.preventDefault(); undo(); }
  });

  // --- Écran de fin ---
  function showDone() {
    const n = { fraud: 0, legit: 0, escalate: 0 };
    decisions.forEach(d => { if (d) n[d] += 1; });
    document.getElementById('nFraud').textContent = n.fraud;
    document.getElementById('nLegit').textContent = n.legit;
    document.getElementById('nEscalate').textContent = n.escalate;
    stage.style.display = 'none';
    controlsEl.style.display = 'none';
    doneEl.hidden = false;
  }
  function hideDone() {
    doneEl.hidden = true;
    stage.style.display = '';
    controlsEl.style.display = '';
  }

  // Construit le rapport structuré des décisions (payload pour audit.py / FeedbackManager)
  function buildPayload() {
    const out = [];
    cards.forEach((c, i) => {
      out.push({
        case_id: c.getAttribute('data-id'),
        card_id: c.getAttribute('data-card'),
        score: parseFloat(c.getAttribute('data-score')),
        category: c.getAttribute('data-category') || '',
        decision: decisions[i] || null,
      });
    });
    return out;
  }

  // Export JSON des décisions (reçu / piste d'audit)
  document.getElementById('downloadBtn').addEventListener('click', () => {
    const payload = JSON.stringify(buildPayload(), null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'decisions.json';
    a.click();
  });

  document.getElementById('restartBtn').addEventListener('click', () => {
    cur = 0;
    decisions.fill(null);
    history.length = 0;
    times.length = 0;
    lastActionTime = Date.now();
    hideDone();
    cards.forEach(c => { c.style.transition = 'none'; });
    restack();
    requestAnimationFrame(() => cards.forEach(c => { c.style.transition = ''; }));
  });

  // Init
  function reveal() {
    const wrap = document.querySelector('.deck-wrap');
    if (wrap) wrap.classList.add('ready');
  }
  window.addEventListener('load', () => { sizeStage(); restack(); reveal(); window.focus(); });
  sizeStage();
  restack();
  reveal();
})();
"""


def _render_empty_state() -> str:
    """Affiché quand il n'y a aucun dossier à réviser (file vide)."""
    return f"""<!DOCTYPE html>
<html>
<head><style>{CARD_CSS}
body {{ padding: 48px 16px; display: flex; justify-content: center; }}
.empty {{
  width: min(560px, 100%); background: var(--c-surface);
  border: 1px solid var(--c-border); border-radius: 16px;
  padding: 48px 24px; text-align: center;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 20px 32px -12px rgba(16,24,40,0.10);
}}
.empty h2 {{ font-size: 18px; font-weight: 600; color: var(--c-text); margin-bottom: 6px; }}
.empty p {{ font-size: 13px; color: var(--c-text-3); }}
</style></head>
<body>
  <div class="empty">
    <h2>Aucun dossier à réviser</h2>
    <p>La file est vide : aucune transaction n'a été signalée pour le moment.</p>
  </div>
</body>
</html>
"""


def render_swipe_deck(cases: list[CaseFile]) -> str:
    """Document HTML complet : pile de dossiers swipables + contrôles + fin.

    Si `cases` est vide, renvoie un état vide propre plutôt qu'un deck cassé.
    """
    if not cases:
        return _render_empty_state()

    cards_html = "\n".join(
        f"""
        <div class="swipe-card" data-index="{i}" data-id="{case.case_id}" data-card="{case.card_id}" data-score="{case.score:.4f}" data-risk="{_risk_key(case.risk_label)}" data-category="{case.merchant_category}">
          <div class="learned-flag">Catégorie jugée fiable — priorité réduite</div>
          {render_card_inner(case)}
          <div class="tint"></div>
          <div class="decision-label"></div>
        </div>
        """
        for i, case in enumerate(cases)
    )

    controls = render_controls()

    return f"""<!DOCTYPE html>
<html>
<head><style>{CARD_CSS}{DECK_CSS}</style></head>
<body>
  <div class="deck-wrap">

    <div class="view-toggle">
      <button class="seg active" type="button" data-view="deck">Révision</button>
      <button class="seg" type="button" data-view="dashboard">Tableau de bord</button>
    </div>

    <div id="deckView">

      <div class="learn-banner" id="learnBanner" hidden></div>

      <div class="stage" id="stage">
        {cards_html}
      </div>

      <div class="deck-controls" id="deckControls">
        <div class="deck-progress">
          <span class="label" id="progressLabel">Dossier 1</span>
          <span class="count" id="progressCount">0 / {len(cases)}</span>
        </div>
        <div class="progress-track"><div class="progress-fill" id="progressFill"></div></div>
        {controls}
        <button id="undoBtn" class="btn btn-undo" type="button" disabled>Annuler la dernière décision (Z)</button>
      </div>

      <div class="deck-done" id="deckDone" hidden>
        <h2>File terminée</h2>
        <p>Toutes les décisions ont été enregistrées.</p>
        <div class="done-stats">
          <div class="done-stat"><div class="n" id="nFraud" style="color:#1E40AF;">0</div><div class="k">Fraude</div></div>
          <div class="done-stat"><div class="n" id="nEscalate" style="color:#CA8A04;">0</div><div class="k">Escaladé</div></div>
          <div class="done-stat"><div class="n" id="nLegit" style="color:#17B26A;">0</div><div class="k">Légitime</div></div>
        </div>
        <div class="done-actions">
          <button id="downloadBtn" class="btn btn-fraud" type="button">Exporter le rapport (JSON)</button>
          <button id="restartBtn" class="btn" type="button">Recommencer</button>
        </div>
      </div>

    </div>

    <div class="dashboard" id="dashboard" hidden>

      <div class="kpi-row">
        <div class="kpi"><div class="kpi-val" id="kpiProgress">0 / {len(cases)}</div><div class="kpi-lbl">Traités</div></div>
        <div class="kpi"><div class="kpi-val" id="kpiFraudRate">—</div><div class="kpi-lbl">Taux de fraude</div></div>
        <div class="kpi"><div class="kpi-val" id="kpiAvgTime">—</div><div class="kpi-lbl">Temps moyen</div></div>
      </div>
      <div class="progress-track" style="margin-bottom: 16px;"><div class="progress-fill" id="dashFill"></div></div>

      <div class="dash-learn" id="dashLearn" hidden></div>

      <div class="dash-section">
        <p class="dash-title">À traiter — par importance</p>
        <div class="dash-row">
          <span class="dash-dot" style="background:#1E40AF;"></span>
          <span class="dash-label">Élevé</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barRemEleve" style="background:#1E40AF;"></span></span>
          <span class="dash-count" id="cntRemEleve">0</span>
        </div>
        <div class="dash-row">
          <span class="dash-dot" style="background:#CA8A04;"></span>
          <span class="dash-label">Moyen</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barRemMoyen" style="background:#CA8A04;"></span></span>
          <span class="dash-count" id="cntRemMoyen">0</span>
        </div>
        <div class="dash-row">
          <span class="dash-dot" style="background:#17B26A;"></span>
          <span class="dash-label">Faible</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barRemFaible" style="background:#17B26A;"></span></span>
          <span class="dash-count" id="cntRemFaible">0</span>
        </div>
      </div>

      <div class="dash-section">
        <p class="dash-title">Traités — par décision</p>
        <div class="dash-row">
          <span class="dash-dot" style="background:#1E40AF;"></span>
          <span class="dash-label">Fraude</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barResFraud" style="background:#1E40AF;"></span></span>
          <span class="dash-count" id="cntResFraud">0</span>
        </div>
        <div class="dash-row">
          <span class="dash-dot" style="background:#CA8A04;"></span>
          <span class="dash-label">Escaladé</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barResEscalate" style="background:#CA8A04;"></span></span>
          <span class="dash-count" id="cntResEscalate">0</span>
        </div>
        <div class="dash-row">
          <span class="dash-dot" style="background:#17B26A;"></span>
          <span class="dash-label">Légitime</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barResLegit" style="background:#17B26A;"></span></span>
          <span class="dash-count" id="cntResLegit">0</span>
        </div>
      </div>

      <div class="dash-section">
        <p class="dash-title">Traités — par importance</p>
        <div class="dash-row">
          <span class="dash-dot" style="background:#1E40AF;"></span>
          <span class="dash-label">Élevé</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barResImpEleve" style="background:#1E40AF;"></span></span>
          <span class="dash-count" id="cntResImpEleve">0</span>
        </div>
        <div class="dash-row">
          <span class="dash-dot" style="background:#CA8A04;"></span>
          <span class="dash-label">Moyen</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barResImpMoyen" style="background:#CA8A04;"></span></span>
          <span class="dash-count" id="cntResImpMoyen">0</span>
        </div>
        <div class="dash-row">
          <span class="dash-dot" style="background:#17B26A;"></span>
          <span class="dash-label">Faible</span>
          <span class="dash-bar-track"><span class="dash-bar-fill" id="barResImpFaible" style="background:#17B26A;"></span></span>
          <span class="dash-count" id="cntResImpFaible">0</span>
        </div>
      </div>
    </div>

  </div>
  <script>{DECK_JS}</script>
</body>
</html>
"""
