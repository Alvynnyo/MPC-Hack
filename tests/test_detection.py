"""Tests pour les 4 couches de détection."""
import pandas as pd
import pytest

from src.detection.layer1_amount import score_amount_deviation
from src.detection.layer2_poisson import score_burst_poisson
from src.detection.layer3_burst import score_burst
from src.detection.layer4_cross_card import score_cross_card


# ---------------------------------------------------------------------------
# Couche 1 — score_amount_deviation
# ---------------------------------------------------------------------------

def test_amount_deviation_fraud_high_score():
    """Une transaction à 500$ sur une carte habituée à 20$ (IQR=10) dépasse 0.8."""
    df = pd.DataFrame({
        "card_id": ["card_001"],
        "amount":  [500.0],
    })
    card_profiles = {"card_001": {"median_amount": 20.0, "iqr_amount": 10.0}}
    scores = score_amount_deviation(df, card_profiles)
    assert scores.iloc[0] > 0.8


def test_amount_deviation_legit_low_score():
    """Une transaction à 22$ sur une carte habituée à 20$ (IQR=10) reste sous 0.2."""
    df = pd.DataFrame({
        "card_id": ["card_001"],
        "amount":  [22.0],
    })
    card_profiles = {"card_001": {"median_amount": 20.0, "iqr_amount": 10.0}}
    scores = score_amount_deviation(df, card_profiles)
    assert scores.iloc[0] < 0.2


# ---------------------------------------------------------------------------
# Couche 2 — score_burst_poisson
# ---------------------------------------------------------------------------

def test_burst_poisson_merchant_fraud_high_score():
    """7 transactions QuickPay en 60 min après 2 jours de faible activité donnent un score > 0.7."""
    base = pd.Timestamp("2025-05-05 00:00:00")
    # 2 transactions de fond sur 48h, puis burst de 7 en 60 minutes
    timestamps = [
        base,
        base + pd.Timedelta(hours=48),
        base + pd.Timedelta(hours=50, minutes=0),
        base + pd.Timedelta(hours=50, minutes=10),
        base + pd.Timedelta(hours=50, minutes=20),
        base + pd.Timedelta(hours=50, minutes=30),
        base + pd.Timedelta(hours=50, minutes=40),
        base + pd.Timedelta(hours=50, minutes=50),
        base + pd.Timedelta(hours=50, minutes=60),
    ]
    df = pd.DataFrame({
        "transaction_id": [f"tx_{i}" for i in range(9)],
        "card_id":        [f"card_{i:03d}" for i in range(9)],
        "merchant_name":  ["QuickPay"] * 9,
        "timestamp":      timestamps,
    })
    scores = score_burst_poisson(df)
    # dernière transaction du burst : 7 txns dans sa fenêtre 2h, λ ≈ 0.35
    assert scores.iloc[8] > 0.7


def test_burst_poisson_legit_spaced_low_score():
    """2 transactions chez le même marchand espacées de 5 heures donnent un score < 0.3."""
    base = pd.Timestamp("2025-05-05 10:00:00")
    df = pd.DataFrame({
        "transaction_id": ["tx_0", "tx_1"],
        "card_id":        ["card_001", "card_002"],
        "merchant_name":  ["QuickPay", "QuickPay"],
        "timestamp":      [base, base + pd.Timedelta(hours=5)],
    })
    scores = score_burst_poisson(df)
    assert scores.max() < 0.3


# ---------------------------------------------------------------------------
# Couche 3 — score_burst (siphonnement)
# ---------------------------------------------------------------------------

def test_siphon_fraud_burst_high_score():
    """4 micro-transactions gift_card en 8 minutes sur la même carte dépassent 0.6."""
    base = pd.Timestamp("2025-05-05 02:00:00")
    df = pd.DataFrame({
        "transaction_id":   ["tx_0", "tx_1", "tx_2", "tx_3"],
        "card_id":          ["card_023"] * 4,
        "amount":           [2.0, 5.0, 8.0, 12.0],
        "merchant_category": ["gift_card"] * 4,
        "timestamp":        [base + pd.Timedelta(minutes=i * 2) for i in range(4)],
    })
    scores = score_burst(df)
    assert scores.max() > 0.6
    assert (scores > 0.6).sum() >= 2


def test_siphon_legit_restaurant_low_score():
    """2 transactions restaurant espacées de 2 heures sur la même carte restent sous 0.2."""
    base = pd.Timestamp("2025-05-05 12:00:00")
    df = pd.DataFrame({
        "transaction_id":   ["tx_0", "tx_1"],
        "card_id":          ["card_001", "card_001"],
        "amount":           [45.0, 45.0],
        "merchant_category": ["restaurant", "restaurant"],
        "timestamp":        [base, base + pd.Timedelta(hours=2)],
    })
    scores = score_burst(df)
    assert scores.max() < 0.2


# ---------------------------------------------------------------------------
# Couche 4 — score_cross_card
# ---------------------------------------------------------------------------

def test_cross_card_fraud_shared_merchant_high_score():
    """Un même marchand utilisé par 6 cartes distinctes en 2h donne un score > 0.7."""
    base = pd.Timestamp("2025-05-05 12:00:00")
    df = pd.DataFrame({
        "transaction_id": [f"tx_{i}" for i in range(6)],
        "card_id":        [f"card_{i:03d}" for i in range(6)],
        "merchant_name":  ["QuickPay"] * 6,
        "amount":         [50.0] * 6,
        "timestamp":      [base + pd.Timedelta(minutes=10 * i) for i in range(6)],
        "device_id":      [None] * 6,
        "ip_address":     [None] * 6,
    })
    scores = score_cross_card(df)
    assert scores.max() > 0.7


def test_cross_card_legit_single_card_low_score():
    """Un marchand vu par une seule carte donne un score < 0.2."""
    base = pd.Timestamp("2025-05-05 12:00:00")
    df = pd.DataFrame({
        "transaction_id": ["tx_0", "tx_1"],
        "card_id":        ["card_001", "card_001"],
        "merchant_name":  ["Tim Hortons", "Tim Hortons"],
        "amount":         [12.0, 14.0],
        "timestamp":      [base, base + pd.Timedelta(minutes=30)],
        "device_id":      [None, None],
        "ip_address":     [None, None],
    })
    scores = score_cross_card(df)
    assert scores.max() < 0.2
