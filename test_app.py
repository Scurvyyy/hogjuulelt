"""Unit tests for app.py (Lab 10): 2 normal, 2 edge case, 1 mock."""
from unittest.mock import patch

import pytest

from app import app, calculate_total, total_with_discount


# --- Normal cases -----------------------------------------------------------
def test_calculate_total_sums_prices():
    # Arrange
    prices = [10, 20, 30]
    # Act
    result = calculate_total(prices)
    # Assert
    assert result == 60


def test_calculate_total_applies_tax():
    # Arrange
    prices = [100]
    # Act
    result = calculate_total(prices, tax_rate=0.1)
    # Assert
    assert result == 110.0


# --- Edge cases -------------------------------------------------------------
def test_calculate_total_empty_list_is_zero():
    assert calculate_total([]) == 0


def test_calculate_total_rejects_negative_price():
    with pytest.raises(ValueError):
        calculate_total([10, -5])


# --- Mock -------------------------------------------------------------------
def test_total_with_discount_uses_mocked_discount():
    # fetch_discount is replaced so only the arithmetic is tested
    with patch("app.fetch_discount", return_value=0.5) as mocked:
        result = total_with_discount([100], "ANYCODE")
    mocked.assert_called_once_with("ANYCODE")
    assert result == 50.0


# --- Extra: endpoints used by Docker/K8s/monitoring labs --------------------
def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_metrics_endpoint_exposes_counters():
    client = app.test_client()
    client.get("/")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"app_requests_total" in response.data
