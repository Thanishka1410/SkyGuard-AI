import React from 'react';
import { AlertCircle, Zap, ShieldCheck, Thermometer, Radio } from 'lucide-react';
import { formatTimeString } from '../utils/formatters';

export default function AlertFeed({ alerts }) {
  const getCauseBadge = (cause) => {
    switch (cause?.toLowerCase()) {
      case 'spike':
        return <span className="px-2 py-0.5 text-[11px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded">SPIKE</span>;
      case 'frozen_value':
        return <span className="px-2 py-0.5 text-[11px] font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded">FROZEN VALUE</span>;
      case 'calibration_drift':
        return <span className="px-2 py-0.5 text-[11px] font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded">DRIFT</span>;
      case 'comm_loss':
        return <span className="px-2 py-0.5 text-[11px] font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded">COMM LOSS</span>;
      case 'real_weather_event':
        return <span className="px-2 py-0.5 text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded">WEATHER EVENT</span>;
      default:
        return <span className="px-2 py-0.5 text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 rounded">ANOMALY</span>;
    }
  };

export default function AlertFeed({ alerts = [], telemetry = [] }) {
  const displayItems = (alerts && alerts.length > 0)
    ? ([...alerts]).reverse().slice(0, 25)
    : ([...(telemetry || [])]).reverse().slice(0, 20);

  const isShowingAnomalies = alerts && alerts.length > 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <AlertCircle className={`w-5 h-5 ${isShowingAnomalies ? 'text-rose-400' : 'text-emerald-400'}`} />
          {isShowingAnomalies ? 'Real-Time Anomaly Alert Feed' : 'Live Telemetry Event & Verification Feed'}
        </h2>
        <span className="text-xs text-slate-400 font-mono">
          {isShowingAnomalies ? `${alerts.length} Active Fault Alerts` : 'Live Stream Validating (1.5s Ticks)'}
        </span>
      </div>

      {/* Alert Feed Container */}
      <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
        {displayItems.map((alert, idx) => {
          const isAnom = alert.is_anomaly_pred;
          return (
            <div
              key={`${alert.station_id}-${alert.timestamp}-${idx}`}
              className={`p-3.5 rounded-lg bg-slate-950 border transition-all text-xs ${
                isAnom ? 'border-rose-500/50 bg-rose-950/20' : 'border-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-sky-400 font-medium">{alert.station_id}</span>
                  {getCauseBadge(alert.root_cause)}
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {formatTimeString(alert.timestamp)}
                </span>
              </div>

              <p className="text-slate-300 mt-1 leading-relaxed">{alert.explanation}</p>

              {alert.spatial_expected_temp != null && isAnom && (
                <div className="mt-2 text-[11px] text-emerald-400 flex items-center gap-1.5 bg-emerald-500/5 px-2.5 py-1 rounded border border-emerald-500/10">
                  <Zap className="w-3 h-3" />
                  <span>Self-Healing Imputation: {alert.temperature_C}°C &rarr; {alert.spatial_expected_temp}°C</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
