"""Small, deterministic engineering calculations for the demo dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid


def simulate_motion(mass_kg: float, force_n: float, duration_s: float, samples: int = 101) -> pd.DataFrame:
    """Simulate constant-force motion from rest (all data is calculated locally)."""
    if not np.isfinite(mass_kg) or mass_kg <= 0:
        raise ValueError("Mass must be a positive finite number.")
    if not np.isfinite(force_n) or force_n < 0:
        raise ValueError("Force must be a non-negative finite number.")
    if not np.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("Duration must be a positive finite number.")
    if samples < 2:
        raise ValueError("At least two samples are required.")

    time_s = np.linspace(0.0, duration_s, samples)
    acceleration_m_s2 = force_n / mass_kg
    velocity_m_s = acceleration_m_s2 * time_s
    distance_m = cumulative_trapezoid(velocity_m_s, time_s, initial=0.0)
    return pd.DataFrame(
        {"time_s": time_s, "velocity_m_s": velocity_m_s, "distance_m": distance_m}
    )


def summarize(mass_kg: float, force_n: float, result: pd.DataFrame) -> dict[str, float]:
    """Return user-facing summary values from validated inputs and simulation."""
    return {
        "acceleration_m_s2": force_n / mass_kg,
        "final_velocity_m_s": float(result["velocity_m_s"].iloc[-1]),
        "distance_m": float(result["distance_m"].iloc[-1]),
    }
