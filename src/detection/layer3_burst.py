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
    df_temp = df_temp.sort_values("timestamp").copy()
    df_temp["tx_count_10m"] = 0.0

    scores = pd.Series(0.0, index=df_temp.index)

    for card_id, grp in df_temp.groupby("card_id"):
        grp = grp.sort_values("timestamp")
        counts = (
            grp.rolling("10min", on="timestamp")["amount"]
            .count()
            .values
        )
        df_temp.loc[grp.index, "tx_count_10m"] = counts

    for idx, row in df_temp.iterrows():
        score = 0.0
        count = row['tx_count_10m']

        if count >= 3:
            score += 0.4
        if count >= 5:
            score += 0.5


        cat = str(row.get('merchant_category', '')).lower()
        if count >= 3 and ('gift_card' in cat or 'online_retail' in cat):
            score += 0.2

        scores[idx] = min(score, 1.0)


    print(f"[DEBUG layer3] min={scores.min():.3f} max={scores.max():.3f} nonzero={(scores > 0).sum()}")
    return scores.reindex(df.index)
