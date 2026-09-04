import React from 'react';
import { Layers, ShieldAlert, Cpu } from 'lucide-react';

import { formatTimeString } from '../utils/formatters';

export default function ExplainabilityTable({ telemetryData, selectedStation, setSelectedStation }) {
  const [filterStation, setFilterStation] = React.useState(selectedStation || 'ALL');

  React.useEffect(() => {
    if (selectedStation) setFilterStation(selectedStation);
  }, [selectedStation]);

  const uniqueStations = Array.from(new Set((telemetryData || []).map(r => r.station_id)));

  const displayData = filterStation && filterStation !== 'ALL'
    ? (telemetryData || []).filter(r => r.station_id === filterStation)
    : (telemetryData || []);

  const sortedRows = ([...displayData]).reverse().slice(0, 25);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-purple-400" />
            3-Layer Signal Evidence & Disambiguation Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Decoupled Physics (S_physics), Temporal ML (S_temporal), and Spatial IDW (S_spatial) score breakdown
          </p>
        </div>

        {/* Station Filter Dropdown */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 shrink-0 font-medium">Filter Station:</span>
          <select
            value={filterStation}
            onChange={(e) => {
              const val = e.target.value;
              setFilterStation(val);
              if (setSelectedStation && val !== 'ALL') setSelectedStation(val);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-sky-400 font-mono font-medium focus:ring-2 focus:ring-purple-500 outline-none"
          >
            <option value="ALL">🌐 All Stations ({uniqueStations.length})</option>
            {uniqueStations.map(st => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 font-medium uppercase border-b border-slate-800">
            <tr>
              <th className="px-3 py-2.5">Timestamp</th>
              <th className="px-3 py-2.5">Station</th>
              <th className="px-3 py-2.5">Raw Temp</th>
              <th className="px-3 py-2.5">Imputed Temp</th>
              <th className="px-3 py-2.5 text-center">Physics Score</th>
              <th className="px-3 py-2.5 text-center">Temporal Score</th>
              <th className="px-3 py-2.5 text-center">Spatial Score</th>
              <th className="px-3 py-2.5">Root Cause</th>
              <th className="px-3 py-2.5">Evidence Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {sortedRows.map((row, idx) => {
              const isAnomaly = row.is_anomaly_pred;
              return (
                <tr key={`${row.station_id}-${row.timestamp}-${idx}`} className={isAnomaly ? 'bg-rose-500/10 border-l-2 border-rose-500' : 'hover:bg-slate-800/40'}>
                  <td className="px-3 py-2 font-mono text-slate-400">{formatTimeString(row.timestamp)}</td>
                  <td className="px-3 py-2 font-mono text-sky-400 font-medium">{row.station_id}</td>
                  <td className="px-3 py-2 font-medium text-white">{row.temperature_C != null ? `${row.temperature_C}°C` : 'NaN'}</td>
                  <td className="px-3 py-2 text-emerald-400 font-medium">{row.corrected_temp_C != null ? `${row.corrected_temp_C}°C` : 'N/A'}</td>
                  <td className="px-3 py-2 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded text-[11px] ${row.physics_score > 0 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'text-slate-400'}`}>
                      {row.physics_score}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded text-[11px] ${row.temporal_score > 0.4 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'text-slate-400'}`}>
                      {row.temporal_score}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded text-[11px] ${row.spatial_score > 0.4 ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'text-slate-400'}`}>
                      {row.spatial_score}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-semibold uppercase text-[11px]">
                    <span className={isAnomaly ? 'text-rose-400 font-bold' : 'text-slate-400'}>{row.root_cause}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-300 max-w-xs truncate" title={row.explanation}>{row.explanation}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
