"""Tests de bout en bout couvrant le profilage, les 4 couches, le scoring, le feedback et le pipeline."""
from __future__ import annotations

import pandas as pd
import pytest

from src.profiling import build_card_profiles
from src.detection.layer1_amount import score_amount_deviation
from src.detection.layer2_poisson import score_burst_poisson
from src.detection.layer3_burst import score_burst
from src.detection.layer4_cross_card import score_cross_card
from src.scoring import Weights, compute_fraud_scores, flag_transactions, process_scoring_pipeline
from src.feedback import FeedbackManager
from src.pipeline import run_pipeline, run_pipeline_and_export


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures et helpers
# ─────────────────────────────────────────────────────────────────────────────

def _full_card_df(amounts, card_id="c1", device_ids=None):
    """DataFrame minimal valide pour build_card_profiles."""
    n = len(amounts)
    return pd.DataFrame({
        "card_id":           [card_id] * n,
        "amount":            amounts,
        "merchant_country":  ["CA"] * n,
        "merchant_category": ["grocery"] * n,
        "channel":           ["online"] * n,
        "device_id":         device_ids if device_ids is not None else ["dev_1"] * n,
        "ip_address":        ["1.2.3.4"] * n,
    })


def _scoring_df(s1=0.0, s2=0.0, s3=0.0, s4=0.0, category="grocery", device="dev_1"):
    """DataFrame minimal pour process_scoring_pipeline."""
    return pd.DataFrame({
        "s1": [s1], "s2": [s2], "s3": [s3], "s4": [s4],
        "merchant_category": [category],
        "device_id":         [device],
    })


@pytest.fixture
def mini_csv(tmp_path):
    """Mini CSV de 15 transactions : 13 normales (10-25$) + 2 extrêmes (800$, 850$) sur la même carte."""
    base = pd.Timestamp("2025-01-15 10:00:00")
    normal_amounts = [10.0, 12.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 22.0, 23.0, 24.0, 25.0]
    fraud_base = base + pd.Timedelta(hours=13)
    timestamps = (
        [base + pd.Timedelta(hours=i) for i in range(13)]
        + [fraud_base, fraud_base + pd.Timedelta(minutes=2)]
    )
    data = {
        "transaction_id":    [f"tx_{i:03d}" for i in range(15)],
        "card_id":           ["card_001"] * 15,
        "amount":            normal_amounts + [800.0, 850.0],
        "timestamp":         timestamps,
        "merchant_name":     ["ShopA"] * 15,
        "merchant_category": ["restaurant"] * 15,
        "channel":           ["in_person"] * 15,
        "merchant_country":  ["CA"] * 15,
        "cardholder_country":["CA"] * 15,
        "device_id":         ["dev_1"] * 15,
        "ip_address":        ["1.2.3.4"] * 15,
    }
    path = tmp_path / "mini.csv"
    pd.DataFrame(data).to_csv(path, index=False)
    return str(path)


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 1 — Profilage
# ─────────────────────────────────────────────────────────────────────────────

def test_profiling_median_iqr_count():
    """Médiane, IQR et count sont calculés correctement — vérifie la base de tout le scoring."""
    df = _full_card_df([10.0, 20.0, 30.0, 40.0])
    p = build_card_profiles(df)["c1"]
    assert p["median_amount"] == pytest.approx(25.0)
    assert p["iqr_amount"]    == pytest.approx(15.0)
    assert p["count"]         == 4


def test_profiling_single_transaction_no_crash():
    """Une carte à transaction unique ne lève pas d'erreur — le fallback IQR de layer1 doit produire un score fini."""
    df = _full_card_df([42.0])
    profiles = build_card_profiles(df)
    assert "c1" in profiles
    scores = score_amount_deviation(df, profiles)
    assert scores.notna().all(), "score NaN sur carte à transaction unique"


