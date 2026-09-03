from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
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

@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "SkyGuard AI", "ps_id": "SIH_26073"}

@app.get("/api/telemetry")
def get_telemetry(dataset: str = Query("simulated")):
    if dataset == "simulated":
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
    telemetry_records = final_df.to_dict(orient='records')

    # Convert timestamps to ISO string format
    for rec in telemetry_records:
        if isinstance(rec.get('timestamp'), (pd.Timestamp, np.datetime64)):
            rec['timestamp'] = str(rec['timestamp'])

    return {
        "dataset": dataset,
        "total": len(final_df),
        "stations": stations,
        "telemetry": telemetry_records
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
