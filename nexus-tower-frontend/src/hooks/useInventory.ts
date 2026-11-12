import { useState, useEffect, useCallback, useMemo } from 'react';
import { InventoryResponse, InventoryItem } from '../types/inventory';
import { fetchInventoryRiskMatrix } from '../services/api';

export function useInventory() {
  const [data, setData] = useState<InventoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchInventoryRiskMatrix();
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load inventory matrix');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredItems = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter((item: InventoryItem) => {
      const itemRisk = (item.inventory_risk || '').toUpperCase();
      const matchRisk = riskFilter === 'ALL' || itemRisk === riskFilter.toUpperCase();
      const storeVal = (item.store_id || item.store || '').toLowerCase();
      const catVal = (item.category_id || item.category || '').toLowerCase();
      const skuVal = (item.sku || '').toLowerCase();
      const search = searchTerm.toLowerCase();

      const matchSearch =
        !search ||
        skuVal.includes(search) ||
        storeVal.includes(search) ||
        catVal.includes(search);
      return matchRisk && matchSearch;
    });
  }, [data, riskFilter, searchTerm]);

  // Aggregate metrics
  const summary = useMemo(() => {
    if (!data?.items || data.items.length === 0) {
      return {
        criticalCount: 0,
        highCount: 0,
        mediumCount: 0,
        lowCount: 0,
        normalCount: 0,
        excessCount: 0,
        totalItems: 0,
        totalReorderQty: 0,
      };
    }
    return data.items.reduce(
      (acc, item) => {
        acc.totalItems += 1;
        acc.totalReorderQty += item.recommended_order_quantity || 0;
        const r = (item.inventory_risk || '').toUpperCase();
        if (r === 'CRITICAL') acc.criticalCount += 1;
        else if (r === 'HIGH') acc.highCount += 1;
        else if (r === 'MEDIUM') acc.mediumCount += 1;
        else if (r === 'LOW') acc.lowCount += 1;
        else if (r === 'NORMAL') acc.normalCount += 1;
        else if (r === 'EXCESS') acc.excessCount += 1;
        return acc;
      },
      {
        criticalCount: 0,
        highCount: 0,
        mediumCount: 0,
        lowCount: 0,
        normalCount: 0,
        excessCount: 0,
        totalItems: 0,
        totalReorderQty: 0,
      }
    );
  }, [data]);

  return {
    data,
    filteredItems,
    summary,
    riskFilter,
    setRiskFilter,
    searchTerm,
    setSearchTerm,
    loading,
    error,
    refetch: loadData,
  };
}