def test_profiling_known_devices_no_nulls():
    """Les device_id null ne doivent jamais apparaître dans known_devices — évite les faux positifs sur device inconnu."""
    df = _full_card_df([10.0, 20.0, 30.0], device_ids=["dev_1", None, "dev_2"])
    p = build_card_profiles(df)["c1"]
    assert None not in p["known_devices"]
    assert set(p["known_devices"]) == {"dev_1", "dev_2"}


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 2 — Couche 1 : z-score robuste
# ─────────────────────────────────────────────────────────────────────────────

def test_layer1_high_amount_flagged():
    """Un montant 10× la médiane doit produire un score > 0.8 — signal de base le plus visible."""
    df = pd.DataFrame({"card_id": ["c1"], "amount": [300.0]})
    profiles = {"c1": {"median_amount": 30.0, "iqr_amount": 20.0}}
    assert score_amount_deviation(df, profiles).iloc[0] > 0.8


def test_layer1_median_amount_zero_score():
    """Un montant égal à la médiane doit produire un score de 0.0 — la référence ne se flag pas elle-même."""
    df = pd.DataFrame({"card_id": ["c1"], "amount": [30.0]})
    profiles = {"c1": {"median_amount": 30.0, "iqr_amount": 20.0}}
    assert score_amount_deviation(df, profiles).iloc[0] == pytest.approx(0.0)


