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
    """

    df_temp = df.copy()
    df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])

    scores = pd.Series(0.0, index=df_temp.index)

    window_counts = df_temp.groupby('card_id').rolling('10min', on='timestamp')['transaction_id'].count()

    window_counts = window_counts.reset_index(level=0).drop(columns='card_id')
    df_temp['tx_count_10m'] = window_counts['transaction_id']

    for idx, row in df_temp.iterrows():
        score = 0.0
        count = row['tx_count_10m']

        # Si plus de 3 transactions en 10 minutes, le risque commence
        if count >= 3:
            score += 0.3
        #plus de 5 ca augmente encore
        if count >= 5:
            score += 0.5
            
        
        cat = str(row.get('merchant_category', '')).lower()
        if count >= 3 and ('gift_card' in cat or 'online_retail' in cat):
            score += 0.2
            
        scores[idx] = min(score, 1.0)
        
    
    return scores.reindex(df.index)
