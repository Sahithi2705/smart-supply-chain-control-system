from datetime import datetime

from events import ShipmentEvent


def create_sample_events():

    events = [
        ShipmentEvent(
            shipment_id="SHP1001",
            order_id="ORD1001",
            sku="SKU001",
            warehouse_id="WH001",
            carrier_id="CARRIER01",
            event_type="SHIPMENT_DELAY",
            planned_eta=datetime(2026, 9, 28, 10, 0),
            current_eta=datetime(2026, 9, 28, 18, 0),
            timestamp=datetime.now()
        ),

        ShipmentEvent(
            shipment_id="SHP1002",
            order_id="ORD1002",
            sku="SKU002",
            warehouse_id="WH002",
            carrier_id="CARRIER02",
            event_type="IN_TRANSIT",
            planned_eta=datetime(2026, 9, 28, 14, 0),
            current_eta=datetime(2026, 9, 28, 15, 0),
            timestamp=datetime.now()
        )
    ]

    return events


if __name__ == "__main__":
    for event in create_sample_events():
        print(event)
