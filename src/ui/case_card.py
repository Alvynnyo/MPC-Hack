"""
[P3] Rendu HTML/CSS de la carte "Dossier d'enquête" (V2 — chemise manille).

Cette carte est insérée dans Streamlit via st.components.v1.html()
(iframe isolée). Tout le CSS est inline pour rester self-contained.

Inspirations visuelles : design-system/fraud-hunter/refs/
Voir design-system/fraud-hunter/MASTER.md pour les règles visuelles.
"""
from __future__ import annotations

from src.ui.mock_data import CaseFile, Evidence, PreviousTx


# --- Helpers d'affichage --------------------------------------------------- #

def _score_bar(score: float, width: int = 10) -> str:
    """Barre ASCII style ▰▰▰▰▰▰▰▰▰░ pour le score."""
    filled = round(score * width)
    return "▰" * filled + "░" * (width - filled)


def _badge_variant(severity: str) -> tuple[str, str, str]:
    """(background, text, border) selon la sévérité — pattern 21st.dev."""
    return {
        "critical": ("#FEE2E2", "#B91C1C", "#FCA5A5"),
        "warning":  ("#FEF3C7", "#B45309", "#FCD34D"),
        "info":     ("#DCFCE7", "#15803D", "#86EFAC"),
    }.get(severity, ("#F5F5F5", "#4A4A4A", "#D4D4D4"))


def _evidence_marker(severity: str) -> str:
    return {"critical": "✗", "warning": "⚠", "info": "✓"}.get(severity, "•")


def _previous_status(status: str) -> tuple[str, str, str]:
    """(label, color, prefix). Prefix vide ou '▶ ' pour la transaction courante."""
    if status == "current":
        return "THIS", "#B91C1C", "▶ "
    if status == "suspect":
        return "?", "#B45309", "  "
    return "OK", "#15803D", "  "


# --- Renderers de sections ------------------------------------------------- #

def _render_avatar_svg() -> str:
    """Silhouette utilisateur stylisée pour le polaroid suspect."""
    return """
    <svg viewBox="0 0 40 40" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="40" height="40" fill="#E5DDD0"/>
      <circle cx="20" cy="15" r="6" fill="#8B7355" opacity="0.8"/>
      <path d="M 8 36 Q 8 24 20 24 Q 32 24 32 36 L 32 40 L 8 40 Z" fill="#8B7355" opacity="0.8"/>
      <rect x="0" y="0" width="40" height="40" fill="none" stroke="#000" stroke-width="0.5" opacity="0.1"/>
    </svg>
    """


def _render_evidence(items: list[Evidence]) -> str:
    rows = []
    for ev in items:
        bg, text, border = _badge_variant(ev.severity)
        marker = _evidence_marker(ev.severity)
        marker_color = {"critical": "#B91C1C", "warning": "#B45309", "info": "#15803D"}.get(
            ev.severity, "#4A4A4A"
        )
        rows.append(
            f"""
            <div class="ev-row">
              <span class="ev-marker" style="color: {marker_color};">{marker}</span>
              <span class="ev-label">{ev.label}</span>
              <span class="ev-value">{ev.value}</span>
              <span class="badge" style="background: {bg}; color: {text}; border-color: {border};">{ev.tag}</span>
            </div>
            """
        )
    return "\n".join(rows)


def _render_previous(items: list[PreviousTx]) -> str:
    rows = []
    for tx in items:
        label, color, prefix = _previous_status(tx.status)
        emphasis = "background: rgba(254,243,199,0.5);" if tx.status == "current" else ""
        rows.append(
            f"""
            <div class="tx-row" style="{emphasis}">
              <span class="tx-prefix" style="color: {color};">{prefix}</span>
              <span class="tx-date">{tx.date}</span>
              <span class="tx-merchant">{tx.merchant}</span>
              <span class="tx-amount">{tx.amount:>7.2f}&nbsp;$</span>
              <span class="tx-status" style="color: {color};">{label}</span>
            </div>
            """
        )
    return "\n".join(rows)


def _render_kbd(key: str) -> str:
    """Rendu d'une touche clavier (inspiré du composant kbd-1 de 21st.dev)."""
    return f'<kbd class="kbd">{key}</kbd>'


