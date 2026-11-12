import { useState, useEffect, useCallback } from 'react';
import {
  ActiveShipmentsResponse,
  ShipmentKPIsResponse,
  GroupedShipmentsResponse,
} from '../types/shipment';
import {
  fetchActiveShipments,
  fetchShipmentKPIs,
  fetchGroupedShipments,
} from '../services/api';

export function useShipments(limit = 100) {
  const [active, setActive] = useState<ActiveShipmentsResponse | null>(null);
  const [kpis, setKpis] = useState<ShipmentKPIsResponse | null>(null);
  const [grouped, setGrouped] = useState<GroupedShipmentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [activeRes, kpisRes, groupedRes] = await Promise.allSettled([
        fetchActiveShipments(limit),
        fetchShipmentKPIs(),
        fetchGroupedShipments(limit),
      ]);

      if (activeRes.status === 'fulfilled') {
        setActive(activeRes.value);
      } else {
        console.warn('Active shipments failed:', activeRes.reason);
      }

      if (kpisRes.status === 'fulfilled') {
        setKpis(kpisRes.value);
      } else {
        console.warn('KPIs failed:', kpisRes.reason);
      }

      if (groupedRes.status === 'fulfilled') {
        setGrouped(groupedRes.value);
      } else {
        console.warn('Grouped shipments failed:', groupedRes.reason);
      }

      // If all three failed, raise error
      if (
        activeRes.status === 'rejected' &&
        kpisRes.status === 'rejected' &&
        groupedRes.status === 'rejected'
      ) {
        setError('Failed to communicate with shipment services');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown shipment fetch error');
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return { active, kpis, grouped, loading, error, refetch: loadData };
}
