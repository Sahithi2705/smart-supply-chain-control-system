import React, { useState, useMemo } from 'react';
import {
  TrendingUp,
  BarChart2,
  Calendar,
  Layers,
  Search,
  Filter,
  RefreshCw,
  Cpu,
  Info,
} from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { DataTable, ColumnDef } from '../components/common/DataTable';
import { ProvenanceNotice } from '../components/common/ProvenanceNotice';
import { EmptyState } from '../components/common/EmptyState';
import { SearchFilterBar } from '../components/common/SearchFilterBar';
import { ForecastLineChart } from '../components/charts/ForecastLineChart';
import { useForecasts } from '../hooks/useForecasts';
import { ForecastRecord } from '../types/forecast';
import { formatDateShort, formatNumber } from '../utilities/formatters';

export const DemandForecastingPage: React.FC = () => {
  const {
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
    refetch,
  } = useForecasts(1000);

  const [searchTerm, setSearchTerm] = useState('');

  // Apply search term filter on top of SKU/store
  const displayedPredictions = useMemo(() => {
    if (!filteredPredictions) return [];
    if (!searchTerm) return filteredPredictions;
    return filteredPredictions.filter((p) =>
      p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.category_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.store_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sales_date.includes(searchTerm)
    );
  }, [filteredPredictions, searchTerm]);

  // Forecast KPIs computed from displayed predictions
  const metrics = useMemo(() => {
    if (displayedPredictions.length === 0) {
      return {
        totalRecords: 0,
        avgActual: 0,
        avgXgboost: 0,
        meanAbsError: 0,
      };
    }
    let sumActual = 0;
    let sumXgb = 0;
    let sumDiff = 0;
    let validCount = 0;

    displayedPredictions.forEach((p) => {
      if (p.actual !== null && p.xgboost_prediction !== null) {
        sumActual += p.actual;
        sumXgb += p.xgboost_prediction;
        sumDiff += Math.abs(p.actual - p.xgboost_prediction);
        validCount += 1;
      }
    });

    return {
      totalRecords: displayedPredictions.length,
      avgActual: validCount ? sumActual / validCount : 0,
      avgXgboost: validCount ? sumXgb / validCount : 0,
      meanAbsError: validCount ? sumDiff / validCount : 0,
    };
  }, [displayedPredictions]);

  const columns: ColumnDef<ForecastRecord>[] = [
    {
      key: 'sales_date',
      header: 'Evaluation Date',
      sortable: true,
      render: (row) => (
        <span className="font-mono text-slate-300">{formatDateShort(row.sales_date)}</span>
      ),
    },
    {
      key: 'sku',
      header: 'SKU Item ID',
      sortable: true,
      render: (row) => <span className="font-semibold text-white">{row.sku}</span>,
    },
    {
      key: 'store_id',
      header: 'Store / Channel',
      sortable: true,
      render: (row) => (
        <span className="font-mono text-[11px] text-slate-400">{row.store_id}</span>
      ),
    },
    {
      key: 'category_id',
      header: 'Category',
      sortable: true,
      render: (row) => (
        <span className="px-2 py-0.5 rounded bg-navy-800 text-brand-cyan text-[11px] font-mono">
          {row.category_id}
        </span>
      ),
    },
    {
      key: 'actual',
      header: 'Actual Sales',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono font-bold text-white">
          {formatNumber(row.actual, 1)}
        </span>
      ),
    },
    {
      key: 'xgboost_prediction',
      header: 'XGBoost Model',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono text-cyan-400 font-semibold">
          {formatNumber(row.xgboost_prediction, 2)}
        </span>
      ),
    },
    {
      key: 'seasonal_naive_prediction',
      header: 'Seasonal Naive',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono text-blue-400">
          {formatNumber(row.seasonal_naive_prediction, 2)}
        </span>
      ),
    },
    {
      key: 'moving_average_prediction',
      header: 'Moving Avg (7d)',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-mono text-amber-400">
          {formatNumber(row.moving_average_prediction, 2)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Demand Forecasting & Multi-Model Evaluation</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Module 3 machine learning benchmark against M5 historical sales test partitions
          </p>
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-850 border border-navy-800 text-xs font-medium text-slate-200 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Reload Predictions</span>
        </button>
      </div>

      {/* Prominent Provenance Notice: STRICT REQUIREMENT */}
      <ProvenanceNotice
        source={data?.source || 'MODULE_3_HISTORICAL_TEST_PREDICTIONS'}
        provenance="HISTORICAL TEST EVALUATION DATA: Model inferences were calculated on historical evaluation folds from M5 dataset. Never interpret these as future live forecasts."
        note={data?.note || 'These are historical test predictions, not future forecasts.'}
        variant="warning"
      />

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Test Records"
          value={data?.available ? metrics.totalRecords : 'Unavailable'}
          subtitle="Observed test intervals"
          provenance="PARQUET FOLD"
          icon={Layers}
          loading={loading}
        />
        <KPICard
          title="Mean Actual Demand"
          value={data?.available ? formatNumber(metrics.avgActual, 2) : 'Unavailable'}
          subtitle="Units / day per SKU"
          icon={TrendingUp}
          loading={loading}
        />
        <KPICard
          title="Mean XGBoost Inference"
          value={data?.available ? formatNumber(metrics.avgXgboost, 2) : 'Unavailable'}
          subtitle="Gradient boosted model"
          provenance="XGBOOST"
          icon={Cpu}
          loading={loading}
        />
        <KPICard
          title="Test Set MAE"
          value={data?.available ? formatNumber(metrics.meanAbsError, 2) : 'Unavailable'}
          subtitle="|Actual - XGBoost|"
          icon={BarChart2}
          loading={loading}
        />
      </div>

      {/* Actual vs Multi-Model Comparison Chart */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-cyan" />
              <span>Historical Sales vs Multi-Model Inferences</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparison across XGBoost, Seasonal Naive, and 7-day Moving Average models
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider">SKU:</span>
            <select
              value={selectedSku}
              onChange={(e) => setSelectedSku(e.target.value)}
              className="bg-navy-950 border border-navy-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-brand-blue"
            >
              <option value="ALL">All SKUs (Aggregated)</option>
              {skus.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            <span className="text-[11px] text-slate-400 uppercase tracking-wider ml-2">Store:</span>
            <select
              value={selectedStore}
              onChange={(e) => setSelectedStore(e.target.value)}
              className="bg-navy-950 border border-navy-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-brand-blue"
            >
              <option value="ALL">All Stores</option>
              {stores.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
        </div>

        {displayedPredictions.length > 0 ? (
          <ForecastLineChart data={displayedPredictions.slice(0, 80)} />
        ) : (
          <div className="py-12 text-center text-slate-500 text-xs">
            No predictions found matching selected SKU and Store criteria.
          </div>
        )}
      </div>

      {/* Detailed Forecast Predictions Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white tracking-tight">
            Prediction Observation Ledger
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {displayedPredictions.length} Rows Retrieved
          </span>
        </div>

        <SearchFilterBar
          searchPlaceholder="Filter by SKU, Category, Store or Date..."
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          totalCount={data?.predictions?.length || 0}
          filteredCount={displayedPredictions.length}
        />

        {!data?.available ? (
          <EmptyState
            title="Module 3 Prediction Output Missing"
            description="The expanded prediction parquet file 'module3_demand_forecasting/outputs/model_predictions_expanded.parquet' could not be located."
            sourceCode={data?.source || 'MODULE_3_OUTPUT_NOT_FOUND'}
            onRetry={refetch}
          />
        ) : (
          <DataTable
            columns={columns}
            data={displayedPredictions}
            keyExtractor={(row, idx) => `${row.sku}-${row.sales_date}-${idx}`}
            emptyMessage="No forecast records matching criteria"
            pageSize={15}
          />
        )}
      </div>
    </div>
  );
};
