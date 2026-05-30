"""Tests pour src/profiling.py"""
import pandas as pd
import pytest

from src.profiling import build_card_profiles
from src.profiling import build_device_profiles
from src.profiling import build_ip_profiles
from src.profiling import build_merchant_profiles


# ---------------------------------------------------------------------------
# build_card_profiles
# ---------------------------------------------------------------------------

def test_card_profile_median_correct():
    """La médiane de [10, 20, 30] est 20."""
    df = pd.DataFrame({
        "card_id":           ["card_001", "card_001", "card_001"],
        "amount":            [10.0, 20.0, 30.0],
        "merchant_country":  ["CA", "CA", "CA"],
        "merchant_category": ["grocery", "grocery", "grocery"],
        "channel":           ["online", "online", "online"],
        "device_id":         ["dev_1", "dev_1", "dev_1"],
        "ip_address":        ["1.1.1.1", "1.1.1.1", "1.1.1.1"],
    })
    profiles = build_card_profiles(df)
    assert profiles["card_001"]["median_amount"] == 20.0


def test_card_profile_null_devices_excluded():
    """Les device_id null ne doivent pas apparaître dans known_devices."""
    df = pd.DataFrame({
        "card_id":           ["card_001", "card_001", "card_001"],
        "amount":            [10.0, 20.0, 30.0],
        "merchant_country":  ["CA", "CA", "CA"],
        "merchant_category": ["grocery", "grocery", "grocery"],
        "channel":           ["online", "online", "online"],
        "device_id":         ["dev_1", None, "dev_2"],
        "ip_address":        ["1.1.1.1", "1.1.1.1", "1.1.1.1"],
    })
    profiles = build_card_profiles(df)
    known = profiles["card_001"]["known_devices"]
    assert None not in known
    assert set(known) == {"dev_1", "dev_2"}


def test_card_profile_iqr_positive_when_amounts_vary():
    """L'IQR est strictement positif quand les montants sont dispersés."""
    df = pd.DataFrame({
        "card_id":           ["card_001"] * 4,
        "amount":            [5.0, 10.0, 50.0, 100.0],
        "merchant_country":  ["CA"] * 4,
        "merchant_category": ["grocery"] * 4,
        "channel":           ["online"] * 4,
        "device_id":         ["dev_1"] * 4,
        "ip_address":        ["1.1.1.1"] * 4,
    })
    profiles = build_card_profiles(df)
    assert profiles["card_001"]["iqr_amount"] > 0


# ---------------------------------------------------------------------------
# build_device_profiles
# ---------------------------------------------------------------------------

def test_device_profile_distinct_cards_count():
    """Un device utilisé par 3 cartes distinctes a distinct_cards=3."""
    df = pd.DataFrame({
        "device_id": ["dev_X", "dev_X", "dev_X"],
        "card_id":   ["card_A", "card_B", "card_C"],
        "amount":    [10.0, 20.0, 30.0],
    })
    profiles = build_device_profiles(df)
    assert profiles["dev_X"]["distinct_cards"] == 3


def test_device_profile_none_not_in_profiles():
    """Les lignes avec device_id=None ne créent pas de profil None."""
    df = pd.DataFrame({
        "device_id": ["dev_X", None, "dev_X"],
        "card_id":   ["card_A", "card_B", "card_A"],
        "amount":    [10.0, 20.0, 30.0],
    })
    profiles = build_device_profiles(df)
    assert None not in profiles


# ---------------------------------------------------------------------------
# build_ip_profiles
# ---------------------------------------------------------------------------

def test_ip_profile_distinct_cards():
    """Une IP vue par 2 cartes distinctes a nombre_cartes_distinctes=2."""
    df = pd.DataFrame({
        "transaction_id": ["tx_1", "tx_2", "tx_3"],
        "card_id":        ["card_A", "card_B", "card_A"],
        "ip_address":     ["10.0.0.1", "10.0.0.1", "10.0.0.1"],
    })
    profiles = build_ip_profiles(df)
    assert profiles["10.0.0.1"]["nombre_cartes_distinctes"] == 2


def test_ip_profile_none_ignored():
    """Les lignes avec ip_address=None ne génèrent pas de profil None."""
    df = pd.DataFrame({
        "transaction_id": ["tx_1", "tx_2"],
        "card_id":        ["card_A", "card_B"],
        "ip_address":     ["10.0.0.1", None],
    })
    profiles = build_ip_profiles(df)
    assert None not in profiles
    assert "10.0.0.1" in profiles


# ---------------------------------------------------------------------------
# build_merchant_profiles
# ---------------------------------------------------------------------------

def test_merchant_profile_median():
    """La médiane de [10, 15, 20] est 15 (montant_habituel)."""
    df = pd.DataFrame({
        "transaction_id": ["tx_1", "tx_2", "tx_3"],
        "card_id":        ["card_A", "card_B", "card_A"],
        "merchant_name":  ["ShopX", "ShopX", "ShopX"],
        "amount":         [10.0, 15.0, 20.0],
    })
    profiles = build_merchant_profiles(df)
    assert profiles["ShopX"]["montant_habituel"] == 15.0


def test_merchant_profile_max():
    """Le montant_maximal de [10, 15, 20] est 20."""
    df = pd.DataFrame({
        "transaction_id": ["tx_1", "tx_2", "tx_3"],
        "card_id":        ["card_A", "card_B", "card_A"],
        "merchant_name":  ["ShopX", "ShopX", "ShopX"],
        "amount":         [10.0, 15.0, 20.0],
    })
    profiles = build_merchant_profiles(df)
    assert profiles["ShopX"]["montant_maximal"] == 20.0


def test_merchant_profile_distinct_cards_not_transactions():
    """nombre_cartes_distinctes compte les cartes uniques, pas le nombre de transactions."""
    df = pd.DataFrame({
        "transaction_id": ["tx_1", "tx_2", "tx_3"],
        "card_id":        ["card_A", "card_B", "card_A"],
        "merchant_name":  ["ShopX", "ShopX", "ShopX"],
        "amount":         [10.0, 15.0, 20.0],
    })
    profiles = build_merchant_profiles(df)
    assert profiles["ShopX"]["nombre_cartes_distinctes"] == 2
    assert profiles["ShopX"]["nombre_total_transactions"] == 3
