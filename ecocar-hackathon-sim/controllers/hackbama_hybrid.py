"""Reliability-first constrained-path controller with optional embedded ML risk gating.

The deterministic planner has final authority.  The learned model can only reduce speed.
Runtime dependencies: numpy and autocross.api.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

from autocross.api import Command, Controller, Observation, TrackInfo, VehicleParams


class HackBamaHybrid(Controller):
    # Offline-trained logistic model. These initial conservative weights are replaced by
    # scripts/train_risk_model.py after grouped validation.
    ML_MEAN = np.array([8.62533055, 1.07371683, 0.26992509, 0.04752239, 0.52811847,
                        0.23564627, 2.50542576, 0.16039577, 1.11500827, 0.06194908])
    ML_SCALE = np.array([3.30864481, 1.39336601, 0.26949538, 0.04576148, 0.36375651,
                         0.20196781, 0.26423009, 0.30783536, 0.99336453, 0.06701579])
    ML_WEIGHTS = np.array([-0.67252543, 1.04393257, 0.10899739, 0.07624144, -0.02910238,
                           -0.22993279, 0.16290036, 0.96937555, -0.10416519, 0.11867307])
    ML_BIAS = -2.54469652

    def on_start(self, track: TrackInfo, vehicle: VehicleParams) -> None:
        super().on_start(track, vehicle)
        c = self.config
        self.ml_enabled = bool(c.get("ml_enabled", True))
        self.a_lat = float(c.get("lat_accel_frac", 0.60)) * vehicle.mu * 9.81
        self.a_dec = float(c.get("decel_frac", 0.40)) * vehicle.max_decel
        self.a_acc = float(c.get("accel_frac", 0.65)) * vehicle.max_accel
        self.v_max = float(c.get("v_max", 22.0))
        self.kp = float(c.get("kp", 0.5))
        self.ki = float(c.get("ki", 0.1))
        self.i_err = 0.0
        self.last_steer = 0.0
        self.last_avoid_sign = 0
        self.last_obstacle_distance = math.inf
        self.last_path_valid = True

    @staticmethod
    def _finite_scalar(value: object, default: float = 0.0) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError, OverflowError):
            return default
        return result if math.isfinite(result) else default

    @staticmethod
    def _path_curvature(path: np.ndarray) -> np.ndarray:
        if len(path) < 3:
            return np.zeros(len(path))
        ds = np.hypot(*np.diff(path, axis=0).T)
        ds = np.maximum(ds, 0.05)
        headings = np.unwrap(np.arctan2(np.diff(path[:, 1]), np.diff(path[:, 0])))
        k_mid = np.diff(headings) / np.maximum(0.5 * (ds[1:] + ds[:-1]), 0.05)
        out = np.zeros(len(path))
        out[1:-1] = k_mid
        out[0], out[-1] = out[1], out[-2]
        return np.clip(out, -0.5, 0.5)

    def _fallback(self, obs: Observation, reason: float) -> Command:
        """Crawl rather than stop indefinitely when perception is temporarily unusable."""
        speed = self._finite_scalar(getattr(obs, "speed", 0.0), 0.0)
        steer = float(np.clip(0.75 * self.last_steer, -0.35, 0.35))
        if speed > 2.5:
            throttle, brake = 0.0, min(0.35, 0.10 + 0.10 * (speed - 2.5))
        elif speed < 1.2:
            throttle, brake = 0.10, 0.0
        else:
            throttle, brake = 0.0, 0.0
        path = np.array([[0.0, 0.0], [3.0, 0.0], [6.0, 0.0]])
        self.last_steer = steer
        return Command(steer=steer, throttle=throttle, brake=brake, path=path,
                       path_frame="vehicle", target_speed=2.0,
                       debug={"fallback": reason, "ml_risk": 1.0})

    def _road_arrays(self, road):
        arrays = (road.preview_s, road.preview_centerline, road.preview_width_left,
                  road.preview_width_right, road.preview_curvature)
        try:
            s = np.asarray(arrays[0], dtype=float).reshape(-1)
            cl = np.asarray(arrays[1], dtype=float).reshape(-1, 2)
            wl = np.asarray(arrays[2], dtype=float).reshape(-1)
            wr = np.asarray(arrays[3], dtype=float).reshape(-1)
            rk = np.asarray(arrays[4], dtype=float).reshape(-1)
        except (TypeError, ValueError):
            return None
        n = min(len(s), len(cl), len(wl), len(wr), len(rk))
        if n < 4:
            return None
        s, cl, wl, wr, rk = s[:n], cl[:n], wl[:n], wr[:n], rk[:n]
        good = np.isfinite(s) & np.isfinite(cl).all(axis=1) & np.isfinite(wl) & np.isfinite(wr) & np.isfinite(rk)
        if good.sum() < 4:
            return None
        s, cl, wl, wr, rk = s[good], cl[good], wl[good], wr[good], rk[good]
        order = np.argsort(s)
        s, cl, wl, wr, rk = s[order], cl[order], wl[order], wr[order], rk[order]
        unique = np.concatenate(([True], np.diff(s) > 0.05))
        s, cl, wl, wr, rk = s[unique], cl[unique], wl[unique], wr[unique], rk[unique]
        if len(s) < 4 or s[-1] < 4.0 or np.any(wl <= 0.2) or np.any(wr <= 0.2):
            return None
        return s, cl, wl, wr, rk

    def _plan_path(self, road, s, center, wl, wr):
        vp = self.vehicle
        tangent = np.gradient(center, axis=0)
        norm = np.linalg.norm(tangent, axis=1)
        if not np.isfinite(norm).all() or np.any(norm < 1e-4):
            return center.copy(), np.zeros(len(s)), False, 0
        tangent /= norm[:, None]
        normal = np.column_stack((-tangent[:, 1], tangent[:, 0]))
        margin = vp.width / 2.0 + 0.28
        low = -wr + margin
        high = wl - margin
        if np.any(low >= high):
            return center.copy(), np.zeros(len(s)), False, 0

        obstacles = []
        for ob in list(getattr(road, "obstacles", []) or []):
            d = self._finite_scalar(getattr(ob, "distance", math.inf), math.inf)
            omin = self._finite_scalar(getattr(ob, "lateral_min", math.nan), math.nan)
            omax = self._finite_scalar(getattr(ob, "lateral_max", math.nan), math.nan)
            if -2.0 <= d <= s[-1] + 1.0 and math.isfinite(omin) and math.isfinite(omax) and omin <= omax:
                obstacles.append((d, omin, omax))
        obstacles.sort()
        obstacles = obstacles[:4]
        if not obstacles:
            self.last_avoid_sign = 0
            self.last_obstacle_distance = math.inf
            return center.copy(), np.zeros(len(s)), True, 0

        choices = []
        clearance = vp.width / 2.0 + 0.82
        collision_clearance = vp.width / 2.0 + 0.30
        for d, omin, omax in obstacles:
            i = int(np.clip(np.searchsorted(s, max(d, 0.0)), 0, len(s) - 1))
            opts = []
            left = omax + clearance
            right = omin - clearance
            if left <= high[i]:
                opts.append(max(left, 0.55))
            if right >= low[i]:
                opts.append(min(right, -0.55))
            choices.append(opts)
        if any(not x for x in choices):
            return center.copy(), np.zeros(len(s)), False, 0

        best = None
        for selected in itertools.product(*choices):
            offset = np.zeros(len(s))
            for (d, _, _), target in zip(obstacles, selected):
                half = 20.0
                z = np.abs(s - d) / half
                bump = np.where(z < 1.0, 0.5 * (1.0 + np.cos(np.pi * np.minimum(z, 1.0))), 0.0)
                # Superpose opposite-side manoeuvres, but same-side requirements use max magnitude.
                proposal = target * bump
                same = np.sign(offset) == np.sign(proposal)
                offset = np.where(same & (np.abs(proposal) > np.abs(offset)), proposal,
                                  np.where(same, offset, offset + proposal))
            if np.any(offset < low) or np.any(offset > high):
                continue
            collision = False
            for d, omin, omax in obstacles:
                near = np.abs(s - d) <= 1.25
                if near.any() and np.any((offset[near] > omin - collision_clearance) &
                                         (offset[near] < omax + collision_clearance)):
                    collision = True
                    break
            if collision:
                continue
            path = center + normal * offset[:, None]
            k = self._path_curvature(path)
            if not np.isfinite(path).all() or not np.isfinite(k).all():
                continue
            first_sign = int(np.sign(selected[0]))
            switch_cost = 0.8 if (self.last_avoid_sign and first_sign != self.last_avoid_sign and
                                  obstacles[0][0] < self.last_obstacle_distance + 5.0) else 0.0
            smooth = float(np.mean(np.diff(offset, n=2) ** 2)) if len(offset) > 2 else 0.0
            cost = 0.08 * float(np.mean(offset ** 2)) + 25.0 * smooth + 0.4 * float(np.max(np.abs(k))) + switch_cost
            if best is None or cost < best[0]:
                best = (cost, path, offset, first_sign)
        if best is None:
            return center.copy(), np.zeros(len(s)), False, 0
        self.last_avoid_sign = best[3]
        self.last_obstacle_distance = obstacles[0][0]
        return best[1], best[2], True, len(obstacles)

    def _ml_risk(self, features: np.ndarray) -> float:
        if not self.ml_enabled:
            return 0.0
        if features.shape != (10,) or not np.isfinite(features).all():
            return 1.0
        z = np.clip((features - self.ML_MEAN) / self.ML_SCALE, -6.0, 6.0)
        logit = float(np.dot(self.ML_WEIGHTS, z) + self.ML_BIAS)
        if not math.isfinite(logit):
            return 1.0
        return 1.0 / (1.0 + math.exp(-float(np.clip(logit, -30.0, 30.0))))

    def step(self, obs: Observation) -> Command:
        road, vp = getattr(obs, "road", None), self.vehicle
        if road is None or not bool(getattr(road, "valid", False)):
            return self._fallback(obs, 1.0)
        data = self._road_arrays(road)
        if data is None:
            return self._fallback(obs, 2.0)
        s, center, wl, wr, road_k = data
        speed = max(self._finite_scalar(obs.speed), 0.0)
        path, offset, feasible, obstacle_count = self._plan_path(road, s, center, wl, wr)
        path_k = self._path_curvature(path)
        if not feasible:
            path = center.copy()
            path_k = self._path_curvature(path)

        delay = max(int(self._finite_scalar(vp.actuation_delay_steps, 0.0)), 0)
        ld_nominal = max(4.0 + 0.8 * delay, (0.50 + 0.12 * delay) * speed + 2.0)
        ld = float(np.clip(ld_nominal, 4.0, max(4.0, s[-1] - 0.5)))
        target = np.array([np.interp(ld, s, path[:, 0]), np.interp(ld, s, path[:, 1])])
        alpha = math.atan2(target[1], max(target[0], 0.1))
        pp_delta = math.atan2(2.0 * vp.wheelbase * math.sin(alpha), max(math.hypot(*target), 1.0))
        k_ld = float(np.interp(ld, s, path_k))
        ff_delta = math.atan(vp.wheelbase * k_ld)
        delta = pp_delta
        raw_steer = float(np.clip(delta / vp.max_steer, -1.0, 1.0))
        steer = raw_steer

        rear_slip = math.degrees(math.atan2(self._finite_scalar(obs.vy) - vp.cg_to_rear * self._finite_scalar(obs.yaw_rate),
                                            max(abs(self._finite_scalar(obs.vx)), 0.1)))
        lat_offset = abs(self._finite_scalar(getattr(road, "lateral_offset", 0.0)))
        heading_error = abs(self._finite_scalar(getattr(road, "heading_error", 0.0)))
        boundary = min(self._finite_scalar(getattr(road, "dist_to_left_boundary", 0.0)),
                       self._finite_scalar(getattr(road, "dist_to_right_boundary", 0.0)))
        max_k = float(np.max(np.abs(path_k)))
        demand = speed * speed * max_k / max(vp.mu * 9.81, 0.1)
        ay_use = abs(self._finite_scalar(obs.ay)) / max(vp.mu * 9.81, 0.1)
        nearest_obstacle = min([self._finite_scalar(o.distance, math.inf) for o in (getattr(road, "obstacles", []) or [])], default=math.inf)
        obstacle_proximity = 0.0 if not math.isfinite(nearest_obstacle) else float(np.clip((25.0 - nearest_obstacle) / 25.0, 0.0, 1.0))
        yaw_residual = abs(self._finite_scalar(obs.yaw_rate) - self._finite_scalar(obs.vx) * self._finite_scalar(road.curvature))
        features = np.array([speed, abs(rear_slip), lat_offset, heading_error, demand,
                             ay_use, boundary, obstacle_proximity, float(delay), yaw_residual])
        ml_risk = self._ml_risk(features)

        speed_k = path_k if obstacle_count else road_k
        curve_speed = np.minimum(np.sqrt(self.a_lat / np.maximum(np.abs(speed_k), 1e-4)), self.v_max)
        curve_speed[-1] = min(curve_speed[-1], 6.0)
        target_speed = float(np.min(np.sqrt(np.maximum(curve_speed ** 2 + 2.0 * self.a_dec * s, 0.0))))
        if obstacle_count:
            target_speed = min(target_speed, math.sqrt(10.0 ** 2 + 2.0 * self.a_dec * max(nearest_obstacle - 13.0, 0.0)))
        if not feasible:
            target_speed = min(target_speed, 3.0)
        tracking_factor = float(np.clip(1.0 - 0.28 * max(lat_offset - 0.65, 0.0) -
                                        0.18 * max(abs(rear_slip) - 5.0, 0.0) / 10.0, 0.55, 1.0))
        delay_factor = max(0.68, 1.0 - 0.12 * delay)
        ml_factor = 1.0 - 0.30 * ml_risk
        target_speed *= min(tracking_factor, delay_factor, ml_factor)
        prior_ref = getattr(self, "v_ref", speed)
        # Speed may drop immediately when a newly visible braking constraint appears;
        # acceleration remains ramp-limited to avoid a horizon-exit surge.
        self.v_ref = min(target_speed, prior_ref + self.a_acc * vp.control_dt)
        target_speed = self.v_ref

        error = target_speed - speed
        self.i_err = float(np.clip(self.i_err + error * vp.control_dt, -4.0, 4.0))
        u = self.kp * error + self.ki * self.i_err
        throttle_cap = max(1.0 - min(ay_use, 1.0) ** 2, 0.12)
        if u >= 0.0:
            throttle, brake = min(u, throttle_cap), 0.0
        else:
            throttle, brake = 0.0, min(-0.62 * u, 0.85)
        if not all(math.isfinite(x) for x in (steer, throttle, brake, target_speed)):
            return self._fallback(obs, 3.0)
        self.last_steer = steer
        self.last_path_valid = feasible
        return Command(steer=steer, throttle=float(np.clip(throttle, 0.0, 1.0)),
                       brake=float(np.clip(brake, 0.0, 1.0)), path=path,
                       path_frame="vehicle", target_speed=max(target_speed, 0.0),
                       debug={"lookahead": ld, "rear_slip_deg": rear_slip,
                              "path_feasible": float(feasible), "planned_curvature": max_k,
                              "grip_demand": demand, "ml_risk": ml_risk,
                              "ml_speed_factor": ml_factor, "fallback": 0.0,
                              "feat_heading_error": heading_error,
                              "feat_ay_use": ay_use, "feat_boundary": boundary,
                              "feat_obstacle": obstacle_proximity,
                              "feat_yaw_residual": yaw_residual})
