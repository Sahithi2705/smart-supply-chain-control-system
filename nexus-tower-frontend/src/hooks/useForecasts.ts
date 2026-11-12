import { useState, useEffect, useCallback, useMemo } from 'react';
import { ForecastResponse, ForecastRecord } from '../types/forecast';
import { fetchForecastPredictions } from '../services/api';

export function useForecasts(limit = 1000) {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedSku, setSelectedSku] = useState<string>('ALL');
  const [selectedStore, setSelectedStore] = useState<string>('ALL');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchForecastPredictions(limit);
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load forecast predictions');
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Derived filter options
  const skus = useMemo(() => {
    if (!data?.predictions) return [];
    return Array.from(new Set(data.predictions.map((p) => p.sku))).sort();
  }, [data]);

  const stores = useMemo(() => {
    if (!data?.predictions) return [];
    return Array.from(new Set(data.predictions.map((p) => p.store_id))).sort();
  }, [data]);

  // Filtered predictions
  const filteredPredictions = useMemo(() => {
    if (!data?.predictions) return [];
    return data.predictions.filter((p: ForecastRecord) => {
      const matchSku = selectedSku === 'ALL' || p.sku === selectedSku;
      const matchStore = selectedStore === 'ALL' || p.store_id === selectedStore;
      return matchSku && matchStore;
    });
  }, [data, selectedSku, selectedStore]);

  return {
    data,
    filteredPredictions,
    skus,
    stores,
    selectedSku,
    setSelectedSku,
    selectedStore,
    setSelectedStore,
    loading,
    error,
    refetch: loadData,
  };
}
