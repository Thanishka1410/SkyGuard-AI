import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from geopy.distance import geodesic

class SpatialAnomalyDetector:
    """
    Spatial Layer: Uses lat/lon ONLY to determine geographic distance to neighbors (k-NN / IDW).
    Computes spatial expected values and measures residual disagreement between station telemetry
    and its surrounding neighbor network.

    Core Disambiguation Logic:
    - High Temporal Deviation + Neighbors DISAGREE -> Sensor Fault (Anomaly)
    - High Temporal Deviation + Neighbors AGREE    -> Real Extreme Weather Event (Not Anomaly)
    """

    def __init__(self, k_neighbors: int = 3, max_dist_km: float = 300.0, idw_power: float = 2.0):
        self.k_neighbors = k_neighbors
        self.max_dist_km = max_dist_km
        self.idw_power = idw_power

    def _get_k_neighbors(
        self,
        curr_st: str,
        curr_coord: Tuple[float, float],
        group_stations: List[str],
        station_coords: Dict[str, Tuple[float, float]]
    ) -> List[Tuple[str, float]]:
        """
        Finds k-nearest neighbors within max_dist_km. Guard clauses used to flatten loop nesting.
        """
        distances = []
        for other_st in group_stations:
            if other_st == curr_st:
                continue
            d = geodesic(curr_coord, station_coords[other_st]).km
            if d <= self.max_dist_km:
                distances.append((other_st, d))

        distances.sort(key=lambda x: x[1])
        return distances[:self.k_neighbors]

    def _calculate_idw_estimates(
        self,
        neighbors: List[Tuple[str, float]],
        station_val_map: pd.DataFrame,
        actual_t: float,
        actual_p: float,
        actual_rh: float
    ) -> Tuple[float, float, float, float, str]:
        """
        Calculates IDW expected values and spatial anomaly score for a station.
        """
        if not neighbors:
            return actual_t, actual_p, actual_rh, 0.0, "No active neighbors within range"

        weights = [1.0 / max(1e-2, dist ** self.idw_power) for _, dist in neighbors]
        sum_w = sum(weights)
        norm_weights = [w / sum_w for w in weights]

        n_temps = [station_val_map.loc[st, 'temperature_C'] for st, _ in neighbors]
        n_press = [station_val_map.loc[st, 'pressure_hPa'] for st, _ in neighbors]
        n_rh = [station_val_map.loc[st, 'humidity_pct'] for st, _ in neighbors]

        valid_t = [(val, w) for val, w in zip(n_temps, norm_weights) if not pd.isna(val)]
        valid_p = [(val, w) for val, w in zip(n_press, norm_weights) if not pd.isna(val)]
        valid_rh = [(val, w) for val, w in zip(n_rh, norm_weights) if not pd.isna(val)]

        exp_t = sum(v * w for v, w in valid_t) / sum(w for _, w in valid_t) if valid_t else actual_t
        exp_p = sum(v * w for v, w in valid_p) / sum(w for _, w in valid_p) if valid_p else actual_p
        exp_rh = sum(v * w for v, w in valid_rh) / sum(w for _, w in valid_rh) if valid_rh else actual_rh

        delta_t = abs(actual_t - exp_t) if not pd.isna(actual_t) else 10.0
        delta_p = abs(actual_p - exp_p) if not pd.isna(actual_p) else 15.0

        t_score = min(1.0, delta_t / 5.0)
        p_score = min(1.0, delta_p / 8.0)
        sp_score = max(t_score, p_score)

        neighbor_names = [st for st, _ in neighbors]
        detail_msg = f"Expected T: {exp_t:.1f}°C (vs Actual: {actual_t:.1f}°C, Delta={delta_t:.1f}°C) based on neighbors {neighbor_names}"

        return exp_t, exp_p, exp_rh, sp_score, detail_msg

    def compute_spatial_interpolations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes IDW neighbor-interpolated expected values and residual disagreement per timestamp.
        """
        df = df.copy()

        expected_t = np.zeros(len(df))
        expected_p = np.zeros(len(df))
        expected_rh = np.zeros(len(df))
        spatial_scores = np.zeros(len(df))
        spatial_details = [""] * len(df)

        stations_meta = df[['station_id', 'lat', 'lon']].drop_duplicates('station_id').set_index('station_id')
        station_coords = {st: (row['lat'], row['lon']) for st, row in stations_meta.iterrows()}

        for ts, group in df.groupby('timestamp'):
            group_stations = group['station_id'].tolist()
            if len(group_stations) <= 1:
                continue

            station_val_map = group.set_index('station_id')

            for row_idx in group.index:
                curr_st = df.loc[row_idx, 'station_id']
                curr_coord = station_coords[curr_st]

                neighbors = self._get_k_neighbors(curr_st, curr_coord, group_stations, station_coords)

                exp_t, exp_p, exp_rh, score, details = self._calculate_idw_estimates(
                    neighbors,
                    station_val_map,
                    df.loc[row_idx, 'temperature_C'],
                    df.loc[row_idx, 'pressure_hPa'],
                    df.loc[row_idx, 'humidity_pct']
                )

                expected_t[row_idx] = exp_t
                expected_p[row_idx] = exp_p
                expected_rh[row_idx] = exp_rh
                spatial_scores[row_idx] = score
                spatial_details[row_idx] = details

        df['spatial_expected_temp'] = np.round(expected_t, 2)
        df['spatial_expected_press'] = np.round(expected_p, 2)
        df['spatial_expected_rh'] = np.round(expected_rh, 2)
        df['spatial_score'] = np.round(spatial_scores, 3)
        df['spatial_details'] = spatial_details

        return df
