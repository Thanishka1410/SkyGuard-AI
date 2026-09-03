import pytest
import pandas as pd
import numpy as np
from src.fusion import FusionEngine
from src.explain import ExplanationGenerator
from src.ingestion.generator import generate_synthetic_aws_data

def test_full_fusion_pipeline():
    df = generate_synthetic_aws_data(num_days=2, seed=42)
    engine = FusionEngine()
    processed_df = engine.process_pipeline(df, train_baseline=True)

    explainer = ExplanationGenerator()
    final_df = explainer.add_explanations_to_dataframe(processed_df)

    assert "is_anomaly_pred" in final_df.columns
    assert "root_cause" in final_df.columns
    assert "explanation" in final_df.columns
    assert "station_health_pct" in final_df.columns

    # Verify 55C spike PS example reproduction
    # Filter rows where a spike anomaly was injected
    spikes = final_df[final_df["anomaly_type"] == "spike"]
    assert len(spikes) > 0
    # Check that fusion pipeline flagged spike as anomaly
    detected_spikes = spikes[spikes["is_anomaly_pred"] == True]
    assert len(detected_spikes) > 0

    first_spike = detected_spikes.iloc[0]
    assert first_spike["root_cause"] == "spike"
    assert "SENSOR ANOMALY DETECTED" in first_spike["explanation"]
