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

        /* Fond papier sur toute l'app */
        .stApp {
            background-color: #FDFBF7;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
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

    # En-tête de page (titre app)
    st.markdown(
        """
        <div style="font-family: 'Space Mono', monospace; text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 11px; letter-spacing: 0.2em; color: #4A4A4A;">
                ▒░▒░ FRAUD HUNTER ░▒░▒
            </div>
            <div style="font-size: 11px; letter-spacing: 0.1em; color: #C4A77D; margin-top: 4px;">
                Trust &amp; Safety — Bureau d'enquête
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Carte dossier (mockée pour l'instant)
    card_html = render_case_card(MOCK_CASE)
    components.html(card_html, height=860, scrolling=False)


if __name__ == "__main__":
    main()
