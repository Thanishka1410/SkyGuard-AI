import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricCards from './components/MetricCards';
import NetworkMap from './components/NetworkMap';
import TelemetryChart from './components/TelemetryChart';
import AlertFeed from './components/AlertFeed';
import ExplainabilityTable from './components/ExplainabilityTable';
import PieChartCard from './components/PieChartCard';
import StationRankings from './components/StationRankings';
import DemoControls from './components/DemoControls';
import {
  INITIAL_STATIONS,
  INITIAL_TELEMETRY,
  MPI_JENA_INITIAL_STATIONS,
  MPI_JENA_INITIAL_TELEMETRY
} from './data/mockData';
import { formatTimeString } from './utils/formatters';
import { Map, Cpu, AlertTriangle, Layers, Sliders } from 'lucide-react';

export default function App() {
  const [activeDataset, setActiveDataset] = useState('live');
  const [selectedStation, setSelectedStation] = useState('AWS_DELHI_01');
  const [stations, setStations] = useState(INITIAL_STATIONS);
  const [telemetry, setTelemetry] = useState(INITIAL_TELEMETRY);
  const [liveStatus, setLiveStatus] = useState('⚡ Live Demo Stream Active');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showDemoControls, setShowDemoControls] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false); // Default STOPPED per user request
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Handle Dataset Switch cleanly without clearing state to 0 items
  const handleDatasetChange = (newDataset) => {
    if (newDataset === activeDataset) return;
    setIsLoading(true);
    setActiveDataset(newDataset);
    if (newDataset === 'live') {
      setIsSimulating(false);
    }
    if (newDataset === 'maxplanck') {
      setSelectedStation('AWS_MPI_JENA_01');
    } else {
      setSelectedStation('AWS_DELHI_01');
    }
  };

  // Fetch data from FastAPI backend (Polls every 1.5s in Live mode when isSimulating is true)
  useEffect(() => {
    let isMounted = true;
    let timerId = null;

    async function fetchData() {
      try {
        const timestamp = Date.now();
        const endpoint = activeDataset === 'live' ? '/api/live/telemetry' : `/api/telemetry?dataset=${activeDataset}`;
        const sep = endpoint.includes('?') ? '&' : '?';
        const primaryUrl = `http://localhost:8000${endpoint}${sep}_t=${timestamp}`;
        const proxyUrl = `${endpoint}${sep}_t=${timestamp}`;

        let res = await fetch(primaryUrl, { cache: 'no-store' }).catch(() => null);
        if (!res || !res.ok) {
          res = await fetch(proxyUrl, { cache: 'no-store' }).catch(() => null);
        }

        if (res && res.ok && isMounted) {
          const data = await res.json();
          if (data.stations && data.stations.length > 0) {
            setStations(data.stations);
            // Ensure selected station matches active dataset stations
            const stationExists = data.stations.some(s => s.station_id === selectedStation);
            if (!stationExists) {
              setSelectedStation(data.stations[0].station_id);
            }
          }
          if (data.telemetry && data.telemetry.length > 0) {
            setTelemetry(data.telemetry);
          }
          if (activeDataset === 'live') {
            setLiveStatus(isSimulating ? '⚡ Live Demo Stream Active' : '⏸️ Live Stream Paused');
          } else if (activeDataset === 'simulated') {
            setLiveStatus('📊 30-Day Batch Network');
          } else {
            setLiveStatus('🌍 Max Planck Weather Data');
          }
        } else if (isMounted) {
          // Backend disconnected / offline fallback
          if (activeDataset === 'maxplanck') {
            setStations(MPI_JENA_INITIAL_STATIONS);
            setTelemetry(MPI_JENA_INITIAL_TELEMETRY);
            setSelectedStation('AWS_MPI_JENA_01');
            setLiveStatus('Max Planck Demo Mode');
          } else {
            setStations(INITIAL_STATIONS);
            setTelemetry(INITIAL_TELEMETRY);
            setSelectedStation('AWS_DELHI_01');
            setLiveStatus('Interactive Demo Mode');
          }
        }
      } catch (err) {
        if (isMounted) {
          if (activeDataset === 'maxplanck') {
            setStations(MPI_JENA_INITIAL_STATIONS);
            setTelemetry(MPI_JENA_INITIAL_TELEMETRY);
            setSelectedStation('AWS_MPI_JENA_01');
            setLiveStatus('Max Planck Demo Mode');
          } else {
            setStations(INITIAL_STATIONS);
            setTelemetry(INITIAL_TELEMETRY);
            setSelectedStation('AWS_DELHI_01');
            setLiveStatus('Interactive Demo Mode');
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchData();

    // In Live mode, poll every 1.5 seconds when isSimulating is true
    if (activeDataset === 'live' && isSimulating) {
      timerId = setInterval(fetchData, 1500);
    }

    return () => {
      isMounted = false;
      if (timerId) clearInterval(timerId);
    };
  }, [activeDataset, isSimulating, refreshTrigger]);

  const activeTelemetry = telemetry.filter((t) => t.station_id === selectedStation);
  const anomalyAlerts = telemetry.filter((t) => t.is_anomaly_pred);

  const metrics = {
    totalObs: telemetry.length,
    anomCount: anomalyAlerts.length,
    weatherEvents: telemetry.filter((t) => t.root_cause === 'real_weather_event').length,
    anomRate: telemetry.length > 0 ? ((anomalyAlerts.length / telemetry.length) * 100).toFixed(1) : '0.0',
    avgHealth: stations.length > 0 ? (stations.reduce((acc, s) => acc + (s.station_health_pct || 0), 0) / stations.length).toFixed(1) : '100.0',
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
        setActiveDataset={handleDatasetChange}
        liveStatus={liveStatus}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6 relative">
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-xs z-50 flex items-center justify-center rounded-xl">
            <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 px-6 py-4 rounded-xl shadow-2xl">
              <div className="w-6 h-6 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm font-semibold text-slate-200">
                Loading {activeDataset === 'live' ? 'Live Demo Stream' : activeDataset === 'simulated' ? 'Simulated India AWS Network' : 'Max Planck Dataset'}...
              </span>
            </div>
          </div>
        )}

        {/* Dataset Status & Controls Header Banner */}
        <div className="flex items-center justify-between bg-slate-900/80 border border-purple-500/30 rounded-xl px-4 py-2.5 text-xs">
          <div className="flex items-center space-x-2.5">
            <span className={`w-2.5 h-2.5 rounded-full ${activeDataset === 'live' ? (isSimulating ? 'bg-emerald-400 animate-ping' : 'bg-amber-400') : 'bg-sky-400'}`}></span>
            <span className="font-bold text-purple-300 text-sm">
              {activeDataset === 'live'
                ? '⚡ Live Demo Stream Active'
                : activeDataset === 'simulated'
                ? '📊 Simulated India AWS Network (30-Day Batch)'
                : '🌍 Max Planck Institute Real Weather Dataset'}
            </span>
            <span className="text-slate-400 font-mono text-xs">
              ({activeDataset === 'live'
                ? (isSimulating ? 'Real-Time 1.5s Ticks' : 'Stream Paused')
                : `${telemetry.length.toLocaleString()} Processed Records`})
            </span>
          </div>
          {activeDataset === 'live' && (
            <button
              onClick={() => setShowDemoControls(!showDemoControls)}
              className="flex items-center space-x-1.5 px-3 py-1 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/40 rounded-lg text-purple-300 transition-colors font-medium"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{showDemoControls ? 'Hide Fault Controls' : 'Show Fault Controls'}</span>
            </button>
          )}
        </div>

        {/* Demo Fault Injection Panel */}
        {showDemoControls && (
          <DemoControls
            isSimulating={isSimulating}
            setIsSimulating={setIsSimulating}
            setActiveDataset={handleDatasetChange}
            setSelectedStation={setSelectedStation}
            onInjectSuccess={() => setRefreshTrigger((prev) => prev + 1)}
          />
        )}

        {/* Top Metric Cards */}
        <MetricCards key={`metrics-${activeDataset}-${telemetry.length}`} metrics={metrics} />

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
          <div key={`overview-${activeDataset}-${telemetry.length}`} className="space-y-6">
            <NetworkMap
              key={`map-${activeDataset}-${stations.length}`}
              stations={stations}
              selectedStation={selectedStation}
              setSelectedStation={setSelectedStation}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PieChartCard key={`pie-${activeDataset}-${telemetry.length}`} telemetry={telemetry} />
              <StationRankings key={`rank-${activeDataset}-${stations.length}`} stations={stations} />
            </div>
          </div>
        )}

        {/* TAB 2: Self-Healing Telemetry Imputation */}
        {activeTab === 'selfhealing' && (
          <div key={`healing-${activeDataset}-${selectedStation}-${activeTelemetry.length}`} className="space-y-6">
            <TelemetryChart
              key={`chart-${activeDataset}-${selectedStation}-${activeTelemetry.length}`}
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
                    {([...(anomalyAlerts || [])]).reverse().slice(0, 15).map((row, idx) => (
                      <tr key={`${row.station_id}-${row.timestamp}-${idx}`} className="hover:bg-slate-800/40">
                        <td className="px-3 py-2 font-mono text-slate-400">{formatTimeString(row.timestamp)}</td>
                        <td className="px-3 py-2 font-mono text-sky-400">{row.station_id}</td>
                        <td className="px-3 py-2 font-medium text-rose-400">{row.temperature_C != null ? `${row.temperature_C}°C` : 'NaN'}</td>
                        <td className="px-3 py-2 text-slate-300">{row.spatial_expected_temp != null ? `${row.spatial_expected_temp}°C` : 'N/A'}</td>
                        <td className="px-3 py-2 text-emerald-400 font-semibold">{row.corrected_temp_C != null ? `${row.corrected_temp_C}°C` : 'N/A'}</td>
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
          <div key={`alerts-${activeDataset}-${anomalyAlerts.length}`} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AlertFeed key={`alertfeed-${activeDataset}-${anomalyAlerts.length}`} alerts={anomalyAlerts} />
            </div>
            <div className="lg:col-span-1">
              <PieChartCard key={`alertpie-${activeDataset}-${telemetry.length}`} telemetry={telemetry} />
            </div>
          </div>
        )}

        {/* TAB 4: 3-Layer Decoupled Signal Evidence */}
        {activeTab === 'evidence' && (
          <ExplainabilityTable key={`evidence-${activeDataset}-${telemetry.length}`} telemetryData={telemetry} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-4 px-6 text-center text-xs text-slate-500">
        SkyGuard AI — Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD) | SIH PS 26073
      </footer>
    </div>
  );
}
