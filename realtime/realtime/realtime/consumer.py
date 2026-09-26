from producer import create_sample_events
from kpi import (
    calculate_eta_variance,
    calculate_delay_status,
    calculate_days_of_supply
)


def process_event(event):

    eta_variance = calculate_eta_variance(
        event.planned_eta,
        event.current_eta
    )

    delay_status = calculate_delay_status(
        eta_variance
    )

    print("\n--- SUPPLY CHAIN EVENT ---")
    print(f"Shipment       : {event.shipment_id}")
    print(f"Order          : {event.order_id}")
    print(f"SKU            : {event.sku}")
    print(f"Warehouse      : {event.warehouse_id}")
    print(f"Event          : {event.event_type}")
    print(f"ETA variance   : {eta_variance:.2f} hours")
    print(f"Delay status   : {delay_status}")


if __name__ == "__main__":

    events = create_sample_events()

    for event in events:
        process_event(event)
