
def calculate_eta_variance(planned_eta, current_eta):
    """Return ETA variance in hours. Positive means late."""
    difference = current_eta - planned_eta
    return difference.total_seconds() / 3600


def calculate_delay_status(eta_variance):
    """Classify a shipment based on ETA variance."""
    if eta_variance <= 0:
        return "ON_TIME"
    if eta_variance <= 4:
        return "MINOR_DELAY"
    if eta_variance <= 8:
        return "MODERATE_DELAY"
    return "SEVERE_DELAY"


def calculate_days_of_supply(available_inventory, average_daily_demand):
    """Estimate how many days inventory can meet average demand."""
    if available_inventory < 0 or average_daily_demand < 0:
        raise ValueError("Inventory and demand cannot be negative.")
    if average_daily_demand == 0:
        return float("inf")
    return available_inventory / average_daily_demand


def calculate_stockout_risk(days_of_supply, lead_time_days):
    """Flag inventory that may run out before replenishment arrives."""
    if days_of_supply < 0 or lead_time_days < 0:
        raise ValueError("Coverage and lead time cannot be negative.")

    if days_of_supply <= lead_time_days:
        return "HIGH"
    if days_of_supply <= lead_time_days + 3:
        return "MEDIUM"
    return "LOW"
