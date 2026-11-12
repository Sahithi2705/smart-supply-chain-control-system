import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { ForecastRecord } from '../../types/forecast';
import { formatDateShort } from '../../utilities/formatters';

interface ForecastLineChartProps {
  data: ForecastRecord[];
  height?: number;
}

export const ForecastLineChart: React.FC<ForecastLineChartProps> = ({
  data,
  height = 360,
}) => {
  // Sort and aggregate points by date if needed
  const chartData = React.useMemo(() => {
    return [...data]
      .sort((a, b) => new Date(a.sales_date).getTime() - new Date(b.sales_date).getTime())
      .map((item) => ({
        date: formatDateShort(item.sales_date),
        rawDate: item.sales_date,
        actual: item.actual,
        xgboost: item.xgboost_prediction !== null ? Number(item.xgboost_prediction.toFixed(2)) : null,
        seasonalNaive: item.seasonal_naive_prediction !== null ? Number(item.seasonal_naive_prediction.toFixed(2)) : null,
        movingAvg: item.moving_average_prediction !== null ? Number(item.moving_average_prediction.toFixed(2)) : null,
      }));
  }, [data]);

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-xs">
        No forecast data points available for chart rendering
      </div>
    );
  }

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
          <XAxis
            dataKey="date"
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
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              borderColor: '#1E293B',
              borderRadius: '0.5rem',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)',
              fontSize: '12px',
              color: '#F1F5F9',
            }}
            labelStyle={{ color: '#06B6D4', fontWeight: 600, marginBottom: '4px' }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '10px', fontSize: '11px', color: '#94A3B8' }}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Sales"
            stroke="#F8FAFC"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#F8FAFC' }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="xgboost"
            name="XGBoost Prediction"
            stroke="#06B6D4"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="seasonalNaive"
            name="Seasonal Naive"
            stroke="#3B82F6"
            strokeWidth={1.5}
            strokeDasharray="2 2"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="movingAvg"
            name="Moving Average (7d)"
            stroke="#F59E0B"
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
