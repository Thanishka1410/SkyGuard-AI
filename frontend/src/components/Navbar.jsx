import React from 'react';
import { Satellite, ShieldCheck, Activity, CloudRain, Cpu, Radio } from 'lucide-react';

export default function Navbar({ activeDataset, setActiveDataset, liveStatus }) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand Title */}
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-sky-500/10 border border-sky-500/30 rounded-xl text-sky-400">
            <Satellite className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">SkyGuard AI</h1>
              <span className="px-2 py-0.5 text-xs font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded-full">
                SIH PS 26073
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD)
            </p>
          </div>
        </div>

        {/* Core Architecture Callout Badges */}
        <div className="hidden lg:flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded-lg text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>3-Layer Decoupled Fusion</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded-lg text-slate-300">
            <CloudRain className="w-4 h-4 text-sky-400" />
            <span>Weather Disambiguation</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded-lg text-slate-300">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span>Self-Healing Network</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-4">
          <select
            value={activeDataset}
            onChange={(e) => setActiveDataset(e.target.value)}
            className="bg-slate-800 text-slate-200 border border-purple-500/50 text-xs font-medium rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500 outline-none shadow-lg"
          >
            <option value="live">🎮 Live Interactive Demo Mode (Judges Control)</option>
            <option value="simulated">📊 Simulated India AWS Network (30-Day Batch)</option>
            <option value="maxplanck">🌍 Max Planck Real Unlabelled Weather Dataset</option>
          </select>

          <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-xs font-medium shrink-0">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>{liveStatus}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
