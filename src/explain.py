import pandas as pd
from typing import Dict, Any

class ExplanationGenerator:
    """
    Generates rich, human-readable explainability logs and evidence strings
    derived from Physics, Spatial, and Temporal detection signals.
    """

    def __init__(self):
        pass

    def generate_explanation(self, row: pd.Series) -> str:
        """
        Generates explanation string for a single telemetry record.
        """
        st_id = row.get('station_id', 'AWS_UNKNOWN')
        cause = row.get('root_cause', 'normal')
        is_anom = row.get('is_anomaly_pred', False)
        temp = row.get('temperature_C', None)
        exp_temp = row.get('spatial_expected_temp', None)
        corr_temp = row.get('corrected_temp_C', None)
        phys_viols = row.get('physics_violations', 'OK')
        spat_details = row.get('spatial_details', '')

        if not is_anom:
            if cause == 'real_weather_event':
                if spat_details and "No active neighbors" not in spat_details:
                    return (
                        f"[{st_id}] REAL METEOROLOGICAL EVENT: Station telemetry deviates from historical diurnal baseline, "
                        f"but surrounding geographic neighbors confirm the localized weather trend. {spat_details}"
                    )
                else:
                    return (
                        f"[{st_id}] REAL METEOROLOGICAL EVENT (Single-Station Mode): Telemetry exhibits a rapid thermal shift, "
                        f"but 100% conforms to thermodynamic laws (dew point Tdew <= Tair, valid gradient, physical bounds). Disambiguated as a genuine weather event."
                    )
            return f"[{st_id}] NORMAL: Observations conform to thermodynamic laws, station temporal baseline, and neighbor network."

        # Sensor Anomaly Case
        parts = [f"[{st_id}] SENSOR ANOMALY DETECTED ({cause.upper()}) - Confidence: {row.get('confidence_score', 1.0):.2f}"]

        # Physics evidence
        if phys_viols != 'OK' and phys_viols != '':
            parts.append(f"Physics Violations: {phys_viols}")

        # Spatial evidence
        if spat_details and "No active neighbors" not in spat_details:
            parts.append(f"Spatial Comparison: {spat_details}")
        elif spat_details:
            parts.append(f"Single-Station Analysis: {spat_details}")

        # Auto-correction suggestion
        impute_target = exp_temp if (exp_temp is not None and not pd.isna(exp_temp)) else corr_temp
        if impute_target is not None and not pd.isna(impute_target):
            parts.append(f"Self-Healing Recommendation: Impute temperature from {temp}°C -> {impute_target:.1f}°C")

        return " | ".join(parts)

    def add_explanations_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends 'explanation' column to processed DataFrame.
        """
        df = df.copy()
        df['explanation'] = [self.generate_explanation(row) for _, row in df.iterrows()]
        return df
