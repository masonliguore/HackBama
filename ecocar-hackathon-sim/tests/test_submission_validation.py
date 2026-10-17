"""Focused validation of V6; set HACKBAMA_CONTROLLER_PATH to retest V4."""
from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path

import numpy as np
import pytest

from autocross.api import ObstacleInfo, Observation, RoadModel, VehicleParams


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / os.environ.get("HACKBAMA_CONTROLLER_PATH", "controllers/hackbama_v6.py")
SPEC = importlib.util.spec_from_file_location("submission_validation", CONTROLLER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def vehicle(**changes):
    values = dict(mass=1845, wheelbase=3, track_width=1.67, length=4.79, width=2.16,
                  cg_to_front=1.45, cg_to_rear=1.55, max_steer=math.radians(35),
                  max_steer_rate=2, mu=0.97, max_accel=5.2, max_decel=9, max_speed=40,
                  control_dt=.05, actuation_delay_steps=0)
    values.update(changes)
    return VehicleParams(**values)


def obstacle(distance, low, high):
    return ObstacleInfo(distance, low, high, np.array([distance, (low + high) / 2]),
                        np.array([[distance, low], [distance, high]]))


def observation(obstacles=(), *, width=2.75, speed=8, n=41, spacing=1, curvature=0,
                vx=None, vy=0, yaw_rate=0, ay=0):
    s = np.arange(n, dtype=float) * spacing
    center = np.column_stack((s, np.zeros(n)))
    widths = np.full(n, width, dtype=float)
    road = RoadModel(True, float(s[-1]) if n else 0, 0, 0, curvature, width, width,
                     width, width, s, np.full(n, curvature), center,
                     widths.copy(), widths.copy(), center.copy(), center.copy(),
                     [], list(obstacles), float("nan"))
    obs = Observation(0, 0, 0, 0, 0, speed if vx is None else vx, vy, yaw_rate, 0,
                      ay, speed, 0, 0, 0, 0, 0, False, road=road)
    return obs


def controller(vp=None):
    c = MODULE.HackBamaController()
    c.on_start(None, vp or vehicle())
    return c


def assert_valid(cmd):
    assert all(math.isfinite(x) for x in (cmd.steer, cmd.throttle, cmd.brake, cmd.target_speed))
    assert -1 <= cmd.steer <= 1
    assert 0 <= cmd.throttle <= 1 and 0 <= cmd.brake <= 1
    assert cmd.throttle == 0 or cmd.brake == 0
    assert cmd.target_speed >= 0
    assert cmd.path_frame == "vehicle" and np.isfinite(cmd.path).all()


@pytest.mark.parametrize("obstacles", [
    [], [obstacle(10, .8, 2.1)], [obstacle(10, -2.1, -.8)],
    [obstacle(10, -.5, .5)],
    [obstacle(10, .8, 2.1), obstacle(13.7, -2.1, -.8)],
    [obstacle(10, .8, 2.1), obstacle(18, .8, 2.1)],
    [obstacle(10, .8, 2.1), obstacle(13.7, -2.1, -.8), obstacle(25, .8, 2.1)],
])
def test_obstacle_layouts_return_valid_commands(obstacles):
    assert_valid(controller().step(observation(obstacles)))


@pytest.mark.parametrize("distance", [-3, -2, 0, 1, 20, 36.3, 40])
def test_obstacle_distance_boundaries(distance):
    pair = [obstacle(distance, .8, 2.1), obstacle(distance + 3.7, -2.1, -.8)]
    assert_valid(controller().step(observation(pair)))


@pytest.mark.parametrize("separation", [0, .01, .5, 1, 3.7, 7.999, 8, 8.001, 19.5, 20, 20.5])
def test_opposite_pair_separation_thresholds(separation):
    pair = [obstacle(10, .8, 2.1), obstacle(10 + separation, -2.1, -.8)]
    assert_valid(controller().step(observation(pair)))


def test_no_feasible_bypass_is_finite_and_deterministic():
    obs = observation([obstacle(10, -2.5, 2.5)], width=2.75, speed=15)
    a, b = controller().step(obs), controller().step(obs)
    assert_valid(a)
    assert np.array_equal(a.path, b.path)
    assert a.target_speed == b.target_speed
    assert a.path[10, 1] == 0  # the present planner continues on centerline
    assert a.target_speed == 11


@pytest.mark.parametrize("low,high,width", [(-2.5, 2.5, 2.75), (-1.5, 1.5, 2.4),
                                            (-2.3, .8, 2.3), (-.8, 2.3, 2.3)])
def test_no_feasible_bypass_geometries(low, high, width):
    cmd = controller().step(observation([obstacle(10, low, high)], width=width))
    assert_valid(cmd)
    assert cmd.path[10, 1] == 0
    assert cmd.target_speed <= 11


@pytest.mark.parametrize("first,second,expected", [
    ((-2, -1), (1, 2), 2),
    ((-2, 0), (0, 2), 0),
    ((-2, 1), (-1, 2), 0),
    ((-3, 3), (-1, 1), 0),
    ((-.5, 1.5), (-1.5, .5), 0),
])
def test_analytical_interval_distance(first, second, expected):
    actual = max(0, max(first[0], second[0]) - min(first[1], second[1]))
    assert actual == expected


def test_submission_does_not_mutate_road_arrays():
    obs = observation([obstacle(10, .8, 2.1)])
    originals = [array.copy() for array in (obs.road.preview_s, obs.road.preview_centerline,
                                             obs.road.preview_curvature, obs.road.preview_width_left,
                                             obs.road.preview_width_right)]
    assert_valid(controller().step(obs))
    for array, original in zip((obs.road.preview_s, obs.road.preview_centerline,
                                obs.road.preview_curvature, obs.road.preview_width_left,
                                obs.road.preview_width_right), originals):
        assert np.array_equal(array, original)


def test_invalid_empty_preview_brakes():
    obs = observation(n=0)
    obs.road.valid = False
    cmd = controller().step(obs)
    assert cmd.brake == 1 and cmd.throttle == 0 and cmd.steer == 0


def test_same_observation_sequence_is_bitwise_deterministic():
    observations = [observation([obstacle(10 - i, .8, 2.1),
                                 obstacle(13 - i, -2.1, -.8)], speed=8 + i)
                    for i in range(5)]
    sequences = []
    for _ in range(2):
        c = controller()
        sequences.append([c.step(obs) for obs in observations])
    for left, right in zip(*sequences):
        assert left.steer == right.steer
        assert left.throttle == right.throttle
        assert left.brake == right.brake
        assert left.target_speed == right.target_speed
        assert np.array_equal(left.path, right.path)


def test_two_separated_tight_pairs_both_slow_down():
    obs = observation([obstacle(10, .8, 2.1), obstacle(13, -2.1, -.8),
                       obstacle(30, .8, 2.1), obstacle(33, -2.1, -.8)], speed=15)
    cmd = controller().step(obs)
    assert cmd.target_speed <= 3.5
    assert cmd.debug["lookahead"] <= 5.0


@pytest.mark.parametrize("separation,expected_speed", [(7.999, 3.5), (8.0, 11.0), (8.001, 11.0)])
def test_tight_pair_distance_rule(separation, expected_speed):
    obs = observation([obstacle(10, .8, 2.1), obstacle(10 + separation, -2.1, -.8)], speed=15)
    assert controller().step(obs).target_speed == expected_speed


def test_same_side_and_wide_gap_pairs_keep_normal_speed():
    same_side = [obstacle(10, .8, 2.1), obstacle(13, .8, 2.1)]
    wide_gap = [obstacle(10, 1.5, 2), obstacle(13, -2, -1.5)]
    assert controller().step(observation(same_side, speed=15)).target_speed == 11
    assert controller(vehicle(width=1.5)).step(observation(wide_gap, width=5, speed=15)).target_speed == 11


def test_multiple_pairs_each_shorten_their_bumps():
    obs = observation([obstacle(10, .8, 2.1), obstacle(13, -2.1, -.8),
                       obstacle(30, .8, 2.1), obstacle(33, -2.1, -.8)])
    path = controller().step(obs).path
    assert path[16, 1] == 0 and path[36, 1] == 0


def test_unrelated_nearby_obstacle_does_not_inherit_tight_clearance():
    third = obstacle(4, .8, 2.1)
    single = controller().step(observation([third], speed=15))
    together = controller().step(observation([obstacle(10, .8, 2.1),
                                               obstacle(13, -2.1, -.8), third], speed=15))
    # The third obstacle is not in the 10/13 pair; its bypass clearance should match.
    assert abs(together.path[4, 1]) >= abs(single.path[4, 1]) - .05


def test_overlapping_intervals_have_zero_gap():
    # Opposite-center obstacle intervals overlap by 4 m; their set distance is zero.
    obs = observation([obstacle(10, -2, 4), obstacle(13, -4, 2)], width=5)
    cmd = controller().step(obs)
    assert cmd.target_speed <= 3.5


def test_start_resets_dynamic_state():
    c = controller()
    c.step(observation(speed=12))
    c.on_start(None, vehicle())
    assert c.i_err == 0 and c.grip_speed_factor == 1
    assert c.step(observation()).target_speed == controller().step(observation()).target_speed


def test_randomized_api_valid_observations():
    rng = np.random.default_rng(20261017)
    for case in range(3000):
        vp = vehicle(width=float(rng.uniform(1.7, 2.4)), mu=float(rng.uniform(.65, 1.1)),
                     actuation_delay_steps=int(rng.integers(0, 4)),
                     mass=float(rng.uniform(1500, 2200)))
        count = int(rng.integers(0, 9))
        obs_list = []
        for _ in range(count):
            dist = float(rng.uniform(-3, 42))
            lo = float(rng.uniform(-3, 2))
            hi = lo + float(rng.uniform(.1, 2))
            obs_list.append(obstacle(dist, lo, hi))
        obs = observation(obs_list, width=float(rng.uniform(2.2, 5)),
                          speed=float(rng.uniform(0, 26)), n=int(rng.integers(2, 81)),
                          spacing=float(rng.uniform(.5, 2)),
                          curvature=float(rng.uniform(-.11, .11)),
                          vy=float(rng.uniform(-2, 2)), yaw_rate=float(rng.uniform(-.6, .6)),
                          ay=float(rng.uniform(-8, 8)))
        try:
            cmd = controller(vp).step(obs)
            assert_valid(cmd)
            assert np.max(np.abs(cmd.path[:, 1])) <= obs.road.width_left - vp.width / 2 - .2 + 1e-6
        except Exception as exc:
            pytest.fail(f"random seed 20261017 case {case}: {exc}")


def test_randomized_stateful_sequences():
    rng = np.random.default_rng(20261018)
    for sequence in range(20):
        c = controller(vehicle(actuation_delay_steps=int(rng.integers(0, 4))))
        for step in range(100):
            obstacles = [obstacle(float(rng.uniform(-2, 40)), float(offset), float(offset + 1.3))
                         for offset in rng.uniform(-2.1, .8, int(rng.integers(0, 6)))]
            obs = observation(obstacles, width=float(rng.uniform(2.75, 4)),
                              speed=float(rng.uniform(0, 24)),
                              curvature=float(rng.uniform(-.08, .08)),
                              vy=float(rng.uniform(-1, 1)), ay=float(rng.uniform(-7, 7)))
            try:
                assert_valid(c.step(obs))
            except Exception as exc:
                pytest.fail(f"random seed 20261018 sequence {sequence} step {step}: {exc}")
