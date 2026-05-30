"""[P1] Tests pour src/detection/*"""
import pandas as pd
import pytest

# from src.detection import score_amount_deviation, score_cross_card


@pytest.mark.skip(reason="TODO P1 : implémenter détection puis activer")
def test_amount_deviation_flags_large_amount():
    """Une transaction 20× la médiane doit recevoir un score élevé."""
    pass


@pytest.mark.skip(reason="TODO P1 : implémenter détection puis activer")
def test_cross_card_flags_shared_device():
    """Un device utilisé par 5 cartes différentes doit recevoir un score élevé."""
    pass
