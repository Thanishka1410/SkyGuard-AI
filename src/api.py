from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
import os
import sys

# Ensure root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.loader import AWSDataLoader
from src.ingestion.generator import generate_synthetic_aws_data
from src.fusion import FusionEngine
from src.explain import ExplanationGenerator

app = FastAPI(
    title="SkyGuard AI REST API",
    description="Backend Service for Intelligent AWS Anomaly Detection (MoES / SIH PS 26073)",
    version="1.0.0"
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTHETIC_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "synthetic_aws_telemetry.csv")
REAL_CLEANED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "mpi_jena_cleaned.csv")
REAL_RAW_DATA_PATH = os.path.join(BASE_DIR, "max_planck_weather_ts.csv")

# Pre-serialized JSON string cache for instantaneous (<10ms) dataset switching
JSON_CACHE = {}

def get_serialized_dataset_cached(dataset_key: str) -> str:
    """
    Computes 3-layer anomaly pipeline once and serializes JSON payload into memory.
    """
    if dataset_key in JSON_CACHE:
        return JSON_CACHE[dataset_key]

    if dataset_key == "simulated":
        if os.path.exists(SYNTHETIC_DATA_PATH):
            df = loader.load_data(SYNTHETIC_DATA_PATH)
        else:
            df = generate_synthetic_aws_data(num_days=3)
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

@app.on_event("startup")
def preload_cache():
    """
    Pre-warms in-memory serialized dataset cache during server launch.
    """
    print("[SkyGuard AI API] Pre-warming serialized dataset cache for instant UI dataset switching...")
    get_serialized_dataset_cached("simulated")
    get_serialized_dataset_cached("maxplanck")
    print("[SkyGuard AI API] Cache pre-warming complete! Dataset switching response is sub-10ms.")

@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "SkyGuard AI", "ps_id": "SIH_26073", "cached_datasets": list(JSON_CACHE.keys())}

@app.get("/api/telemetry")
def get_telemetry(dataset: str = Query("simulated")):
    dataset_key = "maxplanck" if dataset in ["maxplanck", "Max Planck Institute Real Weather Dataset (Unlabelled)"] else "simulated"
    json_data = get_serialized_dataset_cached(dataset_key)
    return Response(content=json_data, media_type="application/json")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
