"""[P2] Tests pour src/scoring.py"""
import pandas as pd
import pytest

from src.scoring import Weights


def test_weights_must_sum_to_one():
    w = Weights(w1=0.5, w2=0.5, w3=0.0, w4=0.0)
    w.validate()  # ne doit pas lever


def test_weights_invalid_sum_raises():
    w = Weights(w1=0.3, w2=0.3, w3=0.3, w4=0.3)  # somme = 1.2
    with pytest.raises(ValueError):
        w.validate()


@pytest.mark.skip(reason="TODO P2 : implémenter compute_fraud_scores puis activer")
def test_compute_fraud_scores_weighted_sum():
    """0.25 * 0.8 + 0.25 * 0.4 + 0.25 * 0.0 + 0.25 * 0.0 = 0.3"""
    pass
