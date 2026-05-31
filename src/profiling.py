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
    """Retourne un profil par carte basé sur les montants, pays, catégories et canaux."""
    profiles: dict = {}

    for card_id, group in df.groupby("card_id"):
        amount = group["amount"]
        mean_amount = round(float(amount.mean()), 2)
        median_amount = float(amount.median())
        max_amount = float(amount.max())
        iqr_amount = float(amount.quantile(0.75) - amount.quantile(0.25))

        country_mode = group["merchant_country"].mode()
        usual_country = country_mode.iloc[0] if not country_mode.empty else None

        top_categories = group["merchant_category"].value_counts().head(3).index.tolist()
        channel_counts = group["channel"].value_counts().to_dict()
        channels = {str(k): int(v) for k, v in channel_counts.items()}

        known_devices = group["device_id"].dropna().unique().tolist()
        known_ips = group["ip_address"].dropna().unique().tolist()

        profiles[card_id] = {
            "count": int(len(group)),
            "mean_amount": mean_amount,
            "median_amount": median_amount,
            "max_amount": max_amount,
            "iqr_amount": iqr_amount,
            "usual_country": usual_country,
            "top_categories": top_categories,
            "channels": channels,
            "known_devices": known_devices,
            "known_ips": known_ips,
        }

    return profiles


def build_device_profiles(df: pd.DataFrame) -> dict:
    """Retourne un profil par device avec cartes distinctes, transactions et montant total."""
    profiles: dict = {}
    device_df = df[df["device_id"].notna()]

    for device_id, group in device_df.groupby("device_id"):
        card_list = group["card_id"].dropna().unique().tolist()
        profiles[device_id] = {
            "distinct_cards": int(group["card_id"].nunique()),
            "total_transactions": int(len(group)),
            "total_amount": round(float(group["amount"].sum()), 2),
            "card_list": card_list,
        }

    return profiles


def build_ip_profiles(df: pd.DataFrame) -> dict:
    """Pour chaque ip_address : nombre de cartes distinctes et total de transactions."""

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
