import numpy as np
import pandas as pd
from typing import Dict, List, Optional

STATION_PROFILES = [
    {"station_id": "AWS_DELHI_01", "region": "Plains", "lat": 28.6139, "lon": 77.2090, "base_temp": 28.0, "temp_amp": 8.0, "base_press": 1008.0, "base_rh": 55.0},
    {"station_id": "AWS_DELHI_02", "region": "Plains", "lat": 28.7041, "lon": 77.1025, "base_temp": 27.8, "temp_amp": 7.8, "base_press": 1008.5, "base_rh": 57.0},
    {"station_id": "AWS_GURUGRAM_01", "region": "Plains", "lat": 28.4595, "lon": 77.0266, "base_temp": 28.5, "temp_amp": 8.2, "base_press": 1007.8, "base_rh": 53.0},
    {"station_id": "AWS_NOIDA_01", "region": "Plains", "lat": 28.5355, "lon": 77.3910, "base_temp": 28.2, "temp_amp": 7.9, "base_press": 1008.2, "base_rh": 56.0},
    {"station_id": "AWS_SHIMLA_01", "region": "Hilly", "lat": 31.1048, "lon": 77.1734, "base_temp": 16.0, "temp_amp": 5.0, "base_press": 880.0, "base_rh": 65.0},
    {"station_id": "AWS_MUMBAI_01", "region": "Coastal", "lat": 19.0760, "lon": 72.8777, "base_temp": 30.0, "temp_amp": 4.0, "base_press": 1012.0, "base_rh": 78.0},
    {"station_id": "AWS_JAIPUR_01", "region": "Desert", "lat": 26.9124, "lon": 75.7873, "base_temp": 32.0, "temp_amp": 10.0, "base_press": 1004.0, "base_rh": 35.0},
]

def generate_synthetic_aws_data(
    num_days: int = 7,
    interval_minutes: int = 15,
    anomaly_prob: float = 0.015,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic multi-station AWS telemetry dataset with diurnal cycles,
    physically realistic temp-humidity inverse correlations, and injected sensor faults.
    """
    np.random.seed(seed)
    timestamps = pd.date_range(start="2026-08-01 00:00", periods=num_days * (1440 // interval_minutes), freq=f"{interval_minutes}min")

    records = []

    for profile in STATION_PROFILES:
        n = len(timestamps)

        # Diurnal thermal phase (peak at 14:00 PM) - convert to float numpy array
        hours = np.array(timestamps.hour + timestamps.minute / 60.0, dtype=float)
        diurnal = np.sin((hours - 8.0) * (2 * np.pi / 24.0))

        # Base physical signals as numpy float arrays
        temp = np.array(profile["base_temp"] + profile["temp_amp"] * diurnal + np.random.normal(0, 0.4, n), dtype=float)

        # Relative Humidity inverse correlation (-0.5 to -0.6 with temp)
        rh = np.array(profile["base_rh"] - 1.8 * profile["temp_amp"] * diurnal + np.random.normal(0, 1.2, n), dtype=float)
        rh = np.clip(rh, 15.0, 98.0)

        # Barometric pressure (small diurnal tide + noise)
        press = np.array(profile["base_press"] + 0.8 * np.cos(hours * (4 * np.pi / 24.0)) + np.random.normal(0, 0.3, n), dtype=float)

        is_anomaly = np.zeros(n, dtype=int)
        anomaly_type = np.array(["none"] * n, dtype=object)

        # Inject specific anomalies
        i = 0
        while i < n:
            if np.random.rand() < anomaly_prob:
                atype = np.random.choice(["spike", "frozen_value", "calibration_drift", "comm_loss", "noise_burst"])
                if atype == "spike":
                    temp[i] += float(np.random.choice([25.0, -20.0])) # e.g., 55°C spike
                    is_anomaly[i] = 1
                    anomaly_type[i] = "spike"
                    i += 1
                elif atype == "frozen_value" and i + 12 < n:
                    temp[i:i+12] = float(temp[i])
                    is_anomaly[i:i+12] = 1
                    for k in range(i, i+12):
                        anomaly_type[k] = "frozen_value"
                    i += 12
                elif atype == "calibration_drift" and i + 24 < n:
                    drift = np.linspace(0, 12.0, 24)
                    temp[i:i+24] += drift
                    is_anomaly[i:i+24] = 1
                    for k in range(i, i+24):
                        anomaly_type[k] = "calibration_drift"
                    i += 24
                elif atype == "comm_loss" and i + 4 < n:
                    temp[i:i+4] = np.nan
                    press[i:i+4] = np.nan
                    rh[i:i+4] = np.nan
                    is_anomaly[i:i+4] = 1
                    for k in range(i, i+4):
                        anomaly_type[k] = "comm_loss"
                    i += 4
                elif atype == "noise_burst" and i + 8 < n:
                    temp[i:i+8] += np.random.normal(0, 8.0, 8)
                    press[i:i+8] += np.random.normal(0, 15.0, 8)
                    is_anomaly[i:i+8] = 1
                    for k in range(i, i+8):
                        anomaly_type[k] = "noise_burst"
                    i += 8
                else:
                    i += 1
            else:
                i += 1

        st_df = pd.DataFrame({
            "timestamp": timestamps,
            "station_id": profile["station_id"],
            "region": profile["region"],
            "lat": profile["lat"],
            "lon": profile["lon"],
            "temperature_C": np.round(temp, 2),
            "pressure_hPa": np.round(press, 2),
            "humidity_pct": np.round(rh, 2),
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type
        })
        records.append(st_df)

    final_df = pd.concat(records, ignore_index=True)
    return final_df

if __name__ == "__main__":
    df = generate_synthetic_aws_data(num_days=3)
    df.to_csv("data/raw/synthetic_aws_telemetry.csv", index=False)
    print(f"Successfully generated {len(df)} telemetry rows across {df['station_id'].nunique()} stations.")
