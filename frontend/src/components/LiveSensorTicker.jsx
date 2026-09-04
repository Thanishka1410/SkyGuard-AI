import React from 'react';
import { Thermometer, Droplets, Gauge, Wind, Clock, Activity, Zap } from 'lucide-react';
import { formatTimeString } from '../utils/formatters';

export default function LiveSensorTicker({ telemetry = [], selectedStation = 'AWS_DELHI_01', isSimulating = true }) {
  // Find latest telemetry reading for selected station
  const stationReadings = telemetry.filter(t => t.station_id === selectedStation);
  const latest = stationReadings.length > 0 ? stationReadings[stationReadings.length - 1] : null;

  if (!latest) {
    return null;
  }

  const isAnomaly = latest.is_anomaly_pred;
  const rawTemp = latest.temperature_C != null ? latest.temperature_C : 'NaN';
  const corrTemp = latest.corrected_temp_C != null ? latest.corrected_temp_C : 'N/A';
  const press = latest.pressure_hPa != null ? latest.pressure_hPa : 'N/A';
  const rh = latest.humidity_pct != null ? latest.humidity_pct : 'N/A';
  const tdew = latest.calculated_tdew != null ? Number(latest.calculated_tdew).toFixed(1) : 'N/A';
  const timeStr = formatTimeString(latest.timestamp);

  return (
    <div className={`rounded-xl p-4 border transition-all duration-300 shadow-2xl ${
      isAnomaly
        ? 'bg-gradient-to-r from-rose-950/80 via-slate-900 to-rose-950/80 border-rose-500/50 shadow-rose-500/10'
        : 'bg-gradient-to-r from-slate-900 via-sky-950/30 to-slate-900 border-sky-500/30 shadow-sky-500/10'
    }`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3 border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2.5">
          <div className={`p-2 rounded-lg border ${
            isAnomaly ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-sky-500/20 text-sky-400 border-sky-500/30'
          }`}>
            <Activity className={`w-5 h-5 ${isSimulating ? 'animate-pulse' : ''}`} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Live Station Feed:</span>
              <span className="text-sm font-bold text-sky-400 font-mono">{selectedStation}</span>
              {isAnomaly && (
                <span className="px-2 py-0.5 text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 rounded-full uppercase animate-pulse">
                  🚨 {latest.root_cause} DETECTED
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Region: <strong className="text-slate-300">{latest.region || 'Plains'}</strong> | Coordinates: [{latest.lat}, {latest.lon}]
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg font-mono">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-400">Tick Time:</span>
            <span className="text-white font-bold">{timeStr}</span>
          </div>
          <div className="flex items-center space-x-1.5 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg font-mono">
            <span className={`w-2 h-2 rounded-full ${isSimulating ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`}></span>
            <span className="text-slate-300 font-semibold">{isSimulating ? 'STREAMING (1.5s)' : 'PAUSED'}</span>
          </div>
        </div>
      </div>

      {/* Sensor Metrics Ticker Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
        {/* Temperature */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Air Temperature</span>
            <Thermometer className={`w-4 h-4 ${isAnomaly ? 'text-rose-400' : 'text-amber-400'}`} />
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className={`text-xl font-bold font-mono tracking-tight ${isAnomaly ? 'text-rose-400' : 'text-white'}`}>
              {rawTemp}°C
            </span>
            {isAnomaly && (
              <span className="text-[10px] text-emerald-400 font-mono font-semibold" title="Self-Healing Imputed">
                &rarr; {corrTemp}°C
              </span>
            )}
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Relative Humidity</span>
            <Droplets className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-1">
            <span className="text-xl font-bold text-white font-mono tracking-tight">{rh}%</span>
          </div>
        </div>

        {/* Barometric Pressure */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Pressure</span>
            <Gauge className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-1">
            <span className="text-xl font-bold text-white font-mono tracking-tight">{press} hPa</span>
          </div>
        </div>

        {/* Dew Point */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Dew Point (Tdew)</span>
            <Wind className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-1">
            <span className="text-xl font-bold text-white font-mono tracking-tight">{tdew}°C</span>
          </div>
        </div>

        {/* Sensor Health */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between col-span-2 sm:col-span-4 lg:col-span-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Station Health</span>
            <Zap className={`w-4 h-4 ${latest.station_health_pct > 80 ? 'text-emerald-400' : 'text-rose-400'}`} />
          </div>
          <div className="mt-1 flex items-baseline space-x-2">
            <span className={`text-xl font-bold font-mono tracking-tight ${
              latest.station_health_pct > 80 ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {latest.station_health_pct || 100}%
            </span>
            <span className="text-[10px] text-slate-500 uppercase">{latest.station_health_pct > 80 ? 'Optimal' : 'Degraded'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
