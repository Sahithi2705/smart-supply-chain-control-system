
import json
from datetime import datetime

from kafka import KafkaConsumer

from kpi import (
    calculate_eta_variance,
    calculate_delay_status,
    calculate_days_of_supply,
    calculate_stockout_risk,
)
from kafka.serializer import Deserializer


class SupplyChainJsonDeserializer(Deserializer):
    def deserialize(self, topic, headers, data):
        if data is None:
            return None
        return json.loads(data.decode("utf-8"))

TOPIC = "shipment-events"
BOOTSTRAP_SERVERS = "localhost:9092"


def process_event(event):
    planned_eta = datetime.fromisoformat(event["planned_eta"])
    current_eta = datetime.fromisoformat(event["current_eta"])

    eta_variance = calculate_eta_variance(
        planned_eta,
        current_eta,
    )
    delay_status = calculate_delay_status(eta_variance)

    print("\n--- SUPPLY CHAIN EVENT ---")
    print(f"Shipment       : {event['shipment_id']}")
    print(f"Order          : {event['order_id']}")
    print(f"SKU            : {event['sku']}")
    print(f"Warehouse      : {event['warehouse_id']}")
    print(f"Event          : {event['event_type']}")
    print(f"ETA variance   : {eta_variance:.2f} hours")
    print(f"Delay status   : {delay_status}")

    # Demonstration inventory values, not live inventory data.
    available_inventory = 120
    average_daily_demand = 30
    lead_time_days = 5

    days_of_supply = calculate_days_of_supply(
        available_inventory,
        average_daily_demand,
    )
    stockout_risk = calculate_stockout_risk(
        days_of_supply,
        lead_time_days,
    )

    print(f"Inventory      : {available_inventory} units")
    print(f"Daily demand   : {average_daily_demand} units")
    print(f"Days of supply : {days_of_supply:.1f}")
    print(f"Stockout risk  : {stockout_risk}")


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="smart-chain-kpi-consumer-v2",
        auto_offset_reset="earliest",
        value_deserializer=SupplyChainJsonDeserializer(),
    )

    print(f"Listening for events on Kafka topic: {TOPIC}")
    print("Press Ctrl+C to stop.")

    try:
        for message in consumer:
            process_event(message.value)
    except KeyboardInterrupt:
        print("\nConsumer stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
