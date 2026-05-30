"""[P1] Tests pour src/profiling.py"""
import pandas as pd
import pytest

# from src.profiling import build_card_profiles


@pytest.mark.skip(reason="TODO P1 : implémenter profiling puis activer ce test")
def test_card_profile_has_median():
    """Vérifie qu'un profil de carte contient bien une médiane des montants."""
    df = pd.DataFrame({
        "card_id": ["card_001", "card_001", "card_001"],
        "amount": [10.0, 20.0, 30.0],
    })
    # profiles = build_card_profiles(df)
    # assert profiles["card_001"]["median"] == 20.0
