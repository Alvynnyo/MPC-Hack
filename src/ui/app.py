"""
[P3] UI Streamlit — "Dossier d'enquête" (Paper Detective + Tinder swipe).

Lancement :
    python -m streamlit run src/ui/app.py

Voir design-system/fraud-hunter/MASTER.md pour les règles visuelles.
Voir PLAN.md étape 5 pour le comportement.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from src.ui.mock_data import MOCK_CASE
from src.ui.case_card import render_case_card


def main() -> None:
    st.set_page_config(
        page_title="Fraud Hunter — Dossier d'enquête",
        page_icon="🔍",  # Temporaire — à remplacer par favicon SVG en fin de projet
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Page background (paper texture) — appliqué au body Streamlit
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

        /* Fond bureau sombre — fait ressortir la chemise manille */
        .stApp {
            background-color: #1F1B17;
            background-image:
                radial-gradient(ellipse at center top, #3A332A 0%, #1F1B17 65%);
        }

        /* Réduit le padding du conteneur principal pour centrer la carte */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 760px;
        }

        /* Cache le menu burger et footer Streamlit pour démo */
        #MainMenu, footer, header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # En-tête de page (titre app) — léger, sur fond sombre
    st.markdown(
        """
        <div style="font-family: 'Space Mono', monospace; text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 11px; letter-spacing: 0.3em; color: #C4A77D;">
                ▒░▒░ FRAUD HUNTER ░▒░▒
            </div>
            <div style="font-size: 10px; letter-spacing: 0.2em; color: #6B5D3F; margin-top: 4px;">
                BUREAU D'ENQUÊTE — TRUST &amp; SAFETY
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Carte dossier (mockée pour l'instant)
    card_html = render_case_card(MOCK_CASE)
    components.html(card_html, height=1100, scrolling=False)


if __name__ == "__main__":
    main()