def test_layer1_unknown_card_zero_score():
    """Une carte absente du profil doit produire 0.0 et non une erreur — carte nouvelle = signal neutre."""
    df = pd.DataFrame({"card_id": ["unknown"], "amount": [999.0]})
    profiles = {"c1": {"median_amount": 30.0, "iqr_amount": 20.0}}
    assert score_amount_deviation(df, profiles).iloc[0] == pytest.approx(0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 3 — Couche 2 : Poisson
# ─────────────────────────────────────────────────────────────────────────────

def _poisson_df(merchant, timestamps, card_ids=None):
    n = len(timestamps)
    return pd.DataFrame({
        "transaction_id": [f"tx_{i}" for i in range(n)],
        "card_id":        card_ids if card_ids else [f"card_{i:03d}" for i in range(n)],
        "merchant_name":  [merchant] * n,
        "timestamp":      timestamps,
    })


def test_poisson_burst_high_score():
    """7 transactions en 60 min pour un marchand à rythme 1/h doivent dépasser 0.7 — capture les pics statistiquement impossibles."""
    base = pd.Timestamp("2025-05-05 00:00:00")
    ts = (
        [base, base + pd.Timedelta(hours=48)]
        + [base + pd.Timedelta(hours=50, minutes=i * 10) for i in range(7)]
    )
    scores = score_burst_poisson(_poisson_df("QuickPay", ts))
    assert scores.iloc[-1] > 0.7


def test_poisson_spaced_low_score():
    """2 transactions espacées de 6 heures ne doivent pas dépasser 0.3 — rythme normal ne déclenche pas d'alerte."""
    base = pd.Timestamp("2025-05-05 10:00:00")
    ts = [base, base + pd.Timedelta(hours=6)]
    scores = score_burst_poisson(_poisson_df("ShopA", ts, card_ids=["c1", "c2"]))
    assert scores.max() < 0.3


def test_poisson_empty_df():
    """Un DataFrame vide doit retourner une Series vide sans erreur — robustesse sur file de révision vide."""
    df = pd.DataFrame(columns=["transaction_id", "card_id", "merchant_name", "timestamp"])
    scores = score_burst_poisson(df)
    assert len(scores) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 4 — Couche 3 : siphonnement
# ─────────────────────────────────────────────────────────────────────────────

def _burst_df(n, category, gap_minutes=2):
    base = pd.Timestamp("2025-05-05 02:00:00")
    return pd.DataFrame({
        "transaction_id":    [f"tx_{i}" for i in range(n)],
        "card_id":           ["card_023"] * n,
        "amount":            [5.0] * n,
        "merchant_category": [category] * n,
        "timestamp":         [base + pd.Timedelta(minutes=i * gap_minutes) for i in range(n)],
    })


def test_siphon_gift_card_third_and_fourth_flagged():
    """Les transactions 3 et 4 d'une rafale gift_card en 8 min doivent valoir 0.7 — les premières n'ont pas de contexte passé."""
    scores = score_burst(_burst_df(4, "gift_card"))
    assert scores.iloc[0] == pytest.approx(0.0)
    assert scores.iloc[1] == pytest.approx(0.0)
    assert scores.iloc[2] == pytest.approx(0.7)
    assert scores.iloc[3] == pytest.approx(0.7)


def test_siphon_spaced_zero_score():
    """2 transactions espacées de 2 heures sur la même carte doivent produire 0.0 — usage légitime."""
    base = pd.Timestamp("2025-05-05 12:00:00")
    df = pd.DataFrame({
        "transaction_id":    ["tx_0", "tx_1"],
        "card_id":           ["card_001"] * 2,
        "amount":            [20.0, 20.0],
        "merchant_category": ["restaurant"] * 2,
        "timestamp":         [base, base + pd.Timedelta(hours=2)],
    })
    assert score_burst(df).max() == pytest.approx(0.0)


def test_siphon_no_category_bonus():
    """5 transactions rapides sans catégorie à risque doivent plafonner à 0.7, pas 1.0 — le bonus catégorie est absent."""
    scores = score_burst(_burst_df(5, "grocery"))
    assert scores.max() == pytest.approx(0.7)
    assert scores.max() < 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 5 — Couche 4 : burst cross-card
# ─────────────────────────────────────────────────────────────────────────────

def _cross_df(n_cards, gap_minutes=10):
    base = pd.Timestamp("2025-05-05 12:00:00")
    return pd.DataFrame({
        "transaction_id": [f"tx_{i}" for i in range(n_cards)],
        "card_id":        [f"card_{i:03d}" for i in range(n_cards)],
        "merchant_name":  ["QuickPay"] * n_cards,
        "amount":         [50.0] * n_cards,
        "timestamp":      [base + pd.Timedelta(minutes=i * gap_minutes) for i in range(n_cards)],
        "device_id":      [None] * n_cards,
        "ip_address":     [None] * n_cards,
    })


def test_cross_card_six_cards_score_09():
    """6 cartes distinctes chez le même marchand en 2h doivent produire 0.9 — seuil terminal compromis."""
    assert score_cross_card(_cross_df(6)).max() == pytest.approx(0.9)


def test_cross_card_three_cards_score_zero():
    """3 cartes distinctes ne dépassent pas le seuil minimal de 4 — pas d'alerte sous le minimum."""
    assert score_cross_card(_cross_df(3)).max() == pytest.approx(0.0)


def test_cross_card_four_cards_score_07():
    """4 cartes distinctes chez le même marchand en 2h doivent produire 0.7 — seuil de suspicion intermédiaire."""
    assert score_cross_card(_cross_df(4)).max() == pytest.approx(0.7)


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 6 — Score composite
# ─────────────────────────────────────────────────────────────────────────────

def test_composite_exact_value():
    """La somme pondérée doit être calculée exactement sans arrondi numérique visible."""
    w = Weights(w1=0.30, w2=0.35, w3=0.25, w4=0.10)
    score = compute_fraud_scores(
        s1=pd.Series([0.8]),
        s2=pd.Series([1.0]),
        s3=pd.Series([0.7]),
        s4=pd.Series([0.0]),
        weights=w,
    )
    expected = 0.30 * 0.8 + 0.35 * 1.0 + 0.25 * 0.7 + 0.10 * 0.0
    assert score.iloc[0] == pytest.approx(expected)


def test_composite_invalid_weights_raises():
    """Des poids dont la somme ≠ 1.0 doivent lever ValueError — invariant de normalisation."""
    with pytest.raises(ValueError):
        Weights(w1=0.3, w2=0.3, w3=0.3, w4=0.3).validate()


def test_composite_flag_threshold():
    """Le flag est True si et seulement si final_score >= threshold — vérification du seuil exact."""
    flags = flag_transactions(pd.Series([0.10, 0.28, 0.50]), threshold=0.28)
    assert list(flags) == [False, True, True]


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 7 — Feedback loop
# ─────────────────────────────────────────────────────────────────────────────

def test_feedback_reduces_score():
    """Deux Innocenter sur gift_card (−0.05 chacun) réduisent le score de 0.35 à 0.25."""
    fm = FeedbackManager()
    fm.record_decision({"merchant_category": "gift_card"}, "Innocenter")
    fm.record_decision({"merchant_category": "gift_card"}, "Innocenter")
    assert fm.category_modifiers.get("gift_card") == pytest.approx(-0.10)

    # s1=0.25, s2=1.0 → 0.20*0.25 + 0.30*1.0 = 0.35 (s1 < 0.8, pas de boost)
    df = _scoring_df(s1=0.25, s2=1.0, category="gift_card")
    result = process_scoring_pipeline(df, Weights(), threshold=0.20, feedback_manager=fm)
    assert not result.empty, "la transaction doit être flaggée avec threshold=0.20"
    assert result["final_score"].iloc[0] == pytest.approx(0.25)


def test_feedback_score_clamped_to_bounds():
    """Un modificateur extrême ne fait jamais sortir le score de [0.0, 1.0]."""
    # Borne basse : modificateur très négatif → clippé à 0.0
    fm_low = FeedbackManager()
    fm_low.category_modifiers["grocery"] = -10.0
    df = _scoring_df(s3=1.0, s4=1.0, category="grocery")  # base = 0.25+0.25 = 0.50
    result_low = process_scoring_pipeline(df, Weights(), threshold=0.0, feedback_manager=fm_low)
    assert result_low["final_score"].min() >= 0.0

    # Borne haute : modificateur très positif → clippé à 1.0
    fm_high = FeedbackManager()
    fm_high.category_modifiers["grocery"] = +10.0
    result_high = process_scoring_pipeline(df.copy(), Weights(), threshold=0.0, feedback_manager=fm_high)
    assert result_high["final_score"].max() <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 8 — Pipeline de bout en bout
# ─────────────────────────────────────────────────────────────────────────────

def test_pipeline_returns_flagged_with_score_columns(mini_csv):
    """run_pipeline doit retourner uniquement les transactions flaggées avec final_score et is_flagged."""
    result = run_pipeline(mini_csv, threshold=0.20)
    assert not result.empty, "les transactions à 800$ et 850$ doivent être flaggées"
    assert "final_score" in result.columns
    assert "is_flagged" in result.columns
    assert result["is_flagged"].all()
    assert (result["final_score"] >= 0.20).all()
    assert (result["amount"] >= 800).any(), "au moins une transaction à montant extrême doit être flaggée"


def test_pipeline_export_csv_coherent(mini_csv, tmp_path):
    """Le CSV exporté doit avoir final_score et is_flagged, cohérents avec run_pipeline — vérifie la correction du bug de divergence."""
    output_path = str(tmp_path / "output.csv")
    flagged = run_pipeline_and_export(mini_csv, output_path)

    exported = pd.read_csv(output_path)
    assert "final_score" in exported.columns
    assert "is_flagged"  in exported.columns
    assert len(exported) == len(pd.read_csv(mini_csv))

    flagged_ids_pipeline = set(flagged["transaction_id"].astype(str))
    flagged_ids_csv = set(
        exported.loc[exported["is_flagged"] == True, "transaction_id"].astype(str)
    )
    assert flagged_ids_pipeline == flagged_ids_csv, (
        f"Divergence entre pipeline ({flagged_ids_pipeline}) et CSV ({flagged_ids_csv})"
    )
