from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import google.generativeai as genai
from dotenv import load_dotenv

import time

# --- Configuration Initiale ---
# Chargement des variables du fichier .env
load_dotenv()

# Configuration de Gemini
# Si la clé est absente, l'API lèvera une erreur explicite à l'exécution.
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# gemini-1.5-flash est l'équivalent de claude-haiku : extrêmement rapide et peu coûteux
MODEL_NAME = 'gemini-2.5-flash'


@dataclass
class FlagContext:
    """Tout ce que Gemini reçoit pour générer une explication."""
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
    Appelle Gemini API et retourne une explication en français, 2-3 phrases.
    """
    # 1. Préparation du contexte BASSÉE SUR LES SCORES DE P1
    anomalies = []
    
    if ctx.layer_scores.get("amount", 0) > 0.5:
        anomalies.append(f"Montant anormalement élevé pour cette carte (Anomalie: {ctx.layer_scores['amount']:.2f}).")
        
    if ctx.layer_scores.get("velocity", 0) > 0.5 or ctx.layer_scores.get("burst", 0) > 0.5:
        anomalies.append("Rafale de transactions détectée dans un laps de temps anormalement court.")
        
    if ctx.layer_scores.get("cross_card", 0) > 0.5:
        anomalies.append("Forte probabilité de fraude croisée (Dispositif ou IP associé à de multiples cartes).")

    if ctx.merchant_country != ctx.cardholder_country:
        anomalies.append(f"Transaction internationale suspecte : marchand en {ctx.merchant_country}, carte en {ctx.cardholder_country}.")

    anomalies_str = " - " + "\n - ".join(anomalies) if anomalies else " - Accumulation de signaux faibles suspects."

    prompt = f"""
    Tu es un analyste en prévention de la fraude financière senior.
    Rédige un verdict concis (2 ou 3 phrases maximum) expliquant pourquoi la transaction suivante est suspecte.
    Le ton doit être professionnel, factuel et direct. Va droit au but.

    DONNÉES DE LA TRANSACTION :
    - Transaction ID : {ctx.transaction_id}
    - Marchand : {ctx.merchant_name} (Catégorie: {ctx.merchant_category})
    - Canal : {ctx.channel}

    ANOMALIES DÉTECTÉES PAR LE MOTEUR :
    {anomalies_str}

    VERDICT :
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt, generation_config={"temperature": 0.1})
        return response.text.strip()
    
    except Exception as e:
        logging.error(f"Erreur API Gemini pour {ctx.transaction_id} : {e}")
        return f"Alerte système : Transaction suspecte (Score global {ctx.fraud_score:.2f}). {anomalies_str}"


def precompute_explanations(flagged_contexts: list[FlagContext], max_workers: int = 3) -> dict[str, str]:
    """
    Génère les explications. max_workers réduit à 3 pour éviter le Rate Limit de l'API.
    """
    results = {}
    if not flagged_contexts:
        return results

    print(f"Génération IA pour {len(flagged_contexts)} transactions... (Mode anti-rate-limit activé)")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_txid = {
            executor.submit(generate_explanation, ctx): ctx.transaction_id 
            for ctx in flagged_contexts
        }

        for future in as_completed(future_to_txid):
            tx_id = future_to_txid[future]
            try:
                results[tx_id] = future.result()
                # Petite pause pour éviter de bombarder l'API
                time.sleep(1.5) 
            except Exception as exc:
                logging.error(f"Échec pour {tx_id}: {exc}")
                results[tx_id] = "Erreur lors de la génération."

    return results

# # --- Test Local (Mock) ---
# if __name__ == "__main__":
#     # Création de fausses données pour tester le script indépendamment de l'équipe Data
#     mock_ctx_1 = FlagContext(
#         transaction_id="tx_001", card_id="c_123", amount=890.0, median_amount_for_card=20.0,
#         merchant_name="Best Buy", merchant_category="electronics", channel="online",
#         cardholder_country="CA", merchant_country="US", device_is_new=True, ip_is_new=True,
#         device_seen_with_n_cards=4, ip_seen_with_n_cards=4, fraud_score=0.92,
#         layer_scores={"amount": 0.9, "velocity": 0.1, "burst": 0.0, "cross_card": 0.95}
#     )
    
#     mock_ctx_2 = FlagContext(
#         transaction_id="tx_002", card_id="c_456", amount=45.0, median_amount_for_card=40.0,
#         merchant_name="Uber Eats", merchant_category="restaurant", channel="online",
#         cardholder_country="CA", merchant_country="CA", device_is_new=False, ip_is_new=False,
#         device_seen_with_n_cards=1, ip_seen_with_n_cards=1, fraud_score=0.76,
#         layer_scores={"amount": 0.1, "velocity": 0.0, "burst": 0.8, "cross_card": 0.0}
#     )

#     # Test du batching
#     contexts = [mock_ctx_1, mock_ctx_2]
#     explanations_dict = precompute_explanations(contexts)
    
#     for tx_id, exp in explanations_dict.items():
#         print(f"\n[Dossier {tx_id}]")
#         print(exp)