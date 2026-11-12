import { useState, useEffect, useCallback } from 'react';
import { AnalyticsSummaryResponse, HealthResponse } from '../types/api';
import { fetchAnalyticsSummary, fetchHealth } from '../services/api';

export function useAnalytics() {
  const [data, setData] = useState<AnalyticsSummaryResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, healthRes] = await Promise.allSettled([
        fetchAnalyticsSummary(),
        fetchHealth(),
      ]);

      if (summaryRes.status === 'fulfilled') {
        setData(summaryRes.value);
      } else {
        setData(null);
      }

      if (healthRes.status === 'fulfilled') {
        setHealth(healthRes.value);
      } else {
        setHealth(null);
      }

      if (summaryRes.status === 'rejected' && healthRes.status === 'rejected') {
        setError('Failed to fetch analytics services');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown analytics error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return { data, health, loading, error, refetch: loadData };
}
