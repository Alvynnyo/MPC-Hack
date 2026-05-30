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
    raise NotImplementedError


def build_merchant_profiles(df: pd.DataFrame) -> dict:
    """
    [Priorité basse] Marchands utilisés par beaucoup de cartes, montants
    anormalement élevés.

    TODO P1 : implémenter si temps disponible.
    """
    raise NotImplementedError
