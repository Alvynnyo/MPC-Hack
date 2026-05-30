"""
[P1] Couche 1 — Écart de montant anormal.

Cherche : une transaction dont le montant explose par rapport aux habitudes
de la carte (amount > N × médiane de la carte).

Voir PLAN.md, étape 2, couche 1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def score_amount_deviation(df: pd.DataFrame, card_profiles: dict) -> pd.Series:
    """Retourne un score [0, 1] par transaction, indexé sur df.index."""
    median_map = {cid: p["median_amount"] for cid, p in card_profiles.items()}
    iqr_map = {cid: p["iqr_amount"] for cid, p in card_profiles.items()}

    median_vals = df["card_id"].map(median_map)
    iqr_vals = df["card_id"].map(iqr_map)

    # fallback pour IQR nul ou carte inconnue
    fallback = median_vals.fillna(0) * 0.1
    scale = iqr_vals * 0.7413
    scale = scale.where(scale > 0, fallback).where(fallback > 0, 1.0)

    z = (df["amount"] - median_vals.fillna(df["amount"])) / scale
    score = (np.abs(z) / 6).clip(0.0, 1.0)

    # carte absente du profil → score 0
    unknown = df["card_id"].map(lambda cid: cid not in card_profiles)
    score = score.where(~unknown, 0.0)

    return score.rename(None)
