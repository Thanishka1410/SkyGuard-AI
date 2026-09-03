import pandas as pd
import numpy as np
from typing import Tuple, Dict
from geopy.distance import geodesic

REQUIRED_COLUMNS = [
    'timestamp', 'station_id', 'region', 'lat', 'lon',
    'temperature_C', 'pressure_hPa', 'humidity_pct'
]

class AWSDataLoader:
    """
    Data loading, schema validation, and metadata extraction for AWS telemetry datasets.
    """

    def __init__(self):
        pass

    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validates that input DataFrame contains all required AWS columns.
        """
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {missing_cols}"
        return True, "Schema valid"

    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Loads CSV file, parses timestamps, validates schema, and returns formatted DataFrame.
        """
        df = pd.read_csv(filepath)
        is_valid, msg = self.validate_schema(df)
        if not is_valid:
            raise ValueError(msg)

        # Parse timestamps and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by=['station_id', 'timestamp']).reset_index(drop=True)

        # Enforce numeric types
        numeric_cols = ['lat', 'lon', 'temperature_C', 'pressure_hPa', 'humidity_pct']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def extract_station_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts unique station metadata (station_id, region, lat, lon).
        """
        meta = df[['station_id', 'region', 'lat', 'lon']].drop_duplicates(subset=['station_id']).reset_index(drop=True)
        return meta

    def calculate_distance_matrix(self, metadata_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates pairwise geodesic distance matrix (in km) between all stations.
        Symmetric optimization: computes upper triangle only to reduce distance calls.
        """
        stations = metadata_df['station_id'].tolist()
        coords = {row['station_id']: (row['lat'], row['lon']) for _, row in metadata_df.iterrows()}

        dist_matrix = pd.DataFrame(0.0, index=stations, columns=stations, dtype=float)
        n = len(stations)

        for i in range(n):
            s1 = stations[i]
            c1 = coords[s1]
            for j in range(i + 1, n):
                s2 = stations[j]
                d = geodesic(c1, coords[s2]).km
                dist_matrix.loc[s1, s2] = d
                dist_matrix.loc[s2, s1] = d

        return dist_matrix

    def clean_max_planck_dataset(
        self,
        input_path: str,
        output_path: str = "data/processed/mpi_jena_cleaned.csv",
        station_id: str = "AWS_MPI_JENA_01",
        region: str = "Central Europe",
        lat: float = 50.9271,
        lon: float = 11.5892
    ) -> pd.DataFrame:
        """
        Cleans the Max Planck Institute weather dataset and reformats it to standard AWS schema.
        Selects timestamp, temperature_C, pressure_hPa, humidity_pct.
        """
        df_raw = pd.read_csv(input_path)
        
        # Column mapping
        col_map = {
            'Date Time': 'timestamp',
            'T (degC)': 'temperature_C',
            'p (mbar)': 'pressure_hPa',
            'rh (%)': 'humidity_pct'
        }
        
        missing = [c for c in col_map.keys() if c not in df_raw.columns]
        if missing:
            raise ValueError(f"Max Planck dataset missing columns: {missing}")

        df_clean = df_raw[list(col_map.keys())].rename(columns=col_map).copy()
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
        df_clean = df_clean.dropna(subset=['timestamp'])
        
        df_clean['station_id'] = station_id
        df_clean['region'] = region
        df_clean['lat'] = lat
        df_clean['lon'] = lon

        # Reorder columns
        df_clean = df_clean[REQUIRED_COLUMNS]
        df_clean = df_clean.sort_values(by=['timestamp']).reset_index(drop=True)
        
        df_clean.to_csv(output_path, index=False)
        return df_clean

