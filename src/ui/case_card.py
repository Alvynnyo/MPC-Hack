"""
[P3] Rendu HTML/CSS de la carte "Dossier d'enquête" (V3 — pro/clean).

Esthétique : outil de triage professionnel type Linear / Stripe / Mercury.
Fond clair, Inter + IBM Plex Mono, icônes SVG Lucide, badges sobres.

Cette carte est insérée dans Streamlit via st.components.v1.html()
(iframe isolée). Tout le CSS est inline pour rester self-contained.

Voir design-system/fraud-hunter/MASTER.md pour les règles visuelles.
"""
from __future__ import annotations

from src.ui.mock_data import CaseFile, Evidence, PreviousTx


# --- Icônes SVG (Lucide, stroke currentColor) ------------------------------ #

_ICON_CRITICAL = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>'
)
_ICON_WARNING = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
    '<path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
)
_ICON_INFO = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>'
)
_ICON_CARD = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>'
)
_ICON_ARROW_LEFT = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>'
)
_ICON_ARROW_RIGHT = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
)
_ICON_ARROW_UP = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>'
)


# --- Helpers d'affichage --------------------------------------------------- #

def _severity_tokens(severity: str) -> dict:
    """Couleurs (bg, fg, border) pour un niveau de sévérité — palette sobre.

    critical → bleu sombre · warning → jaune clair · info → vert.
    """
    return {
        "critical": {"bg": "#EFF4FF", "fg": "#1E3A8A", "border": "#C7D7FE", "icon": _ICON_CRITICAL},
        "warning":  {"bg": "#FEFCE8", "fg": "#854D0E", "border": "#FDE68A", "icon": _ICON_WARNING},
        "info":     {"bg": "#ECFDF3", "fg": "#067647", "border": "#ABEFC6", "icon": _ICON_INFO},
    }.get(severity, {"bg": "#F2F4F7", "fg": "#475467", "border": "#E4E7EC", "icon": _ICON_INFO})


def _risk_tokens(score: float) -> dict:
    """Couleur de la jauge + pill de risque selon le score.

    élevé → bleu sombre · moyen → jaune clair · faible → vert.
    """
    if score >= 0.75:
        return {"bg": "#EFF4FF", "fg": "#1E3A8A", "border": "#C7D7FE", "bar": "#1E40AF"}
    if score >= 0.45:
        return {"bg": "#FEFCE8", "fg": "#854D0E", "border": "#FDE68A", "bar": "#CA8A04"}
    return {"bg": "#ECFDF3", "fg": "#067647", "border": "#ABEFC6", "bar": "#17B26A"}


# --- Renderers de sections ------------------------------------------------- #

def _render_evidence(items: list[Evidence]) -> str:
    rows = []
    for ev in items:
        t = _severity_tokens(ev.severity)
        rows.append(
            f"""
            <div class="ev-row">
              <span class="ev-icon" style="color: {t['fg']};">{t['icon']}</span>
              <span class="ev-label">{ev.label}</span>
              <span class="ev-value">{ev.value}</span>
              <span class="badge" style="background: {t['bg']}; color: {t['fg']}; border-color: {t['border']};">{ev.tag}</span>
            </div>
            """
        )
    return "\n".join(rows)


def _render_previous(items: list[PreviousTx]) -> str:
    status_tokens = {
        "current": ("#1E3A8A", "current", "is-current"),
        "suspect": ("#854D0E", "suspect", ""),
        "ok":      ("#667085", "ok", ""),
    }
    rows = []
    for tx in items:
        color, label, cls = status_tokens.get(tx.status, ("#667085", "ok", ""))
        rows.append(
            f"""
            <div class="tx-row {cls}">
              <span class="tx-date">{tx.date}</span>
              <span class="tx-merchant">{tx.merchant}</span>
              <span class="tx-amount">{tx.amount:,.2f}&nbsp;$</span>
              <span class="tx-status" style="color: {color};">{label}</span>
            </div>
            """
        )
    return "\n".join(rows)


# --- Render principal ------------------------------------------------------ #

