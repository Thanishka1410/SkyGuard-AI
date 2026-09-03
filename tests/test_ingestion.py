import os
import pytest
import pandas as pd
from src.ingestion.loader import AWSDataLoader
from src.ingestion.generator import generate_synthetic_aws_data

def test_synthetic_data_generation():
    df = generate_synthetic_aws_data(num_days=1, interval_minutes=15, seed=42)
    assert not df.empty
    assert "temperature_C" in df.columns
    assert "station_id" in df.columns
    assert df["station_id"].nunique() == 7

def test_data_loader(tmp_path):
    df_gen = generate_synthetic_aws_data(num_days=1, interval_minutes=15, seed=42)
    file_path = tmp_path / "test_telemetry.csv"
    df_gen.to_csv(file_path, index=False)

    loader = AWSDataLoader()
    df = loader.load_data(str(file_path))
    assert len(df) == len(df_gen)

    meta = loader.extract_station_metadata(df)
    assert len(meta) == 7

    dist = loader.calculate_distance_matrix(meta)
    assert dist.shape == (7, 7)
    assert dist.iloc[0, 0] == 0.0
