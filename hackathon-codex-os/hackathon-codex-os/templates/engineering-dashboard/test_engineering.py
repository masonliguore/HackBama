import pytest

from engineering import simulate_motion, summarize


def test_constant_force_motion_matches_analytic_values():
    result = simulate_motion(mass_kg=2, force_n=4, duration_s=3, samples=301)
    metrics = summarize(2, 4, result)
    assert metrics["acceleration_m_s2"] == pytest.approx(2)
    assert metrics["final_velocity_m_s"] == pytest.approx(6)
    assert metrics["distance_m"] == pytest.approx(9, abs=0.001)


@pytest.mark.parametrize("kwargs", [
    {"mass_kg": 0, "force_n": 2, "duration_s": 1},
    {"mass_kg": 1, "force_n": -1, "duration_s": 1},
    {"mass_kg": 1, "force_n": 1, "duration_s": 0},
    {"mass_kg": 1, "force_n": 1, "duration_s": 1, "samples": 1},
])
def test_invalid_inputs_raise_value_error(kwargs):
    with pytest.raises(ValueError):
        simulate_motion(**kwargs)
