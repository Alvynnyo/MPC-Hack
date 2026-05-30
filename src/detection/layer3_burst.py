"""
[P1] Couche 3 — Siphonnement rapide.

Cherche : rafale de transactions (> 3) sur 10 minutes pour la même carte,
montants proches ou identiques, catégories à risque (gift_card, online_retail).

Voir PLAN.md, étape 2, couche 3.
"""
from __future__ import annotations

import pandas as pd


def score_burst(df: pd.DataFrame) -> pd.Series:
    """
    Retourne un score [0, 1] par transaction.

    Idée : fenêtre glissante de 10 minutes par card_id. Compter les transactions
    dans la fenêtre, mesurer la variance des montants. Boost si catégorie à risque.

    TODO P1 : implémenter.
    """
    raise NotImplementedError
