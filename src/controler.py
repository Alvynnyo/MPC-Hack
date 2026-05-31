from __future__ import annotations

import pandas as pd
from src.pipeline import run_pipeline
from src.scoring import Weights
from src.feedback import FeedbackManager
from src.explanations import FlagContext, precompute_explanations
from src.ui.mock_data import CaseFile, Evidence, PreviousTx
from src.detection.layer3_burst import get_burst_transactions
from src.detection.layer2_poisson import get_merchant_burst_transactions


# ---------------------------------------------------------------------------
# Helpers de classification
# ---------------------------------------------------------------------------

def _determine_risk_label(score: float) -> str:
    """Dérive le label de risque textuel en fonction du score final."""
    if score >= 0.60:
        return "ÉLEVÉ"
    if score >= 0.40:
        return "MOYEN"
    return "FAIBLE"


def determine_dominant_signal(layer_scores: dict) -> str:
    """
    Détermine quel signal de fraude prend la priorité pour l'affichage.

    Règles :
    - Seuls les signaux >= 0.3 sont considérés comme actifs.
    - Le signal avec le score le plus élevé gagne.
    - En cas d'égalité parfaite, priorité : cross_card > vitesse > poisson > montant.
    - Si aucun signal n'atteint 0.3, on retourne "montant" par défaut.
    """
    if not layer_scores:
        return "montant"

    THRESHOLD = 0.3

    candidates = {
        "montant":    layer_scores.get("amount", 0),
        "poisson":    layer_scores.get("velocity", 0),
        "vitesse":    layer_scores.get("burst", 0),
        "cross_card": layer_scores.get("cross_card", 0),
    }

    active = {k: v for k, v in candidates.items() if v >= THRESHOLD}

    if not active:
        return "montant"

    return max(active, key=active.get)


# ---------------------------------------------------------------------------
# Génération des signaux (Evidence)
# ---------------------------------------------------------------------------

def _generate_evidence(ctx: FlagContext) -> list[Evidence]:
    """Transforme les scores des couches en objets Evidence avec les sévérités adaptées."""
    evidence = []

    # Couche 1 : Montant atypique
    if ctx.layer_scores.get("amount", 0) > 0.5:
        evidence.append(Evidence(
            label="Montant",
            value=f"{ctx.amount:.2f} $",
            tag="ATYPIQUE",
            severity="critical" if ctx.layer_scores["amount"] >= 0.8 else "warning",
        ))

    # Couche 2 : Anomalie Poisson / Volume Terminal
    if ctx.layer_scores.get("velocity", 0) > 0.5:
        evidence.append(Evidence(
            label="Volume Terminal",
            value="Pic anormal d'activité globale",
            tag="ANOMALIE POISSON",
            severity="critical" if ctx.layer_scores["velocity"] > 0.8 else "warning",
        ))

    # Couche 3 : Vitesse Carte / Rafale
    if ctx.layer_scores.get("burst", 0) > 0.5:
        evidence.append(Evidence(
            label="Vitesse Carte",
            value="Succession de micro-transactions",
            tag="RAFALE DÉTECTÉE",
            severity="critical",
        ))

    # Couche 4 : Réseau / Cross-Card
    if ctx.layer_scores.get("cross_card", 0) > 0.5:

        linked_cards = max(
            ctx.device_seen_with_n_cards,
            ctx.ip_seen_with_n_cards
        )

        if linked_cards > 1:
            evidence.append(Evidence(
                label="Identifiant technique",
                value=f"{linked_cards} cartes liées",
                tag="RÉSEAU SUSPECT",
                severity="critical",
            ))
        else:
            evidence.append(Evidence(
                label="Identifiant technique",
                value="Empreinte d'appareil suspecte",
                tag="PROXY / VPN DETECTÉ",
                severity="warning",
            ))

    if not evidence:
        evidence.append(Evidence(
            label="Analyse",
            value="Comportement global atypique",
            tag="SOUS SURVEILLANCE",
            severity="warning",
        ))

    return evidence


# ---------------------------------------------------------------------------
# Génération de l'historique carte (section basse "montant" et "vitesse")
# ---------------------------------------------------------------------------

