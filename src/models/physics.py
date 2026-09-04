import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class PhysicsAnomalyDetector:
    """
    Physics & Multivariate Rule-Based Detection Layer.
    Uses thermodynamic laws, meteorological constraints, and rate-of-change limits.
    Zero false positives on physical impossibility, providing explicit explainability.
    """

    def __init__(
        self,
        min_temp: float = -50.0,
        max_temp: float = 60.0,
        min_press: float = 800.0,
        max_press: float = 1100.0,
        max_temp_grad_15m: float = 10.0,
        max_press_grad_15m: float = 15.0,
        frozen_window: int = 3
    ):
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.min_press = min_press
        self.max_press = max_press
        self.max_temp_grad_15m = max_temp_grad_15m
        self.max_press_grad_15m = max_press_grad_15m
        self.frozen_window = frozen_window

    @staticmethod
    def calculate_dew_point(temp_c: float, rh_pct: float) -> float:
        """
        Calculates Dew Point Temperature (°C) using Magnus-Tetens formula.
        """
        if pd.isna(temp_c) or pd.isna(rh_pct) or rh_pct <= 0:
            return np.nan
        a = 17.27
        b = 237.7
        alpha = ((a * temp_c) / (b + temp_c)) + np.log(rh_pct / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        return dew_point

    def analyze_record(
        self,
        temp: float,
        press: float,
        rh: float,
        prev_temp: float = None,
        prev_press: float = None,
        temp_history: List[float] = None
    ) -> Tuple[float, List[str]]:
        """
        Analyzes a single observation record against physical and thermodynamic rules.
        Returns: (physics_score, list_of_violations)
        """
        violations = []

        # 1. NaN / Missing check
        if pd.isna(temp) or pd.isna(press) or pd.isna(rh):
            return 1.0, ["PHYSICS_MISSING_DATA: Null sensor telemetry payload"]

        # 2. Thermodynamic Absolute Range Checks
        if temp < self.min_temp or temp > self.max_temp:
            violations.append(f"PHYSICS_TEMP_OUT_OF_RANGE: {temp}°C outside [{self.min_temp}, {self.max_temp}]")
        if press < self.min_press or press > self.max_press:
            violations.append(f"PHYSICS_PRESS_OUT_OF_RANGE: {press}hPa outside [{self.min_press}, {self.max_press}]")
        if rh < 0.0 or rh > 100.0:
            violations.append(f"PHYSICS_RH_OUT_OF_RANGE: {rh}% outside [0, 100]")

        # 3. Dew Point Constraint (Tdew <= Tair)
        t_dew = self.calculate_dew_point(temp, rh)
        if not pd.isna(t_dew) and t_dew > (temp + 0.5):
            violations.append(f"PHYSICS_DEW_POINT_EXCEEDED: Calculated Tdew ({t_dew:.1f}°C) exceeds Tair ({temp:.1f}°C)")

        # 4. Rate of Change (Gradient) Checks
        if prev_temp is not None and not pd.isna(prev_temp):
            delta_t = abs(temp - prev_temp)
            if delta_t > self.max_temp_grad_15m:
                violations.append(f"PHYSICS_TEMP_GRADIENT_EXCEEDED: Delta-T of {delta_t:.1f}°C in 15min exceeds max threshold ({self.max_temp_grad_15m}°C)")

        if prev_press is not None and not pd.isna(prev_press):
            delta_p = abs(press - prev_press)
            if delta_p > self.max_press_grad_15m:
                violations.append(f"PHYSICS_PRESS_GRADIENT_EXCEEDED: Delta-P of {delta_p:.1f}hPa in 15min exceeds max threshold ({self.max_press_grad_15m}hPa)")

        # 5. Frozen Sensor Detection (Flatline over window)
        if temp_history is not None and len(temp_history) >= self.frozen_window:
            recent = temp_history[-self.frozen_window:]
            if len(set(recent)) == 1 and not pd.isna(recent[0]):
                violations.append(f"PHYSICS_FROZEN_SENSOR: Constant reading {recent[0]}°C across {self.frozen_window} consecutive intervals")

        # Score computation (0.0 = normal, 1.0 = highly anomalous)
        score = min(1.0, len(violations) * 0.4)
        return score, violations

    def detect_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs physics checks over an entire DataFrame sorted by (station_id, timestamp).
        Adds 'physics_score', 'physics_violations', and 'calculated_tdew' columns.
        """
        df = df.copy()
        df['calculated_tdew'] = [
            self.calculate_dew_point(t, r) for t, r in zip(df['temperature_C'], df['humidity_pct'])
        ]

        physics_scores = pd.Series(0.0, index=df.index)
        physics_violations_list = pd.Series("OK", index=df.index, dtype=object)

        for station_id, group in df.groupby('station_id'):
            idx = group.index
            group_temps = group['temperature_C'].values
            group_press = group['pressure_hPa'].values
            group_rh = group['humidity_pct'].values

            history_t = []
            for i in range(len(group)):
                t = group_temps[i]
                p = group_press[i]
                r = group_rh[i]

                prev_t = group_temps[i-1] if i > 0 else None
                prev_p = group_press[i-1] if i > 0 else None

                history_t.append(t)

                score, viols = self.analyze_record(
                    temp=t,
                    press=p,
                    rh=r,
                    prev_temp=prev_t,
                    prev_press=prev_p,
                    temp_history=history_t
                )
                physics_scores.loc[idx[i]] = score
                physics_violations_list.loc[idx[i]] = "; ".join(viols) if viols else "OK"

        df['physics_score'] = physics_scores
        df['physics_violations'] = physics_violations_list
        return df
