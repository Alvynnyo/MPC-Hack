"""
[P4] Audit log des décisions du reviewer.

Chaque décision écrit une entrée dans audit_log.json.

Voir PLAN.md, étape 5 (section Audit log).

NB : implémenté par P3 pour brancher l'import des décisions de l'UI
(téléversement du rapport JSON exporté par le deck). À relire par P4.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

AUDIT_PATH = Path("audit_log.json")

Decision = Literal["approve_fraud", "dismiss", "escalate"]


def load_audit_log() -> list[dict]:
    """Retourne toutes les décisions enregistrées (liste vide si aucun fichier)."""
    if not AUDIT_PATH.exists():
        return []
    try:
        return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def log_decision(
    transaction_id: str,
    decision: Decision,
    initial_score: float,
    reasons: list[str],
    reviewer: str = "anonymous",
) -> None:
    """Ajoute une entrée horodatée à audit_log.json."""
    log = load_audit_log()
    log.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "transaction_id": transaction_id,
        "decision": decision,
        "initial_score": round(float(initial_score), 4),
        "reasons": reasons,
        "reviewer": reviewer,
    })
    AUDIT_PATH.write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def undo_last_decision() -> dict | None:
    """Retire et retourne la dernière entrée du log (pour le bouton Undo)."""
    log = load_audit_log()
    if not log:
        return None
    last = log.pop()
    AUDIT_PATH.write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return last
