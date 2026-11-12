import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';

interface InventoryDonutChartProps {
  data: { name: string; value: number }[];
  height?: number;
}

const COLORS: Record<string, string> = {
  CRITICAL: '#EF4444',
  HIGH: '#F59E0B',
  MEDIUM: '#0EA5E9',
  LOW: '#10B981',
  NORMAL: '#0D9488',
  EXCESS: '#8B5CF6',
};

export const InventoryDonutChart: React.FC<InventoryDonutChartProps> = ({
  data,
  height = 240,
}) => {
  const filtered = data.filter((d) => d.value > 0);

  if (filtered.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
        No inventory distribution data available
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={filtered}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={3}
            dataKey="value"
          >
            {filtered.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.name.toUpperCase()] || '#64748B'}
                stroke="#111827"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              borderColor: '#1E293B',
              borderRadius: '0.5rem',
              fontSize: '12px',
              color: '#F1F5F9',
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
