"""
[P2] Génération d'explications en langage naturel via Claude API.

Les explications sont pré-générées à l'ingestion pour éviter la latence
pendant la demo.

Voir PLAN.md, étape 4.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# from anthropic import Anthropic  # à activer une fois la clé fournie


@dataclass
class FlagContext:
    """Tout ce que Claude reçoit pour générer une explication."""
    transaction_id: str
    card_id: str
    amount: float
    median_amount_for_card: float
    merchant_name: str
    merchant_category: str
    channel: str
    cardholder_country: str
    merchant_country: str
    device_is_new: bool
    ip_is_new: bool
    device_seen_with_n_cards: int
    ip_seen_with_n_cards: int
    fraud_score: float
    layer_scores: dict  # {"amount": s1, "velocity": s2, "burst": s3, "cross_card": s4}


def generate_explanation(ctx: FlagContext) -> str:
    """
    Appelle Claude API et retourne une explication en français, 2-3 phrases,
    qui raconte pourquoi cette transaction est suspecte.

    TODO P2 :
        1. Charger ANTHROPIC_API_KEY depuis .env
        2. Construire un prompt court avec le contexte
        3. Appeler claude-haiku-4-5 (rapide, suffisant pour cette tâche)
        4. Retourner le texte

    Voir PLAN.md, étape 4 pour le format attendu de l'explication.
    """
    raise NotImplementedError


def precompute_explanations(flagged_contexts: list[FlagContext]) -> dict[str, str]:
    """
    Génère toutes les explications en batch (en parallèle si possible).
    Retourne un dict transaction_id -> explication.

    TODO P2 : utiliser asyncio ou ThreadPoolExecutor pour paralléliser.
    """
    raise NotImplementedError
