export interface InventoryItem {
  sku: string;
  store_id?: string;
  store?: string;
  category_id?: string;
  category?: string;
  forecast_horizon_days?: number;
  forecast_demand_28d: number;
  average_daily_demand: number;
  daily_demand_std: number;
  lead_time_days: number;
  lead_time_demand: number;
  safety_stock: number;
  reorder_point: number;
  simulated_current_inventory: number;
  days_of_supply?: number | null;
  inventory_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'NORMAL' | 'EXCESS' | string;
  recommended_order_quantity: number;
  priority: 'URGENT' | 'HIGH' | 'NORMAL' | string;
  inventory_data_source?: string;
  inventory_source?: string;
  forecast_source: string;
  service_level_assumption: number;
}

export interface InventoryResponse {
  available: boolean;
  source: string;
  provenance: string;
  items: InventoryItem[];
}
