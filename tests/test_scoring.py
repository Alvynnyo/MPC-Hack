"""[P2] Tests pour src/scoring.py"""
import pandas as pd
import pytest

from src.scoring import Weights, compute_fraud_scores, flag_transactions


def test_weights_must_sum_to_one():
    w = Weights(w1=0.5, w2=0.5, w3=0.0, w4=0.0)
    w.validate()  # ne doit pas lever


def test_weights_invalid_sum_raises():
    w = Weights(w1=0.3, w2=0.3, w3=0.3, w4=0.3)  # somme = 1.2
    with pytest.raises(ValueError):
        w.validate()


def test_compute_fraud_scores_weighted_sum():
    """0.25*0.8 + 0.25*0.4 + 0.25*0.0 + 0.25*0.0 = 0.3"""
    w = Weights(w1=0.25, w2=0.25, w3=0.25, w4=0.25)
    s1 = pd.Series([0.8])
    s2 = pd.Series([0.4])
    s3 = pd.Series([0.0])
    s4 = pd.Series([0.0])
    scores = compute_fraud_scores(s1, s2, s3, s4, w)
    assert scores.iloc[0] == pytest.approx(0.3)


def test_flag_transactions_threshold():
    """Le flag est True au-dessus du seuil, False en dessous."""
    scores = pd.Series([0.1, 0.5, 0.9])
    flags = flag_transactions(scores, threshold=0.5)
    assert list(flags) == [False, True, True]
