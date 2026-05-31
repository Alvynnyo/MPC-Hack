from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from src.feedback import FeedbackManager

@dataclass
class Weights:
    """Poids des 4 couches. Doivent sommer à 1.0."""
    w1: float = 0.20
    w2: float = 0.30
    w3: float = 0.25
    w4: float = 0.25

    def validate(self) -> None:
        total = self.w1 + self.w2 + self.w3 + self.w4
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Les poids doivent sommer à 1.0 (somme actuelle: {total})")

def compute_fraud_scores(
    s1: pd.Series,
    s2: pd.Series,
    s3: pd.Series,
    s4: pd.Series,
    weights: Weights,
) -> pd.Series:
    """
    Calcule la somme pondérée des scores.
    """
    weights.validate()
    return (weights.w1 * s1) + (weights.w2 * s2) + (weights.w3 * s3) + (weights.w4 * s4)

def flag_transactions(scores: pd.Series, threshold: float = 0.5) -> pd.Series:
    """
    Retourne un booléen par transaction : True si flaggée.
    """
    return scores >= threshold

def process_scoring_pipeline(
    df: pd.DataFrame, 
    weights: Weights, 
    threshold: float = 0.5,
    feedback_manager: FeedbackManager = None  
) -> pd.DataFrame:
    """
    Fonction principale à appeler depuis l'UI ou l'API.
    Prend le DataFrame brut avec les colonnes de détection, ajoute le score final,
    et filtre pour ne garder que la file d'attente des transactions suspectes.
    """

    result_df = df.copy()
    
    # 1. Calcul du score de base
    result_df['final_score'] = compute_fraud_scores(
        s1=result_df['s1'], s2=result_df['s2'], 
        s3=result_df['s3'], s4=result_df['s4'], 
        weights=weights
    )

    # 2. Boost account takeover : gros montant + catégorie à haut risque
    high_risk_cats = ['gift_card', 'electronics']
    high_risk_mask = (
        result_df['merchant_category'].isin(high_risk_cats) &
        (result_df['s1'] >= 0.8)
    )
    result_df.loc[high_risk_mask, 'final_score'] += 0.05
    result_df['final_score'] = result_df['final_score'].clip(0.0, 1.0)
    
    # 2. Application du Feedback Loop 
    if feedback_manager:
        for cat, mod in feedback_manager.category_modifiers.items():
            if 'merchant_category' in result_df.columns:
                result_df.loc[result_df['merchant_category'] == cat, 'final_score'] += mod
                
        for dev, mod in feedback_manager.device_modifiers.items():
            if 'device_id' in result_df.columns:
                result_df.loc[result_df['device_id'] == dev, 'final_score'] += mod
                
        result_df['final_score'] = result_df['final_score'].clip(0.0, 1.0)
    
    result_df['is_flagged'] = flag_transactions(result_df['final_score'], threshold)
    queue_df = result_df[result_df['is_flagged']].sort_values(by='final_score', ascending=False)
    
    return queue_df