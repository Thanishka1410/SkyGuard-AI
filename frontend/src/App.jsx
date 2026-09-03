import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricCards from './components/MetricCards';
import NetworkMap from './components/NetworkMap';
import TelemetryChart from './components/TelemetryChart';
import AlertFeed from './components/AlertFeed';
import ExplainabilityTable from './components/ExplainabilityTable';
import PieChartCard from './components/PieChartCard';
import StationRankings from './components/StationRankings';
import { INITIAL_STATIONS, INITIAL_TELEMETRY } from './data/mockData';
import { Map, Cpu, AlertTriangle, Layers } from 'lucide-react';

export default function App() {
  const [activeDataset, setActiveDataset] = useState('simulated');
  const [selectedStation, setSelectedStation] = useState('AWS_DELHI_01');
  const [stations, setStations] = useState(INITIAL_STATIONS);
  const [telemetry, setTelemetry] = useState(INITIAL_TELEMETRY);
  const [liveStatus, setLiveStatus] = useState('SkyGuard Core Online');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch real data from FastAPI backend with instant caching and failover
  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);
      try {
        const primaryUrl = `http://localhost:8000/api/telemetry?dataset=${activeDataset}`;
        const proxyUrl = `/api/telemetry?dataset=${activeDataset}`;

        let res = await fetch(primaryUrl).catch(() => null);
        if (!res || !res.ok) {
          res = await fetch(proxyUrl).catch(() => null);
        }

        if (res && res.ok) {
          const data = await res.json();
          if (data.stations && data.stations.length > 0) {
            setStations(data.stations);
            setSelectedStation(data.stations[0].station_id);
          }
          if (data.telemetry && data.telemetry.length > 0) {
            setTelemetry(data.telemetry);
          }
          setLiveStatus('Live FastAPI Connected');
        } else {
          setLiveStatus('Interactive Demo Mode');
        }
      } catch (err) {
        setLiveStatus('Interactive Demo Mode');
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [activeDataset]);

  const activeTelemetry = telemetry.filter((t) => t.station_id === selectedStation);
  const anomalyAlerts = telemetry.filter((t) => t.is_anomaly_pred);

  const metrics = {
    totalObs: telemetry.length,
    anomCount: anomalyAlerts.length,
    weatherEvents: telemetry.filter((t) => t.root_cause === 'real_weather_event').length,
    anomRate: telemetry.length > 0 ? ((anomalyAlerts.length / telemetry.length) * 100).toFixed(1) : '0.0',
    avgHealth: (stations.reduce((acc, s) => acc + s.station_health_pct, 0) / (stations.length || 1)).toFixed(1),
    activeStations: stations.length
  };

  const tabs = [
    { id: 'overview', label: '🗺️ Network Health & Disambiguation', icon: Map },
    { id: 'selfhealing', label: '🩹 Self-Healing Telemetry Imputation', icon: Cpu },
    { id: 'alerts', label: '🚨 Live Alert Feed & Root Causes', icon: AlertTriangle },
    { id: 'evidence', label: '🔬 3-Layer Decoupled Signal Evidence', icon: Layers }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navigation Bar */}
      <Navbar
        activeDataset={activeDataset}
        setActiveDataset={setActiveDataset}
        liveStatus={liveStatus}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6 relative">
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs z-40 flex items-center justify-center rounded-xl">
            <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 px-5 py-3 rounded-xl shadow-2xl">
              <div className="w-5 h-5 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm font-medium text-slate-200">Switching Dataset Telemetry...</span>
            </div>
          </div>
        )}

        {/* Top Metric Cards */}
        <MetricCards metrics={metrics} />

        {/* Tab Selector Header */}
        <div className="border-b border-slate-800 flex space-x-2 overflow-x-auto pb-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-t-lg font-medium text-xs transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-slate-900 text-sky-400 border-t-2 border-sky-400 border-x border-slate-800'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
              >
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* TAB 1: Network Health & Disambiguation */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <NetworkMap
              stations={stations}
              selectedStation={selectedStation}
              setSelectedStation={setSelectedStation}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PieChartCard telemetry={telemetry} />
              <StationRankings stations={stations} />
            </div>
          </div>
        )}

        {/* TAB 2: Self-Healing Telemetry Imputation */}
        {activeTab === 'selfhealing' && (
          <div className="space-y-6">
            <TelemetryChart
              telemetryData={activeTelemetry.length > 0 ? activeTelemetry : telemetry}
              selectedStation={selectedStation}
            />
            {/* Raw vs Imputed Table for Anomalies */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
              <h3 className="text-sm font-semibold text-white mb-3">Raw vs Self-Healing Imputed Table (Anomalies Only)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 font-medium uppercase border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2">Timestamp</th>
                      <th className="px-3 py-2">Station</th>
                      <th className="px-3 py-2">Raw Temp</th>
                      <th className="px-3 py-2">Spatial Expected</th>
                      <th className="px-3 py-2">Self-Healing Imputed</th>
                      <th className="px-3 py-2">Root Cause</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {anomalyAlerts.slice(0, 10).map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="px-3 py-2 font-mono text-slate-400">{new Date(row.timestamp).toLocaleTimeString()}</td>
                        <td className="px-3 py-2 font-mono text-sky-400">{row.station_id}</td>
                        <td className="px-3 py-2 font-medium text-rose-400">{row.temperature_C}°C</td>
                        <td className="px-3 py-2 text-slate-300">{row.spatial_expected_temp}°C</td>
                        <td className="px-3 py-2 text-emerald-400 font-semibold">{row.corrected_temp_C}°C</td>
                        <td className="px-3 py-2 font-semibold uppercase text-rose-400">{row.root_cause}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: Live Alert Feed & Root Causes */}
        {activeTab === 'alerts' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AlertFeed alerts={anomalyAlerts} />
            </div>
            <div className="lg:col-span-1">
              <PieChartCard telemetry={telemetry} />
            </div>
          </div>
        )}

        {/* TAB 4: 3-Layer Decoupled Signal Evidence */}
        {activeTab === 'evidence' && (
          <ExplainabilityTable telemetryData={telemetry} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-4 px-6 text-center text-xs text-slate-500">
        SkyGuard AI — Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD) | SIH PS 26073
      </footer>
    </div>
  );
}
