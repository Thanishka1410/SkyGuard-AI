import React from 'react';
import { Award, Radio } from 'lucide-react';

export default function StationRankings({ stations }) {
  const sortedStations = [...stations].sort((a, b) => b.station_health_pct - a.station_health_pct);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Award className="w-5 h-5 text-amber-400" />
          Station Health Index Rankings
        </h2>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Rolling reliability score ($0-100\%$) per Automatic Weather Station
      </p>

      <div className="space-y-3 overflow-y-auto max-h-[260px] pr-1">
        {sortedStations.map((st, idx) => {
          const isHealthy = st.station_health_pct >= 70;
          return (
            <div key={st.station_id} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-xs">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center space-x-2">
                  <span className="w-4 h-4 rounded-full bg-slate-800 flex items-center justify-center text-[10px] text-slate-400 font-mono">
                    {idx + 1}
                  </span>
                  <span className="font-mono text-slate-200 font-medium">{st.station_id}</span>
                  <span className="text-[11px] text-slate-500">({st.region})</span>
                </div>
                <span className={isHealthy ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
                  {st.station_health_pct}%
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500'}`}
                  style={{ width: `${st.station_health_pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
