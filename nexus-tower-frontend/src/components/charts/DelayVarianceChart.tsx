import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';

interface DelayVarianceChartProps {
  data: { status: string; count: number }[];
  height?: number;
}

const DELAY_COLORS: Record<string, string> = {
  ON_TIME: '#10B981',
  MINOR_DELAY: '#3B82F6',
  MODERATE_DELAY: '#F59E0B',
  SEVERE_DELAY: '#EF4444',
};

export const DelayVarianceChart: React.FC<DelayVarianceChartProps> = ({
  data,
  height = 240,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
        No shipment delay data available
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
          <XAxis
            dataKey="status"
            stroke="#64748B"
            tick={{ fill: '#94A3B8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={{ stroke: '#334155' }}
          />
          <YAxis
            stroke="#64748B"
            tick={{ fill: '#94A3B8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={{ stroke: '#334155' }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              borderColor: '#1E293B',
              borderRadius: '0.5rem',
              fontSize: '12px',
              color: '#F1F5F9',
            }}
            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
          />
          <Bar dataKey="count" name="Shipments" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={DELAY_COLORS[entry.status.toUpperCase()] || '#3B82F6'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