def _generate_previous_tx(
    card_group: pd.DataFrame,
    current_tx_id: str,
    flagged_tx_set: set,
    df_full: pd.DataFrame | None = None,
    dominant_signal: str = "montant",
    anchor_timestamp=None,
) -> list[PreviousTx]:
    """
    Génère la liste des transactions à afficher dans la section basse.

    - dominant_signal == "vitesse" : extrait les tx de la rafale réelle (±10 min)
      pour montrer la séquence serrée qui a déclenché l'alerte.
    - Autres signaux : renvoie les 4 dernières tx + la tx courante forcée,
      triées chronologiquement décroissant, pour montrer l'écart de comportement.

    Le statut de chaque ligne :
      "current"  → la transaction analysée (mise en évidence en rouge)
      "suspect"  → autre tx de cette carte qui était aussi flaggée
      "ok"       → tx normale validée
    """
    if dominant_signal == "vitesse" and df_full is not None and anchor_timestamp is not None:
        card_id = card_group['card_id'].iloc[0] if not card_group.empty else ""
        burst_df = get_burst_transactions(df_full, card_id, anchor_timestamp, window_minutes=10)
        source = burst_df if not burst_df.empty else card_group.sort_values('timestamp', ascending=False).head(5)
    else:
        # Toujours inclure la tx courante + les 4 autres les plus récentes
        recent = card_group.sort_values(by="timestamp", ascending=False)
        current_row = recent[recent['transaction_id'].astype(str) == str(current_tx_id)]
        other_rows  = recent[recent['transaction_id'].astype(str) != str(current_tx_id)].head(4)
        source = pd.concat([current_row, other_rows]).sort_values('timestamp', ascending=False)

    previous_list = []
    for _, tx in source.iterrows():
        dt = pd.to_datetime(tx["timestamp"])
        date_str = dt.strftime("%m-%d %H:%M")
        tx_id_str = str(tx["transaction_id"])

        if tx_id_str == str(current_tx_id):
            status = "current"
        elif tx_id_str in flagged_tx_set:
            status = "suspect"
        else:
            status = "ok"

        previous_list.append(PreviousTx(
            date=date_str,
            merchant=str(tx["merchant_name"]),
            amount=float(tx["amount"]),
            status=status,
        ))
    return previous_list


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def initialize_fraud_queue(
    csv_path: str = "data/transactions.csv",
    weights: Weights | None = None,
    threshold: float = 0.28,
    feedback_manager: FeedbackManager | None = None,
) -> list[CaseFile]:
    """Point d'entrée principal pour l'UI Streamlit."""
    if weights is None:
        weights = Weights()

    df_flagged = run_pipeline(csv_path, weights, threshold, feedback_manager)
    if df_flagged.empty:
        return []

    df_full = pd.read_csv(csv_path)

    # Ensemble des tx flaggées — utilisé pour colorier les lignes "suspect"
    flagged_tx_set = set(df_flagged['transaction_id'].astype(str).values)

    # ── Étape 1 : construction des FlagContext pour Gemini ──────────────────
    contexts = []
    for _, row in df_flagged.iterrows():
        card_id    = str(row['card_id'])
        card_group = df_full[df_full['card_id'] == card_id]

        current_device = row.get('device_id')
        current_ip     = row.get('ip_address')

        cards_on_device = (
            df_full[df_full['device_id'] == current_device]['card_id'].nunique()
            if pd.notna(current_device) else 1
        )
        cards_on_ip = (
            df_full[df_full['ip_address'] == current_ip]['card_id'].nunique()
            if pd.notna(current_ip) else 1
        )
        real_cards_linked = max(int(cards_on_device), int(cards_on_ip))

        ctx = FlagContext(
            transaction_id=str(row['transaction_id']),
            card_id=card_id,
            amount=float(row['amount']),
            median_amount_for_card=float(card_group['amount'].median()),
            merchant_name=str(row['merchant_name']),
            merchant_category=str(row['merchant_category']),
            channel=str(row['channel']),
            cardholder_country=str(row['cardholder_country']),
            merchant_country=str(row['merchant_country']),
            device_is_new=False,
            ip_is_new=False,
            device_seen_with_n_cards=real_cards_linked,
            ip_seen_with_n_cards=int(cards_on_ip),
            fraud_score=float(row['final_score']),
            layer_scores={
                "amount":     float(row.get('s1', 0)),
                "velocity":   float(row.get('s2', 0)),
                "burst":      float(row.get('s3', 0)),
                "cross_card": float(row.get('s4', 0)),
            },
        )
        contexts.append(ctx)

    # Génération parallèle des verdicts Gemini
    explanations_dict = precompute_explanations(contexts)

    # ── Étape 2 : construction des CaseFiles ────────────────────────────────
    ui_cases    = []
    total_cases = len(contexts)

    for i, ctx in enumerate(contexts):
        match_mask = df_flagged['transaction_id'].astype(str) == str(ctx.transaction_id)
        if not match_mask.any():
            continue

        row_flagged = df_flagged[match_mask].iloc[0]
        card_group  = df_full[df_full['card_id'] == ctx.card_id]
        anchor_ts   = row_flagged.get('timestamp')

        # Signal dominant — détermine quelle section basse afficher
        signal = determine_dominant_signal(ctx.layer_scores)

        # ── CaseFile de base ─────────────────────────────────────────────────
        case = CaseFile(
            case_id=ctx.transaction_id,
            case_index=i + 1,
            case_total=total_cases,
            card_id=ctx.card_id,
            amount=ctx.amount,
            score=ctx.fraud_score,
            risk_label=_determine_risk_label(ctx.fraud_score),
            verdict=explanations_dict.get(ctx.transaction_id, "Alerte générée automatiquement."),
            merchant_category=ctx.merchant_category,  # requis par la boucle de feedback (clé de similarité)
            evidence=_generate_evidence(ctx),
            previous=_generate_previous_tx(
                card_group=card_group,
                current_tx_id=ctx.transaction_id,
                flagged_tx_set=flagged_tx_set,
                df_full=df_full,
                dominant_signal=signal,
                anchor_timestamp=anchor_ts,
            ),
        )

        # ── Enrichissement dynamique ─────────────────────────────────────────
        case.dominant_signal = signal
        case.merchant        = ctx.merchant_name

        # Données Poisson : pic réel sur le terminal marchand (fenêtre 2h)
        if ctx.layer_scores.get("velocity", 0) > 0.5 and anchor_ts is not None:
            merchant_txs = get_merchant_burst_transactions(
                df_full,
                merchant_name=ctx.merchant_name,
                anchor_timestamp=anchor_ts,
                window_minutes=120,
            )
        else:
            merchant_txs = (
                df_full[df_full['merchant_name'] == ctx.merchant_name]
                .sort_values(by="timestamp", ascending=False)
                .head(8)
            )

        case.merchant_data = [
            {
                "date":    pd.to_datetime(m_row['timestamp']).strftime("%m-%d %H:%M"),
                "card_id": str(m_row['card_id']),
                "amount":  float(m_row['amount']),
                "status":  "SUSPECT" if str(m_row['transaction_id']) in flagged_tx_set else "OK",
            }
            for _, m_row in merchant_txs.iterrows()
        ]

        # Données Cross-Card : autres cartes sur le même appareil
        current_device = row_flagged.get('device_id')
        current_ip = row_flagged.get('ip_address')

        network_frames = []

        # Cartes partageant le même appareil
        if pd.notna(current_device):
            network_frames.append(
                df_full[
                    (df_full['device_id'] == current_device)
                    & (df_full['card_id'] != ctx.card_id)
                ]
            )

        # Cartes partageant la même IP
        if pd.notna(current_ip):
            network_frames.append(
                df_full[
                    (df_full['ip_address'] == current_ip)
                    & (df_full['card_id'] != ctx.card_id)
                ]
            )

        if network_frames:

            network_txs = (
                pd.concat(network_frames)
                .drop_duplicates(subset=["transaction_id"])
                .sort_values(by="timestamp", ascending=False)
                .head(10)
            )

            case.device_data = [
                {
                    "last_seen": pd.to_datetime(n_row["timestamp"]).strftime("%m-%d %H:%M"),
                    "card_id": str(n_row["card_id"]),
                    "tx_count": int(
                        len(
                            df_full[
                                df_full["card_id"] == n_row["card_id"]
                            ]
                        )
                    ),
                    "amount": float(n_row["amount"]),
                    "merchant": str(n_row["merchant_name"]),
                }
                for _, n_row in network_txs.iterrows()
            ]

        else:
            case.device_data = []

        ui_cases.append(case)

    return ui_cases


if __name__ == "__main__":
    print("🚀 Lancement du test du contrôleur...")
    poids_test = Weights(w1=0.20, w2=0.30, w3=0.25, w4=0.25)
    try:
        queue = initialize_fraud_queue(
            csv_path="data/transactions.csv",
            weights=poids_test,
            threshold=0.28,
        )
        print(f"\n✅ Succès ! Le contrôleur a généré {len(queue)} dossiers.")
    except FileNotFoundError:
        print("\n❌ Erreur : Le fichier 'data/transactions.csv' est introuvable.")