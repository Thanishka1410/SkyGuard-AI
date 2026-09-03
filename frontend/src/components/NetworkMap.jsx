import React from 'react';
import { MapPin, CheckCircle2, AlertCircle, Cpu } from 'lucide-react';

export default function NetworkMap({ stations, selectedStation, setSelectedStation }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-sky-400" />
            AWS Station Network Map & Health Status
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Geographic stations with real-time health index and spatial neighbor IDW topology
          </p>
        </div>
      </div>

      {/* Grid of Stations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {stations.map((st) => {
          const isSelected = st.station_id === selectedStation;
          const isHealthy = st.station_health_pct >= 70;
          return (
            <div
              key={st.station_id}
              onClick={() => setSelectedStation(st.station_id)}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-sky-500/10 border-sky-500 ring-2 ring-sky-500/30'
                  : 'bg-slate-850 border-slate-800 hover:border-slate-700 hover:bg-slate-800/80'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold text-slate-200">
                  {st.station_id}
                </span>
                {isHealthy ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                )}
              </div>

              <div className="mt-2.5 flex items-center justify-between text-xs">
                <span className="text-slate-400">Region: <strong className="text-slate-200">{st.region}</strong></span>
                <span className="text-slate-400">Lat/Lon: {st.lat}, {st.lon}</span>
              </div>

              {/* Health Bar */}
              <div className="mt-3">
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Health Index</span>
                  <span className={isHealthy ? 'text-emerald-400 font-medium' : 'text-amber-400 font-medium'}>
                    {st.station_health_pct}%
                  </span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isHealthy ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${st.station_health_pct}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
