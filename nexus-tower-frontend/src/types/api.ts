export interface ApiResponseMeta {
  available: boolean;
  source?: string;
  provenance?: string;
  note?: string;
}

export interface HealthResponse {
  status: string;
  sources: {
    module2_sqlite: boolean;
    module3_predictions: boolean;
    module4_outputs: boolean;
    module5_outputs: boolean;
  };
}

export interface OverviewResponse {
  range: string;
  data_provenance: string;
  shipment_count: number;
  delayed_shipments: number;
  sources_available: {
    module2?: boolean;
    module3?: boolean;
    module4?: boolean;
    module5?: boolean;
  };
  note: string;
}

export interface AnalyticsSummaryResponse {
  module2_events: number | null;
  module3_predictions_available: boolean;
  module4_summary: Array<{
    inventory_risk: string;
    sku_store_count?: number;
    sku_store_pairs?: number;
  }> | null;
  module5_summary: Array<{
    risk_level: string;
    shipment_count?: number;
    event_count: number;
    average_risk_score?: number;
  }> | null;
}
