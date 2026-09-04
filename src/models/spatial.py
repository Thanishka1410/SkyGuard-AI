import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from geopy.distance import geodesic

class SpatialFusionLayer:
    """
    Geodesic Spatial Fusion Layer using Inverse Distance Weighting (IDW).
    Compares target station reading with geographic k-NN neighbors.
    CRITICAL: Station location (lat, lon) is strictly restricted to neighbor distance lookup — ZERO FEATURE LEAKAGE.
    """

    def __init__(self, k_neighbors: int = 3, max_dist_km: float = 800.0, power: float = 2.0):
        self.k_neighbors = k_neighbors
        self.max_dist_km = max_dist_km
        self.power = power

    def _get_k_neighbors(
        self,
        target_station: str,
        target_coord: Tuple[float, float],
        active_stations: List[str],
        station_coords: Dict[str, Tuple[float, float]]
    ) -> List[Tuple[str, float]]:
        """
        Calculates Geodesic distances to active stations and returns k nearest neighbors within max_dist_km.
        """
        distances = []
        for st_id in active_stations:
            if st_id == target_station:
                continue
            coord = station_coords.get(st_id)
            if coord:
                dist_km = geodesic(target_coord, coord).km
                if dist_km <= self.max_dist_km:
                    distances.append((st_id, dist_km))

        # Sort by distance ascending
        distances.sort(key=lambda x: x[1])
        return distances[:self.k_neighbors]

    def _calculate_idw_estimates(
        self,
        neighbors: List[Tuple[str, float]],
        station_val_map: pd.DataFrame,
        target_temp: float,
        target_press: float,
        target_rh: float
    ) -> Tuple[float, float, float, float, str]:
        """
        Computes IDW weighted average expected signals from nearest neighbors.
        """
        if not neighbors:
            return np.nan, np.nan, np.nan, 0.0, "No spatial neighbors within distance threshold"

        weights = []
        temps = []
        pressures = []
        humidities = []

        for st_id, dist in neighbors:
            if st_id in station_val_map.index:
                st_data = station_val_map.loc[st_id]
                # Handle duplicated station entries if any
                if isinstance(st_data, pd.DataFrame):
                    st_data = st_data.iloc[0]

                t_val = st_data['temperature_C']
                p_val = st_data['pressure_hPa']
                rh_val = st_data['humidity_pct']

                if not np.isnan(t_val):
                    w = 1.0 / max(1e-3, dist ** self.power)
                    weights.append(w)
                    temps.append(t_val)
                    pressures.append(p_val if not np.isnan(p_val) else 1013.25)
                    humidities.append(rh_val if not np.isnan(rh_val) else 50.0)

        if not weights or sum(weights) == 0:
            return np.nan, np.nan, np.nan, 0.0, "Neighbors present but all readings missing/NaN"

        w_arr = np.array(weights)
        w_norm = w_arr / np.sum(w_arr)

        expected_temp = np.sum(w_norm * np.array(temps))
        expected_press = np.sum(w_norm * np.array(pressures))
        expected_rh = np.sum(w_norm * np.array(humidities))

        # Spatial Disagreement Residual Score
        if pd.isna(target_temp):
            spatial_score = 0.85  # High disagreement if target sensor drops out completely
        else:
            temp_diff = abs(target_temp - expected_temp)
            spatial_score = np.clip(temp_diff / 10.0, 0.0, 1.0)

        details = f"IDW interpolated from {len(temps)} neighbors (Expected T: {expected_temp:.1f}°C vs Actual T: {target_temp if not pd.isna(target_temp) else 'NaN'}°C)"

        return expected_temp, expected_press, expected_rh, float(spatial_score), details

    def compute_spatial_interpolations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes IDW neighbor-interpolated expected values and residual disagreement per timestamp.
        """
        df = df.copy()

        expected_t = pd.Series(np.nan, index=df.index)
        expected_p = pd.Series(np.nan, index=df.index)
        expected_rh = pd.Series(np.nan, index=df.index)
        spatial_scores = pd.Series(0.0, index=df.index)
        spatial_details = pd.Series("", index=df.index)

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

                expected_t.loc[row_idx] = exp_t
                expected_p.loc[row_idx] = exp_p
                expected_rh.loc[row_idx] = exp_rh
                spatial_scores.loc[row_idx] = score
                spatial_details.loc[row_idx] = details

        df['spatial_expected_temp'] = np.round(expected_t.values, 2)
        df['spatial_expected_press'] = np.round(expected_p.values, 2)
        df['spatial_expected_rh'] = np.round(expected_rh.values, 2)
        df['spatial_score'] = np.round(spatial_scores.values, 3)
        df['spatial_details'] = spatial_details.values

        return df

# Alias for backward compatibility
SpatialAnomalyDetector = SpatialFusionLayer
