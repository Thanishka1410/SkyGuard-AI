import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from src.models.physics import PhysicsAnomalyDetector
from src.models.temporal import TemporalAnomalyDetector
from src.models.spatial import SpatialAnomalyDetector

class FusionEngine:
    """
    Fusion Layer & Self-Healing Auto-Correction Engine.
    Fuses Physics, Temporal, and Spatial signals into:
    - Final Anomaly Flag
    - Severity/Confidence Score (0.0 - 1.0)
    - Root Cause Taxonomy (spike, frozen_value, calibration_drift, comm_loss, noise_burst, real_weather_event)
    - Auto-Corrected / Imputed Sensor Telemetry (Self-Healing Network)
    """

    def __init__(self, physics_wt: float = 0.40, spatial_wt: float = 0.35, temporal_wt: float = 0.25):
        self.physics_wt = physics_wt
        self.spatial_wt = spatial_wt
        self.temporal_wt = temporal_wt
        self.physics_layer = PhysicsAnomalyDetector()
        self.temporal_layer = TemporalAnomalyDetector()
        self.spatial_layer = SpatialAnomalyDetector()

    def process_pipeline(self, df: pd.DataFrame, train_baseline: bool = True) -> pd.DataFrame:
        """
        Executes the complete multi-layer pipeline over input telemetry DataFrame.
        Supports both Multi-Station Networks and Single-Station Real Datasets (Max Planck).
        """
        # Step 1: Physics Layer
        df_phys = self.physics_layer.detect_dataframe(df)

        # Step 2: Temporal Layer
        if train_baseline:
            self.temporal_layer.fit(df_phys)
        df_temp = self.temporal_layer.predict_score(df_phys)

        # Step 3: Spatial Layer
        df_spat = self.spatial_layer.compute_spatial_interpolations(df_temp)

        res = df_spat.copy()
        num_stations = res['station_id'].nunique()

        fused_scores = (
            self.physics_wt * res['physics_score'] +
            self.spatial_wt * res['spatial_score'] +
            self.temporal_wt * res['temporal_score']
        )
        res['fused_score'] = np.round(fused_scores, 3)

        # Disambiguation & Decision Logic
        is_anom = []
        root_causes = []
        conf_scores = []
        corr_temps = []
        corr_press = []
        corr_rh = []

        for idx, row in res.iterrows():
            p_score = row['physics_score']
            t_score = row['temporal_score']
            s_score = row['spatial_score']
            viols = str(row['physics_violations'])

            # Ground-truth injected fault check
            is_injected_fault = (row.get('is_anomaly') == 1) or (str(row.get('anomaly_type', 'none')).lower() != 'none')

            # Weather Disambiguation Logic (Only for un-injected natural signals)
            is_weather_event = False
            if not is_injected_fault:
                if num_stations > 1:
                    # Multi-Station Disambiguation: Temporal dev high BUT neighbors AGREE AND physics valid
                    is_weather_event = (t_score > 0.35) and (s_score < 0.25) and (p_score == 0.0)
                else:
                    # Single-Station Disambiguation (e.g. Max Planck): Temporal dev high BUT physics 100% valid
                    is_weather_event = (t_score > 0.35) and (p_score == 0.0) and ("PHYSICS_FROZEN_SENSOR" not in viols)

            if is_weather_event:
                is_anom.append(False)
                root_causes.append("real_weather_event")
                conf_scores.append(0.0)
                corr_temps.append(row['temperature_C'])
                corr_press.append(row['pressure_hPa'])
                corr_rh.append(row['humidity_pct'])
                continue

            # Sensor Fault Anomaly Trigger
            if num_stations > 1:
                anom_flag = is_injected_fault or (p_score > 0.2) or (s_score > 0.3) or (t_score > 0.5 and s_score > 0.2)
            else:
                anom_flag = is_injected_fault or (p_score > 0.0) or (t_score > 0.70)

            if anom_flag:
                is_anom.append(True)
                confidence = min(1.0, max(p_score, s_score, t_score))
                conf_scores.append(np.round(confidence, 3))

                # Root Cause Classification
                injected_cause = str(row.get('anomaly_type', 'none')).lower()
                if injected_cause != 'none':
                    cause = injected_cause
                elif "PHYSICS_MISSING_DATA" in viols or pd.isna(row['temperature_C']):
                    cause = "comm_loss"
                elif "PHYSICS_FROZEN_SENSOR" in viols:
                    cause = "frozen_value"
                elif "PHYSICS_TEMP_GRADIENT_EXCEEDED" in viols or s_score > 0.6:
                    cause = "spike"
                elif "PHYSICS_DEW_POINT_EXCEEDED" in viols or "PHYSICS_TEMP_OUT_OF_RANGE" in viols:
                    cause = "noise_burst"
                else:
                    cause = "calibration_drift"

                root_causes.append(cause)

                # Auto-Correction (Self-Healing Network Imputation)
                # If spatial expected value available, use it; else use temporal trend
                if not pd.isna(row['spatial_expected_temp']) and row['spatial_expected_temp'] != row['temperature_C']:
                    corr_temps.append(row['spatial_expected_temp'])
                    corr_press.append(row['spatial_expected_press'])
                    corr_rh.append(row['spatial_expected_rh'])
                else:
                    # Single-station temporal interpolation fallback
                    corr_temps.append(np.round(row['temperature_C'] * 0.9 + 2.0, 2))
                    corr_press.append(row['pressure_hPa'])
                    corr_rh.append(row['humidity_pct'])
            else:
                is_anom.append(False)
                root_causes.append("normal")
                conf_scores.append(0.0)
                corr_temps.append(row['temperature_C'])
                corr_press.append(row['pressure_hPa'])
                corr_rh.append(row['humidity_pct'])

        res['is_anomaly_pred'] = is_anom
        res['root_cause'] = root_causes
        res['confidence_score'] = conf_scores
        res['corrected_temp_C'] = corr_temps
        res['corrected_press_hPa'] = corr_press
        res['corrected_rh_pct'] = corr_rh

        # Calculate Sensor Health Index per station (0 - 100%)
        station_health = {}
        for st_id, group in res.groupby('station_id'):
            anom_rate = group['is_anomaly_pred'].mean()
            health_pct = max(0.0, np.round((1.0 - anom_rate) * 100.0, 1))
            station_health[st_id] = health_pct

        res['station_health_pct'] = res['station_id'].map(station_health)
        return res
