from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration Initiale ---
load_dotenv()

# Configuration de la clé API Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = 'gemini-2.5-flash'

# Cache disque des explications (clé = transaction_id) : un dossier déjà expliqué
# n'est jamais re-soumis à l'API → démarrages quasi instantanés au-delà du 1er run.
CACHE_PATH = Path("data/explanations_cache.json")
_FALLBACK_PREFIXES = ("Alerte système", "Erreur", "Pattern identifié")


def _load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict[str, str]) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        logging.warning("Impossible d'écrire le cache d'explications : %s", exc)


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


# ---------------------------------------------------------------------------
# Helpers internes : traduction des scores en langage humain
# ---------------------------------------------------------------------------

def _build_pattern_context(ctx: FlagContext) -> tuple[list[str], str]:
    """
    Traduit les scores des couches en descriptions de patterns lisibles.
    Retourne (liste d'anomalies textuelles, signal dominant sous forme de clé).
    """
    anomalies = []
    dominant = "montant"
    dominant_score = 0.0

    # Couche 1 — Montant atypique
    s_amount = ctx.layer_scores.get("amount", 0)
    if s_amount > 0.5:
        if ctx.median_amount_for_card > 0:
            ratio = round(ctx.amount / ctx.median_amount_for_card)
            anomalies.append(
                f"Le montant de {ctx.amount:.2f} $ est environ {ratio}× supérieur "
                f"aux habitudes habituelles de cette carte."
            )
        else:
            anomalies.append(
                f"Le montant de {ctx.amount:.2f} $ est nettement supérieur "
                f"au profil de dépense habituel de cette carte."
            )
        if s_amount > dominant_score:
            dominant_score = s_amount
            dominant = "montant"

    # Couche 2 — Pic de volume sur le terminal marchand (Poisson)
    s_vel = ctx.layer_scores.get("velocity", 0)
    if s_vel > 0.5:
        anomalies.append(
            f"Le terminal de {ctx.merchant_name} enregistre un pic inhabituel "
            f"de transactions sur une courte fenêtre de temps — activité incohérente "
            f"avec le rythme normal de ce marchand."
        )
        if s_vel > dominant_score:
            dominant_score = s_vel
            dominant = "poisson"

    # Couche 3 — Rafale sur la carte (burst / card-testing)
    s_burst = ctx.layer_scores.get("burst", 0)
    if s_burst > 0.5:
        anomalies.append(
            "Succession rapide de micro-transactions sur cette carte — "
            "schéma caractéristique du card-testing : on valide la carte "
            "avec de petits montants avant une exploitation à plus grande échelle."
        )
        if s_burst > dominant_score:
            dominant_score = s_burst
            dominant = "vitesse"

    # Couche 4 — Réseau cross-card
    s_cross = ctx.layer_scores.get("cross_card", 0)
    if s_cross > 0.5:
        if ctx.device_seen_with_n_cards > 1:
            anomalies.append(
                f"Le même appareil a servi à opérer {ctx.device_seen_with_n_cards} cartes "
                f"différentes — infrastructure typique d'une fraude organisée pilotée "
                f"depuis un terminal unique compromis."
            )
        else:
            anomalies.append(
                "L'empreinte technique de connexion (appareil ou adresse réseau) "
                "est associée à des activités suspectes impliquant plusieurs comptes."
            )
        if s_cross > dominant_score:
            dominant_score = s_cross
            dominant = "cross_card"

    # Contexte géographique — signal contextuel (pas une couche scorée)
    if ctx.merchant_country != ctx.cardholder_country:
        anomalies.append(
            f"La transaction est émise depuis {ctx.merchant_country} alors que "
            f"la carte est enregistrée au {ctx.cardholder_country} — "
            f"incohérence géographique à confirmer."
        )

    if not anomalies:
        anomalies.append(
            "Accumulation de signaux comportementaux cohérents avec "
            "un usage frauduleux de la carte."
        )

    return anomalies, dominant


def _build_fallback(ctx: FlagContext, anomalies: list[str]) -> str:
    """
    Fallback lisible si l'API Gemini échoue ou si aucune clé n'est fournie.
    Zéro score, zéro terme technique interne.
    """
    pattern_labels = {
        "montant":    "montant anormalement élevé par rapport au profil habituel",
        "poisson":    "pic de volume inhabituel sur le terminal marchand",
        "vitesse":    "rafale de micro-transactions (card-testing)",
        "cross_card": "fraude croisée — plusieurs cartes sur le même appareil",
    }
    _, dominant = _build_pattern_context(ctx)
    pattern_label = pattern_labels.get(dominant, "comportement de paiement atypique")

    # On prend la première anomalie textualisée pour enrichir le fallback
    first_anomaly = anomalies[0] if anomalies else "Un comportement inhabituel a été relevé."

    return (
        f"Pattern identifié : {pattern_label}. "
        f"{first_anomaly} "
        f"Une vérification manuelle est recommandée avant d'autoriser cette transaction."
    )


