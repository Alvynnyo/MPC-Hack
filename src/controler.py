from __future__ import annotations

import pandas as pd
from src.pipeline import run_pipeline
from src.scoring import Weights
from src.feedback import FeedbackManager
from src.explanations import FlagContext, precompute_explanations
from src.ui.mock_data import CaseFile, Evidence, PreviousTx

def _determine_risk_label(score: float) -> str:
    """Dérive le label de risque en fonction du score."""
    if score >= 0.60:
        return "ÉLEVÉ"
    if score >= 0.40:
        return "MOYEN"
    return "FAIBLE"

def _generate_evidence(ctx: FlagContext) -> list[Evidence]:
    """Transforme les scores bruts en objets Evidence pour l'UI."""
    evidence = []
    
    if ctx.layer_scores.get("amount", 0) > 0.5:
        evidence.append(Evidence(
            label="Montant",
            value=f"{ctx.amount:.2f} $",
            tag=f"ATYPIQUE",
            severity="warning" if ctx.layer_scores["amount"] < 0.8 else "critical"
        ))
        
    if ctx.layer_scores.get("velocity", 0) > 0.5 or ctx.layer_scores.get("burst", 0) > 0.5:
        evidence.append(Evidence(
            label="Vitesse",
            value="Transactions rapprochées",
            tag="RAFALE DÉTECTÉE",
            severity="critical"
        ))
        
    if ctx.layer_scores.get("cross_card", 0) > 0.5:
        evidence.append(Evidence(
            label="Dispositif",
            value=f"{ctx.device_seen_with_n_cards} cartes liées",
            tag="RÉSEAU SUSPECT",
            severity="critical"
        ))
        
    if not evidence:
         evidence.append(Evidence(
            label="Analyse",
            value="Comportement global atypique",
            tag="SOUS SURVEILLANCE",
            severity="warning"
        ))
         
    return evidence

def _generate_previous_tx(card_group: pd.DataFrame, current_tx_id: str) -> list[PreviousTx]:
    """Génère l'historique récent de la carte."""
    recent = card_group.sort_values(by="timestamp", ascending=False).head(5)
    previous_list = []
    
    for _, tx in recent.iterrows():
        dt = pd.to_datetime(tx["timestamp"])
        date_str = dt.strftime("%m-%d %H:%M")
        status = "current" if str(tx["transaction_id"]) == str(current_tx_id) else "ok"
        
        previous_list.append(PreviousTx(
            date=date_str,
            merchant=str(tx["merchant_name"]),
            amount=float(tx["amount"]),
            status=status
        ))
        
    return previous_list

def initialize_fraud_queue(
    csv_path: str = "data/transactions.csv",
    weights: Weights | None = None,
    threshold: float = 0.28,
    feedback_manager: FeedbackManager | None = None
) -> list[CaseFile]:
    """Point d'entrée principal pour l'UI."""
    if weights is None:
        weights = Weights()
        
    df_flagged = run_pipeline(csv_path, weights, threshold, feedback_manager)
    
    if df_flagged.empty:
        return []

    df_full = pd.read_csv(csv_path) 
    contexts = []
    
    for _, row in df_flagged.iterrows():
        card_group = df_full[df_full['card_id'] == row['card_id']]
        
        ctx = FlagContext(
            transaction_id=str(row['transaction_id']),
            card_id=str(row['card_id']),
            amount=float(row['amount']),
            median_amount_for_card=float(card_group['amount'].median()),
            merchant_name=str(row['merchant_name']),
            merchant_category=str(row['merchant_category']),
            channel=str(row['channel']),
            cardholder_country=str(row['cardholder_country']),
            merchant_country=str(row['merchant_country']),
            device_is_new=False, 
            ip_is_new=False,     
            device_seen_with_n_cards=int(row.get('s4', 0) > 0.5) * 3, 
            ip_seen_with_n_cards=1,
            fraud_score=float(row['final_score']),
            layer_scores={
                "amount": float(row.get('s1', 0)), 
                "velocity": float(row.get('s2', 0)), 
                "burst": float(row.get('s3', 0)), 
                "cross_card": float(row.get('s4', 0))
            }
        )
        contexts.append(ctx)

    explanations_dict = precompute_explanations(contexts)

    ui_cases = []
    total_cases = len(contexts)
    
    for i, ctx in enumerate(contexts):
        card_group = df_full[df_full['card_id'] == ctx.card_id]
        
        case = CaseFile(
            case_id=ctx.transaction_id,
            case_index=i + 1,
            case_total=total_cases,
            card_id=ctx.card_id,
            amount=ctx.amount,
            score=ctx.fraud_score,
            risk_label=_determine_risk_label(ctx.fraud_score),
            verdict=explanations_dict.get(ctx.transaction_id, "Alerte générée automatiquement."),
            evidence=_generate_evidence(ctx),
            previous=_generate_previous_tx(card_group, ctx.transaction_id)
        )
        ui_cases.append(case)

    return ui_cases

# --- Bloc de Test Local ---
if __name__ == "__main__":
    from src.scoring import Weights
    
    print("🚀 Lancement du test du contrôleur (orchestrator.py)...")
    
    # On utilise le même seuil que P1 (0.33) pour s'attendre à ~69 cas
    poids_test = Weights(w1=0.25, w2=0.25, w3=0.25, w4=0.25)
    
    try:
        # Génération de la file d'attente
        queue = initialize_fraud_queue(
            csv_path="data/transactions.csv",
            weights=poids_test,
            threshold=0.28
        )
        
        print(f"\n✅ Succès ! Le contrôleur a généré {len(queue)} dossiers (CaseFile).")
        
        if queue:
            print("\n--- 🔍 Aperçu du Top 3 des dossiers les plus suspects ---")
            # On n'affiche que les 3 premiers pour ne pas polluer le terminal
            for case in queue[:3]:
                print(f"\n📂 DOSSIER {case.case_id} ({case.case_index} / {case.case_total})")
                print(f"   💳 Carte   : {case.card_id}")
                print(f"   💰 Montant : {case.amount:.2f} $")
                print(f"   🚨 Risque  : {case.score:.2f} [{case.risk_label}]")
                print(f"   🤖 Verdict IA : {case.verdict}")
                
                print(f"   🔎 Preuves ({len(case.evidence)} signaux) :")
                for ev in case.evidence:
                    print(f"      - {ev.label} : {ev.value} [{ev.tag}] (Sévérité: {ev.severity})")
                    
                print(f"   🕒 Historique ({len(case.previous)} tx récentes) :")
                for prev in case.previous:
                    marqueur = "👈 (Transaction analysée)" if prev.status == "current" else ""
                    print(f"      - {prev.date} | {prev.merchant} | {prev.amount:.2f} $ {marqueur}")

    except FileNotFoundError:
        print("\n❌ Erreur : Le fichier 'data/transactions.csv' est introuvable.")
        print("Assure-toi de lancer la commande depuis la racine du projet (MPC-Hack/).")