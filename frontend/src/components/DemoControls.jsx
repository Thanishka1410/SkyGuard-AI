import React, { useState } from 'react';
import { Zap, Snowflake, TrendingUp, Radio, Volume2, ShieldAlert, CheckCircle2, Play, Pause } from 'lucide-react';

const STATIONS = [
  { id: 'AWS_DELHI_01', label: 'AWS_DELHI_01 (Plains)' },
  { id: 'AWS_MUMBAI_01', label: 'AWS_MUMBAI_01 (Coastal)' },
  { id: 'AWS_CHENNAI_01', label: 'AWS_CHENNAI_01 (Coastal)' },
  { id: 'AWS_LUCKNOW_01', label: 'AWS_LUCKNOW_01 (Plains)' },
  { id: 'AWS_SHIMLA_01', label: 'AWS_SHIMLA_01 (Hilly)' },
  { id: 'AWS_JAISALMER_01', label: 'AWS_JAISALMER_01 (Desert)' }
];

export default function DemoControls({ isSimulating, setIsSimulating, onInjectSuccess }) {
  const [selectedStation, setSelectedStation] = useState('AWS_DELHI_01');
  const [durationTicks, setDurationTicks] = useState(10);
  const [activeStatus, setActiveStatus] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInject = async (anomalyType, label) => {
    setIsSubmitting(true);
    setActiveStatus(null);
    const payload = {
      station_id: selectedStation,
      anomaly_type: anomalyType,
      duration_ticks: durationTicks
    };

    try {
      let res = await fetch('http://localhost:8000/api/demo/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).catch(() => null);

      if (!res || !res.ok) {
        res = await fetch('/api/demo/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).catch(() => null);
      }

      if (res && res.ok) {
        const data = await res.json();
        // Ensure simulation is running when injecting
        if (!isSimulating) {
          setIsSimulating(true);
        }
        setActiveStatus({
          type: 'success',
          msg: `Injected '${label}' on ${selectedStation} for ${durationTicks} ticks! Streaming live detections...`
        });
        if (onInjectSuccess) onInjectSuccess();
      } else {
        setActiveStatus({ type: 'error', msg: 'Injection failed. Backend offline or endpoint error.' });
      }
    } catch (err) {
      setActiveStatus({ type: 'error', msg: 'Cannot connect to FastAPI backend.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-slate-900 via-purple-950/40 to-slate-900 border border-purple-500/30 rounded-xl p-5 shadow-2xl space-y-4">
      {/* Panel Header with Master Start/Pause Button */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-purple-500/20 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-lg">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-2">
              🎛️ Live Fault Injection & Simulation Panel
              <span className="px-2 py-0.5 text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/40 rounded-full font-mono">
                Interactive Controls
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Start/pause live telemetry stream and trigger real sensor hardware faults on demand.
            </p>
          </div>
        </div>

        {/* Master Start / Pause Simulation Button */}
        <button
          onClick={() => setIsSimulating(!isSimulating)}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-lg shrink-0 ${
            isSimulating
              ? 'bg-emerald-500 hover:bg-emerald-600 text-slate-950 border border-emerald-400 shadow-emerald-500/20'
              : 'bg-amber-500 hover:bg-amber-600 text-slate-950 border border-amber-400 shadow-amber-500/20'
          }`}
        >
          {isSimulating ? (
            <>
              <Pause className="w-4 h-4 fill-slate-950" />
              <span>PAUSE LIVE STREAM</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-slate-950" />
              <span>START LIVE SIMULATION</span>
            </>
          )}
        </button>
      </div>

      {/* Control Parameters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
        {/* Station Selector */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Select Target AWS Station</label>
          <select
            value={selectedStation}
            onChange={(e) => setSelectedStation(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
          >
            {STATIONS.map((st) => (
              <option key={st.id} value={st.id}>
                {st.label}
              </option>
            ))}
          </select>
        </div>

        {/* Duration Ticks Slider */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-medium text-slate-300">Fault Duration</label>
            <span className="text-xs font-mono text-purple-400 font-semibold">{durationTicks} ticks ({durationTicks * 15} mins)</span>
          </div>
          <input
            type="range"
            min="3"
            max="24"
            step="1"
            value={durationTicks}
            onChange={(e) => setDurationTicks(Number(e.target.value))}
            className="w-full accent-purple-500 bg-slate-950 rounded-lg cursor-pointer"
          />
        </div>
      </div>

      {/* Fault Injection Trigger Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-1">
        {/* 1. Spike */}
        <button
          disabled={isSubmitting}
          onClick={() => handleInject('spike', 'Thermal Spike')}
          className="flex flex-col items-center justify-center p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 hover:bg-rose-500/20 text-rose-300 transition-all group disabled:opacity-50"
        >
          <Zap className="w-5 h-5 mb-1 text-rose-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-semibold">Inject Spike</span>
          <span className="text-[10px] text-rose-400/80 mt-0.5">+25°C Jump</span>
        </button>

        {/* 2. Frozen Value */}
        <button
          disabled={isSubmitting}
          onClick={() => handleInject('frozen_value', 'Frozen Sensor')}
          className="flex flex-col items-center justify-center p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 hover:bg-cyan-500/20 text-cyan-300 transition-all group disabled:opacity-50"
        >
          <Snowflake className="w-5 h-5 mb-1 text-cyan-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-semibold">Inject Frozen</span>
          <span className="text-[10px] text-cyan-400/80 mt-0.5">Flatline Sensor</span>
        </button>

        {/* 3. Calibration Drift */}
        <button
          disabled={isSubmitting}
          onClick={() => handleInject('calibration_drift', 'Calibration Drift')}
          className="flex flex-col items-center justify-center p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 hover:bg-amber-500/20 text-amber-300 transition-all group disabled:opacity-50"
        >
          <TrendingUp className="w-5 h-5 mb-1 text-amber-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-semibold">Inject Drift</span>
          <span className="text-[10px] text-amber-400/80 mt-0.5">+12°C Ramp</span>
        </button>

        {/* 4. Comm Loss */}
        <button
          disabled={isSubmitting}
          onClick={() => handleInject('comm_loss', 'Communication Loss')}
          className="flex flex-col items-center justify-center p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 text-purple-300 transition-all group disabled:opacity-50"
        >
          <Radio className="w-5 h-5 mb-1 text-purple-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-semibold">Comm Loss</span>
          <span className="text-[10px] text-purple-400/80 mt-0.5">NaN Dropouts</span>
        </button>

        {/* 5. Noise Burst */}
        <button
          disabled={isSubmitting}
          onClick={() => handleInject('noise_burst', 'Noise Burst')}
          className="flex flex-col items-center justify-center p-3 rounded-xl bg-pink-500/10 border border-pink-500/30 hover:bg-pink-500/20 text-pink-300 transition-all group disabled:opacity-50 col-span-2 sm:col-span-1"
        >
          <Volume2 className="w-5 h-5 mb-1 text-pink-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-semibold">Noise Burst</span>
          <span className="text-[10px] text-pink-400/80 mt-0.5">High Variance</span>
        </button>
      </div>

      {/* Active Status Notification Banner */}
      {activeStatus && (
        <div className={`p-3 rounded-lg text-xs flex items-center space-x-2 border ${
          activeStatus.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{activeStatus.msg}</span>
        </div>
      )}
    </div>
  );
}
