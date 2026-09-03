import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { PieChart as PieIcon } from 'lucide-react';

const COLORS = ['#10b981', '#f43f5e', '#0284c7', '#f59e0b', '#06b6d4', '#a855f7'];

export default function PieChartCard({ telemetry }) {
  // Aggregate root causes
  const causeCounts = telemetry.reduce((acc, row) => {
    const cause = row.root_cause || 'normal';
    acc[cause] = (acc[cause] || 0) + 1;
    return acc;
  }, {});

  const data = Object.keys(causeCounts).map((key) => ({
    name: key.toUpperCase().replace('_', ' '),
    value: causeCounts[key]
  }));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <PieIcon className="w-5 h-5 text-sky-400" />
          Sensor Faults vs Weather Disambiguation
        </h2>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Distribution of Normal, Severe Weather Events, and Sensor Fault Types
      </p>

      <div className="h-64 w-full flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="#0f172a" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '12px' }}
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
