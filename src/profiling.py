"""
[P1] Profilage : construit les profils de comportement normal.

À exposer :
    - build_card_profiles(df) -> dict[card_id -> profil]
    - build_device_profiles(df) -> dict[device_id -> profil]
    - build_ip_profiles(df) -> dict[ip -> profil]
    - build_merchant_profiles(df) -> dict[merchant -> profil]  (priorité basse)

Voir PLAN.md, étape 1.
"""
from __future__ import annotations

import pandas as pd


def build_card_profiles(df: pd.DataFrame) -> dict:
    """
    Pour chaque card_id : count, mean, median, max, pays habituel,
    catégories fréquentes, canaux, devices vus, IPs vues.

    TODO P1 : implémenter.
    """
    raise NotImplementedError


def build_device_profiles(df: pd.DataFrame) -> dict:
    """
    Pour chaque device_id : nombre de cartes distinctes, total transactions,
    montant total.

    TODO P1 : implémenter.
    """
    raise NotImplementedError


def build_ip_profiles(df: pd.DataFrame) -> dict:
    """
    Pour chaque ip_address : nombre de cartes distinctes, total transactions.

    TODO P1 : implémenter.
    """

    df_ip = df.dropna(subset=['ip_address'])

    ip_grouped = df_ip.groupby('ip_address').agg(
        nombre_cartes_distinctes=('card_id','nunique'),
        nombre_total_transactions = ('transaction_id','count')
    ).reset_index()

    ip_profiles = ip_grouped.set_index('ip_address').to_dict(orient='index')
    return ip_profiles


def build_merchant_profiles(df: pd.DataFrame) -> dict:
    """
    [Priorité basse] Marchands utilisés par beaucoup de cartes, montants
    anormalement élevés.

    TODO P1 : implémenter si temps disponible.
    """

    merchant_grouped = df.groupby('merchant_name').agg(
        nombre_cartes_distinctes=('card_id','nunique'),
        montant_total=('amount', 'sum'),
        montant_habituel=('amount', 'median'),
        montant_maximal=('amount', 'max'),
        nombre_total_transactions=('transaction_id', 'count')
    ).reset_index()

    merchant_profiles = merchant_grouped.set_index('merchant_name').to_dict(orient='index')
    return merchant_profiles
