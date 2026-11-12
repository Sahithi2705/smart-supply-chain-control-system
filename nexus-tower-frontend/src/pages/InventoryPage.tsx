import React from 'react';
import {
  Boxes,
  AlertTriangle,
  RotateCcw,
  ShoppingCart,
  ShieldAlert,
  Search,
  Filter,
  RefreshCw,
  PackageCheck,
  Percent,
} from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { DataTable, ColumnDef } from '../components/common/DataTable';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceNotice } from '../components/common/ProvenanceNotice';
import { EmptyState } from '../components/common/EmptyState';
import { SearchFilterBar } from '../components/common/SearchFilterBar';
import { InventoryDonutChart } from '../components/charts/InventoryDonutChart';
import { useInventory } from '../hooks/useInventory';
import { InventoryItem } from '../types/inventory';
import { formatNumber } from '../utilities/formatters';

export const InventoryPage: React.FC = () => {
  const {
    data,
    filteredItems,
    summary,
    riskFilter,
    setRiskFilter,
    searchTerm,
    setSearchTerm,
    loading,
    error,
    refetch,
  } = useInventory();

  // Chart data dynamically computed from real data distribution
  const donutData = React.useMemo(() => {
    if (!data?.items || !data?.available) return [];
    const counts: Record<string, number> = {};
    data.items.forEach((item) => {
      const risk = (item.inventory_risk || 'UNKNOWN').toUpperCase();
      counts[risk] = (counts[risk] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({
      name: name.charAt(0) + name.slice(1).toLowerCase(),
      value,
    }));
  }, [data]);

  const columns: ColumnDef<InventoryItem>[] = [
    {
      key: 'sku',
      header: 'SKU Item',
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-semibold text-white">{row.sku}</span>
          <div className="text-[10px] text-slate-500 font-mono">Store: {row.store_id || row.store || '—'}</div>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      sortable: true,
      render: (row) => (
        <span className="text-[11px] text-slate-300 font-mono uppercase">{row.category_id || row.category || '—'}</span>
      ),
    },
    {
      key: 'inventory_risk',
      header: 'Risk Level',
      sortable: true,
      render: (row) => <StatusBadge type="risk" value={row.inventory_risk} />,
    },
    {
      key: 'priority',
      header: 'Priority',
      sortable: true,
      render: (row) => <StatusBadge type="priority" value={row.priority} />,
    },
    {
      key: 'simulated_current_inventory',
      header: 'Simulated Stock',
      sortable: true,
      align: 'right',
      render: (row) => (
        <div className="text-right">
          <span className="font-mono font-bold text-white">
            {formatNumber(row.simulated_current_inventory, 1)}
          </span>
          <div className="text-[10px] text-amber-400 font-mono">Simulated</div>
        </div>
      ),
    },
    {
      key: 'reorder_point',
      header: 'Reorder Point (ROP)',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono text-slate-300 font-medium">
          {formatNumber(row.reorder_point, 1)}
        </span>
      ),
    },
    {
      key: 'safety_stock',
      header: 'Safety Stock',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono text-slate-400">
          {formatNumber(row.safety_stock, 1)}
        </span>
      ),
    },
    {
      key: 'forecast_demand_28d',
      header: '28d Forecast',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono text-cyan-400 font-medium">
          {formatNumber(row.forecast_demand_28d, 1)}
        </span>
      ),
    },
    {
      key: 'days_of_supply',
      header: 'Days Supply',
      sortable: true,
      align: 'right',
      render: (row) => {
        const d =
          row.days_of_supply !== null && row.days_of_supply !== undefined
            ? row.days_of_supply
            : row.average_daily_demand && row.average_daily_demand > 0
            ? row.simulated_current_inventory / row.average_daily_demand
            : null;
        if (d === null) return <span className="text-slate-500 font-mono">—</span>;
        const isLow = d <= (row.lead_time_days || 7);
        return (
          <span className={`font-mono font-semibold ${isLow ? 'text-rose-400' : 'text-slate-300'}`}>
            {formatNumber(d, 1)}d
          </span>
        );
      },
    },
    {
      key: 'recommended_order_quantity',
      header: 'Recommended Order',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono font-bold text-emerald-400">
          {formatNumber(row.recommended_order_quantity, 1)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Inventory Optimization & Replenishment Matrix</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Module 4 buffer calculation based on historical test demand and lead-time variability
          </p>
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-850 border border-navy-800 text-xs font-medium text-slate-200 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Inventory Matrix</span>
        </button>
      </div>

      {/* Prominent Provenance Notice: STRICT REQUIREMENT */}
      <ProvenanceNotice
        source={data?.source || 'MODULE_4'}
        provenance="SIMULATED INVENTORY POSITIONS: Starting inventory is simulated (14-day stock assumption, 7-day lead time, 95% service level). Forecast source is historical Module 3 test predictions."
        note="Do not treat simulated current stock or recommended quantities as live physical warehouse count."
        variant="warning"
      />

      {/* KPIs Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="SKU-Store Positions"
          value={data?.available ? summary.totalItems : 'Unavailable'}
          subtitle="Monitored stocking nodes"
          icon={Boxes}
          loading={loading}
          badge={
            data?.available && summary.totalItems > 0
              ? { text: `${summary.totalItems} Nodes`, variant: 'positive' }
              : undefined
          }
        />
        <KPICard
          title="Low Buffer Risk"
          value={data?.available ? (summary.lowCount || summary.criticalCount) : 'Unavailable'}
          subtitle="Stock below target replenishment"
          icon={ShieldAlert}
          badge={
            data?.available
              ? {
                  text: (summary.lowCount || summary.criticalCount) > 0 ? `${summary.lowCount || summary.criticalCount} Low Stock` : 'Adequate',
                  variant: (summary.lowCount || summary.criticalCount) > 0 ? 'warning' : 'positive',
                }
              : undefined
          }
          loading={loading}
        />
        <KPICard
          title="Normal Stock Buffer"
          value={data?.available ? summary.normalCount : 'Unavailable'}
          subtitle="Stock within optimal safety bounds"
          icon={PackageCheck}
          badge={
            data?.available && summary.normalCount > 0
              ? {
                  text: `${summary.normalCount} Optimal`,
                  variant: 'positive',
                }
              : undefined
          }
          loading={loading}
        />
        <KPICard
          title="Recommended Replenishment"
          value={data?.available ? formatNumber(summary.totalReorderQty, 0) : 'Unavailable'}
          subtitle="Total recommended reorder units"
          icon={ShoppingCart}
          loading={loading}
        />
      </div>

      {/* Risk Chart Card */}
      {data?.available && (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <Boxes className="w-4 h-4 text-brand-cyan" />
              <span>Simulated Stockout Risk Profile</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Service Level: 95% (z = 1.645)
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Distribution of SKU-Store pairs across low, normal, and excess buffer coverage
          </p>
          <InventoryDonutChart data={donutData} />
        </div>
      )}

      {/* Inventory Matrix Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white tracking-tight">
            Inventory Risk & Replenishment Ledger
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {filteredItems.length} Records Shown
          </span>
        </div>

        <SearchFilterBar
          searchPlaceholder="Search by SKU, Category, or Store..."
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          totalCount={data?.items?.length || 0}
          filteredCount={filteredItems.length}
          filters={[
            {
              id: 'risk',
              label: 'Risk Level',
              value: riskFilter,
              options: [
                { label: 'All Risk Levels', value: 'ALL' },
                { label: 'Low Buffer (Stockout Risk)', value: 'LOW' },
                { label: 'Normal Buffer', value: 'NORMAL' },
                { label: 'Excess Inventory', value: 'EXCESS' },
                { label: 'Critical Risk', value: 'CRITICAL' },
                { label: 'High Risk', value: 'HIGH' },
              ],
              onChange: setRiskFilter,
            },
          ]}
        />

        {!data?.available ? (
          <EmptyState
            title="Module 4 Inventory Analysis Output Not Generated"
            description="The output file 'module4_inventory_optimization/outputs/inventory_risk_analysis.csv' has not been generated by the inventory optimizer pipeline. The control tower refuses to fabricate dummy inventory figures."
            sourceCode={data?.source || 'MODULE_4_OUTPUT_NOT_GENERATED'}
            onRetry={refetch}
          />
        ) : (
          <DataTable
            columns={columns}
            data={filteredItems}
            keyExtractor={(row) => `${row.sku}-${row.store_id || row.store || ''}`}
            emptyMessage="No inventory positions match current filters"
            pageSize={15}
          />
        )}
      </div>
    </div>
  );
};
