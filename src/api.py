from fastapi import FastAPI, Query, Response, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
import os
import sys
import threading
import time
from typing import Dict, Any, Optional

# Ensure root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.loader import AWSDataLoader
from src.ingestion.generator import generate_synthetic_aws_data
from src.data_simulator import generate_batch_dataset, LiveSimulator
from src.fusion import FusionEngine
from src.explain import ExplanationGenerator

app = FastAPI(
    title="SkyGuard AI REST API & Live Demo Engine",
    description="Backend Service & Real-Time Fault Injection Simulator for AWS Anomaly Detection (MoES / SIH PS 26073)",
    version="2.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

loader = AWSDataLoader()
engine = FusionEngine()
explainer = ExplanationGenerator()
live_simulator = LiveSimulator()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIMULATED_DATA_PATH = os.path.join(BASE_DIR, "data", "simulated_aws_data.csv")
SYNTHETIC_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "synthetic_aws_telemetry.csv")
REAL_CLEANED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "mpi_jena_cleaned.csv")
REAL_RAW_DATA_PATH = os.path.join(BASE_DIR, "max_planck_weather_ts.csv")

# Pre-serialized JSON string cache for instantaneous (<10ms) batch dataset switching
JSON_CACHE = {}

# Rolling buffer for real-time Live Demo simulation mode (stores last 200 tick observations)
LIVE_TELEMETRY_BUFFER: list = []
LIVE_LOCK = threading.Lock()


def get_serialized_dataset_cached(dataset_key: str) -> str:
    """
    Computes 3-layer anomaly pipeline once and serializes JSON payload into memory.
    """
    if dataset_key in JSON_CACHE:
        return JSON_CACHE[dataset_key]

    if dataset_key == "simulated":
        if os.path.exists(SIMULATED_DATA_PATH):
            df = loader.load_data(SIMULATED_DATA_PATH)
            df = df.iloc[:2000].copy()
        elif os.path.exists(SYNTHETIC_DATA_PATH):
            df = loader.load_data(SYNTHETIC_DATA_PATH)
        else:
            df = generate_batch_dataset(days=3)
    else:
        if not os.path.exists(REAL_CLEANED_DATA_PATH):
            df = loader.clean_max_planck_dataset(REAL_RAW_DATA_PATH, REAL_CLEANED_DATA_PATH)
        else:
            df = loader.load_data(REAL_CLEANED_DATA_PATH)
        df = df.iloc[:1000].copy()

    processed_df = engine.process_pipeline(df, train_baseline=True)
    final_df = explainer.add_explanations_to_dataframe(processed_df)

    stations = final_df[['station_id', 'region', 'lat', 'lon', 'station_health_pct']].drop_duplicates('station_id').to_dict(orient='records')

    # Fast JSON string serialization
    telemetry_records = final_df.to_dict(orient='records')
    for rec in telemetry_records:
        if isinstance(rec.get('timestamp'), (pd.Timestamp, np.datetime64)):
            rec['timestamp'] = str(rec['timestamp'])

    payload_dict = {
        "dataset": dataset_key,
        "total": len(final_df),
        "stations": stations,
        "telemetry": telemetry_records
    }

    json_bytes = json.dumps(payload_dict, default=str)
    JSON_CACHE[dataset_key] = json_bytes
    return json_bytes


def live_simulation_worker():
    """
    Background worker thread running LiveSimulator.tick() every 1.5 seconds.
    Processes live ticks through 3-layer pipeline + fusion engine.
    """
    print("[SkyGuard AI Live Worker] Real-Time Live Demo Simulation Thread Started.")
    # Initialize baseline buffer
    initial_ticks = []
    for _ in range(8):
        initial_ticks.extend(live_simulator.tick())
    
    df_init = pd.DataFrame(initial_ticks)
    proc_init = engine.process_pipeline(df_init, train_baseline=True)
    final_init = explainer.add_explanations_to_dataframe(proc_init)
    
    with LIVE_LOCK:
        LIVE_TELEMETRY_BUFFER.clear()
        LIVE_TELEMETRY_BUFFER.extend(final_init.to_dict(orient='records'))

    while True:
        try:
            time.sleep(1.5)
            new_tick = live_simulator.tick()
            tick_df = pd.DataFrame(new_tick)

            # Pass tick through 3-layer fusion engine
            processed_tick = engine.process_pipeline(tick_df, train_baseline=False)
            explained_tick = explainer.add_explanations_to_dataframe(processed_tick)

            records = explained_tick.to_dict(orient='records')
            for r in records:
                if isinstance(r.get('timestamp'), (pd.Timestamp, np.datetime64)):
                    r['timestamp'] = str(r['timestamp'])

            with LIVE_LOCK:
                LIVE_TELEMETRY_BUFFER.extend(records)
                if len(LIVE_TELEMETRY_BUFFER) > 200:
                    del LIVE_TELEMETRY_BUFFER[:-200]

        except Exception as e:
            print(f"[SkyGuard AI Live Worker Error]: {e}")
            time.sleep(2)


@app.on_event("startup")
def preload_cache_and_start_live_worker():
    """
    Launches background live simulator and async cache pre-warmer.
    """
    t = threading.Thread(target=live_simulation_worker, daemon=True)
    t.start()
    print("[SkyGuard AI API] Live Simulator background thread running.")


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "SkyGuard AI",
        "ps_id": "SIH_26073",
        "live_demo_active": True,
        "cached_datasets": list(JSON_CACHE.keys())
    }


@app.get("/api/telemetry")
def get_telemetry(dataset: str = Query("simulated")):
    if dataset == "live":
        return get_live_telemetry()

    dataset_key = "maxplanck" if dataset in ["maxplanck", "Max Planck Institute Real Weather Dataset (Unlabelled)"] else "simulated"
    json_data = get_serialized_dataset_cached(dataset_key)
    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/api/live/telemetry")
def get_live_telemetry():
    """
    Returns rolling real-time live telemetry stream buffer processed through 3-layer fusion engine.
    """
    with LIVE_LOCK:
        records = list(LIVE_TELEMETRY_BUFFER)

    if not records:
        return {"dataset": "live", "total": 0, "stations": [], "telemetry": []}

    df = pd.DataFrame(records)
    stations = df[['station_id', 'region', 'lat', 'lon', 'station_health_pct']].drop_duplicates('station_id').to_dict(orient='records')

    payload = {
        "dataset": "live",
        "total": len(records),
        "stations": stations,
        "telemetry": records
    }
    return Response(
        content=json.dumps(payload, default=str),
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.post("/api/demo/inject")
@app.post("/demo/inject")
def inject_fault_demo(payload: Dict[str, Any] = Body(...)):
    """
    On-demand fault injection endpoint for live judge demonstrations.
    Accepts: { "station_id": str, "anomaly_type": str, "duration_ticks": int }
    """
    station_id = payload.get("station_id")
    anomaly_type = payload.get("anomaly_type")
    duration_ticks = payload.get("duration_ticks", 10)

    if not station_id or not anomaly_type:
        raise HTTPException(status_code=400, detail="Parameters 'station_id' and 'anomaly_type' are required.")

    try:
        res = live_simulator.inject_anomaly(
            station_id=station_id,
            anomaly_type=anomaly_type,
            duration_ticks=int(duration_ticks)
        )
        return {
            "success": True,
            "message": f"Injected '{anomaly_type}' fault on station '{station_id}' for {duration_ticks} ticks.",
            "details": res
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
