import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

# 6 Representative Indian AWS Stations across Diverse Climate Zones
SIMULATED_STATION_PROFILES = [
    {
        "station_id": "AWS_MUMBAI_01",
        "region": "Coastal",
        "lat": 19.0760,
        "lon": 72.8777,
        "base_temp": 30.0,
        "temp_amp": 4.0,
        "base_press": 1012.0,
        "base_rh": 78.0
    },
    {
        "station_id": "AWS_CHENNAI_01",
        "region": "Coastal",
        "lat": 13.0827,
        "lon": 80.2707,
        "base_temp": 31.0,
        "temp_amp": 4.5,
        "base_press": 1010.0,
        "base_rh": 75.0
    },
    {
        "station_id": "AWS_DELHI_01",
        "region": "Plains",
        "lat": 28.6139,
        "lon": 77.2090,
        "base_temp": 28.0,
        "temp_amp": 8.0,
        "base_press": 1008.0,
        "base_rh": 55.0
    },
    {
        "station_id": "AWS_LUCKNOW_01",
        "region": "Plains",
        "lat": 26.8467,
        "lon": 80.9462,
        "base_temp": 27.0,
        "temp_amp": 8.5,
        "base_press": 1009.0,
        "base_rh": 60.0
    },
    {
        "station_id": "AWS_SHIMLA_01",
        "region": "Hilly",
        "lat": 31.1048,
        "lon": 77.1734,
        "base_temp": 16.0,
        "temp_amp": 5.0,
        "base_press": 880.0,
        "base_rh": 65.0
    },
    {
        "station_id": "AWS_JAISALMER_01",
        "region": "Desert",
        "lat": 26.9157,
        "lon": 70.9083,
        "base_temp": 33.0,
        "temp_amp": 11.0,
        "base_press": 1004.0,
        "base_rh": 30.0
    }
]


