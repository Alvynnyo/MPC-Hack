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
    merchant_category: str = ""   # ex. "online_retail" — clé de similarité pour le feedback loop
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
    merchant_category="online_retail",
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


# --- File de dossiers mockés (pour le deck de swipe) ----------------------- #
# Plusieurs cas variés (scores, signaux, montants différents) pour démontrer
# la file de révision. Sera remplacé par le pipeline P2 (scoring + Gemini).

_TOTAL = 67

MOCK_CASES: list[CaseFile] = [
    MOCK_CASE,
    CaseFile(
        case_id="0143",
        case_index=43,
        case_total=_TOTAL,
        card_id="card_017",
        amount=1250.00,
        score=0.86,
        risk_label="ÉLEVÉ",
        merchant_category="electronics",
        verdict=(
            "Le device dev_4b1e a servi à 6 cartes différentes en 2 heures, "
            "dont celle-ci. Aucune de ces cartes n'avait jamais utilisé cet "
            "appareil auparavant. Signature typique de fraude croisée pilotée "
            "depuis un seul terminal compromis."
        ),
        evidence=[
            Evidence("Device", "dev_4b1e09f7", "6 CARTES", "critical"),
            Evidence("IP", "45.83.201.9", "6 CARTES", "critical"),
            Evidence("Catégorie", "electronics", "ATYPIQUE", "warning"),
            Evidence("Montant", "1 250.00 $", "21× MÉDIANE", "warning"),
        ],
        previous=[
            PreviousTx("04-27 19:02", "Loblaws", 64.20, "ok"),
            PreviousTx("04-29 12:40", "Esso", 48.00, "ok"),
            PreviousTx("05-02 14:10", "Couche-Tard", 9.75, "ok"),
            PreviousTx("05-04 23:55", "BestBuy.ca", 1250.00, "current"),
        ],
    ),
    CaseFile(
        case_id="0144",
        case_index=44,
        case_total=_TOTAL,
        card_id="card_008",
        amount=540.00,
        score=0.64,
        risk_label="MOYEN",
        merchant_category="online_retail",
        verdict=(
            "Achat de 540 $ en électronique alors que cette carte dépense "
            "habituellement moins de 60 $ en épicerie et essence. Le device "
            "et l'IP sont connus de la carte — pas d'autre signal fort. "
            "À examiner, mais pourrait être un achat légitime ponctuel."
        ),
        evidence=[
            Evidence("Montant", "540.00 $", "9× MÉDIANE", "warning"),
            Evidence("Catégorie", "electronics", "ATYPIQUE", "warning"),
            Evidence("Device", "dev_77c2a1", "CONNU", "info"),
            Evidence("IP", "24.114.1.85", "CONNUE", "info"),
        ],
        previous=[
            PreviousTx("04-28 09:30", "Provigo", 52.10, "ok"),
            PreviousTx("04-30 17:45", "Shell", 60.00, "ok"),
            PreviousTx("05-03 11:20", "Maxi", 41.30, "ok"),
            PreviousTx("05-05 16:02", "Canada Computers", 540.00, "current"),
        ],
    ),
    CaseFile(
        case_id="0145",
        case_index=45,
        case_total=_TOTAL,
        card_id="card_023",
        amount=12.00,
        score=0.79,
        risk_label="ÉLEVÉ",
        merchant_category="gift_card",
        verdict=(
            "Rafale de 4 achats de cartes-cadeaux en 13 minutes sur cette "
            "carte, montants croissants de 2 $ à 12 $. Comportement de test "
            "de carte volée : on valide que la carte fonctionne avant un "
            "achat plus important."
        ),
        evidence=[
            Evidence("Vitesse", "4 tx / 13 min", "RAFALE", "critical"),
            Evidence("Catégorie", "gift_card", "À RISQUE", "warning"),
            Evidence("Heure", "03:11", "INHABITUELLE", "warning"),
            Evidence("Device", "dev_e5c222", "NOUVEAU", "critical"),
        ],
        previous=[
            PreviousTx("05-01 03:05", "GiftCardMall", 2.00, "suspect"),
            PreviousTx("05-01 03:09", "GiftCardMall", 5.00, "suspect"),
            PreviousTx("05-01 03:14", "GiftCardMall", 8.00, "suspect"),
            PreviousTx("05-01 03:18", "GiftCardMall", 12.00, "current"),
        ],
    ),
    CaseFile(
        case_id="0146",
        case_index=46,
        case_total=_TOTAL,
        card_id="card_031",
        amount=210.00,
        score=0.52,
        risk_label="MOYEN",
        merchant_category="travel",
        verdict=(
            "Transaction en ligne depuis une IP située en Allemagne alors "
            "que la carte est canadienne. Le montant reste dans les habitudes "
            "de la carte et le marchand est connu. Possible voyage ou VPN — "
            "signal isolé, à confirmer."
        ),
        evidence=[
            Evidence("IP", "91.64.12.7", "ÉTRANGÈRE (DE)", "warning"),
            Evidence("Pays", "DE ≠ CA", "INCOHÉRENT", "warning"),
            Evidence("Montant", "210.00 $", "DANS LA NORME", "info"),
            Evidence("Device", "dev_22ab90", "CONNU", "info"),
        ],
        previous=[
            PreviousTx("04-26 10:00", "Spotify", 10.99, "ok"),
            PreviousTx("04-29 20:15", "Amazon.ca", 180.00, "ok"),
            PreviousTx("05-02 08:40", "Uber", 24.50, "ok"),
            PreviousTx("05-06 13:22", "Booking.com", 210.00, "current"),
        ],
    ),
    CaseFile(
        case_id="0147",
        case_index=47,
        case_total=_TOTAL,
        card_id="card_049",
        amount=6.00,
        score=0.71,
        risk_label="ÉLEVÉ",
        merchant_category="online_retail",
        verdict=(
            "Trois micro-transactions identiques de 2 $ en moins de 5 minutes "
            "chez un marchand en ligne jamais vu sur cette carte. Montants "
            "ronds et répétés : test de validité de carte typique."
        ),
        evidence=[
            Evidence("Vitesse", "3 tx / 4 min", "RAFALE", "critical"),
            Evidence("Marchand", "PayFlow Net", "JAMAIS VU", "critical"),
            Evidence("Montant", "2.00 $ ×3", "RÉPÉTÉ", "warning"),
            Evidence("Heure", "01:58", "INHABITUELLE", "warning"),
        ],
        previous=[
            PreviousTx("04-30 18:30", "IGA", 73.40, "ok"),
            PreviousTx("05-01 01:54", "PayFlow Net", 2.00, "suspect"),
            PreviousTx("05-01 01:56", "PayFlow Net", 2.00, "suspect"),
            PreviousTx("05-01 01:58", "PayFlow Net", 2.00, "current"),
        ],
    ),
]
