import React from 'react';
import { Activity, AlertTriangle, ShieldCheck, HeartPulse, Radio } from 'lucide-react';

export default function MetricCards({ metrics = {} }) {
  const totalObs = typeof metrics.totalObs === 'number' ? metrics.totalObs.toLocaleString() : '0';
  const anomCount = typeof metrics.anomCount === 'number' ? metrics.anomCount.toLocaleString() : '0';
  const weatherEvents = typeof metrics.weatherEvents === 'number' ? metrics.weatherEvents.toLocaleString() : '0';
  const anomRate = metrics.anomRate !== undefined && metrics.anomRate !== null ? metrics.anomRate : '0.0';
  const avgHealth = metrics.avgHealth !== undefined && metrics.avgHealth !== null ? metrics.avgHealth : '100.0';
  const activeStations = typeof metrics.activeStations === 'number' ? metrics.activeStations : 0;

  const cards = [
    {
      title: 'Total Telemetry Rows',
      value: totalObs,
      subtitle: 'Processed Observations',
      icon: Activity,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    },
    {
      title: 'Sensor Fault Anomalies',
      value: anomCount,
      subtitle: `${anomRate}% anomaly rate`,
      icon: AlertTriangle,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      title: 'Real Weather Events Saved',
      value: weatherEvents,
      subtitle: 'Spatial Disambiguated',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Network Health Index',
      value: `${avgHealth}%`,
      subtitle: 'Self-Correcting Target',
      icon: HeartPulse,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20'
    },
    {
      title: 'Active AWS Stations',
      value: activeStations,
      subtitle: 'Multi-Region Network',
      icon: Radio,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl border ${card.bg} backdrop-blur-sm flex flex-col justify-between transition-all hover:scale-[1.02]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">{card.title}</span>
              <Icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-white tracking-tight">{card.value}</div>
              <div className="text-xs text-slate-400 mt-1">{card.subtitle}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
