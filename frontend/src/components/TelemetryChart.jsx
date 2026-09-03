import React from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ReferenceDot
} from 'recharts';
import { LineChart as LineIcon, Cpu } from 'lucide-react';

export default function TelemetryChart({ telemetryData, selectedStation }) {
  const chartData = telemetryData.map((row) => ({
    time: new Date(row.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    fullTime: row.timestamp,
    rawTemp: row.temperature_C,
    correctedTemp: row.corrected_temp_C,
    isAnomaly: row.is_anomaly_pred,
    rootCause: row.root_cause,
    explanation: row.explanation
  }));

  const anomalyPoints = chartData.filter((d) => d.isAnomaly);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <LineIcon className="w-5 h-5 text-sky-400" />
            Telemetry & Self-Healing Auto-Correction Overlay
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Station: <strong className="text-sky-400">{selectedStation}</strong> — Raw sensor readings vs spatially imputed corrected values
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-slate-400"></span>
            <span className="text-slate-300">Raw Sensor Telemetry</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-emerald-400"></span>
            <span className="text-emerald-400 font-medium">Self-Healing Imputed</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            <span className="text-rose-400">Flagged Sensor Anomaly</span>
          </div>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} unit="°C" />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem' }}
              labelStyle={{ color: '#94a3b8', fontSize: '12px' }}
              itemStyle={{ fontSize: '12px' }}
            />
            <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />

            {/* Raw Telemetry Line */}
            <Line
              type="monotone"
              dataKey="rawTemp"
              name="Raw Telemetry (°C)"
              stroke="#94a3b8"
              strokeWidth={1.5}
              dot={false}
            />

            {/* Auto-Corrected Line */}
            <Line
              type="monotone"
              dataKey="correctedTemp"
              name="Self-Healing Imputed (°C)"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />

            {/* Anomaly Dots */}
            {anomalyPoints.map((pt, idx) => (
              <ReferenceDot
                key={idx}
                x={pt.time}
                y={pt.rawTemp}
                r={5}
                fill="#f43f5e"
                stroke="#fff"
                strokeWidth={1.5}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
