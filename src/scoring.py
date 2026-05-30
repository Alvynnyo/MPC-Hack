from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass
class Weights:
    """Poids des 4 couches. Doivent sommer à 1.0."""
    w1: float = 0.25
    w2: float = 0.25
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

# --- AJOUT CRUCIAL : La fonction manquante ---
def process_scoring_pipeline(
    df: pd.DataFrame, 
    weights: Weights, 
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Fonction principale à appeler depuis l'UI ou l'API.
    Prend le DataFrame brut avec les colonnes de détection, ajoute le score final,
    et filtre pour ne garder que la file d'attente des transactions suspectes.
    """
    result_df = df.copy()
    
    # On assume que P1 a nommé ses colonnes 's1', 's2', 's3', 's4'
    result_df['final_score'] = compute_fraud_scores(
        s1=result_df['s1'],
        s2=result_df['s2'],
        s3=result_df['s3'],
        s4=result_df['s4'],
        weights=weights
    )
    
    result_df['is_flagged'] = flag_transactions(result_df['final_score'], threshold)
    
    # Préparer la file d'attente pour le réviseur
    queue_df = result_df[result_df['is_flagged']].sort_values(by='final_score', ascending=False)
    
    return queue_df
