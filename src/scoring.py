"""
[P2] Scoring : combine les 4 scores en un score final pondéré.

Voir PLAN.md, étape 3.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Weights:
    """Poids des 4 couches. Doivent sommer à 1.0."""
    w1: float = 0.25
    w2: float = 0.25
    w3: float = 0.25
    w4: float = 0.25

    def validate(self) -> None:
        total = self.w1 + self.w2 + self.w3 + self.w4
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Les poids doivent sommer à 1.0 (somme actuelle: {total})")


def compute_fraud_scores(
    s1: pd.Series,
    s2: pd.Series,
    s3: pd.Series,
    s4: pd.Series,
    weights: Weights,
) -> pd.Series:
    """
    fraud_score = w1·s1 + w2·s2 + w3·s3 + w4·s4

    TODO P2 : implémenter (somme pondérée simple).
    """
    raise NotImplementedError


def flag_transactions(scores: pd.Series, threshold: float = 0.5) -> pd.Series:
    """
    Retourne un booléen par transaction : True si flaggée.

    TODO P2 : implémenter.
    """
    raise NotImplementedError
