from dataclasses import dataclass
from datetime import datetime


@dataclass
class ShipmentEvent:
    shipment_id: str
    order_id: str
    sku: str
    warehouse_id: str
    carrier_id: str
    event_type: str
    planned_eta: datetime
    current_eta: datetime
    timestamp: datetime
