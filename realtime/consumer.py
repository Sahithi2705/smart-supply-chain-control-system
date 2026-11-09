
import json
from datetime import datetime

from kafka import KafkaConsumer
from kafka.serializer import Deserializer

try:
    from .storage import save_shipment_event
    from .kpi import (
        calculate_eta_variance,
        calculate_delay_status,
        calculate_days_of_supply,
        calculate_stockout_risk,
    )
except ImportError:
    from storage import save_shipment_event
    from kpi import (
        calculate_eta_variance,
        calculate_delay_status,
        calculate_days_of_supply,
        calculate_stockout_risk,
    )


TOPIC = "shipment-events"
BOOTSTRAP_SERVERS = "localhost:9092"


class SupplyChainJsonDeserializer(Deserializer):

    def deserialize(self, topic, headers, data):
        if data is None:
            return None

        return json.loads(data.decode("utf-8"))


def process_event(event):

    planned_eta = datetime.fromisoformat(event["planned_eta"])
    current_eta = datetime.fromisoformat(event["current_eta"])

    # Calculate shipment delay KPIs
    eta_variance = calculate_eta_variance(
        planned_eta,
        current_eta,
    )

    delay_status = calculate_delay_status(eta_variance)

    print("\n--- SUPPLY CHAIN EVENT ---")
    print(f"Event ID       : {event['event_id']}")
    print(f"Shipment       : {event['shipment_id']}")
    print(f"Order          : {event['order_id']}")
    print(f"SKU            : {event['sku']}")
    print(f"Warehouse      : {event['warehouse_id']}")
    print(f"Event          : {event['event_type']}")
    print(f"ETA variance   : {eta_variance:.2f} hours")
    print(f"Delay status   : {delay_status}")

    # Demonstration inventory values (not live inventory data)
    available_inventory = 120
    average_daily_demand = 30
    lead_time_days = 5

    # Calculate inventory KPIs
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

    # Prepare event data for SQLite
    event_data = {
        "event_id": event["event_id"],
        "shipment_id": event["shipment_id"],
        "order_id": event["order_id"],
        "sku": event["sku"],
        "warehouse_id": event["warehouse_id"],
        "carrier_id": event["carrier_id"],
        "event_type": event["event_type"],
        "planned_eta": event["planned_eta"],
        "current_eta": event["current_eta"],
        "timestamp": event["timestamp"],
    }

    # Prepare calculated KPIs for SQLite
    kpis = {
        "eta_variance_hours": eta_variance,
        "delay_status": delay_status,
        "available_inventory": available_inventory,
        "average_daily_demand": average_daily_demand,
        "days_of_supply": days_of_supply,
        "stockout_risk": stockout_risk,
    }

    # Save the event and KPIs exactly once
    saved = save_shipment_event(event_data, kpis)

    if saved:
        print("Database status : Event saved successfully")
    else:
        print("Database status : Duplicate event ignored")


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
