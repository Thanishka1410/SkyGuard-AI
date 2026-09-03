import pytest
import pandas as pd
import numpy as np
from src.models.spatial import SpatialAnomalyDetector

def test_spatial_ps_example_55c_spike():
    detector = SpatialAnomalyDetector(k_neighbors=3)

    # 4 stations close to each other in Delhi region
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-08-01 12:00")] * 4,
        "station_id": ["AWS_DELHI_01", "AWS_DELHI_02", "AWS_GURUGRAM_01", "AWS_NOIDA_01"],
        "region": ["Plains"] * 4,
        "lat": [28.6139, 28.7041, 28.4595, 28.5355],
        "lon": [77.2090, 77.1025, 77.0266, 77.3910],
        "temperature_C": [55.0, 30.0, 29.5, 30.2],  # AWS_DELHI_01 reports 55°C, neighbors report ~30°C
        "pressure_hPa": [1008.0, 1008.1, 1007.9, 1008.2],
        "humidity_pct": [50.0, 52.0, 49.0, 51.0]
    })

    res = detector.compute_spatial_interpolations(df)

    # AWS_DELHI_01 should have expected temp ~30°C and high spatial score
    st1 = res[res["station_id"] == "AWS_DELHI_01"].iloc[0]
    assert st1["spatial_expected_temp"] < 32.0
    assert st1["spatial_expected_temp"] > 28.0
    assert st1["spatial_score"] > 0.8
    assert "Expected T: 30." in st1["spatial_details"] or "vs Actual: 55.0°C" in st1["spatial_details"]

def test_spatial_weather_event_neighbors_agree():
    detector = SpatialAnomalyDetector(k_neighbors=3)

    # All stations experience a heatwave / temperature jump simultaneously (39°C - 40°C)
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-08-01 12:00")] * 4,
        "station_id": ["AWS_DELHI_01", "AWS_DELHI_02", "AWS_GURUGRAM_01", "AWS_NOIDA_01"],
        "region": ["Plains"] * 4,
        "lat": [28.6139, 28.7041, 28.4595, 28.5355],
        "lon": [77.2090, 77.1025, 77.0266, 77.3910],
        "temperature_C": [39.8, 40.1, 39.5, 40.0],  # All stations agree
        "pressure_hPa": [1008.0, 1008.1, 1007.9, 1008.2],
        "humidity_pct": [50.0, 52.0, 49.0, 51.0]
    })

    res = detector.compute_spatial_interpolations(df)

    st1 = res[res["station_id"] == "AWS_DELHI_01"].iloc[0]
    # Small spatial disagreement since neighbors also report high temperature
    assert st1["spatial_score"] < 0.2
