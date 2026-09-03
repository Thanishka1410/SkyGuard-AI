# AWS Anomaly Detection System (SIH PS 26073)

## Executive Overview
Automatic Weather Stations (AWS) managed by meteorological agencies like the India Meteorological Department (IMD) continuously transmit high-frequency observation data:
- **Temperature (°C)**
- **Atmospheric Pressure (hPa)**
- **Relative Humidity (%)**

Sensors deployed in hostile environmental conditions suffer from multiple failure modes:
1. **Spikes**: Instantaneous physical non-sequitur readings (e.g. $55^\circ\text{C}$ spike due to sensor power surges).
2. **Frozen Values**: Constant flatlined outputs due to hardware hangs.
3. **Calibration Drift**: Gradual upward or downward creep due to sensor aging or biofouling.
4. **Communication Loss**: Missing data packets, corrupted payload frames, or NaN bursts.
5. **Noise Bursts**: High-frequency electrical interference.

Standard single-variable thresholds generate excessive false alarms during genuine localized severe weather events (e.g., cloudbursts, severe heatwaves, dust storms). This solution implements a **3-Layer Physics-Informed & Spatial Sensor Fusion Framework** with **Self-Healing Auto-Correction**.

---

## 3-Layer Detection Architecture

### Layer 1: Physics & Multivariate Rule Engine
- **Dew Point Limit**: Computes dew point $T_{dew}$ via Magnus-Tetens formula ($T_{dew} \le T_{air}$).
- **Thermodynamic Bounds**: Hard physical limits ($T \in [-50, 60]^\circ\text{C}$, $P \in [800, 1100]\text{hPa}$, $RH \in [0, 100]\%$).
- **Diurnal Correlation Check**: Flags abnormal positive correlation between Temperature and Relative Humidity during peak daylight hours.
- **Gradient/Rate-of-Change Limits**: Maximum rate of change per 15-minute telemetry step ($\Delta T_{max} = 10^\circ\text{C}$, $\Delta P_{max} = 15\text{hPa}$).

### Layer 2: Temporal Per-Station Baseline Model
- Builds individual historical models per station (Isolation Forest / Rolling Z-Score).
- Learns each station's micro-climatic baseline, diurnal rhythm, and seasonal variation.
- Detects subtle statistical shifts and anomalies independent of geographic location.

### Layer 3: Geodesic Spatial Neighbor Comparison
- Computes geodesic distance matrices between stations using Haversine formulas (`lat`, `lon` used **only** for spatial proximity lookup).
- Calculates spatial expectation $\hat{y}_i$ via Inverse Distance Weighting (IDW):
  $$\hat{y}_i = \frac{\sum_{j \in \mathcal{N}(i)} w_{ij} y_j}{\sum_{j \in \mathcal{N}(i)} w_{ij}}, \quad w_{ij} = \frac{1}{d(i,j)^p}$$
- **Disambiguation Logic**:
  - `Station deviates from temporal history AND neighbors disagree` $\rightarrow$ **Sensor Fault Anomaly**
  - `Station deviates from temporal history AND neighbors agree` $\rightarrow$ **Genuine Severe Weather Event**

---

## Fusion & Self-Healing Auto-Correction
- **Fusion Engine**: Synthesizes output from all 3 layers into a final anomaly flag, confidence score ($0.0 - 1.0$), and root-cause taxonomy (`spike`, `frozen_value`, `calibration_drift`, `comm_loss`, `noise_burst`).
- **Self-Healing Auto-Correction**: Replaces corrupted/anomaly readings with spatially interpolated values ($\hat{y}_i$) blended with temporal exponential smoothing, realizing the IMD vision of a self-aware, self-healing observation network.
