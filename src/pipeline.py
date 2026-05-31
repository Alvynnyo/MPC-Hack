from __future__ import annotations

import pandas as pd

from src.profiling import build_card_profiles
from src.detection.layer1_amount import score_amount_deviation
from src.detection.layer2_poisson import score_burst_poisson
from src.detection.layer3_burst import score_burst as score_siphon
from src.detection.layer4_cross_card import score_cross_card
from src.feedback import FeedbackManager
from src.scoring import Weights, process_scoring_pipeline


def _prepare_detection_df(csv_path: str) -> pd.DataFrame:
    """Lit le CSV et ajoute les scores de détection s1..s4."""
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    card_profiles = build_card_profiles(df)
    df["s1"] = score_amount_deviation(df, card_profiles)
    df["s2"] = score_burst_poisson(df)
    df["s3"] = score_siphon(df)
    df["s4"] = score_cross_card(df)

    return df


def run_pipeline(
    csv_path: str,
    weights: Weights | None = None,
    threshold: float = 0.28,
    feedback_manager: FeedbackManager | None = None,
) -> pd.DataFrame:
    """Exécute le pipeline de détection et retourne les transactions flaggées."""
    df = _prepare_detection_df(csv_path)
    if weights is None:
        weights = Weights()

    return process_scoring_pipeline(df, weights, threshold, feedback_manager)


def run_pipeline_and_export(
    csv_path: str,
    output_path: str,
    weights: Weights | None = None,
    threshold: float = 0.28,
) -> pd.DataFrame:
    """Exécute le pipeline, exporte le DataFrame complet et retourne les flaggées."""
    df = _prepare_detection_df(csv_path)

    if weights is None:
        weights = Weights()


    flagged_df = process_scoring_pipeline(df, weights, threshold)
    scored_cols = flagged_df[["transaction_id", "final_score", "is_flagged"]]
    df = df.merge(scored_cols, on="transaction_id", how="left")
    df["is_flagged"] = df["is_flagged"].fillna(False)
    df["final_score"] = df["final_score"].fillna(0.0)
    df.to_csv(output_path, index=False)
    return flagged_df
