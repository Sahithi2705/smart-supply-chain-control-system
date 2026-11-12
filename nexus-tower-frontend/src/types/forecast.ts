export interface ForecastRecord {
  sales_date: string;
  sku: string;
  store_id: string;
  category_id: string;
  actual: number | null;
  xgboost_prediction: number | null;
  seasonal_naive_prediction: number | null;
  moving_average_prediction: number | null;
}

export interface ForecastResponse {
  available: boolean;
  source: string;
  note: string;
  columns: string[];
  predictions: ForecastRecord[];
}
