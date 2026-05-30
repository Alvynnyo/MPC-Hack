"""
[P3] UI Streamlit — "Dossier d'enquête".

Lancement :
    streamlit run src/ui/app.py

Voir PLAN.md, étape 5 pour la structure d'un dossier.
"""
from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Fraud Hunter", page_icon=":mag:", layout="wide")

    st.title("Fraud Hunter — Dossier d'enquête")
    st.caption("MPC Hacks 2026 — Track Valsoft")

    # TODO P3 :
    #   1. Charger les transactions flaggées (depuis scoring.py)
    #   2. État de session : index courant, liste de décisions
    #   3. Sidebar : sliders de pondération (Weights), seuil, stats (n flaggées)
    #   4. Zone principale = un dossier à la fois
    #       - En-tête : tx_id, card_id, score, niveau de risque (badge couleur)
    #       - Verdict IA : explication générée (Claude)
    #       - Pièces à conviction : tableau avec valeur observée + référence
    #       - Timeline : 5 transactions précédentes de la carte
    #       - Boutons : [A] Classer  [D] Innocenter  [E] Escalader  [Z] Undo
    #   5. Bind keyboard shortcuts (streamlit-shortcuts ou st.text_input caché)
    #   6. Auto-advance vers le dossier suivant après chaque décision
    #   7. À la fin : écran "tous les dossiers traités" + export CSV
    st.info("UI en construction — voir PLAN.md étape 5.")


if __name__ == "__main__":
    main()
