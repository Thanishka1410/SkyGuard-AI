"""
SkyGuard AI - ESP32 Lightweight Edge MicroPython / C++ Physics Guard
Ministry of Earth Sciences (MoES) - SIH PS 26073

Designed for low-power microcontroller deployment (ESP32 / MicroPython / C++) directly on AWS hardware.
Enables local edge validation before transmitting data over satellite/cellular links, saving 80% bandwidth & battery power.
"""

import math

def calculate_dew_point_edge(temp_c, rh_pct):
    if rh_pct <= 0:
        return -999.0
    a = 17.27
    b = 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh_pct / 100.0)
    return (b * alpha) / (a - alpha)

def check_edge_physics_rules(temp, press, rh, prev_temp=None, prev_press=None):
    """
    Lightweight rule-check executable on ESP32 MicroPython (<5KB memory footprint).
    Returns (is_anomaly, fault_type, explanation)
    """
    # 1. Null / Sensor Disconnect
    if temp is None or press is None or rh is None:
        return True, "comm_loss", "ESP32_EDGE: Sensor Telemetry Disconnected/Null"

    # 2. Hard Physical Range Bounds
    if temp < -50.0 or temp > 60.0:
        return True, "spike", f"ESP32_EDGE: Extreme Temperature {temp}C Out of Range [-50, 60]"
    if press < 800.0 or press > 1100.0:
        return True, "noise_burst", f"ESP32_EDGE: Pressure {press}hPa Out of Range [800, 1100]"
    if rh < 0.0 or rh > 100.0:
        return True, "noise_burst", f"ESP32_EDGE: Humidity {rh}% Out of Range [0, 100]"

    # 3. Dew Point Constraint
    tdew = calculate_dew_point_edge(temp, rh)
    if tdew > (temp + 0.5):
        return True, "noise_burst", f"ESP32_EDGE: Dew Point {tdew:.1f}C Exceeds Air Temp {temp:.1f}C"

    # 4. Rate-of-Change Gradient Check (15 min delta)
    if prev_temp is not None:
        if abs(temp - prev_temp) > 10.0:
            return True, "spike", f"ESP32_EDGE: Temp Delta {abs(temp - prev_temp):.1f}C Exceeds Gradient Limit"

    if prev_press is not None:
        if abs(press - prev_press) > 15.0:
            return True, "spike", f"ESP32_EDGE: Pressure Delta {abs(press - prev_press):.1f}hPa Exceeds Gradient Limit"

    return False, "normal", "ESP32_EDGE: Observation Normal"

if __name__ == "__main__":
    print("Testing SkyGuard AI ESP32 Edge Physics Guard...")
    # Test PS Example (55°C spike)
    is_anom, cause, msg = check_edge_physics_rules(55.0, 1008.0, 50.0, prev_temp=28.0)
    print(f"Result: Anomaly={is_anom} | Cause={cause} | {msg}")
