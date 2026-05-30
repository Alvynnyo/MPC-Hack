"""
[P3] Données mockées pour itérer sur l'UI sans dépendre du backend P1/P2.

Une fois P2 livré, ce module sera remplacé par un chargement depuis
src/scoring.py + src/explanations.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Evidence:
    """Une pièce à conviction sur la carte."""
    label: str       # ex: "Device"
    value: str       # ex: "dev_a3f9"
    tag: str         # ex: "JAMAIS VU"
    severity: str    # "critical" | "warning" | "info"


@dataclass
class PreviousTx:
    """Une transaction précédente affichée dans la timeline."""
    date: str        # "04-29 14:22"
    merchant: str
    amount: float
    status: str      # "ok" | "suspect" | "current"


@dataclass
class CaseFile:
    """Un dossier d'enquête complet (une transaction flaggée)."""
    case_id: str            # "0142"
    case_index: int         # 42 (pour "42/67 traités")
    case_total: int         # 67
    card_id: str
    amount: float
    score: float            # 0..1
    risk_label: str         # "ÉLEVÉ" | "MOYEN" | "FAIBLE"
    verdict: str            # Texte naturel généré par Claude
    evidence: list[Evidence] = field(default_factory=list)
    previous: list[PreviousTx] = field(default_factory=list)


MOCK_CASE = CaseFile(
    case_id="0142",
    case_index=42,
    case_total=67,
    card_id="card_042",
    amount=890.00,
    score=0.91,
    risk_label="ÉLEVÉ",
    verdict=(
        "Cette carte fait habituellement des achats entre 20 $ et 80 $ "
        "dans des restaurants canadiens. Ce soir : 4 micro-transactions "
        "sous 5 $ sur un nouveau marchand en ligne entre 2 h et 3 h, "
        "suivies d'un achat Amazon de 890 $. Schéma classique de "
        "card-testing avant exploitation."
    ),
    evidence=[
        Evidence("Device", "dev_a3f9c821", "JAMAIS VU", "critical"),
        Evidence("IP", "89.234.117.42", "ÉTRANGÈRE (FR)", "critical"),
        Evidence("Heure", "02:47", "INHABITUELLE", "warning"),
        Evidence("Montant", "890.00 $", "14× MÉDIANE", "warning"),
    ],
    previous=[
        PreviousTx("04-29 14:22", "Tim Hortons", 12.50, "ok"),
        PreviousTx("04-30 08:15", "Métro Plus", 85.00, "ok"),
        PreviousTx("05-01 02:43", "QuickPay Online", 3.00, "suspect"),
        PreviousTx("05-01 02:45", "QuickPay Online", 4.00, "suspect"),
        PreviousTx("05-01 02:47", "Amazon.ca", 890.00, "current"),
    ],
)