def generate_batch_dataset(
    days: int = 30,
    interval_minutes: int = 15,
    anomaly_prob: float = 0.015,
    output_path: Optional[str] = "data/simulated_aws_data.csv",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a full 30-day realistic multi-station AWS dataset.
    Schema: timestamp, station_id, region, lat, lon, temperature_C, pressure_hPa, humidity_pct, is_anomaly, anomaly_type
    """
    np.random.seed(seed)
    start_time = datetime(2026, 8, 1, 0, 0)
    total_periods = days * (1440 // interval_minutes)
    timestamps = [start_time + timedelta(minutes=i * interval_minutes) for i in range(total_periods)]

    records = []

    for profile in SIMULATED_STATION_PROFILES:
        n = len(timestamps)

        # Time components
        hours = np.array([ts.hour + ts.minute / 60.0 for ts in timestamps], dtype=float)
        day_indices = np.array([(ts - start_time).total_seconds() / 86400.0 for ts in timestamps], dtype=float)

        # Diurnal thermal phase (peak at 14:00 PM) + seasonal drift
        diurnal_temp = np.sin((hours - 8.0) * (2 * np.pi / 24.0))
        seasonal_drift = 1.5 * np.sin(day_indices * (2 * np.pi / 30.0))

        # Base Physical Signals
        temp = profile["base_temp"] + profile["temp_amp"] * diurnal_temp + seasonal_drift + np.random.normal(0, 0.4, n)

        # Inverse Temp-Humidity Correlation (r ≈ -0.55)
        rh = profile["base_rh"] - 1.8 * profile["temp_amp"] * diurnal_temp + np.random.normal(0, 1.2, n)
        rh = np.clip(rh, 10.0, 99.0)

        # Pressure (Semi-diurnal solar tide + multi-day weather wave)
        semi_tide = 0.8 * np.cos(hours * (4 * np.pi / 24.0))
        weather_wave = 3.0 * np.cos(day_indices * (2 * np.pi / 5.0))
        press = profile["base_press"] + semi_tide + weather_wave + np.random.normal(0, 0.3, n)

        is_anomaly = np.zeros(n, dtype=int)
        anomaly_type = np.array(["none"] * n, dtype=object)

        # Inject Faults
        i = 0
        while i < n:
            if np.random.rand() < anomaly_prob:
                atype = np.random.choice(["spike", "frozen_value", "calibration_drift", "comm_loss", "noise_burst"])
                if atype == "spike":
                    temp[i] += float(np.random.choice([25.0, -20.0]))
                    is_anomaly[i] = 1
                    anomaly_type[i] = "spike"
                    i += 1
                elif atype == "frozen_value" and i + 12 < n:
                    temp[i:i+12] = float(temp[i])
                    is_anomaly[i:i+12] = 1
                    anomaly_type[i:i+12] = "frozen_value"
                    i += 12
                elif atype == "calibration_drift" and i + 24 < n:
                    drift = np.linspace(0, 10.0, 24)
                    temp[i:i+24] += drift
                    is_anomaly[i:i+24] = 1
                    anomaly_type[i:i+24] = "calibration_drift"
                    i += 24
                elif atype == "comm_loss" and i + 4 < n:
                    # Communication Loss produces NaNs
                    temp[i:i+4] = np.nan
                    press[i:i+4] = np.nan
                    rh[i:i+4] = np.nan
                    is_anomaly[i:i+4] = 1
                    anomaly_type[i:i+4] = "comm_loss"
                    i += 4
                elif atype == "noise_burst" and i + 8 < n:
                    temp[i:i+8] += np.random.normal(0, 8.0, 8)
                    press[i:i+8] += np.random.normal(0, 15.0, 8)
                    is_anomaly[i:i+8] = 1
                    anomaly_type[i:i+8] = "noise_burst"
                    i += 8
                else:
                    i += 1
            else:
                i += 1

        st_df = pd.DataFrame({
            "timestamp": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
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

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_df.to_csv(output_path, index=False)
        print(f"[DataSimulator] Saved {len(final_df)} batch records to {output_path}")

    return final_df


class LiveSimulator:
    """
    Real-Time Interactive AWS Data Simulator for Live Judge Demonstration.
    Generates realistic 1-tick observations across all 6 stations and accepts
    operator fault injection overrides.
    """

    def __init__(self):
        self.profiles = SIMULATED_STATION_PROFILES
        self.current_time = datetime.now()
        self.tick_count = 0
        # Active fault overrides: { station_id: { "anomaly_type": str, "remaining_ticks": int, "base_val": float, "step": int } }
        self.active_faults: Dict[str, Dict[str, Any]] = {}

    def inject_anomaly(self, station_id: str, anomaly_type: str, duration_ticks: int = 10) -> Dict[str, Any]:
        """
        Operator / Judge triggered fault injection on demand.
        """
        valid_types = ["spike", "frozen_value", "calibration_drift", "comm_loss", "noise_burst"]
        if anomaly_type not in valid_types:
            raise ValueError(f"Invalid anomaly_type '{anomaly_type}'. Must be one of {valid_types}")

        self.active_faults[station_id] = {
            "anomaly_type": anomaly_type,
            "remaining_ticks": duration_ticks,
            "total_duration": duration_ticks,
            "step": 0,
            "frozen_val": None
        }
        print(f"[LiveSimulator] Injected fault '{anomaly_type}' on '{station_id}' for {duration_ticks} ticks.")
        return {
            "status": "success",
            "station_id": station_id,
            "anomaly_type": anomaly_type,
            "duration_ticks": duration_ticks
        }

    def tick(self) -> List[Dict[str, Any]]:
        """
        Generates 1 fresh reading per station for the current tick timestamp.
        Applies active fault overrides if present.
        """
        self.tick_count += 1
        self.current_time += timedelta(minutes=15)
        ts_str = self.current_time.strftime("%Y-%m-%d %H:%M:%S")

        hour = self.current_time.hour + self.current_time.minute / 60.0
        diurnal_temp = np.sin((hour - 8.0) * (2 * np.pi / 24.0))

        tick_records = []

        for profile in self.profiles:
            st_id = profile["station_id"]

            # Base realistic weather signals
            raw_temp = profile["base_temp"] + profile["temp_amp"] * diurnal_temp + np.random.normal(0, 0.3)
            raw_rh = profile["base_rh"] - 1.8 * profile["temp_amp"] * diurnal_temp + np.random.normal(0, 1.0)
            raw_rh = float(np.clip(raw_rh, 10.0, 99.0))
            raw_press = profile["base_press"] + 0.8 * np.cos(hour * (4 * np.pi / 24.0)) + np.random.normal(0, 0.2)

            is_anom = 0
            anom_type = "none"

            # Check if station has active injected fault override
            if st_id in self.active_faults:
                fault_info = self.active_faults[st_id]
                atype = fault_info["anomaly_type"]
                rem = fault_info["remaining_ticks"]
                step = fault_info["step"]

                is_anom = 1
                anom_type = atype

                if atype == "spike":
                    raw_temp += 24.5  # Sudden 50°C+ thermal jump
                elif atype == "frozen_value":
                    if fault_info["frozen_val"] is None:
                        fault_info["frozen_val"] = round(raw_temp, 2)
                    raw_temp = fault_info["frozen_val"]
                elif atype == "calibration_drift":
                    drift_offset = (step / max(1, fault_info["total_duration"])) * 12.0
                    raw_temp += drift_offset
                elif atype == "comm_loss":
                    raw_temp = np.nan
                    raw_press = np.nan
                    raw_rh = np.nan
                elif atype == "noise_burst":
                    raw_temp += float(np.random.normal(0, 7.5))
                    raw_press += float(np.random.normal(0, 12.0))

                # Decrement remaining fault ticks
                fault_info["remaining_ticks"] -= 1
                fault_info["step"] += 1
                if fault_info["remaining_ticks"] <= 0:
                    del self.active_faults[st_id]

            rec = {
                "timestamp": ts_str,
                "station_id": st_id,
                "region": profile["region"],
                "lat": profile["lat"],
                "lon": profile["lon"],
                "temperature_C": round(float(raw_temp), 2) if not np.isnan(raw_temp) else None,
                "pressure_hPa": round(float(raw_press), 2) if not np.isnan(raw_press) else None,
                "humidity_pct": round(float(raw_rh), 2) if not np.isnan(raw_rh) else None,
                "is_anomaly": is_anom,
                "anomaly_type": anom_type
            }
            tick_records.append(rec)

        return tick_records


if __name__ == "__main__":
    df_batch = generate_batch_dataset(days=30)
    print(f"Batch dataset generated: {len(df_batch)} rows across {df_batch['station_id'].nunique()} stations.")

    sim = LiveSimulator()
    sim.inject_anomaly("AWS_DELHI_01", "spike", duration_ticks=3)
    t1 = sim.tick()
    print("Sample Live Tick 1 (Delhi Spike Injected):", t1[2])
