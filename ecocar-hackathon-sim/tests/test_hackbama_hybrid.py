from types import SimpleNamespace

import numpy as np

from autocross.api import TrackInfo, VehicleParams
from controllers.hackbama_hybrid import HackBamaHybrid


def vehicle(delay=0):
    return VehicleParams(1845, 3.0, 1.67, 4.79, 2.16, 1.45, 1.55,
                         np.deg2rad(35), 2.0, 0.95, 5.2, 9.0, 40.0, 0.05, delay)


def controller(delay=0):
    c = HackBamaHybrid({"ml_enabled": False})
    empty = np.empty((0, 2))
    c.on_start(TrackInfo("course", False, 1, empty, np.empty(0), np.empty(0),
                         empty, np.empty(0), empty, empty, np.empty((0, 2, 2)), False),
               vehicle(delay))
    return c


def straight_road(obstacles=()):
    s = np.arange(0.0, 41.0)
    return SimpleNamespace(valid=True, preview_s=s,
                           preview_centerline=np.column_stack((s, np.zeros_like(s))),
                           preview_width_left=np.full_like(s, 2.75),
                           preview_width_right=np.full_like(s, 2.75),
                           preview_curvature=np.zeros_like(s), obstacles=list(obstacles),
                           lateral_offset=0.0, heading_error=0.0, curvature=0.0,
                           dist_to_left_boundary=2.75, dist_to_right_boundary=2.75)


def observation(road, speed=5.0):
    return SimpleNamespace(road=road, speed=speed, vx=speed, vy=0.0, yaw_rate=0.0,
                           ay=0.0, ax=0.0)


def test_nonfinite_or_short_preview_uses_finite_crawl_fallback():
    c = controller()
    road = straight_road()
    road.preview_s = np.array([0.0, np.nan])
    cmd = c.step(observation(road))
    assert np.isfinite([cmd.steer, cmd.throttle, cmd.brake]).all()
    assert cmd.throttle == 0.0 and 0.0 < cmd.brake <= 0.35
    assert cmd.path.shape == (3, 2)


def test_ml_failure_is_conservative_and_disableable():
    c = controller()
    assert c._ml_risk(np.full(10, np.nan)) == 0.0  # disabled
    c.ml_enabled = True
    assert c._ml_risk(np.full(10, np.nan)) == 1.0


def test_opposite_obstacles_do_not_cancel_into_collision():
    c = controller()
    obs = [SimpleNamespace(distance=15.0, lateral_min=-2.2, lateral_max=-1.2),
           SimpleNamespace(distance=26.0, lateral_min=1.2, lateral_max=2.2)]
    road = straight_road(obs)
    data = c._road_arrays(road)
    path, offset, feasible, count = c._plan_path(road, *data[:4])
    assert feasible and count == 2 and np.isfinite(path).all()
    clearance = c.vehicle.width / 2 + 0.30
    for ob in obs:
        lateral = float(np.interp(ob.distance, data[0], offset))
        assert lateral <= ob.lateral_min - clearance or lateral >= ob.lateral_max + clearance


def test_commands_and_path_remain_bounded_on_valid_road():
    cmd = controller().step(observation(straight_road(), speed=8.0))
    assert -1.0 <= cmd.steer <= 1.0
    assert 0.0 <= cmd.throttle <= 1.0
    assert 0.0 <= cmd.brake <= 1.0
    assert not (cmd.throttle > 0.0 and cmd.brake > 0.0)
    assert cmd.path.shape[1] == 2 and np.isfinite(cmd.path).all()
