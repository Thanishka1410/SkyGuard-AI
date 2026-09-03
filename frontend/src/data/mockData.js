// Mock fallback dataset for instant React UI rendering when FastAPI backend is disconnected
export const INITIAL_STATIONS = [
  { station_id: 'AWS_DELHI_01', region: 'Plains', lat: 28.6139, lon: 77.2090, station_health_pct: 58.4 },
  { station_id: 'AWS_DELHI_02', region: 'Plains', lat: 28.7041, lon: 77.1025, station_health_pct: 64.2 },
  { station_id: 'AWS_GURUGRAM_01', region: 'Plains', lat: 28.4595, lon: 77.0266, station_health_pct: 61.8 },
  { station_id: 'AWS_NOIDA_01', region: 'Plains', lat: 28.5355, lon: 77.3910, station_health_pct: 62.0 },
  { station_id: 'AWS_SHIMLA_01', region: 'Hilly', lat: 31.1048, lon: 77.1734, station_health_pct: 88.5 },
  { station_id: 'AWS_MUMBAI_01', region: 'Coastal', lat: 19.0760, lon: 72.8777, station_health_pct: 91.2 },
  { station_id: 'AWS_JAIPUR_01', region: 'Desert', lat: 26.9124, lon: 75.7873, station_health_pct: 82.0 },
];

export const INITIAL_TELEMETRY = Array.from({ length: 48 }, (_, i) => {
  const date = new Date(Date.now() - (47 - i) * 15 * 60 * 1000);
  const hour = date.getHours();
  const diurnal = Math.sin((hour - 8) * (2 * Math.PI / 24));

  const isAnomaly = i === 12 || i === 28 || i === 35;
  const isSpike = i === 12;
  const isFrozen = i >= 28 && i <= 31;

  let rawTemp = 28 + 8 * diurnal + (Math.random() * 0.8 - 0.4);
  if (isSpike) rawTemp = 55.0; // 55°C PS spike example
  if (isFrozen) rawTemp = 24.5;

  const expTemp = 28 + 8 * diurnal;
  const correctedTemp = isAnomaly ? expTemp : rawTemp;

  let rootCause = 'normal';
  if (isSpike) rootCause = 'spike';
  if (isFrozen) rootCause = 'frozen_value';

  let explanation = 'NORMAL: Observations conform to thermodynamic laws, station temporal baseline, and neighbor network.';
  if (isSpike) {
    explanation = '[AWS_DELHI_01] SENSOR ANOMALY DETECTED (SPIKE) - Confidence: 1.00 | Spatial Comparison: Expected T: 31.2°C (vs Actual: 55.0°C, Delta=23.8°C) based on neighbors [AWS_DELHI_02, AWS_NOIDA_01] | Self-Healing Recommendation: Impute temperature from 55.0°C -> 31.2°C';
  } else if (isFrozen) {
    explanation = '[AWS_DELHI_01] SENSOR ANOMALY DETECTED (FROZEN_VALUE) - Confidence: 0.85 | Physics Violations: PHYSICS_FROZEN_SENSOR: Constant reading 24.5°C across 4 consecutive intervals';
  }

  return {
    timestamp: date.toISOString(),
    station_id: 'AWS_DELHI_01',
    temperature_C: Number(rawTemp.toFixed(2)),
    pressure_hPa: 1008.0,
    humidity_pct: 55.0,
    spatial_expected_temp: Number(expTemp.toFixed(2)),
    corrected_temp_C: Number(correctedTemp.toFixed(2)),
    physics_score: isAnomaly ? 0.8 : 0.0,
    temporal_score: isAnomaly ? 0.9 : 0.1,
    spatial_score: isSpike ? 1.0 : 0.0,
    is_anomaly_pred: isAnomaly,
    root_cause: rootCause,
    explanation: explanation
  };
});
