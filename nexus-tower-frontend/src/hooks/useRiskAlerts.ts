import { useState, useEffect, useCallback, useMemo } from 'react';
import { RiskAlertsResponse, RiskIncident } from '../types/risk';
import { fetchRiskAlerts } from '../services/api';

export function useRiskAlerts() {
  const [data, setData] = useState<RiskAlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRiskAlerts();
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load risk incidents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredAlerts = useMemo(() => {
    if (!data?.alerts) return [];
    return data.alerts.filter((alert: RiskIncident) => {
      const matchSeverity =
        severityFilter === 'ALL' ||
        (alert.risk_level || '').toUpperCase() === severityFilter.toUpperCase();
      const search = searchTerm.toLowerCase();
      const matchSearch =
        !search ||
        (alert.incident_id || '').toLowerCase().includes(search) ||
        (alert.shipment_id || '').toLowerCase().includes(search) ||
        (alert.risk_reason || '').toLowerCase().includes(search) ||
        (alert.sku || '').toLowerCase().includes(search) ||
        (alert.carrier_id || '').toLowerCase().includes(search) ||
        (alert.warehouse_id || '').toLowerCase().includes(search);
      return matchSeverity && matchSearch;
    });
  }, [data, severityFilter, searchTerm]);

  // Aggregate stats
  const stats = useMemo(() => {
    if (!data?.alerts || data.alerts.length === 0) {
      return {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        total: 0,
        avgScore: 0,
      };
    }
    let totalScore = 0;
    const res = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      total: data.alerts.length,
      avgScore: 0,
    };
    data.alerts.forEach((a) => {
      totalScore += a.risk_score || 0;
      const lvl = (a.risk_level || '').toUpperCase();
      if (lvl === 'CRITICAL') res.critical += 1;
      else if (lvl === 'HIGH') res.high += 1;
      else if (lvl === 'MEDIUM') res.medium += 1;
      else if (lvl === 'LOW') res.low += 1;
    });
    res.avgScore = Math.round(totalScore / data.alerts.length);
    return res;
  }, [data]);

  return {
    data,
    filteredAlerts,
    stats,
    severityFilter,
    setSeverityFilter,
    searchTerm,
    setSearchTerm,
    loading,
    error,
    refetch: loadData,
  };
}
