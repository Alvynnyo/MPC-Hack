"""
[P3] Rendu HTML/CSS de la carte "Dossier d'enquête".

Cette carte est insérée dans Streamlit via st.components.v1.html()
(iframe isolée). Tout le CSS est inline pour rester self-contained.

Voir design-system/fraud-hunter/MASTER.md pour les règles visuelles.
"""
from __future__ import annotations

from src.ui.mock_data import CaseFile, Evidence, PreviousTx


def _score_bar(score: float, width: int = 10) -> str:
    """Barre ASCII style ▰▰▰▰▰▰▰▰▰░ pour le score."""
    filled = round(score * width)
    return "▰" * filled + "░" * (width - filled)


def _evidence_marker(severity: str) -> str:
    """Renvoie le caractère marqueur selon la sévérité."""
    return {"critical": "✗", "warning": "⚠", "info": "✓"}.get(severity, "•")


def _evidence_color(severity: str) -> str:
    """Couleur du marqueur selon la sévérité (tokens du design system)."""
    return {
        "critical": "#B91C1C",  # stamp-red
        "warning": "#B45309",   # stamp-amber
        "info": "#15803D",      # stamp-green
    }.get(severity, "#4A4A4A")


def _previous_status(status: str) -> tuple[str, str]:
    """Renvoie (icône, couleur) pour le statut d'une transaction précédente."""
    if status == "current":
        return "⚠ THIS", "#B91C1C"
    if status == "suspect":
        return "?", "#B45309"
    return "✓", "#4A4A4A"


def _render_evidence(items: list[Evidence]) -> str:
    rows = []
    for ev in items:
        marker = _evidence_marker(ev.severity)
        color = _evidence_color(ev.severity)
        rows.append(
            f"""
            <div class="ev-row">
              <span class="ev-marker" style="color: {color};">{marker}</span>
              <span class="ev-label">{ev.label}</span>
              <span class="ev-value">{ev.value}</span>
              <span class="ev-tag" style="color: {color};">[{ev.tag}]</span>
            </div>
            """
        )
    return "\n".join(rows)


def _render_previous(items: list[PreviousTx]) -> str:
    rows = []
    for tx in items:
        icon, color = _previous_status(tx.status)
        emphasis = "font-weight: 700;" if tx.status == "current" else ""
        rows.append(
            f"""
            <div class="tx-row" style="{emphasis}">
              <span class="tx-date">{tx.date}</span>
              <span class="tx-merchant">{tx.merchant}</span>
              <span class="tx-amount">{tx.amount:>7.2f}&nbsp;$</span>
              <span class="tx-status" style="color: {color};">{icon}</span>
            </div>
            """
        )
    return "\n".join(rows)


def render_case_card(case: CaseFile) -> str:
    """Renvoie le HTML complet (avec CSS inline) d'une carte dossier."""
    score_bar = _score_bar(case.score)
    evidence_html = _render_evidence(case.evidence)
    previous_html = _render_previous(case.previous)

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  font-family: 'Space Mono', monospace;
  background-color: #FDFBF7;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
  color: #1A1A1A;
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}}

.card {{
  width: min(640px, 100%);
  background-color: #FDFBF7;
  border: 1px solid #D4A574;
  box-shadow: 0 2px 0 #4A4A4A, 0 4px 12px rgba(0,0,0,0.08);
  position: relative;
}}

