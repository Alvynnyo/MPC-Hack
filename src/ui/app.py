"""
[P3] UI Streamlit — "Dossier d'enquête" (file de triage pro).

Lancement :
    python -m streamlit run src/ui/app.py

Voir design-system/fraud-hunter/MASTER.md pour les règles visuelles.
Voir PLAN.md étape 5 pour le comportement.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

#from src.ui.mock_data import MOCK_CASES
from src.ui.swipe_deck import render_swipe_deck

from src.controler import initialize_fraud_queue
from src.scoring import Weights
from src.feedback import FeedbackManager
from src.ui.swipe_deck import render_swipe_deck


def main() -> None:
    st.set_page_config(
        page_title="Fraud Hunter",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Style global de l'app (fond clair, header pro)
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Fond clair neutre */
        .stApp {
            background: #F2F4F7;
        }

        .block-container {
            padding-top: 2.5rem;
            padding-bottom: 2rem;
            max-width: 640px;
        }

        /* Cache le menu burger et footer Streamlit pour démo */
        #MainMenu, footer, header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # En-tête de page (titre app) — sobre, sur fond clair
    st.markdown(
        """
        <div style="font-family: 'Inter', sans-serif; margin-bottom: 1.25rem;
                    display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 28px; height: 28px; border-radius: 7px;
                            background: #101828; display: flex; align-items: center;
                            justify-content: center;">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none"
                         stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"
                         stroke-linejoin="round"><circle cx="11" cy="11" r="8"/>
                         <path d="m21 21-4.3-4.3"/></svg>
                </div>
                <span style="font-size: 16px; font-weight: 600; color: #101828;">Fraud Hunter</span>
            </div>
            <span style="font-size: 12px; color: #98A2B3;">Trust &amp; Safety · File de révision</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- INITIALISATION DE L'ÉTAT ET DES DONNÉES RÉELLES ---
    if "feedback" not in st.session_state:
        st.session_state.feedback = FeedbackManager()

    @st.cache_data(show_spinner=False)
    def fetch_real_cases(_feedback):
        return initialize_fraud_queue(
            csv_path="data/transactions.csv",
            # weights=Weights(w1=0.25, w2=0.25, w3=0.25, w4=0.25),
            threshold=0.28,
            feedback_manager=_feedback
        )

    with st.spinner("Analyse des transactions et verdicts IA en cours..."):
        cases_queue = fetch_real_cases(st.session_state.feedback)

    if not cases_queue:
        st.success("File d'attente vide. Aucune fraude détectée.")
        return

    deck_html = render_swipe_deck(cases_queue)
    components.html(deck_html, height=1160, scrolling=False)   

if __name__ == "__main__":
    main()
