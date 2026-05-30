"""
[P1] Couche 4 — Fraude croisée (cross-card).

Cherche : un même device_id ou ip_address associé à > K card_id distincts
dans le dataset. Pattern invisible si on regarde les cartes une par une.

Voir PLAN.md, étape 2, couche 4.
"""
from __future__ import annotations

import pandas as pd


def score_cross_card(df: pd.DataFrame, device_profiles: dict, ip_profiles: dict) -> pd.Series:
    """
    Retourne un score [0, 1] par transaction.

    Idée : si le device de la transaction a vu > K cartes, score élevé.
    Idem pour l'IP. Prendre le max des deux.

    TODO P1 : implémenter.
    """
    raise NotImplementedError
