import React, { useState, useMemo } from 'react';
import {
  Truck,
  Clock,
  AlertCircle,
  Layers,
  ArrowUpDown,
  Search,
  Filter,
  RefreshCw,
  Eye,
  Calendar,
  Building,
  Box,
} from 'lucide-react';
import { KPICard } from '../components/common/KPICard';
import { DataTable, ColumnDef } from '../components/common/DataTable';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProvenanceNotice } from '../components/common/ProvenanceNotice';
import { EmptyState } from '../components/common/EmptyState';
import { SearchFilterBar } from '../components/common/SearchFilterBar';
import { DelayVarianceChart } from '../components/charts/DelayVarianceChart';
import { useShipments } from '../hooks/useShipments';
import { ShipmentEvent, GroupedShipment } from '../types/shipment';
import { formatDate, formatVariance } from '../utilities/formatters';

export const ShipmentsPage: React.FC = () => {
  const { active, kpis, grouped, loading, error, refetch } = useShipments(200);

  const [activeTab, setActiveTab] = useState<'grouped' | 'events'>('grouped');
  const [searchTerm, setSearchTerm] = useState('');
  const [delayFilter, setDelayFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [selectedShipment, setSelectedShipment] = useState<GroupedShipment | null>(null);

  // Grouped Shipments filtering
  const filteredGrouped = useMemo(() => {
    if (!grouped?.shipments) return [];
    return grouped.shipments.filter((shp) => {
      const latest = shp.latest_event;
      const matchDelay =
        delayFilter === 'ALL' ||
        (latest?.delay_status || '').toUpperCase() === delayFilter.toUpperCase();
      const matchRisk =
        riskFilter === 'ALL' ||
        (latest?.stockout_risk || '').toUpperCase() === riskFilter.toUpperCase();
      const matchSearch =
        !searchTerm ||
        shp.shipment_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        shp.order_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        shp.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        shp.carrier_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        shp.warehouse_id?.toLowerCase().includes(searchTerm.toLowerCase());
      return matchDelay && matchRisk && matchSearch;
    });
  }, [grouped, delayFilter, riskFilter, searchTerm]);

  // Raw Active Events filtering
  const filteredEvents = useMemo(() => {
    if (!active?.shipments) return [];
    return active.shipments.filter((evt) => {
      const matchDelay =
        delayFilter === 'ALL' ||
        (evt.delay_status || '').toUpperCase() === delayFilter.toUpperCase();
      const matchRisk =
        riskFilter === 'ALL' ||
        (evt.stockout_risk || '').toUpperCase() === riskFilter.toUpperCase();
      const matchSearch =
        !searchTerm ||
        evt.shipment_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        evt.order_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        evt.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        evt.carrier_id?.toLowerCase().includes(searchTerm.toLowerCase());
      return matchDelay && matchRisk && matchSearch;
    });
  }, [active, delayFilter, riskFilter, searchTerm]);

  // Delay chart distribution from real events
  const delayChartData = useMemo(() => {
    const list = active?.shipments || [];
    const counts: Record<string, number> = {
      ON_TIME: 0,
      MINOR_DELAY: 0,
      MODERATE_DELAY: 0,
      SEVERE_DELAY: 0,
    };
    list.forEach((e) => {
      const st = (e.delay_status || '').toUpperCase();
      if (counts[st] !== undefined) counts[st] += 1;
      else if (st === 'NO_DELAY') counts.ON_TIME += 1;
    });
    return [
      { status: 'ON_TIME', count: counts.ON_TIME },
      { status: 'MINOR_DELAY', count: counts.MINOR_DELAY },
      { status: 'MODERATE_DELAY', count: counts.MODERATE_DELAY },
      { status: 'SEVERE_DELAY', count: counts.SEVERE_DELAY },
    ];
  }, [active]);

  // Columns for Grouped Shipments
  const groupedColumns: ColumnDef<GroupedShipment>[] = [
    {
      key: 'shipment_id',
      header: 'Shipment ID',
      sortable: true,
      render: (row) => (
        <span className="font-semibold text-white">{row.shipment_id}</span>
      ),
    },
    {
      key: 'order_id',
      header: 'Order / SKU',
      sortable: true,
      render: (row) => (
        <div>
          <div className="text-slate-200">{row.order_id || '—'}</div>
          <div className="text-[10px] text-slate-500 font-mono">{row.sku}</div>
        </div>
      ),
    },
    {
      key: 'carrier_id',
      header: 'Carrier / Hub',
      render: (row) => (
        <div>
          <div className="text-slate-200">{row.carrier_id || '—'}</div>
          <div className="text-[10px] text-slate-500 font-mono">{row.warehouse_id}</div>
        </div>
      ),
    },
    {
      key: 'delay_status',
      header: 'Status',
      sortable: true,
      render: (row) => (
        <StatusBadge type="delay" value={row.latest_event?.delay_status || 'UNKNOWN'} />
      ),
    },
    {
      key: 'eta_variance',
      header: 'ETA Variance',
      sortable: true,
      render: (row) => {
        const v = formatVariance(row.latest_event?.eta_variance_hours);
        return (
          <span className={v.positive ? 'text-emerald-400' : 'text-rose-400 font-bold'}>
            {v.text}
          </span>
        );
      },
    },
    {
      key: 'stockout_risk',
      header: 'Stockout Risk',
      render: (row) => (
        <StatusBadge type="risk" value={row.latest_event?.stockout_risk} />
      ),
    },
    {
      key: 'event_count',
      header: 'Events',
      align: 'center',
      render: (row) => (
        <span className="px-2 py-0.5 rounded bg-navy-800 text-slate-300 font-mono text-[11px]">
          {row.event_count}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      align: 'right',
      render: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedShipment(row);
          }}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-navy-800 hover:bg-navy-700 text-brand-cyan hover:text-white transition-colors text-xs"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Timeline</span>
        </button>
      ),
    },
  ];

  // Columns for Active Raw Events
  const eventColumns: ColumnDef<ShipmentEvent>[] = [
    {
      key: 'id',
      header: 'Event ID',
      sortable: true,
      render: (row) => <span className="font-mono text-slate-400">#{row.id}</span>,
    },
    {
      key: 'shipment_id',
      header: 'Shipment',
      sortable: true,
      render: (row) => <span className="font-semibold text-white">{row.shipment_id}</span>,
    },
    {
      key: 'event_type',
      header: 'Event Type',
      sortable: true,
      render: (row) => (
        <span className="font-mono text-[11px] text-brand-cyan uppercase">
          {row.event_type || 'IN_TRANSIT'}
        </span>
      ),
    },
    {
      key: 'delay_status',
      header: 'Delay Classification',
      render: (row) => <StatusBadge type="delay" value={row.delay_status} />,
    },
    {
      key: 'eta_variance_hours',
      header: 'Variance',
      sortable: true,
      render: (row) => {
        const v = formatVariance(row.eta_variance_hours);
        return (
          <span className={v.positive ? 'text-emerald-400' : 'text-rose-400 font-bold'}>
            {v.text}
          </span>
        );
      },
    },
    {
      key: 'days_of_supply',
      header: 'Days Supply',
      render: (row) => (
        <span className="font-mono text-slate-300">
          {row.days_of_supply !== null && row.days_of_supply !== undefined
            ? `${row.days_of_supply.toFixed(1)}d`
            : '—'}
        </span>
      ),
    },
    {
      key: 'recorded_at',
      header: 'Recorded Time',
      sortable: true,
      render: (row) => (
        <span className="text-[11px] text-slate-400">{formatDate(row.recorded_at)}</span>
      ),
    },
  ];

  const isDataAvailable = active?.available || grouped?.available;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Shipment Telemetry & Route Visibility</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time Kafka ingestion and SQLite event log tracking
          </p>
        </div>

        <button
          onClick={refetch}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-850 border border-navy-800 text-xs font-medium text-slate-200 transition-colors shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Shipments</span>
        </button>
      </div>

      {/* Provenance Banner */}
      <ProvenanceNotice
        source={active?.source || 'MODULE_2_SQLITE'}
        provenance="Events consumed via Apache Kafka pipeline and persisted to SQLite shipment_events schema."
        note="Non-duplicate shipment records are evaluated for ETA variance, delay status, and replenishment buffer."
        variant={isDataAvailable ? 'info' : 'warning'}
      />

      {/* KPIs Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Shipments"
          value={
            kpis?.available && kpis.total_shipments !== undefined
              ? kpis.total_shipments
              : grouped?.available && grouped.count !== undefined
              ? grouped.count
              : 'Unavailable'
          }
          subtitle="Unique tracking identifiers"
          icon={Truck}
          loading={loading}
        />
        <KPICard
          title="Total Events Logged"
          value={
            kpis?.available && kpis.event_count !== undefined
              ? kpis.event_count
              : active?.available && active.count !== undefined
              ? active.count
              : 'Unavailable'
          }
          subtitle="Status updates received"
          icon={Layers}
          loading={loading}
        />
        <KPICard
          title="Delayed Events"
          value={
            kpis?.available && kpis.delayed_events !== undefined
              ? kpis.delayed_events
              : 'Unavailable'
          }
          subtitle="Variance > 0 hours"
          icon={Clock}
          badge={
            kpis?.available && typeof kpis.delayed_events === 'number'
              ? {
                  text: `${kpis.delayed_events} Delayed`,
                  variant: kpis.delayed_events > 0 ? 'warning' : 'positive',
                }
              : undefined
          }
          loading={loading}
        />
        <KPICard
          title="Avg ETA Variance"
          value={
            kpis?.available &&
            kpis?.average_eta_variance_hours !== null &&
            kpis?.average_eta_variance_hours !== undefined
              ? `${kpis.average_eta_variance_hours.toFixed(1)} hrs`
              : 'Unavailable'
          }
          subtitle="Planned vs Current ETA"
          icon={ArrowUpDown}
          loading={loading}
        />
      </div>

      {/* Delay Distribution Chart (if records exist) */}
      {isDataAvailable && (active?.count || 0) > 0 && (
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-white tracking-tight mb-3">
            Delay Severity Distribution
          </h3>
          <DelayVarianceChart data={delayChartData} />
        </div>
      )}

      {/* Tabs & Filters */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-navy-800 pb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('grouped')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'grouped'
                  ? 'bg-brand-blue text-white shadow-sm'
                  : 'bg-navy-900 text-slate-400 hover:text-white border border-navy-800'
              }`}
            >
              Grouped Shipments ({grouped?.count || 0})
            </button>
            <button
              onClick={() => setActiveTab('events')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'events'
                  ? 'bg-brand-blue text-white shadow-sm'
                  : 'bg-navy-900 text-slate-400 hover:text-white border border-navy-800'
              }`}
            >
              Active Event Stream ({active?.count || 0})
            </button>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <SearchFilterBar
          searchPlaceholder="Search shipment ID, SKU, order, carrier..."
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          totalCount={activeTab === 'grouped' ? grouped?.count || 0 : active?.count || 0}
          filteredCount={activeTab === 'grouped' ? filteredGrouped.length : filteredEvents.length}
          filters={[
            {
              id: 'delay',
              label: 'Delay',
              value: delayFilter,
              options: [
                { label: 'All Delay Statuses', value: 'ALL' },
                { label: 'On Time', value: 'ON_TIME' },
                { label: 'Minor Delay', value: 'MINOR_DELAY' },
                { label: 'Moderate Delay', value: 'MODERATE_DELAY' },
                { label: 'Severe Delay', value: 'SEVERE_DELAY' },
              ],
              onChange: setDelayFilter,
            },
            {
              id: 'risk',
              label: 'Stockout Risk',
              value: riskFilter,
              options: [
                { label: 'All Stockout Risks', value: 'ALL' },
                { label: 'Critical', value: 'CRITICAL' },
                { label: 'High', value: 'HIGH' },
                { label: 'Medium', value: 'MEDIUM' },
                { label: 'Low', value: 'LOW' },
              ],
              onChange: setRiskFilter,
            },
          ]}
        />

        {/* Data Table or Empty State */}
        {!isDataAvailable ? (
          <EmptyState
            title="Shipment Database Unreachable or Not Initialized"
            description="The shipment event database 'data/shipment_events.db' was not found or contains no records. In accordance with zero-fake-data requirements, dummy shipments will not be displayed."
            sourceCode={active?.source || 'SQLITE_NOT_FOUND'}
            onRetry={refetch}
          />
        ) : activeTab === 'grouped' ? (
          <DataTable
            columns={groupedColumns}
            data={filteredGrouped}
            keyExtractor={(row) => row.shipment_id}
            onRowClick={(row) => setSelectedShipment(row)}
            emptyMessage="No shipments match the current filters"
          />
        ) : (
          <DataTable
            columns={eventColumns}
            data={filteredEvents}
            keyExtractor={(row) => row.id}
            emptyMessage="No shipment events match the current filters"
          />
        )}
      </div>

      {/* Shipment Event Timeline Modal Drawer */}
      {selectedShipment && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-navy-900 border border-navy-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-navy-800 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Truck className="w-5 h-5 text-brand-cyan" />
                  <h3 className="text-base font-bold text-white font-mono">
                    {selectedShipment.shipment_id}
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  SKU: {selectedShipment.sku} • Order: {selectedShipment.order_id || 'N/A'} • Carrier: {selectedShipment.carrier_id}
                </p>
              </div>

              <button
                onClick={() => setSelectedShipment(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-navy-800"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Event Progression Log ({selectedShipment.events.length} Events)
              </h4>

              <div className="relative border-l-2 border-navy-800 ml-3 space-y-6">
                {selectedShipment.events.map((evt, idx) => (
                  <div key={evt.id || idx} className="relative pl-6">
                    <span className="absolute -left-[7px] top-1.5 w-3 h-3 rounded-full bg-brand-cyan border-2 border-navy-900" />
                    <div className="p-3 bg-navy-950 border border-navy-800 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white font-mono uppercase">
                          {evt.event_type || 'STATUS_UPDATE'}
                        </span>
                        <StatusBadge type="delay" value={evt.delay_status} />
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Timestamp: {formatDate(evt.event_timestamp || evt.recorded_at)}
                      </div>
                      <div className="flex items-center gap-4 text-[11px] pt-1">
                        <div>
                          Planned ETA: <span className="text-slate-300">{formatDate(evt.planned_eta)}</span>
                        </div>
                        <div>
                          Current ETA: <span className="text-slate-300">{formatDate(evt.current_eta)}</span>
                        </div>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Days of Supply: <span className="font-mono text-slate-200">{evt.days_of_supply ?? '—'}</span> | Stockout Risk:{' '}
                        <span className="font-mono text-slate-200">{evt.stockout_risk || '—'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 border-t border-navy-800 bg-navy-950/60 flex justify-end">
              <button
                onClick={() => setSelectedShipment(null)}
                className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-xs font-medium text-white transition-colors"
              >
                Close Timeline
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