# ---------------------------------------------------------------------------
# Génération Gemini
# ---------------------------------------------------------------------------

def generate_explanation(ctx: FlagContext) -> str:
    """
    Appelle Gemini et retourne une explication en français, 2-3 phrases,
    centrée sur les patterns concrets — sans aucun score ni terme technique interne.
    """
    anomalies, dominant = _build_pattern_context(ctx)
    anomalies_str = "\n".join(f"- {a}" for a in anomalies)

    # Protection : Si aucune clé API n'est configurée, on passe directement au fallback propre
    if not os.getenv("GEMINI_API_KEY"):
        return _build_fallback(ctx, anomalies)

    # Prompt de haute qualité avec tes règles strictes d'analyste senior
    prompt = f"""Tu es un analyste senior en prévention de la fraude financière.

Rédige un verdict de 2 à 3 phrases maximum expliquant POURQUOI cette transaction est suspecte.

RÈGLES ABSOLUES — à respecter impérativement :
- Ne mentionne JAMAIS de score, de chiffre de probabilité, de pourcentage ou de valeur numérique technique.
- N'utilise JAMAIS les mots : "anomalie", "s1", "s2", "s3", "s4", "couche", "moteur", "score global", "taux".
- Décris le PATTERN comportemental concret (séquence d'actions, contexte, incohérence).
- Reste factuel, professionnel, directement compréhensible par un analyste humain non technique.
- Ne commence PAS par "Cette transaction" — commence par le comportement ou le contexte détecté.
- Ne conclus PAS par une recommandation générique ("surveiller", "vérifier", etc.) : la conclusion doit nommer le risque précis.

CONTEXTE DE LA TRANSACTION :
- Marchand : {ctx.merchant_name} (catégorie : {ctx.merchant_category})
- Canal : {ctx.channel}
- Pays carte → pays marchand : {ctx.cardholder_country} → {ctx.merchant_country}

PATTERNS IDENTIFIÉS PAR LE MOTEUR DE DÉTECTION :
{anomalies_str}

VERDICT (2-3 phrases, ton analyste senior) :"""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.15, "max_output_tokens": 200}
        )
        text = response.text.strip()

        # Garde-fou : si Gemini glisse un terme interdit, on bascule sur le fallback propre
        forbidden_keywords = [
            "score", "anomalie:", "0.", "1.", " s1", " s2", " s3", " s4",
            "couche", "moteur", "taux", "%"
        ]
        if any(kw in text.lower() for kw in forbidden_keywords):
            logging.warning(
                f"[{ctx.transaction_id}] Gemini a produit un terme interdit — fallback activé."
            )
            return _build_fallback(ctx, anomalies)

        return text

    except Exception as e:
        logging.error(f"Erreur API Gemini pour {ctx.transaction_id} : {e}")
        return _build_fallback(ctx, anomalies)


def precompute_explanations(flagged_contexts: list[FlagContext], max_workers: int = 4) -> dict[str, str]:
    """
    Génère les explications en parallèle, avec cache disque.

    - Les dossiers déjà en cache ne rappellent pas l'API (démarrage instantané).
    - Seuls les vrais succès sont mis en cache (jamais les verdicts de repli de secours),
      pour qu'ajouter une clé API plus tard régénère de vraies explications.
    """
    results: dict[str, str] = {}
    if not flagged_contexts:
        return results

    cache = _load_cache()
    todo = []
    for ctx in flagged_contexts:
        cached = cache.get(ctx.transaction_id)
        if cached:
            results[ctx.transaction_id] = cached
        else:
            todo.append(ctx)

    if todo:
        print(f"Génération IA pour {len(todo)} transactions (cache: {len(results)})...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_txid = {
                executor.submit(generate_explanation, ctx): ctx.transaction_id
                for ctx in todo
            }
            for future in as_completed(future_to_txid):
                tx_id = future_to_txid[future]
                try:
                    text = future.result()
                except Exception as exc:
                    logging.error(f"Échec pour {tx_id}: {exc}")
                    text = "Erreur lors de la génération."
                results[tx_id] = text
                # ne met en cache que les vraies explications (pas les replis)
                if not text.startswith(_FALLBACK_PREFIXES):
                    cache[tx_id] = text
        _save_cache(cache)

    return results