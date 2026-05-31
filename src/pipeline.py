from __future__ import annotations

import pandas as pd

from src.profiling import build_card_profiles, build_device_profiles
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
    device_profiles = build_device_profiles(df)

    df["s1"] = score_amount_deviation(df, card_profiles)
    df["s2"] = score_burst_poisson(df)
    df["s3"] = score_siphon(df)
    df["s4"] = score_cross_card(df, device_profiles, {})

    return df


def run_pipeline(
    csv_path: str,
    weights: Weights | None = None,
    threshold: float = 0.5,
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
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Exécute le pipeline, exporte le DataFrame complet et retourne les flaggées."""
    df = _prepare_detection_df(csv_path)
    flagged_df = run_pipeline(csv_path, weights, threshold)
    df.to_csv(output_path, index=False)
    return flagged_df
