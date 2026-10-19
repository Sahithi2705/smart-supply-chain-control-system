
import pytest

from realtime.kpi import (
    calculate_eta_variance,
    calculate_delay_status,
    calculate_days_of_supply,
    calculate_stockout_risk,
)


def test_delay_status():
    assert calculate_delay_status(0) == "ON_TIME"
    assert calculate_delay_status(2) == "MINOR_DELAY"
    assert calculate_delay_status(8) == "MODERATE_DELAY"
    assert calculate_delay_status(10) == "SEVERE_DELAY"


def test_days_of_supply():
    assert calculate_days_of_supply(120, 30) == 4.0


def test_zero_demand():
    assert calculate_days_of_supply(120, 0) == float("inf")


def test_stockout_risk():
    assert calculate_stockout_risk(4, 5) == "HIGH"
    assert calculate_stockout_risk(6, 5) == "MEDIUM"
    assert calculate_stockout_risk(10, 5) == "LOW"


def test_negative_inventory_rejected():
    with pytest.raises(ValueError):
        calculate_days_of_supply(-1, 30)
