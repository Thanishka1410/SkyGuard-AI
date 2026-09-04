import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pyod.models.iforest import IForest

class TemporalAnomalyLayer:
    """
    Temporal Anomaly Detection Layer using Station-Specific Isolation Forest ML models.
    Learns per-station historical diurnal thermal cycle and flags baseline temporal deviations.
    """

    def __init__(self, contamination: float = 0.03):
        self.contamination = contamination
        self.models: Dict[str, IForest] = {}

    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extracts temporal and physical delta features for Isolation Forest.
        """
        ts = pd.to_datetime(df['timestamp'])
        hour = ts.dt.hour + ts.dt.minute / 60.0

        # Sinusoidal hour encoding for smooth 24-hour periodicity
        sin_hour = np.sin(2 * np.pi * hour / 24.0)
        cos_hour = np.cos(2 * np.pi * hour / 24.0)

        # Primary physical signals with NaN imputation fallback
        temp = df['temperature_C'].fillna(df['temperature_C'].median()).values
        press = df['pressure_hPa'].fillna(df['pressure_hPa'].median()).values
        rh = df['humidity_pct'].fillna(df['humidity_pct'].median()).values

        # First-order rate-of-change deltas
        temp_diff = np.concatenate([[0], np.diff(temp)])

        X = np.column_stack([sin_hour, cos_hour, temp, press, rh, temp_diff])
        return X

    def fit(self, df: pd.DataFrame):
        """
        Trains independent Isolation Forest models for each station.
        """
        for station_id, group in df.groupby('station_id'):
            if len(group) < 10:
                continue
            X = self.extract_features(group)
            model = IForest(
                contamination=self.contamination,
                n_estimators=50,
                random_state=42,
                n_jobs=1
            )
            model.fit(X)
            self.models[station_id] = model

    def predict_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predicts normalized anomaly score [0.0, 1.0] for each station.
        Adds 'temporal_score' column.
        """
        df = df.copy()
        temporal_scores = pd.Series(0.0, index=df.index)

        for station_id, group in df.groupby('station_id'):
            idx = group.index
            X = self.extract_features(group)

            if station_id in self.models:
                model = self.models[station_id]
                # PyOD decision_function gives anomaly scores
                raw_scores = model.decision_function(X)
                # Min-max scale or sigmoid normalize raw scores into [0, 1]
                p95 = np.percentile(raw_scores, 95) if len(raw_scores) > 1 else 1.0
                p05 = np.percentile(raw_scores, 5) if len(raw_scores) > 1 else 0.0
                denom = max(1e-5, p95 - p05)
                norm_scores = np.clip((raw_scores - p05) / denom, 0.0, 1.0)
                temporal_scores.loc[idx] = norm_scores
            else:
                # Fallback rolling z-score if un-fitted
                t = group['temperature_C'].values
                t_mean = np.nanmean(t)
                t_std = max(1e-3, np.nanstd(t))
                z = np.abs((t - t_mean) / t_std)
                temporal_scores.loc[idx] = np.clip(z / 4.0, 0.0, 1.0)

        df['temporal_score'] = np.round(temporal_scores.values, 3)
        return df

# Alias for backward compatibility
TemporalAnomalyDetector = TemporalAnomalyLayer
