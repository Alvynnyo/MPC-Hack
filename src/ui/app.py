from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from src.controler import initialize_fraud_queue
from src.scoring import Weights
from src.feedback import FeedbackManager
from src import audit

# --- AJOUT DES IMPORTS MANQUANTS POUR L'INTERFACE ---
from src.ui.swipe_deck import render_swipe_deck


# Mappage décision UI -> labels backend
_AUDIT_DECISION = {"fraud": "approve_fraud", "legit": "dismiss", "escalate": "escalate"}
_FEEDBACK_LABEL = {"legit": "Innocenter", "fraud": "Classer"}  # escalate = neutre


def render_decision_importer() -> None:
    """Téléverse le rapport JSON exporté par le deck et le rejoue côté serveur :
    alimente le FeedbackManager (modificateurs) et persiste l'audit log."""
    with st.expander("Importer un rapport de décisions (audit + feedback)"):
        up = st.file_uploader("Glissez le fichier decisions.json", type="json", key="dec_upload")
        data = None
        if up is not None:
            try:
                data = json.load(up)
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"JSON invalide : {exc}")

        if data and st.button("Enregistrer ces décisions", type="primary"):
            fb = st.session_state.feedback
            processed = 0
            for d in data:
                dec = d.get("decision")
                if not dec:
                    continue  # dossier non traité
                label = _FEEDBACK_LABEL.get(dec)
                if label:
                    fb.record_decision(
                        {"merchant_category": d.get("category"), "device_id": d.get("device_id")},
                        label,
                    )
                audit.log_decision(
                    transaction_id=d.get("case_id", ""),
                    decision=_AUDIT_DECISION.get(dec, "dismiss"),
                    initial_score=d.get("score", 0.0),
                    reasons=[f"catégorie {d.get('category', '?')}"],
                )
                processed += 1
            st.success(f"{processed} décision(s) enregistrée(s) dans l'audit log.")
            mods = {**fb.category_modifiers, **fb.device_modifiers}
            if mods:
                st.caption("Modificateurs appris (rejoués au prochain scoring) :")
                st.json(mods)

        log = audit.load_audit_log()
        if log:
            st.caption(f"Audit log — {len(log)} entrée(s) (15 dernières) :")
            st.dataframe(log[-15:], use_container_width=True, hide_index=True)

def main() -> None:
    st.set_page_config(
        page_title="Fraud Hunter",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Feuille de style globale de l'application (Fond neutre et conteneur centré)
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        .stApp {
            background: #F2F4F7;
        }

        .block-container {
            padding-top: 2.5rem;
            padding-bottom: 2rem;
            max-width: 640px;
        }

        /* Masquage des ornements Streamlit pour épurer la démo technique */
        #MainMenu, footer, header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # En-tête de la plateforme (Branding minimalist et professionnel)
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
            <span style="font-size: 12px; color: #98A2B3;">Trust &amp; Safety · File de révision en direct</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- INITIALISATION DE L'ÉTAT ET DES DONNÉES RÉELLES ---
    if "feedback" not in st.session_state:
        st.session_state.feedback = FeedbackManager()

    def fetch_real_cases(_feedback):
        return initialize_fraud_queue(
            csv_path="data/transactions.csv",
            threshold=0.28,
            feedback_manager=_feedback
        )

    with st.spinner("Analyse multicouche des transactions et verdicts IA..."):
        cases_queue = fetch_real_cases(st.session_state.feedback)

    if not cases_queue:
        st.success("Félicitations. La file de triage est vide. Aucun risque détecté.")
        return

    # Compilation et rendu du deck interactif de cartes
    deck_html = render_swipe_deck(cases_queue)
    
    # --- OPTIMISATION : Hauteur ajustée de 1250 à 680 suite au fix CSS compact ---
    components.html(deck_html, height=1600, scrolling=False)

    render_decision_importer()

if __name__ == "__main__":
    main()