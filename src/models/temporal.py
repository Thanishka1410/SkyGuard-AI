import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pyod.models.iforest import IForest
from pyod.models.ecod import ECOD

class TemporalAnomalyDetector:
    """
    Temporal Layer: Trains a per-station model (Isolation Forest / ECOD) on historical telemetry
    plus diurnal cycle features (sin/cos of hour of day) to learn station-specific normal patterns.
    Flags values that deviate from the station's own temporal baseline.
    """

    def __init__(self, contamination: float = 0.05, model_type: str = "iforest"):
        self.contamination = contamination
        self.model_type = model_type
        self.models: Dict[str, object] = {}

    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extracts temporal features: raw values + diurnal sin/cos encoding.
        """
        timestamps = pd.to_datetime(df['timestamp'])
        hours = timestamps.dt.hour + timestamps.dt.minute / 60.0

        sin_hour = np.sin(2 * np.pi * hours / 24.0)
        cos_hour = np.cos(2 * np.pi * hours / 24.0)

        t = df['temperature_C'].fillna(df['temperature_C'].median()).values
        p = df['pressure_hPa'].fillna(df['pressure_hPa'].median()).values
        h = df['humidity_pct'].fillna(df['humidity_pct'].median()).values

        X = np.column_stack([t, p, h, sin_hour, cos_hour])
        return X

    def fit(self, df: pd.DataFrame):
        """
        Fits a separate temporal model for each unique station in df.
        """
        for station_id, group in df.groupby('station_id'):
            X = self.extract_features(group)
            if len(X) < 10:
                continue

            if self.model_type == "iforest":
                model = IForest(contamination=self.contamination, random_state=42)
            else:
                model = ECOD(contamination=self.contamination)

            model.fit(X)
            self.models[station_id] = model

    def predict_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predicts normalized anomaly score [0.0, 1.0] for each station.
        Adds 'temporal_score' column.
        """
        df = df.copy()
        temporal_scores = np.zeros(len(df))

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
                temporal_scores[idx] = norm_scores
            else:
                # Fallback rolling z-score if un-fitted
                t = group['temperature_C'].values
                t_mean = np.nanmean(t)
                t_std = max(1e-3, np.nanstd(t))
                z = np.abs((t - t_mean) / t_std)
                temporal_scores[idx] = np.clip(z / 4.0, 0.0, 1.0)

        df['temporal_score'] = np.round(temporal_scores, 3)
        return df
