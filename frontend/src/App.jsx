import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricCards from './components/MetricCards';
import NetworkMap from './components/NetworkMap';
import TelemetryChart from './components/TelemetryChart';
import AlertFeed from './components/AlertFeed';
import ExplainabilityTable from './components/ExplainabilityTable';
import { INITIAL_STATIONS, INITIAL_TELEMETRY } from './data/mockData';

export default function App() {
  const [activeDataset, setActiveDataset] = useState('simulated');
  const [selectedStation, setSelectedStation] = useState('AWS_DELHI_01');
  const [stations, setStations] = useState(INITIAL_STATIONS);
  const [telemetry, setTelemetry] = useState(INITIAL_TELEMETRY);
  const [liveStatus, setLiveStatus] = useState('SkyGuard Core Online');
  const [isLoading, setIsLoading] = useState(false);

  // Fetch real data from FastAPI backend with instant caching
  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);
      try {
        const res = await fetch(`/api/telemetry?dataset=${activeDataset}`);
        if (res.ok) {
          const data = await res.json();
          if (data.stations && data.stations.length > 0) {
            setStations(data.stations);
            // Default selectedStation to first available station in dataset
            if (!data.stations.some(s => s.station_id === selectedStation)) {
              setSelectedStation(data.stations[0].station_id);
            }
          }
          if (data.telemetry) setTelemetry(data.telemetry);
          setLiveStatus('Live FastAPI Connected');
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

        {/* Station Network Map */}
        <NetworkMap
          stations={stations}
          selectedStation={selectedStation}
          setSelectedStation={setSelectedStation}
        />

        {/* Telemetry Chart & Alert Feed Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TelemetryChart
              telemetryData={activeTelemetry.length > 0 ? activeTelemetry : telemetry}
              selectedStation={selectedStation}
            />
          </div>
          <div className="lg:col-span-1">
            <AlertFeed alerts={anomalyAlerts} />
          </div>
        </div>

        {/* Explainability Signal Table */}
        <ExplainabilityTable telemetryData={telemetry} />
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-4 px-6 text-center text-xs text-slate-500">
        SkyGuard AI — Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD) | SIH PS 26073
      </footer>
    </div>
  );
}
