import pytest
import pandas as pd
import numpy as np
from src.models.physics import PhysicsAnomalyDetector

def test_dew_point_calculation():
    detector = PhysicsAnomalyDetector()
    tdew = detector.calculate_dew_point(30.0, 70.0)
    assert not pd.isna(tdew)
    assert tdew < 30.0
    assert tdew > 20.0  # At 30C, 70% RH, Tdew ~ 23.9C

def test_physics_dew_point_exceeded():
    detector = PhysicsAnomalyDetector()
    # Impossible state: Tair=20C, RH=150% (or Tdew higher than Tair)
    score, viols = detector.analyze_record(temp=20.0, press=1013.0, rh=110.0)
    assert score > 0.0
    assert any("PHYSICS_RH_OUT_OF_RANGE" in v for v in viols)

def test_physics_spike_gradient():
    detector = PhysicsAnomalyDetector()
    score, viols = detector.analyze_record(temp=45.0, press=1013.0, rh=50.0, prev_temp=25.0)
    assert score > 0.0
    assert any("PHYSICS_TEMP_GRADIENT_EXCEEDED" in v for v in viols)

def test_physics_frozen_sensor():
    detector = PhysicsAnomalyDetector()
    history = [25.0] * 8
    score, viols = detector.analyze_record(temp=25.0, press=1013.0, rh=50.0, temp_history=history)
    assert score > 0.0
    assert any("PHYSICS_FROZEN_SENSOR" in v for v in viols)

def test_physics_dataframe_detection():
    detector = PhysicsAnomalyDetector()
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-08-01", periods=10, freq="15min"),
        "station_id": ["AWS_01"] * 10,
        "region": ["Plains"] * 10,
        "lat": [28.6] * 10,
        "lon": [77.2] * 10,
        "temperature_C": [25.0, 25.2, 25.1, 55.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0],
        "pressure_hPa": [1010.0] * 10,
        "humidity_pct": [60.0] * 10
    })
    res = detector.detect_dataframe(df)
    assert "physics_score" in res.columns
    assert res.loc[3, "physics_score"] > 0.0  # 55°C spike flagged
