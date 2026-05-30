"""[P1] Tests pour src/profiling.py"""
import pandas as pd
import pytest

# from src.profiling import build_card_profiles
from src.profiling import build_ip_profiles,build_merchant_profiles


@pytest.mark.skip(reason="TODO P1 : implémenter profiling puis activer ce test")
def test_card_profile_has_median():
    """Vérifie qu'un profil de carte contient bien une médiane des montants."""
    df = pd.DataFrame({
        "card_id": ["card_001", "card_001", "card_001"],
        "amount": [10.0, 20.0, 30.0],
    })
    # profiles = build_card_profiles(df)
    # assert profiles["card_001"]["median"] == 20.0

@pytest.mark.skip(reason="Mis en pause")
def test_build_ip_profiles_calcule_les_bonnes_metriques():
    """Vérifie que le carnet des IP compte bien les cartes uniques et ignore les lignes vides."""
    df_test = pd.DataFrame({
        'transaction_id': ['tx_001', 'tx_002', 'tx_003', 'tx_004'],
        'card_id':        ['card_A', 'card_B', 'card_A', 'card_C'],
        'amount':         [10.0,     20.0,     5.0,      500.0],
        'merchant_name':  ['Tim Hortons', 'Tim Hortons', 'Amazon.ca', 'FakeShop'],
        'ip_address':     ['192.168.1.1', '192.168.1.1', '192.168.1.2', None]
    })

    ip_profiles = build_ip_profiles(df_test)


    print(ip_profiles)
    assert '192.168.1.1' in ip_profiles
    assert ip_profiles['192.168.1.1']['nombre_cartes_distinctes'] == 2
    assert ip_profiles['192.168.1.1']['nombre_total_transactions'] == 2

    assert None not in ip_profiles
    assert len(ip_profiles) == 2


@pytest.mark.skip(reason="Mis en pause")
def test_build_merchant_profiles_calcule_les_bonnes_statistiques():
    """Vérifie que le carnet des marchands trouve la bonne médiane (montant habituel) et le maximum."""
    df_test = pd.DataFrame({
        'transaction_id': ['tx_001', 'tx_002', 'tx_003'],
        'card_id':        ['card_A', 'card_B', 'card_A'],
        'amount':         [10.0,     20.0,     15.0],
        'merchant_name':  ['Tim Hortons', 'Tim Hortons', 'Tim Hortons'],
    })

    merchant_profiles = build_merchant_profiles(df_test)
    
    
    print(merchant_profiles)

    assert 'Tim Hortons' in merchant_profiles
    assert merchant_profiles['Tim Hortons']['montant_habituel'] == 15.0
    assert merchant_profiles['Tim Hortons']['montant_maximal'] == 20.0
    assert merchant_profiles['Tim Hortons']['nombre_cartes_distinctes'] == 2