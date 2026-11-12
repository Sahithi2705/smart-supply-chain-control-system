import React from 'react';
import {
  Truck,
  AlertTriangle,
  Boxes,
  ShieldAlert,
  Server,
  RefreshCw,
  Clock,
  Layers,
} from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { ProvenanceNotice } from '../components/common/ProvenanceNotice';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';
import { InventoryDonutChart } from '../components/charts/InventoryDonutChart';
import { RiskDistributionBar } from '../components/charts/RiskDistributionBar';
import { useOverview } from '../hooks/useOverview';
import { formatDate } from '../utilities/formatters';

export const OverviewPage: React.FC = () => {
  const {
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
    refetch,
  } = useOverview('28D');

  return (
    <div className="space-y-6">
      {/* Header Banner & Data Provenance */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight text-white">
              Control Tower Telemetry
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-navy-850 text-brand-cyan border border-brand-cyan/20">
              RANGE: 28D
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time multi-cloud operational health and active supply chain signals
          </p>
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-850 border border-navy-800 text-xs font-medium text-slate-200 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Global Data Provenance Notice */}
      <ProvenanceNotice
        source={overview?.data_provenance || 'PROJECT_DATA'}
        provenance="Backend integration adheres to zero synthetic mock policy. Data availability mirrors underlying pipeline execution states."
        note={overview?.note || 'Unavailable source files are reported accurately and never replaced with demo metrics.'}
        variant="neutral"
      />

      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Shipments"
          value={metrics.totalShipments}
          subtitle={
            kpis?.event_count
              ? `${kpis.event_count} lifecycle events recorded`
              : 'Tracked logistics units'
          }
          provenance="MODULE 2"
          icon={Truck}
          loading={loading}
          badge={
            typeof metrics.totalShipments === 'number'
              ? { text: `${metrics.totalShipments} Shipments`, variant: 'positive' }
              : undefined
          }
        />
        <KPICard
          title="Delayed Shipments"
          value={metrics.delayedShipments}
          subtitle="ETA variance > 0.0 hrs"
          provenance="MODULE 2"
          icon={Clock}
          loading={loading}
          badge={
            typeof metrics.delayedShipments === 'number'
              ? {
                  text: `${metrics.delayedShipments} Delayed`,
                  variant: metrics.delayedShipments > 0 ? 'warning' : 'positive',
                }
              : undefined
          }
        />
        <KPICard
          title="Critical Risk Incidents"
          value={metrics.criticalIncidents}
          subtitle="Severity score ≥ 75"
          provenance="MODULE 5"
          icon={ShieldAlert}
          loading={loading}
          badge={
            typeof metrics.criticalIncidents === 'number'
              ? {
                  text: `${metrics.criticalIncidents} Critical of ${metrics.totalIncidents} Incidents`,
                  variant: metrics.criticalIncidents > 0 ? 'negative' : 'positive',
                }
              : undefined
          }
        />
        <KPICard
          title="Inventory SKUs Tracked"
          value={metrics.inventoryCount}
          subtitle={
            typeof metrics.inventoryCount === 'number'
              ? `${metrics.inventoryCount} SKU-Store allocations`
              : 'Simulated stock positions'
          }
          provenance="MODULE 4"
          icon={Boxes}
          loading={loading}
          badge={
            moduleStatus.module4
              ? { text: 'Active Matrix', variant: 'positive' }
              : undefined
          }
        />
      </div>

      {/* System Health & Module Availability Status Grid */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-brand-cyan" />
            <h3 className="text-sm font-semibold text-white tracking-tight">
              Module Pipeline Execution Matrix
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Source: <span className="text-slate-200">GET /health</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Module 2 */}
          <div className="p-3.5 rounded-lg bg-navy-950 border border-navy-800 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-200">Module 2</div>
              <div className="text-[11px] text-slate-400">Real-Time Visibility (Kafka/SQLite)</div>
            </div>
            {moduleStatus.module2 ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ACTIVE
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
                SQLITE_NOT_FOUND
              </span>
            )}
          </div>

          {/* Module 3 */}
          <div className="p-3.5 rounded-lg bg-navy-950 border border-navy-800 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-200">Module 3</div>
              <div className="text-[11px] text-slate-400">Demand Forecasting (Parquet)</div>
            </div>
            {moduleStatus.module3 ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                READY (M5 TEST)
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                NOT_FOUND
              </span>
            )}
          </div>

          {/* Module 4 */}
          <div className="p-3.5 rounded-lg bg-navy-950 border border-navy-800 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-200">Module 4</div>
              <div className="text-[11px] text-slate-400">Inventory Optimization (CSV)</div>
            </div>
            {moduleStatus.module4 ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                READY
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
                NOT_GENERATED
              </span>
            )}
          </div>

          {/* Module 5 */}
          <div className="p-3.5 rounded-lg bg-navy-950 border border-navy-800 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-200">Module 5</div>
              <div className="text-[11px] text-slate-400">Risk Intelligence (Incidents)</div>
            </div>
            {moduleStatus.module5 ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                READY
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
                NOT_GENERATED
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Middle Grid: Charts & Analytics Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inventory Risk Distribution */}
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <Boxes className="w-4 h-4 text-brand-cyan" />
              <span>Inventory Risk Classification</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-400">MODULE 4</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Safety stock coverage across SKU-Store allocations (Simulated Inventory)
          </p>

          {inventory.length > 0 ? (
            <InventoryDonutChart data={inventoryDist} />
          ) : (
            <EmptyState
              title="Inventory Matrix Not Generated"
              description="Module 4 inventory analysis output is currently awaiting execution or input parameters. Real-time simulated stock positions will appear once generated."
              sourceCode="MODULE_4_OUTPUT_NOT_GENERATED"
            />
          )}
        </div>

        {/* Risk Incidents Breakdown */}
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Risk Incident Severity Distribution</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-400">MODULE 5</span>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Disruption severity scores derived from delay and stockout telemetry
          </p>

          {alerts.length > 0 ? (
            <RiskDistributionBar data={riskDist} />
          ) : (
            <EmptyState
              title="No Risk Incidents Emitted"
              description="Module 5 risk intelligence engine currently has 0 active incident records generated from the pipeline."
              sourceCode="MODULE_5_OUTPUT_NOT_GENERATED"
            />
          )}
        </div>
      </div>

      {/* Bottom Section: Recent Alerts Stream */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <h3 className="text-sm font-semibold text-white tracking-tight">
              Active Control Tower Alert Stream
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {alerts.length} Incidents Logged
          </span>
        </div>

        {alerts.length === 0 ? (
          <EmptyState
            title="Alert Stream Idle"
            description="No active disruptions or high-risk incidents detected by Module 5 risk engine."
            sourceCode="MODULE_5_ALERTS_EMPTY"
          />
        ) : (
          <div className="space-y-2.5">
            {alerts.slice(0, 5).map((alert, idx) => (
              <div
                key={alert.incident_id || alert.id || idx}
                className="p-3 bg-navy-950 border border-navy-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-3">
                  <StatusBadge type="risk" value={alert.risk_level} />
                  <div>
                    <div className="font-semibold text-white font-mono flex items-center gap-2">
                      {alert.incident_id && (
                        <span className="text-brand-cyan">{alert.incident_id}</span>
                      )}
                      <span>Shipment: {alert.shipment_id}</span>
                    </div>
                    <div className="text-slate-400 text-[11px] mt-0.5">
                      SKU: {alert.sku || 'N/A'} • Carrier: {alert.carrier_id || 'N/A'} • Hub: {alert.warehouse_id || 'N/A'}
                    </div>
                    {alert.risk_reason && (
                      <div className="text-amber-400/90 text-[11px] mt-0.5 font-mono">
                        Reason: {alert.risk_reason}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4 text-[11px] font-mono">
                  <div>
                    <span className="text-slate-500">Risk Score: </span>
                    <span className="text-white font-bold">{alert.risk_score}/100</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Status: </span>
                    <span className="text-slate-300 uppercase">{alert.incident_status || 'OPEN'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
