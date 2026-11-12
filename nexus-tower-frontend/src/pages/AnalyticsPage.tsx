import React from 'react';
import {
  BarChart3,
  Layers,
  Database,
  Cpu,
  Boxes,
  ShieldAlert,
  Server,
  RefreshCw,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { ProvenanceNotice } from '../components/common/ProvenanceNotice';
import { EmptyState } from '../components/common/EmptyState';
import { RiskDistributionBar } from '../components/charts/RiskDistributionBar';
import { InventoryDonutChart } from '../components/charts/InventoryDonutChart';
import { useAnalytics } from '../hooks/useAnalytics';

export const AnalyticsPage: React.FC = () => {
  const { data, health, loading, error, refetch } = useAnalytics();

  // Parse module 4 summary if available: [{ inventory_risk: string, sku_store_count?: number, sku_store_pairs?: number }]
  const inventorySummaryChart = React.useMemo(() => {
    if (!data?.module4_summary) return [];
    return data.module4_summary.map((row) => ({
      name: row.inventory_risk,
      value: row.sku_store_count ?? row.sku_store_pairs ?? 0,
    }));
  }, [data]);

  // Parse module 5 summary if available: [{ risk_level: string, event_count: number }]
  const riskSummaryChart = React.useMemo(() => {
    if (!data?.module5_summary) return [];
    return data.module5_summary.map((row) => ({
      level: row.risk_level,
      count: row.event_count,
    }));
  }, [data]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Control Tower Cross-Module Analytics</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Integrated metrics across Data Ingestion, Streaming, Forecasting, Inventory & Risk Engines
          </p>
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-850 border border-navy-800 text-xs font-medium text-slate-200 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Analytics</span>
        </button>
      </div>

      {/* Provenance Notice */}
      <ProvenanceNotice
        source="UNIFIED_ANALYTICS_SERVICE"
        provenance="Aggregated directly from FastAPI backend endpoint GET /api/v1/analytics/summary. Zero synthetic metrics policy enforced."
        note="When source databases or intermediate CSV outputs are absent, metrics report null rather than simulated placeholders."
        variant="neutral"
      />

      {/* KPI Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Module 2 Events"
          value={data?.module2_events !== null && data?.module2_events !== undefined ? data.module2_events : 'Unavailable'}
          subtitle="Total SQLite shipment events"
          provenance="MODULE 2"
          icon={Database}
          loading={loading}
          badge={{
            text: data?.module2_events ? `${data.module2_events} Events` : 'Uninitialized',
            variant: data?.module2_events ? 'positive' : 'neutral',
          }}
        />
        <KPICard
          title="Module 3 Model Predictions"
          value={data?.module3_predictions_available ? 'Available' : 'Missing'}
          subtitle="M5 historical test inferences"
          provenance="MODULE 3"
          icon={Cpu}
          loading={loading}
          badge={{
            text: data?.module3_predictions_available ? 'Parquet Active' : 'Not Found',
            variant: data?.module3_predictions_available ? 'positive' : 'negative',
          }}
        />
        <KPICard
          title="Module 4 Inventory Summary"
          value={data?.module4_summary ? `${data.module4_summary.length} Risk Tiers` : 'Not Generated'}
          subtitle="Inventory optimization output"
          provenance="MODULE 4"
          icon={Boxes}
          loading={loading}
          badge={{
            text: data?.module4_summary ? 'CSV Present' : 'Pending',
            variant: data?.module4_summary ? 'positive' : 'neutral',
          }}
        />
        <KPICard
          title="Module 5 Risk Summary"
          value={data?.module5_summary ? `${data.module5_summary.length} Risk Levels` : 'Not Generated'}
          subtitle="Disruption assessment summary"
          provenance="MODULE 5"
          icon={ShieldAlert}
          loading={loading}
          badge={{
            text: data?.module5_summary ? 'CSV Present' : 'Pending',
            variant: data?.module5_summary ? 'positive' : 'neutral',
          }}
        />
      </div>

      {/* Pipeline Status Matrix */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
            <Server className="w-4 h-4 text-brand-cyan" />
            <span>Architecture & Data Lake Pipeline Health</span>
          </h3>
          <span className="text-[11px] font-mono text-slate-400">
            Status: {health?.status?.toUpperCase() || 'CONNECTING'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Module 1 & 2 */}
          <div className="p-4 bg-navy-950 border border-navy-800 rounded-lg space-y-3">
            <div className="flex items-center justify-between border-b border-navy-800 pb-2">
              <span className="text-xs font-semibold text-slate-200">
                1. Ingestion & 2. Real-Time Kafka Streaming
              </span>
              {health?.sources?.module2_sqlite ? (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ONLINE</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>SQLITE_NOT_FOUND</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Consumes Kafka shipment topic partitions into SQLite database. When producer and consumer run, events are scored for ETA variance and stockout exposure.
            </p>
          </div>

          {/* Module 3 */}
          <div className="p-4 bg-navy-950 border border-navy-800 rounded-lg space-y-3">
            <div className="flex items-center justify-between border-b border-navy-800 pb-2">
              <span className="text-xs font-semibold text-slate-200">
                3. Demand Forecasting (ML / SageMaker)
              </span>
              {health?.sources?.module3_predictions ? (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>PARQUET_VERIFIED</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] text-rose-400 font-mono">
                  <XCircle className="w-3.5 h-3.5" />
                  <span>UNAVAILABLE</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Trains XGBoost, Seasonal Naive and Moving Average estimators on M5 historical partitions. Provides recursive multi-step historical predictions for inventory replenishment.
            </p>
          </div>

          {/* Module 4 */}
          <div className="p-4 bg-navy-950 border border-navy-800 rounded-lg space-y-3">
            <div className="flex items-center justify-between border-b border-navy-800 pb-2">
              <span className="text-xs font-semibold text-slate-200">
                4. Inventory Optimization & Replenishment
              </span>
              {health?.sources?.module4_outputs ? (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>OUTPUT_GENERATED</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>OUTPUT_NOT_GENERATED</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Calculates safety stock, reorder point (ROP), simulated current stock, and recommended reorder quantities using normal distribution z-quantiles (95% service level).
            </p>
          </div>

          {/* Module 5 */}
          <div className="p-4 bg-navy-950 border border-navy-800 rounded-lg space-y-3">
            <div className="flex items-center justify-between border-b border-navy-800 pb-2">
              <span className="text-xs font-semibold text-slate-200">
                5. Risk Intelligence & Disruption Scoring
              </span>
              {health?.sources?.module5_outputs ? (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>OUTPUT_GENERATED</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>OUTPUT_NOT_GENERATED</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Executes composite risk scoring (0-100) combining transit delay status and inventory vulnerability. Emits incidents for all records reaching HIGH or CRITICAL score thresholds.
            </p>
          </div>
        </div>
      </div>

      {/* Module Summaries Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Module 4 Summary Visual */}
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-white tracking-tight mb-2">
            Module 4: Inventory Risk Summary
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Aggregated SKU-Store pairs per risk category from inventory_summary.csv
          </p>
          {data?.module4_summary && data.module4_summary.length > 0 ? (
            <InventoryDonutChart data={inventorySummaryChart} />
          ) : (
            <EmptyState
              title="Inventory Summary Not Generated"
              description="Backend endpoint GET /api/v1/analytics/summary reports module4_summary as null because 'module4_inventory_optimization/outputs/inventory_summary.csv' does not exist."
              sourceCode="MODULE_4_SUMMARY_NULL"
            />
          )}
        </div>

        {/* Module 5 Summary Visual */}
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-white tracking-tight mb-2">
            Module 5: Risk Level Summary
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Incident event counts grouped by risk classification from risk_summary.csv
          </p>
          {data?.module5_summary && data.module5_summary.length > 0 ? (
            <RiskDistributionBar data={riskSummaryChart} />
          ) : (
            <EmptyState
              title="Risk Summary Not Generated"
              description="Backend endpoint GET /api/v1/analytics/summary reports module5_summary as null because 'module5_risk_intelligence/outputs/risk_summary.csv' does not exist."
              sourceCode="MODULE_5_SUMMARY_NULL"
            />
          )}
        </div>
      </div>
    </div>
  );
};
