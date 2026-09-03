# 🛰️ SkyGuard AI: Intelligent Real-Time Anomaly Detection for AWS Networks

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](http://localhost:8501)
[![SIH PS 26073](https://img.shields.io/badge/SIH%202024-PS%2026073-green.svg)](https://www.sih.gov.in/)

**Target Agency**: Ministry of Earth Sciences (MoES) / India Meteorological Department (IMD)  
**Problem Statement 26073**: *AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations (AWS)*

---

## 📌 Executive Overview

Automatic Weather Stations (AWS) continuously record and transmit **Temperature (°C)**, **Atmospheric Pressure (hPa)**, and **Relative Humidity (%)**. Sensors in hostile field conditions suffer from spikes, frozen values, calibration drift, communication loss, and electrical noise. 

Standard single-variable thresholds generate excessive false alarms during genuine localized extreme weather events (heatwaves, cloudbursts, squalls). **SkyGuard AI** implements a **Decoupled 3-Layer Physics-Informed & Spatial Sensor Fusion Framework** with **Self-Healing Auto-Correction** that accurately distinguishes sensor anomalies from real weather events.

---

## 🏛️ 3-Layer Fusion Architecture

```
                              ┌─────────────────────────┐
                              │  AWS Sensor Telemetry   │
                              └────────────┬────────────┘
                                           │
             ┌─────────────────────────────┼─────────────────────────────┐
             ▼                             ▼                             ▼
  ┌────────────────────┐        ┌────────────────────┐        ┌────────────────────┐
  │   PHYSICS LAYER    │        │   TEMPORAL LAYER   │        │   SPATIAL LAYER    │
  │ (Multivariate Rules│        │  (Per-Station ML   │        │ (Geodesic k-NN IDW │
  │   Dew Point, Grad) │        │  Isolation Forest) │        │ Zero-Data-Leakage) │
  └──────────┬─────────┘        └──────────┬─────────┘        └──────────┬─────────┘
             │                             │                             │
             └─────────────────────────────┼─────────────────────────────┘
                                           ▼
                                ┌─────────────────────┐
                                │    FUSION LAYER     │
                                │ (Flag, Score, Cause)│
                                └──────────┬──────────┘
                                           │
                               ┌───────────┴───────────┐
                               ▼                       ▼
                     ┌──────────────────┐    ┌──────────────────┐
                     │ EXPLANATION GEN  │    │ AUTO-CORRECTION  │
                     │  (Audit Evidence)│    │  (Self-Healing)  │
                     └──────────────────┘    └──────────────────┘
```

1. **Physics & Multivariate Layer** (`src/models/physics.py`): Deterministic checks ($T_{dew} \le T_{air}$ via Magnus-Tetens formula, gradient rate-of-change, thermodynamic bounds).
2. **Temporal Per-Station Baseline** (`src/models/temporal.py`): Station-specific Isolation Forest learning historical diurnal rhythm with sine/cosine hour encoding.
3. **Geodesic Spatial Layer** (`src/models/spatial.py`): Geodesic distance matrices and Inverse Distance Weighting (IDW) interpolation among $k$-nearest neighbors. Location (`lat`/`lon`) is strictly restricted to neighbor distance lookup — **zero feature leakage**.
4. **Disambiguation Rule**:
   $$\text{Temporal Deviation} \uparrow \text{ AND Spatial Disagreement} \downarrow \longrightarrow \mathbf{\text{Real Severe Weather Event}}$$
5. **Self-Healing Auto-Correction** (`src/fusion.py`): Automatically replaces confirmed sensor faults with spatially expected values.
6. **ESP32 Edge AI MicroPython Guard** (`src/edge/esp32_guard.py`): Lightweight physics filter (<5KB) for low-power solar AWS microcontrollers.

---

## 📁 Repository Structure

```
SkyGuard-AI/
├── data/
│   ├── raw/
│   │   └── synthetic_aws_telemetry.csv  # 2,016 multi-station telemetry rows
│   └── processed/
│       └── mpi_jena_cleaned.csv         # Cleaned Max Planck weather dataset
├── src/
│   ├── ingestion/
│   │   ├── loader.py                    # Schema validator & distance matrix generator
│   │   └── generator.py                 # Multi-station AWS synthetic dataset generator
│   ├── models/
│   │   ├── physics.py                   # Layer 1: Thermodynamic & rate-of-change rules
│   │   ├── temporal.py                  # Layer 2: Per-station Isolation Forest ML
│   │   └── spatial.py                   # Layer 3: Geodesic k-NN IDW interpolation
│   ├── edge/
│   │   └── esp32_guard.py               # MicroPython C++ edge physics guard (<5KB)
│   ├── fusion.py                        # Layer 4: Signal fusion & self-healing imputation
│   └── explain.py                       # Layer 5: Explainability text generator
├── dashboard/
│   └── app.py                           # Interactive Streamlit Dashboard UI
├── tests/
│   ├── test_ingestion.py
│   ├── test_physics.py
│   ├── test_spatial.py
│   ├── test_temporal.py
│   └── test_fusion.py
├── docs/
│   ├── use_cases.md                     # Detailed system use cases
│   ├── code_review_and_roadmap.md       # Developer code review & technical roadmap
│   └── compliance_checklist.md          # SIH PS 26073 requirement compliance matrix
├── main.py                              # End-to-end command-line pipeline
└── requirements.txt
```

---

## ⚙️ Installation & Running

### 1. Clone Repository & Install Dependencies

```bash
git clone https://github.com/Thanishka1410/SkyGuard-AI.git
cd SkyGuard-AI
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
python -m pytest tests/
```

### 3. Execute End-to-End Pipeline

```bash
python main.py
```

### 4. Launch Interactive Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```
*Access the live dashboard in your web browser at `http://localhost:8501`*

---

## 🎯 Alignment with SIH Evaluation Criteria

| Criteria | Weight | Implementation |
| :--- | :---: | :--- |
| **Innovation & Novelty** | **25%** | Decoupled 3-layer signal fusion with weather vs anomaly spatial agreement disambiguation. |
| **Detection Accuracy** | **20%** | Zero false positives on physics impossibilities + station-specific Isolation Forest baselines. |
| **Real-Time Capability** | **15%** | Live Streamlit UI dashboard and optimized symmetric distance calculations. |
| **Explainability** | **10%** | Audit-proof text evidence generator detailing exact broken physics rules and neighbor deltas. |
| **Scalability** | **10%** | Ingestion module capable of scaling to IMD's 3,500+ AWS network stations. |
| **Practical Deployability** | **10%** | Clean modular architecture, unit test suite, and CLI entry point `main.py`. |
| **Visualization / UI** | **5%** | Multi-tab dashboard with interactive map, dual-trace plots, alert logs, and pie charts. |
| **Energy Efficiency** | **5%** | MicroPython ESP32 edge guard script (`src/edge/esp32_guard.py`) filtering sensor faults before transmission. |

---

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.
