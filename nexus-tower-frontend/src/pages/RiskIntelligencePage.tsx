import React from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  Activity,
  Flame,
  Search,
  Filter,
  RefreshCw,
  Compass,
  CheckCircle,
  Clock,
  Zap,
} from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { DataTable, ColumnDef } from '../components/common/DataTable';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceNotice } from '../components/common/ProvenanceNotice';
import { EmptyState } from '../components/common/EmptyState';
import { SearchFilterBar } from '../components/common/SearchFilterBar';
import { RiskDistributionBar } from '../components/charts/RiskDistributionBar';
import { useRiskAlerts } from '../hooks/useRiskAlerts';
import { RiskIncident } from '../types/risk';
import { formatDate, formatVariance } from '../utilities/formatters';

export const RiskIntelligencePage: React.FC = () => {
  const {
    data,
    filteredAlerts,
    stats,
    severityFilter,
    setSeverityFilter,
    searchTerm,
    setSearchTerm,
    loading,
    error,
    refetch,
  } = useRiskAlerts();

  const barChartData = React.useMemo(() => [
    { level: 'CRITICAL', count: stats.critical },
    { level: 'HIGH', count: stats.high },
    { level: 'MEDIUM', count: stats.medium },
    { level: 'LOW', count: stats.low },
  ], [stats]);

  // Derive recommended action based on incident profile
  const getActionRecommendation = (alert: RiskIncident): string => {
    if (alert.recommended_action) return alert.recommended_action;
    const score = alert.risk_score || 0;
    const delay = (alert.delay_status || '').toUpperCase();
    const stock = (alert.stockout_risk || '').toUpperCase();

    if (score >= 75 || delay === 'SEVERE_DELAY' || stock === 'CRITICAL') {
      return 'Initiate priority carrier reroute; notify destination warehouse of delayed cross-dock';
    }
    if (score >= 50 || delay === 'MODERATE_DELAY' || stock === 'HIGH') {
      return 'Expedite replenishment purchase order; audit upstream supplier buffer';
    }
    return 'Maintain standard monitoring; check next Kafka tracking heartbeat';
  };

  const columns: ColumnDef<RiskIncident>[] = [
    {
      key: 'shipment_id',
      header: 'Incident / Shipment ID',
      sortable: true,
      render: (row) => (
        <div>
          <div className="font-semibold text-white font-mono flex items-center gap-1.5">
            {row.incident_id && <span className="text-brand-cyan">{row.incident_id}</span>}
            <span>{row.shipment_id}</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            SKU: {row.sku || 'N/A'} • Carrier: {row.carrier_id || 'N/A'}
          </div>
          {row.risk_reason && (
            <div className="text-[11px] text-amber-400 font-mono mt-0.5">
              Reason: {row.risk_reason}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'risk_level',
      header: 'Risk Level',
      sortable: true,
      render: (row) => <StatusBadge type="risk" value={row.risk_level} />,
    },
    {
      key: 'risk_score',
      header: 'Risk Score',
      sortable: true,
      align: 'center',
      render: (row) => {
        const score = row.risk_score ?? 0;
        let color = 'text-emerald-400';
        if (score >= 75) color = 'text-rose-400 font-bold';
        else if (score >= 50) color = 'text-amber-400 font-bold';
        else if (score >= 25) color = 'text-sky-400';

        return (
          <div className="inline-flex items-center gap-1 font-mono">
            <span className={`text-sm ${color}`}>{score}</span>
            <span className="text-[10px] text-slate-500">/100</span>
          </div>
        );
      },
    },
    {
      key: 'delay_status',
      header: 'Delay Factor',
      sortable: true,
      render: (row) => (
        <div>
          <StatusBadge type="delay" value={row.delay_status} />
          {row.eta_variance_hours !== null && row.eta_variance_hours !== undefined && (
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">
              Variance: {formatVariance(row.eta_variance_hours).text}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'stockout_risk',
      header: 'Stockout Exposure',
      render: (row) => (
        <div>
          <span className="font-mono text-[11px] text-slate-200 uppercase">
            {row.stockout_risk || 'LOW'}
          </span>
          <div className="text-[10px] text-slate-500 font-mono">
            Supply: {row.days_of_supply !== null && row.days_of_supply !== undefined ? `${row.days_of_supply.toFixed(1)}d` : '—'}
          </div>
        </div>
      ),
    },
    {
      key: 'recommended_action',
      header: 'Recommended Remediation',
      render: (row) => (
        <span className="text-xs text-slate-300 leading-snug line-clamp-2 max-w-xs font-sans">
          {getActionRecommendation(row)}
        </span>
      ),
    },
    {
      key: 'recorded_at',
      header: 'Detected Time',
      sortable: true,
      render: (row) => (
        <span className="text-[11px] text-slate-400 font-mono">
          {formatDate(row.recorded_at)}
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
            <span>Risk Intelligence & Disruption Assessment</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Module 5 rule-based and composite risk scoring engine across supply chain nodes
          </p>
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-850 border border-navy-800 text-xs font-medium text-slate-200 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Incidents</span>
        </button>
      </div>

      {/* Provenance Notice */}
      <ProvenanceNotice
        source={data?.source || 'MODULE_5_RISK_ENGINE'}
        provenance="Composite scoring combines delay thresholds, days-of-supply exposure, and stockout vulnerability (0–100 scale). Incidents emitted for score ≥ 50."
        note="Excludes duplicate shipment signals. Missing source files are reported accurately without synthetic mocks."
        variant={data?.available ? 'info' : 'neutral'}
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Active Risk Incidents"
          value={data?.available ? stats.total : 'Unavailable'}
          subtitle="Emitted high/critical events"
          icon={AlertTriangle}
          loading={loading}
        />
        <KPICard
          title="Critical Severity"
          value={data?.available ? stats.critical : 'Unavailable'}
          subtitle="Score 75–100 (Immediate action)"
          icon={Flame}
          badge={
            data?.available
              ? {
                  text: stats.critical > 0 ? `${stats.critical} Critical` : '0 Critical',
                  variant: stats.critical > 0 ? 'negative' : 'positive',
                }
              : undefined
          }
          loading={loading}
        />
        <KPICard
          title="High Severity"
          value={data?.available ? stats.high : 'Unavailable'}
          subtitle="Score 50–74 (Investigation)"
          icon={ShieldAlert}
          badge={
            data?.available && stats.high > 0
              ? {
                  text: `${stats.high} Incidents`,
                  variant: 'warning',
                }
              : undefined
          }
          loading={loading}
        />
        <KPICard
          title="Mean Incident Score"
          value={data?.available && stats.total > 0 ? `${stats.avgScore} / 100` : 'Unavailable'}
          subtitle="Composite risk index"
          icon={Activity}
          loading={loading}
        />
      </div>

      {/* Risk Distribution Chart */}
      {data?.available && (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <Compass className="w-4 h-4 text-brand-cyan" />
              <span>Incident Severity Distribution</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Scoring Thresholds: Critical (≥75), High (≥50), Medium (≥25)
            </span>
          </div>
          <RiskDistributionBar data={barChartData} />
        </div>
      )}

      {/* Incident Stream Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white tracking-tight">
            Active Incident Stream & Mitigation Actions
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {filteredAlerts.length} Incidents Listed
          </span>
        </div>

        <SearchFilterBar
          searchPlaceholder="Search by shipment ID, SKU, carrier, or warehouse..."
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          totalCount={data?.alerts?.length || 0}
          filteredCount={filteredAlerts.length}
          filters={[
            {
              id: 'severity',
              label: 'Severity',
              value: severityFilter,
              options: [
                { label: 'All Severity Levels', value: 'ALL' },
                { label: 'Critical Only (≥75)', value: 'CRITICAL' },
                { label: 'High Only (50–74)', value: 'HIGH' },
                { label: 'Medium (25–49)', value: 'MEDIUM' },
                { label: 'Low (0–24)', value: 'LOW' },
              ],
              onChange: setSeverityFilter,
            },
          ]}
        />

        {!data?.available ? (
          <EmptyState
            title="Module 5 Risk Incidents Not Generated"
            description="The risk output file 'module5_risk_intelligence/outputs/risk_incidents.csv' has not been generated by the risk assessment engine. Real incidents will populate here when computed."
            sourceCode={data?.source || 'MODULE_5_OUTPUT_NOT_GENERATED'}
            onRetry={refetch}
          />
        ) : (
          <DataTable
            columns={columns}
            data={filteredAlerts}
            keyExtractor={(row) => row.incident_id || (typeof row.id === 'string' || typeof row.id === 'number' ? String(row.id) : row.shipment_id)}
            emptyMessage="No risk incidents match the current filter parameters"
            pageSize={15}
          />
        )}
      </div>
    </div>
  );
};
