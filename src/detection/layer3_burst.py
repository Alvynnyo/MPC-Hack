"""
[P1] Couche 3 — Siphonnement rapide.

Cherche : rafale de transactions (> 3) sur 10 minutes pour la même carte,
montants proches ou identiques, catégories à risque (gift_card, online_retail).

Voir PLAN.md, étape 2, couche 3.
"""
from __future__ import annotations

import pandas as pd


def score_burst(df: pd.DataFrame) -> pd.Series:
    df_temp = df.copy()
    df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])
    df_temp = df_temp.sort_values(['card_id', 'timestamp'])

    counts = []
    for idx, row in df_temp.iterrows():
        window_start = row['timestamp'] - pd.Timedelta(minutes=10)
        window_end   = row['timestamp'] + pd.Timedelta(minutes=10)
        mask = (
            (df_temp['card_id'] == row['card_id']) &
            (df_temp['timestamp'] >= window_start) &
            (df_temp['timestamp'] <= window_end)
        )
        counts.append(mask.sum())
    df_temp['tx_count_10m'] = counts

    scores = pd.Series(0.0, index=df_temp.index)

    for idx, row in df_temp.iterrows():
        score = 0.0
        count = row['tx_count_10m']

        if count >= 3:
            score += 0.4
        if count >= 5:
            score += 0.3

        cat = str(row.get('merchant_category', '')).lower()
        if count >= 3 and ('gift_card' in cat or 'online_retail' in cat):
            score += 0.3

        scores[idx] = min(score, 1.0)

    return scores.reindex(df.index)


def get_burst_transactions(
    df: pd.DataFrame,
    card_id: str,
    anchor_timestamp,
    window_minutes: int = 10,
) -> pd.DataFrame:
    """
    Retourne les transactions de la rafale réelle pour une carte donnée.

    On cherche toutes les tx de `card_id` dans la fenêtre
    [anchor_timestamp - window_minutes, anchor_timestamp + window_minutes],
    triées chronologiquement.

    Utilisé par controler.py pour construire case.previous quand
    le signal dominant est "vitesse", afin d'afficher la séquence réelle
    de la rafale plutôt que l'historique général de la carte.
    """
    df_temp = df.copy()
    df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])
    anchor = pd.to_datetime(anchor_timestamp)

    window_start = anchor - pd.Timedelta(minutes=window_minutes)
    window_end   = anchor + pd.Timedelta(minutes=window_minutes)

    mask = (
        (df_temp['card_id'] == card_id) &
        (df_temp['timestamp'] >= window_start) &
        (df_temp['timestamp'] <= window_end)
    )

    return df_temp[mask].sort_values('timestamp')