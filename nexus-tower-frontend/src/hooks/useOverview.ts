import { useState, useEffect, useCallback, useMemo } from 'react';
import { OverviewResponse, HealthResponse } from '../types/api';
import { ShipmentKPIsResponse } from '../types/shipment';
import { RiskIncident } from '../types/risk';
import { InventoryItem } from '../types/inventory';
import {
  fetchOverview,
  fetchHealth,
  fetchShipmentKPIs,
  fetchRiskAlerts,
  fetchInventoryRiskMatrix,
} from '../services/api';

export function useOverview(range = '28D') {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [kpis, setKpis] = useState<ShipmentKPIsResponse | null>(null);
  const [alerts, setAlerts] = useState<RiskIncident[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [alertsAvailable, setAlertsAvailable] = useState<boolean | null>(null);
  const [inventoryAvailable, setInventoryAvailable] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, hlRes, kpRes, alRes, invRes] = await Promise.allSettled([
        fetchOverview(range),
        fetchHealth(),
        fetchShipmentKPIs(),
        fetchRiskAlerts(),
        fetchInventoryRiskMatrix(),
      ]);

      if (ovRes.status === 'fulfilled') {
        setOverview(ovRes.value);
      } else {
        setOverview(null);
      }

      if (hlRes.status === 'fulfilled') {
        setHealth(hlRes.value);
      } else {
        setHealth(null);
      }

      if (kpRes.status === 'fulfilled') {
        setKpis(kpRes.value);
      } else {
        setKpis(null);
      }

      if (alRes.status === 'fulfilled') {
        setAlertsAvailable(alRes.value.available);
        setAlerts(alRes.value.available ? alRes.value.alerts || [] : []);
      } else {
        setAlertsAvailable(false);
        setAlerts([]);
      }

      if (invRes.status === 'fulfilled') {
        setInventoryAvailable(invRes.value.available);
        setInventory(invRes.value.available ? invRes.value.items || [] : []);
      } else {
        setInventoryAvailable(false);
        setInventory([]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to query control tower telemetry');
    } finally {
      setLoading(false);
    }
  }, [range]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Interpret module execution status from health.sources and overview.sources_available
  const moduleStatus = useMemo(() => {
    return {
      module2: Boolean(health?.sources?.module2_sqlite ?? overview?.sources_available?.module2),
      module3: Boolean(health?.sources?.module3_predictions ?? overview?.sources_available?.module3),
      module4: Boolean(health?.sources?.module4_outputs ?? overview?.sources_available?.module4),
      module5: Boolean(health?.sources?.module5_outputs ?? overview?.sources_available?.module5),
    };
  }, [health, overview]);

  // Derived metrics adhering to zero-synthetic and true availability policy
  const metrics = useMemo(() => {
    // Total Shipments: prefer kpis.total_shipments (unique shipments), fallback to overview.shipment_count
    let totalShipments: number | string = 'Unavailable';
    if (kpis?.available && kpis.total_shipments !== undefined && kpis.total_shipments !== null) {
      totalShipments = kpis.total_shipments;
    } else if (overview?.shipment_count !== undefined && overview?.shipment_count !== null && moduleStatus.module2) {
      totalShipments = overview.shipment_count;
    }

    // Delayed Shipments
    let delayedShipments: number | string = 'Unavailable';
    if (overview?.delayed_shipments !== undefined && overview?.delayed_shipments !== null && moduleStatus.module2) {
      delayedShipments = overview.delayed_shipments;
    } else if (kpis?.available && kpis.delayed_events !== undefined && kpis.delayed_events !== null) {
      delayedShipments = kpis.delayed_events;
    }

    // Critical Incidents: derived only if risk engine output is available
    let criticalIncidents: number | string = 'Unavailable';
    let totalIncidents = 0;
    if (alertsAvailable === true || moduleStatus.module5) {
      criticalIncidents = alerts.filter((a) => (a.risk_level || '').toUpperCase() === 'CRITICAL').length;
      totalIncidents = alerts.length;
    }

    // Inventory Allocations: derived only if inventory output is available
    let inventoryCount: number | string = 'Unavailable';
    if (inventoryAvailable === true || moduleStatus.module4) {
      inventoryCount = inventory.length;
    }

    return {
      totalShipments,
      delayedShipments,
      criticalIncidents,
      totalIncidents,
      inventoryCount,
    };
  }, [kpis, overview, alerts, inventory, alertsAvailable, inventoryAvailable, moduleStatus]);

  // Dynamic inventory risk category distribution
  const inventoryDist = useMemo(() => {
    if (!inventory || inventory.length === 0) return [];
    const counts: Record<string, number> = {};
    inventory.forEach((item) => {
      const raw = item.inventory_risk || 'UNKNOWN';
      const key = raw.toUpperCase();
      counts[key] = (counts[key] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({
      name: name.charAt(0) + name.slice(1).toLowerCase(),
      value,
    }));
  }, [inventory]);

  // Risk incident distribution
  const riskDist = useMemo(() => {
    if (!alerts || alerts.length === 0) return [];
    const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    alerts.forEach((alert) => {
      const lvl = (alert.risk_level || '').toUpperCase();
      if (counts[lvl] !== undefined) counts[lvl] += 1;
    });
    return [
      { level: 'CRITICAL', count: counts.CRITICAL },
      { level: 'HIGH', count: counts.HIGH },
      { level: 'MEDIUM', count: counts.MEDIUM },
      { level: 'LOW', count: counts.LOW },
    ].filter((d) => d.count > 0 || alerts.length > 0);
  }, [alerts]);

  return {
    overview,
    health,
    kpis,
    alerts,
    inventory,
    alertsAvailable,
    inventoryAvailable,
    moduleStatus,
    metrics,
    inventoryDist,
    riskDist,
    loading,
    error,
    refetch: loadData,
  };
}