# --- Render principal ------------------------------------------------------ #

def render_case_card(case: CaseFile) -> str:
    """Renvoie le HTML complet (avec CSS inline) d'une carte dossier — V2."""
    score_bar = _score_bar(case.score)
    evidence_html = _render_evidence(case.evidence)
    previous_html = _render_previous(case.previous)
    avatar_svg = _render_avatar_svg()

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Caveat:wght@400;700&display=swap');

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  font-family: 'Space Mono', monospace;
  /* Fond sombre du bureau autour de la chemise */
  background-color: #2A2620;
  background-image:
    radial-gradient(ellipse at top, #3A332A 0%, #1F1B17 100%);
  color: #1A1A1A;
  padding: 24px 16px 48px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
}}

/* ─────────────────────────────────────────────
   CHEMISE MANILLE (l'enveloppe du dossier)
   ───────────────────────────────────────────── */

.folder {{
  position: relative;
  width: min(680px, 100%);
  background-color: #E8D9B0;
  background-image:
    /* Grain papier */
    url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.22'/%3E%3C/svg%3E"),
    /* Légère variation de teinte */
    linear-gradient(180deg, #ECDCB4 0%, #E0D0A4 100%);
  border: 1px solid #B8A074;
  box-shadow:
    /* Pli + ombre portée */
    inset 16px 0 0 -12px #C4A862,
    inset 0 -2px 0 -1px #B8A074,
    0 4px 0 #A89060,
    0 12px 28px rgba(0, 0, 0, 0.55),
    0 24px 40px rgba(0, 0, 0, 0.35);
  padding: 0 0 20px 28px; /* padding-left + reserve la place du pli */
  overflow: hidden;
}}

/* Pli vertical (épaisseur de la chemise) */
.folder::before {{
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 14px;
  background:
    linear-gradient(90deg, #B8A074 0%, #D4B870 60%, transparent 100%);
  opacity: 0.85;
}}

/* Trous de classeur sur le pli */
.folder .punch {{
  position: absolute;
  left: 4px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2A2620;
  box-shadow: 0 1px 0 rgba(255,255,255,0.15);
}}

/* ─────────────────────────────────────────────
   HEADER : titre dossier + tampon + polaroid
   ───────────────────────────────────────────── */

.case-header {{
  position: relative;
  padding: 22px 28px 18px;
  border-bottom: 2px dashed #B8A074;
  display: grid;
  grid-template-columns: 70px 1fr auto;
  gap: 18px;
  align-items: center;
}}

.polaroid {{
  width: 60px;
  height: 72px;
  background: #FAFAF5;
  padding: 4px 4px 12px;
  border: 1px solid #D4C8A0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  transform: rotate(-3deg);
}}

.polaroid svg {{
  display: block;
}}

.case-title {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

.case-id {{
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #1A1A1A;
  text-transform: uppercase;
}}

.case-meta {{
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6B5D3F;
}}

/* Tampon rouge "DOSSIER ACTIF" */
.stamp {{
  font-family: 'Space Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #B91C1C;
  border: 3px solid #B91C1C;
  padding: 6px 12px;
  transform: rotate(-8deg);
  filter: contrast(1.1);
  opacity: 0.88;
  position: relative;
  white-space: nowrap;
}}

.stamp::before {{
  content: '';
  position: absolute;
  inset: -2px;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='r'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='2' /%3E%3CfeDisplacementMap in='SourceGraphic' scale='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' fill='%23FFFFFF' filter='url(%23r)' opacity='0.15'/%3E%3C/svg%3E");
  mix-blend-mode: lighten;
  pointer-events: none;
}}

/* ─────────────────────────────────────────────
   BODY : sections du dossier
   ───────────────────────────────────────────── */

.body {{
  padding: 22px 28px 8px;
}}

/* Bloc identité */
.identity {{
  margin-bottom: 8px;
}}

.id-row {{
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 14px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}}

.id-label {{
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6B5D3F;
  font-weight: 700;
}}

.id-value {{
  font-weight: 700;
  font-size: 15px;
  color: #1A1A1A;
}}

.score-bar {{
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #B91C1C;
}}

/* Séparateurs section */
.section-label {{
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 22px 0 12px;
}}

.section-label::before,
.section-label::after {{
  content: '';
  flex: 1;
  height: 1px;
  background: repeating-linear-gradient(
    90deg,
    #B8A074 0,
    #B8A074 4px,
    transparent 4px,
    transparent 8px
  );
}}

.section-label span {{
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #6B5D3F;
  font-weight: 700;
}}

/* ─────────────────────────────────────────────
   POST-IT : verdict IA
   ───────────────────────────────────────────── */

.postit-wrap {{
  position: relative;
  margin: 14px auto 22px;
  width: min(440px, 90%);
}}

.postit {{
  position: relative;
  background:
    linear-gradient(135deg, #FDF09C 0%, #F5E47A 100%);
  padding: 22px 22px 20px;
  font-family: 'Caveat', 'Space Mono', cursive;
  font-size: 18px;
  line-height: 1.45;
  color: #1A1A1A;
  transform: rotate(-1.2deg);
  box-shadow:
    0 1px 1px rgba(0,0,0,0.15),
    0 6px 12px rgba(0,0,0,0.25),
    0 18px 24px rgba(0,0,0,0.20);
}}

.postit::after {{
  /* Coin écorné en bas à droite */
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  background:
    linear-gradient(225deg,
      rgba(0,0,0,0.18) 0%,
      transparent 40%),
    linear-gradient(135deg, transparent 50%, #E0D0A4 50%);
}}

.tape {{
  position: absolute;
  top: -10px;
  width: 60px;
  height: 18px;
  background: rgba(220, 210, 180, 0.55);
  border: 1px solid rgba(180, 165, 130, 0.3);
  box-shadow: 0 1px 2px rgba(0,0,0,0.12);
}}

.tape-left {{
  left: 12px;
  transform: rotate(-6deg);
}}

.tape-right {{
  right: 12px;
  transform: rotate(7deg);
}}

/* ─────────────────────────────────────────────
   PIÈCES À CONVICTION
   ───────────────────────────────────────────── */

.evidence {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}}

.ev-row {{
  display: grid;
  grid-template-columns: 24px 90px 1fr auto;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  padding: 6px 4px;
  border-bottom: 1px dotted rgba(184, 160, 116, 0.4);
}}

.ev-row:last-child {{
  border-bottom: none;
}}

.ev-marker {{
  font-weight: 700;
  font-size: 16px;
  text-align: center;
}}

.ev-label {{
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6B5D3F;
  font-weight: 700;
}}

.ev-value {{
  font-weight: 400;
  color: #1A1A1A;
  font-size: 13px;
}}

/* Badge inspiré 21st.dev — variant system */
.badge {{
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  font-family: 'Space Mono', monospace;
}}

/* ─────────────────────────────────────────────
   TIMELINE
   ───────────────────────────────────────────── */

.timeline {{
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  background: rgba(255, 250, 235, 0.5);
  padding: 8px 10px;
  border: 1px solid rgba(184, 160, 116, 0.3);
}}

.tx-row {{
  display: grid;
  grid-template-columns: 16px 90px 1fr 80px 48px;
  gap: 8px;
  align-items: center;
  padding: 4px 6px;
  border-radius: 2px;
}}

.tx-prefix {{
  font-weight: 700;
  font-size: 11px;
}}

.tx-date {{
  color: #6B5D3F;
  font-size: 11px;
}}

.tx-merchant {{
  color: #1A1A1A;
  font-size: 12px;
}}

.tx-amount {{
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}}

.tx-status {{
  text-align: right;
  font-size: 10px;
  letter-spacing: 0.08em;
  font-weight: 700;
}}

/* ─────────────────────────────────────────────
   FOOTER : actions + raccourcis
   ───────────────────────────────────────────── */

.footer {{
  padding: 18px 28px 4px;
  border-top: 2px dashed #B8A074;
  background: rgba(0, 0, 0, 0.03);
  margin-top: 20px;
}}

.actions {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}}

.btn {{
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 12px 8px;
  border: 1.5px solid #1A1A1A;
  background-color: #FAFAF5;
  color: #1A1A1A;
  cursor: pointer;
  transition: transform 120ms, background-color 180ms, color 180ms;
  box-shadow: 0 2px 0 rgba(0,0,0,0.25);
}}

.btn:hover {{
  transform: translateY(-1px);
  box-shadow: 0 3px 0 rgba(0,0,0,0.30);
}}

.btn:active {{
  transform: translateY(1px);
  box-shadow: 0 1px 0 rgba(0,0,0,0.20);
}}

.btn:focus-visible {{
  outline: 2px solid #1A1A1A;
  outline-offset: 3px;
}}

.btn-fraud {{ border-color: #B91C1C; color: #B91C1C; }}
.btn-fraud:hover {{ background-color: #B91C1C; color: #FAFAF5; }}

.btn-escalate {{ border-color: #B45309; color: #B45309; }}
.btn-escalate:hover {{ background-color: #B45309; color: #FAFAF5; }}

.btn-innocent {{ border-color: #15803D; color: #15803D; }}
.btn-innocent:hover {{ background-color: #15803D; color: #FAFAF5; }}

/* Composant Kbd (inspiré kbd-1 de 21st.dev) */
.kbd {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #1A1A1A;
  background: #FAFAF5;
  border: 1px solid #B8A074;
  border-radius: 4px;
  box-shadow: 0 1px 0 #B8A074, 0 2px 0 rgba(0,0,0,0.15);
  margin: 0 1px;
}}

.shortcuts {{
  text-align: center;
  font-size: 11px;
  letter-spacing: 0.05em;
  color: #6B5D3F;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}}

.shortcut-group {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}

.shortcut-sep {{
  color: #B8A074;
  margin: 0 6px;
}}
</style>
</head>
<body>
  <div class="folder">
    <!-- Trous de classeur sur le pli -->
    <span class="punch" style="top: 18%;"></span>
    <span class="punch" style="top: 50%;"></span>
    <span class="punch" style="top: 82%;"></span>

    <!-- HEADER -->
    <div class="case-header">
      <div class="polaroid">{avatar_svg}</div>

      <div class="case-title">
        <div class="case-id">DOSSIER #{case.case_id}</div>
        <div class="case-meta">{case.case_index} / {case.case_total} traités · Trust &amp; Safety</div>
      </div>

      <div class="stamp">DOSSIER ACTIF</div>
    </div>

    <!-- BODY -->
    <div class="body">

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

      <!-- POST-IT VERDICT IA -->
      <div class="section-label"><span>Verdict IA</span></div>

      <div class="postit-wrap">
        <div class="postit">
          <span class="tape tape-left"></span>
          <span class="tape tape-right"></span>
          {case.verdict}
        </div>
      </div>

      <!-- PIÈCES À CONVICTION -->
      <div class="section-label"><span>Pièces à conviction</span></div>
      <div class="evidence">
        {evidence_html}
      </div>

      <!-- TIMELINE -->
      <div class="section-label"><span>5 dernières transactions de la carte</span></div>
      <div class="timeline">
        {previous_html}
      </div>

    </div>

    <!-- FOOTER -->
    <div class="footer">
      <div class="actions">
        <button class="btn btn-fraud" type="button">← Classer fraude</button>
        <button class="btn btn-escalate" type="button">↑ Escalader</button>
        <button class="btn btn-innocent" type="button">Innocenter →</button>
      </div>
      <div class="shortcuts">
        <span class="shortcut-group">{_render_kbd('A')}<span style="margin: 0 4px;">ou</span>{_render_kbd('←')}<span style="margin-left: 4px;">fraude</span></span>
        <span class="shortcut-sep">·</span>
        <span class="shortcut-group">{_render_kbd('E')}<span style="margin: 0 4px;">ou</span>{_render_kbd('↑')}<span style="margin-left: 4px;">escalader</span></span>
        <span class="shortcut-sep">·</span>
        <span class="shortcut-group">{_render_kbd('D')}<span style="margin: 0 4px;">ou</span>{_render_kbd('→')}<span style="margin-left: 4px;">innocenter</span></span>
        <span class="shortcut-sep">·</span>
        <span class="shortcut-group">{_render_kbd('Z')}<span style="margin-left: 4px;">annuler</span></span>
      </div>
    </div>

  </div>
</body>
</html>
"""
