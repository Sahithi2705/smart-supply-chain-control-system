
import json
from dataclasses import asdict
from datetime import datetime

from kafka import KafkaProducer
from events import ShipmentEvent

from kafka.serializer import Serializer


class SupplyChainJsonSerializer(Serializer):
    def serialize(self, topic, headers, data):
        if data is None:
            return None
        return json.dumps(data).encode("utf-8")


TOPIC = "shipment-events"
BOOTSTRAP_SERVERS = "localhost:9092"


def create_sample_events():
    return [
        ShipmentEvent(
            shipment_id="SHP1001",
            order_id="ORD1001",
            sku="SKU001",
            warehouse_id="WH001",
            carrier_id="CARRIER01",
            event_type="SHIPMENT_DELAY",
            planned_eta=datetime(2026, 9, 28, 10, 0),
            current_eta=datetime(2026, 9, 28, 18, 0),
            timestamp=datetime.now(),
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
            timestamp=datetime.now(),
        ),
    ]


def serialize_event(event):
    event_data = asdict(event)

    # Convert datetime fields to ISO 8601 strings for JSON.
    for key, value in event_data.items():
        if isinstance(value, datetime):
            event_data[key] = value.isoformat()

    return event_data


def publish_events():
    producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=SupplyChainJsonSerializer(),
)

    try:
        for event in create_sample_events():
            event_data = serialize_event(event)

            future = producer.send(TOPIC, value=event_data)
            metadata = future.get(timeout=10)

            print(
                f"Published {event_data['shipment_id']} "
                f"to topic={metadata.topic}, "
                f"partition={metadata.partition}, "
                f"offset={metadata.offset}"
            )
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    publish_events()
