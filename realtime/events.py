
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


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
    event_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid4())
