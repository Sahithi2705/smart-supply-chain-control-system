
import numpy as np


def tsb_forecast(
    demand,
    horizon,
    alpha=0.1,
    beta=0.1
):
    """
    Teunter-Syntetos-Babai intermittent demand forecasting.

    alpha: demand-size smoothing parameter
    beta: demand-occurrence probability smoothing parameter
    """

    demand = np.asarray(demand, dtype=float)

    if horizon < 1:
        raise ValueError("Horizon must be at least 1.")

    if not 0 < alpha <= 1 or not 0 < beta <= 1:
        raise ValueError("Alpha and beta must be between 0 and 1.")

    if np.any(demand < 0):
        raise ValueError("Demand cannot contain negative values.")

    nonzero = np.flatnonzero(demand > 0)

    if len(nonzero) == 0:
        return np.zeros(horizon)

    first = nonzero[0]

    probability = 1.0 / (first + 1)
    demand_size = demand[first]

    for value in demand[first + 1:]:

        occurrence = 1.0 if value > 0 else 0.0

        probability = (
            beta * occurrence
            + (1 - beta) * probability
        )

        if occurrence:
            demand_size = (
                alpha * value
                + (1 - alpha) * demand_size
            )

    forecast = probability * demand_size

    return np.full(
        horizon,
        max(0.0, forecast)
    )


if __name__ == "__main__":

    example_demand = [
        0, 0, 5, 0, 0, 0, 8, 0, 0, 4,
        0, 0, 0, 6, 0, 0, 0, 0, 7, 0
    ]

    result = tsb_forecast(
        example_demand,
        horizon=28
    )

    print("TSB FORECAST")
    print("Daily forecast:", round(result[0], 4))
    print("28-day forecast:", round(result.sum(), 4))