def render_case_card(case: CaseFile) -> str:
    """Renvoie le HTML complet (avec CSS inline) d'une carte dossier — V3 pro."""
    evidence_html = _render_evidence(case.evidence)
    previous_html = _render_previous(case.previous)
    risk = _risk_tokens(case.score)
    score_pct = round(case.score * 100)

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --c-canvas: #F2F4F7;
  --c-surface: #FFFFFF;
  --c-border: #E4E7EC;
  --c-border-strong: #D0D5DD;
  --c-text: #101828;
  --c-text-2: #475467;
  --c-text-3: #98A2B3;
  --font-sans: 'Inter', -apple-system, system-ui, sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
}}

body {{
  font-family: var(--font-sans);
  background: var(--c-canvas);
  color: var(--c-text);
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  -webkit-font-smoothing: antialiased;
}}

/* ─────────────────────────────────────────────
   CARTE
   ───────────────────────────────────────────── */

.card {{
  width: min(560px, 100%);
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 16px;
  box-shadow:
    0 1px 2px rgba(16, 24, 40, 0.04),
    0 4px 8px -2px rgba(16, 24, 40, 0.06),
    0 20px 32px -12px rgba(16, 24, 40, 0.10);
  overflow: hidden;
}}

/* ── HEADER ── */
.header {{
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--c-border);
}}

.avatar {{
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #F2F4F7;
  border: 1px solid var(--c-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-2);
}}
.avatar svg {{ width: 22px; height: 22px; }}

.header-main {{ flex: 1; min-width: 0; }}

.header-top {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}}

.case-label {{
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--c-text-3);
}}

.case-id {{
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text);
}}

.case-counter {{
  font-size: 12px;
  color: var(--c-text-3);
}}

.risk-pill {{
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid {risk['border']};
  background: {risk['bg']};
  color: {risk['fg']};
}}
.risk-dot {{ width: 6px; height: 6px; border-radius: 50%; background: {risk['bar']}; }}

/* ── BODY ── */
.body {{ padding: 20px 24px; }}

/* Métriques (montant + score) */
.metrics {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}}

.metric {{
  border: 1px solid var(--c-border);
  border-radius: 10px;
  padding: 12px 14px;
  background: #FCFCFD;
}}

.metric-label {{
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--c-text-3);
  margin-bottom: 6px;
}}

.metric-value {{
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 600;
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
}}

.score-track {{
  height: 6px;
  border-radius: 999px;
  background: #EAECF0;
  margin-top: 8px;
  overflow: hidden;
}}
.score-fill {{
  height: 100%;
  width: {score_pct}%;
  background: {risk['bar']};
  border-radius: 999px;
}}

/* Section label */
.section {{
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--c-text-3);
  margin: 0 0 10px;
}}

/* ── VERDICT IA (callout) ── */
.verdict {{
  position: relative;
  background: #F9FAFB;
  border: 1px solid var(--c-border);
  border-left: 3px solid #1E40AF;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 22px;
}}
.verdict-text {{
  font-size: 14px;
  line-height: 1.6;
  color: var(--c-text);
}}

/* ── PIÈCES À CONVICTION ── */
.evidence {{ margin-bottom: 22px; }}

.ev-row {{
  display: grid;
  grid-template-columns: 20px 96px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 9px 0;
  border-bottom: 1px solid #F2F4F7;
}}
.ev-row:last-child {{ border-bottom: none; }}

.ev-icon {{ width: 18px; height: 18px; display: flex; }}
.ev-icon svg {{ width: 18px; height: 18px; }}

.ev-label {{
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--c-text-3);
}}

.ev-value {{
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--c-text);
}}

.badge {{
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
}}

/* ── TIMELINE ── */
.timeline {{
  border: 1px solid var(--c-border);
  border-radius: 10px;
  overflow: hidden;
}}

.tx-row {{
  display: grid;
  grid-template-columns: 84px 1fr auto 64px;
  gap: 10px;
  align-items: center;
  padding: 9px 14px;
  border-bottom: 1px solid #F2F4F7;
  position: relative;
}}
.tx-row:last-child {{ border-bottom: none; }}
.tx-row.is-current {{
  background: #EFF4FF;
  box-shadow: inset 3px 0 0 #1E40AF;
}}

