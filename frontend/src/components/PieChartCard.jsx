import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { PieChart as PieIcon, ShieldCheck, AlertTriangle } from 'lucide-react';

const COLOR_MAP = {
  NORMAL: '#10b981',
  'REAL WEATHER EVENT': '#0284c7',
  SPIKE: '#f43f5e',
  'CALIBRATION DRIFT': '#f59e0b',
  'FROZEN VALUE': '#06b6d4',
  'COMM LOSS': '#a855f7',
  'NOISE BURST': '#ec4899'
};

const DEFAULT_COLORS = ['#10b981', '#0284c7', '#f43f5e', '#f59e0b', '#06b6d4', '#a855f7'];

export default function PieChartCard({ telemetry }) {
  const causeCounts = telemetry.reduce((acc, row) => {
    const cause = row.root_cause || 'normal';
    const label = cause.toUpperCase().replace(/_/g, ' ');
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});

  const total = telemetry.length || 1;

  const data = Object.keys(causeCounts).map((key) => ({
    name: key,
    value: causeCounts[key],
    percentage: ((causeCounts[key] / total) * 100).toFixed(1),
    color: COLOR_MAP[key] || DEFAULT_COLORS[0]
  }));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between h-full">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <PieIcon className="w-5 h-5 text-sky-400" />
            Disambiguation & Root Cause Distribution
          </h2>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Breakdown of Normal, Real Meteorological Events, and Sensor Faults
        </p>
      </div>

      {/* Main Content: Donut Chart + Side Legend */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center flex-1">
        {/* Donut Chart */}
        <div className="md:col-span-5 h-48 relative flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                paddingAngle={3}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '12px' }}
                itemStyle={{ color: '#f8fafc' }}
                formatter={(value, name) => [`${value} rows (${((value / total) * 100).toFixed(1)}%)`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Donut Center Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-lg font-bold text-white leading-none">{total.toLocaleString()}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 uppercase tracking-wider">Total Rows</span>
          </div>
        </div>

        {/* Custom Clean Legend List with Progress Bars */}
        <div className="md:col-span-7 space-y-2 max-h-52 overflow-y-auto pr-1">
          {data.map((item, idx) => (
            <div key={idx} className="p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="font-semibold text-slate-200">{item.name}</span>
                </div>
                <span className="font-mono text-slate-400 font-medium">
                  {item.value} <span className="text-slate-500 text-[11px]">({item.percentage}%)</span>
                </span>
              </div>
              <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
