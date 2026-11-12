export interface ShipmentEvent {
  id: number;
  shipment_id: string;
  order_id?: string | null;
  sku?: string | null;
  warehouse_id?: string | null;
  carrier_id?: string | null;
  event_type?: string | null;
  planned_eta?: string | null;
  current_eta?: string | null;
  event_timestamp?: string | null;
  eta_variance_hours?: number | null;
  delay_status?: 'ON_TIME' | 'MINOR_DELAY' | 'MODERATE_DELAY' | 'SEVERE_DELAY' | string | null;
  available_inventory?: number | null;
  average_daily_demand?: number | null;
  days_of_supply?: number | null;
  stockout_risk?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string | null;
  recorded_at?: string | null;
  event_id?: string | null;
  duplicate_of_id?: number | null;
}

export interface ActiveShipmentsResponse {
  available: boolean;
  source: string;
  shipments: ShipmentEvent[];
  count: number;
}

export interface ShipmentKPIsResponse {
  available: boolean;
  source?: string;
  total_shipments?: number;
  event_count?: number;
  delayed_events?: number;
  average_eta_variance_hours?: number | null;
}

export interface GroupedShipment {
  shipment_id: string;
  order_id: string | null;
  sku: string | null;
  warehouse_id: string | null;
  carrier_id: string | null;
  events: ShipmentEvent[];
  latest_event: ShipmentEvent;
  event_count: number;
}

export interface GroupedShipmentsResponse {
  available: boolean;
  source: string;
  count: number;
  shipments: GroupedShipment[];
}
