export interface RiskIncident {
  incident_id?: string;
  id?: number | string;
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
  delay_status?: string | null;
  available_inventory?: number | null;
  average_daily_demand?: number | null;
  days_of_supply?: number | null;
  stockout_risk?: string | null;
  recorded_at?: string | null;
  risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  risk_reason?: string;
  incident_required?: boolean;
  recommended_action?: string;
  incident_status?: 'OPEN' | 'INVESTIGATING' | 'MITIGATED' | 'RESOLVED' | string;
}

export interface RiskAlertsResponse {
  available: boolean;
  source: string;
  alerts: RiskIncident[];
}
