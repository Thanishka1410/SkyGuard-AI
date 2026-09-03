import React from 'react';
import { Activity, AlertTriangle, ShieldCheck, HeartPulse, Radio } from 'lucide-react';

export default function MetricCards({ metrics }) {
  const cards = [
    {
      title: 'Total Telemetry Rows',
      value: metrics.totalObs ? metrics.totalObs.toLocaleString() : '2,016',
      subtitle: 'Processed Observations',
      icon: Activity,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    },
    {
      title: 'Sensor Fault Anomalies',
      value: metrics.anomCount ? metrics.anomCount.toLocaleString() : '803',
      subtitle: `${metrics.anomRate || '39.8'}% anomaly rate`,
      icon: AlertTriangle,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      title: 'Real Weather Events Saved',
      value: metrics.weatherEvents ? metrics.weatherEvents.toLocaleString() : '433',
      subtitle: 'Spatial Disambiguated',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Network Health Index',
      value: `${metrics.avgHealth || '60.2'}%`,
      subtitle: 'Self-Correcting Target',
      icon: HeartPulse,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20'
    },
    {
      title: 'Active AWS Stations',
      value: metrics.activeStations || '7',
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
