"""
[P1] Couche 4 — Fraude croisée (cross-card).

Cherche : un même device_id ou ip_address associé à > K card_id distincts
dans le dataset. Pattern invisible si on regarde les cartes une par une.

Voir PLAN.md, étape 2, couche 4.
"""
from __future__ import annotations

import pandas as pd

def score_cross_card(
    df: pd.DataFrame,
    device_profiles: dict,
    ip_profiles: dict,
) -> pd.Series:
    """
    Retourne un score [0, 1] par transaction.

    Pour chaque transaction, compte le nombre de cartes distinctes
    ayant utilisé le même marchand dans les 2h précédentes.
    Score fort si >= 4 cartes distinctes.
    """
    scores = pd.Series(0.0, index=df.index)

    df_temp = df.copy()
    df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])
    df_temp = df_temp.sort_values('timestamp')

    card_median = df_temp.groupby('card_id')['amount'].median().to_dict()

    scores = pd.Series(0.0, index=df_temp.index)

    for idx, row in df_temp.iterrows():
        window_start = row['timestamp'] - pd.Timedelta(hours=2)
        window_end   = row['timestamp'] + pd.Timedelta(hours=2)
        mask = (
            (df_temp['merchant_name'] == row['merchant_name'])
            & (df_temp['timestamp'] >= window_start)
            & (df_temp['timestamp'] <= window_end)
        )
        distinct_cards = df_temp[mask]['card_id'].nunique()

        if distinct_cards >= 6:
            score = 0.9
        elif distinct_cards >= 4:
            score = 0.7
        else:
            score = 0.0

        if score > 0:
            median = card_median.get(row['card_id'], row['amount'])
            ratio = row['amount'] / median if median > 0 else 1.0
            if ratio > 3:
                score += min((ratio - 1) / 20, 0.1)

        scores[idx] = min(score, 1.0)

    return scores.reindex(df.index)