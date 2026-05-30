"""
[P1] Couche 2 — Burst temporel (loi de Poisson).

Cherche : un rythme de transactions statistiquement improbable, soit chez
un marchand précis (terminal compromis), soit sur une carte précise (card testing).

Voir PLAN.md, étape 2, couche 2.
"""
from __future__ import annotations

import pandas as pd
from scipy.stats import poisson
import numpy as np


def score_burst_poisson(df: pd.DataFrame) -> pd.Series:
    """Détecte des bursts temporels via la loi de Poisson.

    Retourne une `pd.Series` de scores [0,1] indexée comme `df`.
    """
    if df.empty:
        return pd.Series(dtype=float, index=df.index)

    df2 = df.copy()
    df2["timestamp"] = pd.to_datetime(df2["timestamp"])

    span_hours = max(
        (df2["timestamp"].max() - df2["timestamp"].min()).total_seconds() / 3600,
        1e-6,
    )

    merchant_counts = df2["merchant_name"].value_counts()
    merchant_rate_per_hour = (merchant_counts / span_hours).to_dict()
    card_counts = df2["card_id"].value_counts()
    card_rate_per_hour = (card_counts / span_hours).to_dict()

    def window_counts(series_ts: pd.Series, window_seconds: int):
        res = np.zeros(len(series_ts), dtype=int)
        if series_ts.empty:
            return res
        ts_ns = series_ts.values.astype("datetime64[ns]").astype("int64")
        ts_s = (ts_ns // 10**9).astype("int64")
        for i in range(len(ts_s)):
            left = ts_s[i] - window_seconds
            l = np.searchsorted(ts_s, left, side="left")
            res[i] = i - l + 1
        return res

    merchant_counts_window = np.zeros(len(df2), dtype=int)
    card_counts_window = np.zeros(len(df2), dtype=int)

    two_hours = 2 * 3600
    for _, grp in df2.groupby("merchant_name"):
        idx = grp.index
        counts = window_counts(grp["timestamp"].reset_index(drop=True), two_hours)
        merchant_counts_window[idx] = counts

    thirty_mins = 30 * 60
    for _, grp in df2.groupby("card_id"):
        idx = grp.index
        counts = window_counts(grp["timestamp"].reset_index(drop=True), thirty_mins)
        card_counts_window[idx] = counts

    scores = np.zeros(len(df2), dtype=float)

    for i, row in df2.reset_index(drop=True).iterrows():
        merchant = row.get("merchant_name")
        card = row.get("card_id")

        # Burst marchand
        k_m = int(merchant_counts_window[i])
        rate_m = float(merchant_rate_per_hour.get(merchant, 0.0))
        lam_m = max(rate_m * 2.0, 0.01)
        p_m = 1.0 - poisson.cdf(max(0, k_m - 1), lam_m)
        if p_m <= 0:
            score_m = 1.0
        else:
            score_m = min(1.0, -np.log10(p_m) / 8.0)

        # Burst carte
        k_c = int(card_counts_window[i])
        rate_c = float(card_rate_per_hour.get(card, 0.0))
        lam_c = max(rate_c * 0.5, 0.01)
        p_c = 1.0 - poisson.cdf(max(0, k_c - 1), lam_c)
        if p_c <= 0:
            score_c = 1.0
        else:
            score_c = min(1.0, -np.log10(p_c) / 8.0)

        scores[i] = max(score_m, score_c)

    return pd.Series(scores, index=df2.index)
