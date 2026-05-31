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

    """
    scores = pd.Series(0.0, index=df.index)

    print(f"[DEBUG] device_profiles sample: {list(device_profiles.items())[:3]}")

    for idx, row in df.iterrows():
        score_device = 0.0
        score_ip = 0.0

        #utilisation de device_profiles
        device_id = row.get('device_id')
        if pd.notna(device_id) and device_id in device_profiles:
            nb_cartes_dev = device_profiles[device_id].get('distinct_cards', 1)
            score_device = min(1.0, (nb_cartes_dev - 1) / 2)

        # profil ip
        ip_addr = row.get('ip_address')
        if pd.notna(ip_addr) and ip_addr in ip_profiles:
            nb_cartes_ip = ip_profiles[ip_addr].get('nombre_cartes_distinctes', 1)
            score_ip = min(1.0, (nb_cartes_ip - 1) / 2)

        final_score = max(score_device, score_ip)
        scores[idx] = min(final_score, 1.0)

    print(f"[DEBUG layer4] min={scores.min():.3f} max={scores.max():.3f} nonzero={(scores > 0).sum()}")
    return scores
