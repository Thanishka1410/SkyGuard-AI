import os
import sys
import pandas as pd

from src.ingestion.loader import AWSDataLoader
from src.ingestion.generator import generate_synthetic_aws_data
from src.fusion import FusionEngine
from src.explain import ExplanationGenerator

def main():
    print("=" * 75)
    print("  SkyGuard AI: Intelligent Anomaly Detection System for AWS (SIH PS 26073)")
    print("  Ministry of Earth Sciences (MoES) / India Meteorological Department")
    print("=" * 75)

    loader = AWSDataLoader()
    engine = FusionEngine()
    explainer = ExplanationGenerator()

    # --- PART 1: Simulated Multi-Station Network ---
    print("\n[PART 1] Running 3-Layer Pipeline on Simulated Multi-Station Telemetry...")
    syn_file = "data/raw/synthetic_aws_telemetry.csv"
    if not os.path.exists(syn_file):
        df_syn = generate_synthetic_aws_data(num_days=3)
        df_syn.to_csv(syn_file, index=False)
    else:
        df_syn = loader.load_data(syn_file)

    processed_syn = engine.process_pipeline(df_syn, train_baseline=True)
    final_syn = explainer.add_explanations_to_dataframe(processed_syn)

    total_syn = len(final_syn)
    anom_syn = final_syn['is_anomaly_pred'].sum()
    print(f"  Total Telemetry Records Processed : {total_syn}")
    print(f"  Detected Sensor Fault Anomalies    : {anom_syn} ({anom_syn/total_syn*100:.2f}%)")
    print(f"  Average Station Health Index       : {final_syn['station_health_pct'].mean():.1f}%")
    print("\n  Root Cause Classification Breakdown:")
    for cause, count in final_syn['root_cause'].value_counts().items():
        print(f"    - {cause:20s}: {count:5d} ({count/total_syn*100:5.2f}%)")

    # Sample alert printing
    print("\n  Sample Detected Anomaly Alerts & Explanations:")
    alerts = final_syn[final_syn['is_anomaly_pred']].head(3)
    for idx, row in alerts.iterrows():
        print(f"    - {row['explanation']}")

    # --- PART 2: Real Single-Station Dataset (Max Planck Institute Weather) ---
    real_file = "max_planck_weather_ts.csv"
    if os.path.exists(real_file):
        print("\n[PART 2] Running 3-Layer Pipeline on Real Unlabelled Max Planck Dataset...")
        cleaned_real_file = "data/processed/mpi_jena_cleaned.csv"
        if not os.path.exists(cleaned_real_file):
            df_real = loader.clean_max_planck_dataset(real_file, cleaned_real_file)
        else:
            df_real = loader.load_data(cleaned_real_file)

        # Process first 5,000 rows for demonstration
        sample_real = df_real.iloc[:5000].copy()
        processed_real = engine.process_pipeline(sample_real, train_baseline=True)
        final_real = explainer.add_explanations_to_dataframe(processed_real)

        print(f"  Processed {len(final_real)} Unlabelled Real Records.")
        anom_real = final_real['is_anomaly_pred'].sum()
        print(f"  Physics & Temporal Layer Flagged   : {anom_real} data-quality anomalies ({anom_real/len(final_real)*100:.2f}%)")
        if anom_real > 0:
            print("  Sample Real-World Anomaly Explanation:")
            real_alert = final_real[final_real['is_anomaly_pred']].iloc[0]
            print(f"    - {real_alert['explanation']}")

    print("\n" + "=" * 70)
    print("  Pipeline execution complete!")
    print("  To launch the interactive dashboard, run:")
    print("  streamlit run dashboard/app.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
