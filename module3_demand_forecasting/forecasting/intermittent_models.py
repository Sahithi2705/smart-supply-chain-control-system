
import numpy as np
import pandas as pd


def croston_forecast(
    demand,
    horizon,
    alpha=0.1,
    sba=False
):
    """
    Croston/SBA forecast for intermittent demand.

    demand: historical daily demand array
    horizon: number of future days
    alpha: smoothing parameter between 0 and 1
    sba: apply SBA bias correction when True
    """

    demand = np.asarray(demand, dtype=float)

    if horizon < 1:
        raise ValueError("Horizon must be at least 1.")

    if not 0 < alpha <= 1:
        raise ValueError("Alpha must be between 0 and 1.")

    if np.any(demand < 0):
        raise ValueError("Demand cannot contain negative values.")

    nonzero_positions = np.flatnonzero(demand > 0)

    if len(nonzero_positions) == 0:
        return np.zeros(horizon)

    first_position = nonzero_positions[0]

    demand_size = demand[first_position]
    demand_interval = first_position + 1

    previous_position = first_position

    for position in nonzero_positions[1:]:
        interval = position - previous_position
        observed_demand = demand[position]

        demand_size = (
            alpha * observed_demand
            + (1 - alpha) * demand_size
        )

        demand_interval = (
            alpha * interval
            + (1 - alpha) * demand_interval
        )

        previous_position = position

    forecast = demand_size / demand_interval

    if sba:
        forecast *= (1 - alpha / 2)

    return np.full(horizon, max(0.0, forecast))


def croston(demand, horizon, alpha=0.1):
    return croston_forecast(
        demand,
        horizon,
        alpha=alpha,
        sba=False
    )


def sba(demand, horizon, alpha=0.1):
    return croston_forecast(
        demand,
        horizon,
        alpha=alpha,
        sba=True
    )


if __name__ == "__main__":
    example_demand = [
        0, 0, 5, 0, 0, 0, 8, 0, 0, 4,
        0, 0, 0, 6, 0, 0, 0, 0, 7, 0
    ]

    horizon = 28

    croston_result = croston(
        example_demand,
        horizon
    )

    sba_result = sba(
        example_demand,
        horizon
    )

    print("CROSTON FORECAST")
    print("Daily forecast:", round(croston_result[0], 4))
    print("28-day forecast:", round(croston_result.sum(), 4))

    print("\nSBA FORECAST")
    print("Daily forecast:", round(sba_result[0], 4))
    print("28-day forecast:", round(sba_result.sum(), 4))
