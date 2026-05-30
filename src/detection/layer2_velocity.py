"""
[P1] Couche 2 — Vitesse impossible.

Cherche : deux transactions in-person consécutives sur la même carte avec
des merchant_country différents en moins de quelques heures.

Voir PLAN.md, étape 2, couche 2.
"""
from __future__ import annotations

import pandas as pd


def score_impossible_velocity(df: pd.DataFrame) -> pd.Series:
    """
    Retourne un score [0, 1] par transaction.

    Idée : trier par card_id puis timestamp, comparer pour chaque transaction
    in-person la précédente du même card_id. Si pays différent ET delta < seuil
    horaire, score élevé.

    TODO P1 : implémenter.
    """
    raise NotImplementedError
