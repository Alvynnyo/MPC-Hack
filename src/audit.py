"""
[P4] Audit log des décisions du reviewer.

Chaque décision écrit une entrée dans audit_log.json.

Voir PLAN.md, étape 5 (section Audit log).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

AUDIT_PATH = Path("audit_log.json")

Decision = Literal["approve_fraud", "dismiss", "escalate"]


def log_decision(
    transaction_id: str,
    decision: Decision,
    initial_score: float,
    reasons: list[str],
    reviewer: str = "anonymous",
) -> None:
    """
    Ajoute une entrée à audit_log.json.

    TODO P4 :
        1. Charger l'audit log existant (ou liste vide)
        2. Append l'entrée avec timestamp ISO
        3. Réécrire le fichier

    Format d'une entrée :
        {
            "timestamp": "2026-05-30T14:23:00",
            "transaction_id": "tx_000123",
            "decision": "approve_fraud",
            "initial_score": 0.87,
            "reasons": ["nouveau device", "IP étrangère", "montant 14× médiane"],
            "reviewer": "anonymous"
        }
    """
    raise NotImplementedError


def load_audit_log() -> list[dict]:
    """Retourne toutes les décisions enregistrées."""
    raise NotImplementedError


def undo_last_decision() -> dict | None:
    """Retire et retourne la dernière entrée du log (pour le bouton Undo)."""
    raise NotImplementedError