/* Header crénelé */
.card-header {{
  background-color: #F5F0E6;
  padding: 14px 24px;
  border-bottom: 1px dashed #C4A77D;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}}

.case-id {{
  color: #1A1A1A;
}}

.case-counter {{
  color: #4A4A4A;
  font-weight: 400;
  font-size: 11px;
}}

/* Section identité */
.card-body {{
  padding: 24px;
}}

.identity {{
  margin-bottom: 20px;
}}

.id-row {{
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}}

.id-label {{
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #4A4A4A;
  font-weight: 700;
}}

.id-value {{
  font-weight: 700;
  font-size: 16px;
}}

.score-bar {{
  font-weight: 700;
  letter-spacing: 0.05em;
}}

/* Séparateurs */
.sep {{
  text-align: center;
  font-size: 11px;
  letter-spacing: 0.15em;
  color: #C4A77D;
  margin: 18px 0 12px;
}}

/* Verdict IA */
.verdict {{
  font-size: 14px;
  line-height: 1.6;
  color: #1A1A1A;
  padding: 0 8px;
}}

/* Pièces à conviction */
.evidence {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.ev-row {{
  display: grid;
  grid-template-columns: 24px 80px 1fr auto;
  gap: 10px;
  align-items: center;
  font-size: 13px;
  padding: 4px 0;
}}

.ev-marker {{
  font-weight: 700;
  font-size: 16px;
  text-align: center;
}}

.ev-label {{
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #4A4A4A;
}}

.ev-value {{
  font-weight: 400;
  color: #1A1A1A;
}}

.ev-tag {{
  font-size: 11px;
  letter-spacing: 0.05em;
  font-weight: 700;
}}

/* Timeline */
.timeline {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}}

.tx-row {{
  display: grid;
  grid-template-columns: 100px 1fr 100px 60px;
  gap: 8px;
  align-items: center;
  padding: 3px 0;
}}

.tx-date {{
  color: #4A4A4A;
  font-size: 12px;
}}

.tx-merchant {{
  color: #1A1A1A;
}}

.tx-amount {{
  text-align: right;
  font-variant-numeric: tabular-nums;
}}

.tx-status {{
  text-align: right;
  font-size: 11px;
  letter-spacing: 0.05em;
}}

/* Footer actions */
.card-footer {{
  padding: 16px 24px;
  border-top: 1px dashed #C4A77D;
  background-color: #F5F0E6;
}}

.actions {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}}

.btn {{
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 10px 12px;
  border: 1px solid #1A1A1A;
  background-color: #FDFBF7;
  color: #1A1A1A;
  cursor: pointer;
  transition: background-color 200ms, color 200ms;
}}

.btn:hover {{
  background-color: #1A1A1A;
  color: #FDFBF7;
}}

.btn:focus-visible {{
  outline: 2px solid #1A1A1A;
  outline-offset: 2px;
}}

.btn-fraud {{ border-color: #B91C1C; color: #B91C1C; }}
.btn-fraud:hover {{ background-color: #B91C1C; color: #FDFBF7; }}

.btn-innocent {{ border-color: #15803D; color: #15803D; }}
.btn-innocent:hover {{ background-color: #15803D; color: #FDFBF7; }}

.btn-escalate {{ border-color: #B45309; color: #B45309; }}
.btn-escalate:hover {{ background-color: #B45309; color: #FDFBF7; }}

.shortcuts {{
  text-align: center;
  font-size: 10px;
  letter-spacing: 0.1em;
  color: #4A4A4A;
  margin-top: 6px;
}}

.kbd {{
  display: inline-block;
  padding: 1px 6px;
  border: 1px solid #C4A77D;
  background-color: #FDFBF7;
  color: #1A1A1A;
  font-weight: 700;
  margin: 0 2px;
}}
</style>
</head>
<body>
  <div class="card">

    <div class="card-header">
      <div class="case-id">▒░▒░ DOSSIER #{case.case_id} ░▒░▒</div>
      <div class="case-counter">{case.case_index}/{case.case_total} traités</div>
    </div>

    <div class="card-body">

      <div class="identity">
        <div class="id-row">
          <span class="id-label">Suspect</span>
          <span class="id-value">{case.card_id}</span>
        </div>
        <div class="id-row">
          <span class="id-label">Montant</span>
          <span class="id-value">{case.amount:,.2f} $</span>
        </div>
        <div class="id-row">
          <span class="id-label">Score</span>
          <span class="id-value">
            <span class="score-bar">{score_bar}</span>
            &nbsp;{case.score:.2f} — {case.risk_label}
          </span>
        </div>
      </div>

      <div class="sep">─── VERDICT IA ───</div>
      <div class="verdict">{case.verdict}</div>

      <div class="sep">─── PIÈCES À CONVICTION ───</div>
      <div class="evidence">
        {evidence_html}
      </div>

      <div class="sep">─── 5 DERNIÈRES SUR CETTE CARTE ───</div>
      <div class="timeline">
        {previous_html}
      </div>

    </div>

    <div class="card-footer">
      <div class="actions">
        <button class="btn btn-fraud" type="button">← Classer fraude</button>
        <button class="btn btn-escalate" type="button">↑ Escalader</button>
        <button class="btn btn-innocent" type="button">Innocenter →</button>
      </div>
      <div class="shortcuts">
        <span class="kbd">A</span> ou <span class="kbd">←</span> fraude
        &nbsp;·&nbsp;
        <span class="kbd">E</span> ou <span class="kbd">↑</span> escalader
        &nbsp;·&nbsp;
        <span class="kbd">D</span> ou <span class="kbd">→</span> innocenter
        &nbsp;·&nbsp;
        <span class="kbd">Z</span> annuler
      </div>
    </div>

  </div>
</body>
</html>
"""
