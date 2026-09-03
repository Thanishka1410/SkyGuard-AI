import pytest
import pandas as pd
import numpy as np
from src.models.temporal import TemporalAnomalyDetector
from src.ingestion.generator import generate_synthetic_aws_data

def test_temporal_detector():
    df = generate_synthetic_aws_data(num_days=3, seed=42)
    detector = TemporalAnomalyDetector(contamination=0.05)
    detector.fit(df)
    res = detector.predict_score(df)

    assert "temporal_score" in res.columns
    assert res["temporal_score"].max() <= 1.0
    assert res["temporal_score"].min() >= 0.0

    # Ensure spike anomalies score high on temporal baseline
    spikes = res[res["anomaly_type"] == "spike"]
    assert len(spikes) > 0
    assert spikes["temporal_score"].mean() > 0.5
