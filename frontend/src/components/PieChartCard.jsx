import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { PieChart as PieIcon } from 'lucide-react';

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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between h-full overflow-hidden">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-sky-400" />
            Disambiguation & Root Cause Distribution
          </h2>
        </div>
        <p className="text-[11px] text-slate-400 mb-3">
          Breakdown of Normal, Real Meteorological Events, and Sensor Faults
        </p>
      </div>

      {/* Main Content: Donut Chart + Side Legend */}
      <div className="flex flex-col sm:flex-row items-center gap-3 flex-1 overflow-hidden">
        {/* Donut Chart with Compact Radius */}
        <div className="w-full sm:w-2/5 h-40 relative flex items-center justify-center min-w-[140px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={38}
                outerRadius={58}
                paddingAngle={3}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '11px', padding: '6px 10px' }}
                itemStyle={{ color: '#f8fafc' }}
                formatter={(value, name) => [`${value} rows (${((value / total) * 100).toFixed(1)}%)`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Donut Center Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-base font-bold text-white leading-none">{total.toLocaleString()}</span>
            <span className="text-[9px] text-slate-400 mt-0.5 uppercase tracking-wider">Total</span>
          </div>
        </div>

        {/* Custom Clean Legend List with Progress Bars */}
        <div className="w-full sm:w-3/5 space-y-1.5 max-h-48 overflow-y-auto pr-1">
          {data.map((item, idx) => (
            <div key={idx} className="p-1.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-[11px]">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-1.5 truncate">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="font-medium text-slate-200 truncate">{item.name}</span>
                </div>
                <span className="font-mono text-slate-400 font-medium shrink-0 ml-1">
                  {item.value} <span className="text-slate-500 text-[10px]">({item.percentage}%)</span>
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
