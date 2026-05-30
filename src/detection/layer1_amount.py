"""
[P1] Couche 1 — Écart de montant anormal.

Cherche : une transaction dont le montant explose par rapport aux habitudes
de la carte (amount > N × médiane de la carte).

Voir PLAN.md, étape 2, couche 1.
"""
from __future__ import annotations

import pandas as pd


def score_amount_deviation(df: pd.DataFrame, card_profiles: dict) -> pd.Series:
    """
    Retourne un score [0, 1] par transaction, indexé sur df.index.

    Idée : ratio = amount / médiane(card). On mappe le ratio à [0, 1] via une
    sigmoïde ou un clamp simple (ex: min(ratio / 15, 1)).

    TODO P1 : implémenter et calibrer.
    """
    raise NotImplementedError