.tx-date {{ font-family: var(--font-mono); font-size: 12px; color: var(--c-text-3); }}
.tx-merchant {{ font-size: 13px; color: var(--c-text); }}
.tx-amount {{
  font-family: var(--font-mono);
  font-size: 13px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--c-text);
}}
.tx-status {{
  font-size: 11px;
  font-weight: 600;
  text-align: right;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

/* ── FOOTER ── */
.footer {{
  padding: 16px 24px 20px;
  border-top: 1px solid var(--c-border);
  background: #FCFCFD;
}}

.actions {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}}

.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 12px;
  border-radius: 9px;
  border: 1px solid var(--c-border-strong);
  background: var(--c-surface);
  color: var(--c-text);
  cursor: pointer;
  transition: background-color 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
}}
.btn svg {{ width: 15px; height: 15px; }}
.btn:hover {{ box-shadow: 0 1px 2px rgba(16,24,40,0.06); }}
.btn:focus-visible {{ outline: 2px solid #1E40AF; outline-offset: 2px; }}

.btn-fraud {{ border-color: #C7D7FE; color: #1E3A8A; background: #FBFCFF; }}
.btn-fraud:hover {{ background: #EFF4FF; border-color: #A4BCFD; }}

.btn-escalate {{ border-color: #FDE68A; color: #854D0E; background: #FFFEF7; }}
.btn-escalate:hover {{ background: #FEFCE8; border-color: #FDE047; }}

.btn-innocent {{ border-color: #ABEFC6; color: #067647; background: #FBFEFC; }}
.btn-innocent:hover {{ background: #ECFDF3; border-color: #75E0A7; }}

/* Raccourcis */
.shortcuts {{
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: var(--c-text-3);
}}
.shortcut {{ display: inline-flex; align-items: center; gap: 6px; }}
.kbd {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--c-text-2);
  background: var(--c-surface);
  border: 1px solid var(--c-border-strong);
  border-radius: 5px;
  box-shadow: 0 1px 0 var(--c-border-strong);
}}
.dot-sep {{ color: var(--c-border-strong); }}
</style>
</head>
<body>
  <div class="card">

    <!-- HEADER -->
    <div class="header">
      <div class="avatar">{_ICON_CARD}</div>
      <div class="header-main">
        <div class="header-top">
          <span class="case-label">Dossier</span>
          <span class="case-id">#{case.case_id}</span>
        </div>
        <div class="case-counter">{case.case_index} / {case.case_total} traités · Trust &amp; Safety</div>
      </div>
      <div class="risk-pill"><span class="risk-dot"></span>Risque {case.risk_label.lower()}</div>
    </div>

    <!-- BODY -->
    <div class="body">

      <!-- Métriques -->
      <div class="metrics">
        <div class="metric">
          <div class="metric-label">Carte</div>
          <div class="metric-value">{case.card_id}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Montant</div>
          <div class="metric-value">{case.amount:,.2f} $</div>
        </div>
        <div class="metric" style="grid-column: 1 / -1;">
          <div class="metric-label">Score de risque</div>
          <div class="metric-value">{case.score:.2f}</div>
          <div class="score-track"><div class="score-fill"></div></div>
        </div>
      </div>

      <!-- Verdict IA -->
      <p class="section">Analyse IA</p>
      <div class="verdict">
        <div class="verdict-text">{case.verdict}</div>
      </div>

      <!-- Pièces à conviction -->
      <p class="section">Signaux détectés</p>
      <div class="evidence">
        {evidence_html}
      </div>

      <!-- Timeline -->
      <p class="section">Historique récent de la carte</p>
      <div class="timeline">
        {previous_html}
      </div>

    </div>

    <!-- FOOTER -->
    <div class="footer">
      <div class="actions">
        <button class="btn btn-fraud" type="button">{_ICON_ARROW_LEFT} Fraude</button>
        <button class="btn btn-escalate" type="button">{_ICON_ARROW_UP} Escalader</button>
        <button class="btn btn-innocent" type="button">Légitime {_ICON_ARROW_RIGHT}</button>
      </div>
      <div class="shortcuts">
        <span class="shortcut"><span class="kbd">A</span><span class="kbd">←</span> fraude</span>
        <span class="dot-sep">·</span>
        <span class="shortcut"><span class="kbd">E</span><span class="kbd">↑</span> escalader</span>
        <span class="dot-sep">·</span>
        <span class="shortcut"><span class="kbd">D</span><span class="kbd">→</span> légitime</span>
        <span class="dot-sep">·</span>
        <span class="shortcut"><span class="kbd">Z</span> annuler</span>
      </div>
    </div>

  </div>
</body>
</html>
"""
