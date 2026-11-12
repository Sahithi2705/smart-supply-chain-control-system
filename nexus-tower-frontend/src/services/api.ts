import axios, { AxiosError } from 'axios';
import {
  HealthResponse,
  OverviewResponse,
  AnalyticsSummaryResponse,
} from '../types/api';
import {
  ActiveShipmentsResponse,
  ShipmentKPIsResponse,
  GroupedShipmentsResponse,
} from '../types/shipment';
import { ForecastResponse } from '../types/forecast';
import { InventoryResponse } from '../types/inventory';
import { RiskAlertsResponse } from '../types/risk';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ApiStatus {
  connected: boolean;
  checkedAt: string;
  error?: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await apiClient.get<HealthResponse>('/health');
  return res.data;
}

export async function checkApiHealth(): Promise<{ status: HealthResponse; connected: boolean }> {
  try {
    const data = await fetchHealth();
    return { status: data, connected: true };
  } catch (err) {
    const message = err instanceof AxiosError ? err.message : 'API unreachable';
    throw new Error(message);
  }
}

export async function fetchRoot(): Promise<{ service: string; docs: string; status: string }> {
  const res = await apiClient.get('/');
  return res.data;
}

export async function fetchOverview(range = '28D'): Promise<OverviewResponse> {
  const res = await apiClient.get<OverviewResponse>('/api/v1/overview', {
    params: { range },
  });
  return res.data;
}

export async function fetchActiveShipments(limit = 100): Promise<ActiveShipmentsResponse> {
  const res = await apiClient.get<ActiveShipmentsResponse>('/api/v1/shipments/active', {
    params: { limit },
  });
  return res.data;
}

export async function fetchShipmentKPIs(): Promise<ShipmentKPIsResponse> {
  const res = await apiClient.get<ShipmentKPIsResponse>('/api/v1/shipments/kpis');
  return res.data;
}

export async function fetchGroupedShipments(limit = 100): Promise<GroupedShipmentsResponse> {
  const res = await apiClient.get<GroupedShipmentsResponse>('/api/v1/shipments/grouped', {
    params: { limit },
  });
  return res.data;
}

export async function fetchForecastPredictions(limit = 500): Promise<ForecastResponse> {
  const res = await apiClient.get<ForecastResponse>('/api/v1/forecasts/predictions', {
    params: { limit },
  });
  return res.data;
}

export async function fetchInventoryRiskMatrix(): Promise<InventoryResponse> {
  const res = await apiClient.get<InventoryResponse>('/api/v1/inventory/risk-matrix');
  return res.data;
}

export async function fetchRiskAlerts(): Promise<RiskAlertsResponse> {
  const res = await apiClient.get<RiskAlertsResponse>('/api/v1/alerts/stream');
  return res.data;
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  const res = await apiClient.get<AnalyticsSummaryResponse>('/api/v1/analytics/summary');
  return res.data;
}
