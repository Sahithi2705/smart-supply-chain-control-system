from datetime import datetime


def calculate_eta_variance(planned_eta, current_eta):
    """
    Calculate shipment ETA variance in hours.
    Positive value means the shipment is delayed.
    """
    difference = current_eta - planned_eta
    return difference.total_seconds() / 3600


def calculate_delay_status(eta_variance):
    if eta_variance <= 0:
        return "ON_TIME"

    if eta_variance <= 4:
        return "MINOR_DELAY"

    if eta_variance <= 8:
        return "MODERATE_DELAY"

    return "SEVERE_DELAY"


def calculate_days_of_supply(
    available_inventory,
    average_daily_demand
):
    if average_daily_demand <= 0:
        return float("inf")

    return available_inventory / average_daily_demand
