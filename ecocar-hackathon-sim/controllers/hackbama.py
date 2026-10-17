"""HackBama autocross controller: preview speed and smooth obstacle bypasses.

Uses only the current road model and published vehicle limits. No course map or disk access.
"""
from __future__ import annotations

import math

import numpy as np

from autocross.api import Command, Controller, Observation, TrackInfo, VehicleParams


class HackBamaController(Controller):
    def on_start(self, track: TrackInfo, vehicle: VehicleParams) -> None:
        super().on_start(track, vehicle)
        c = self.config
        self.k_ld = float(c.get("lookahead_gain", 0.5))
        self.ld_min = float(c.get("lookahead_min", 4.0))
        self.a_lat = float(c.get("lat_accel_frac", 0.60)) * vehicle.mu * 9.81
        self.a_dec = float(c.get("decel_frac", 0.40)) * vehicle.max_decel
        self.a_acc = float(c.get("accel_frac", 0.65)) * vehicle.max_accel
        self.v_max = float(c.get("v_max", 22.0))
        self.kp, self.ki = float(c.get("kp", 0.5)), float(c.get("ki", 0.1))
        self.i_err = 0.0
        # The published delay is part of the vehicle interface. Increase preview and
        # lower speed when commands will be applied to an older vehicle state.
        delay = max(vehicle.actuation_delay_steps, 0)
        self.k_ld += 0.12 * delay
        self.ld_min += 0.8 * delay
        self.delay_speed_factor = max(0.65, 1.0 - 0.13 * delay)
        self.grip_speed_factor = 1.0
        self.slip_threshold = float(c.get("slip_threshold_deg", 3.7 if delay else 999.0))

    def step(self, obs: Observation) -> Command:
        road, vp = obs.road, self.vehicle
        if road is None or not road.valid:
            return Command(brake=1.0)
        v = max(obs.speed, 0.0)
        # With actuator delay, a growing rear slip calls for extra speed margin.
        rear_slip = math.degrees(math.atan2(obs.vy - vp.cg_to_rear * obs.yaw_rate,
                                            max(abs(obs.vx), 0.1)))
        if abs(rear_slip) > self.slip_threshold:
            self.grip_speed_factor = min(self.grip_speed_factor, 0.72)
        else:
            self.grip_speed_factor = min(1.0, self.grip_speed_factor + 0.015 * vp.control_dt)

        # Shift the centerline only where an obstacle occupies the driving corridor.
        # A compact cosine bump joins the bypass to the centerline with zero slope.
        path = road.preview_centerline.copy()
        s = road.preview_s
        left_offsets = np.zeros_like(s)
        right_offsets = np.zeros_like(s)
        for ob in road.obstacles:
            if ob.distance < -2.0:
                continue
            d = ob.distance
            i = int(np.clip(np.searchsorted(s, max(d, 0.0)), 0, len(s) - 1))
            left_limit = float(road.preview_width_left[i] - vp.width / 2 - 0.22)
            right_limit = float(road.preview_width_right[i] - vp.width / 2 - 0.22)
            clearance = vp.width / 2 + 0.80
            left_target = ob.lateral_max + clearance
            right_target = ob.lateral_min - clearance
            candidates = []
            if left_target <= left_limit:
                candidates.append(max(left_target, 0.65))
            if right_target >= -right_limit:
                candidates.append(min(right_target, -0.65))
            if not candidates:
                continue
            target = min(candidates, key=abs)
            half_length = 20.0
            z = np.abs(s - d) / half_length
            bump = np.where(z < 1.0, 0.5 * (1.0 + np.cos(np.pi * np.minimum(z, 1.0))), 0.0)
            if target > 0.0:
                left_offsets = np.maximum(left_offsets, target * bump)
            else:
                right_offsets = np.minimum(right_offsets, target * bump)
        offsets = left_offsets + right_offsets
        offsets = np.clip(offsets, -road.preview_width_right + vp.width / 2 + 0.2,
                          road.preview_width_left - vp.width / 2 - 0.2)
        tangent = np.gradient(path, axis=0)
        tangent /= np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-6)
        normal = np.column_stack((-tangent[:, 1], tangent[:, 0]))
        path += normal * offsets[:, None]

        # steering: pure pursuit to the planned path point `ld` metres ahead
        ld = max(self.ld_min, self.k_ld * v + 2.0)
        tgt = np.array([np.interp(ld, s, path[:, 0]), np.interp(ld, s, path[:, 1])])
        alpha = math.atan2(tgt[1], max(tgt[0], 0.1))
        delta = math.atan2(2.0 * vp.wheelbase * math.sin(alpha), max(math.hypot(*tgt), 1.0))
        steer = float(np.clip(delta / vp.max_steer, -1.0, 1.0))

        # speed: fastest speed from which every previewed point can still be taken at
        # sqrt(a_lat / |curvature|); the end of the preview is treated as a possible slow corner
        v_curve = np.minimum(np.sqrt(self.a_lat / np.maximum(np.abs(road.preview_curvature), 1e-4)), self.v_max)
        v_curve[-1] = min(v_curve[-1], float(self.config.get("v_horizon", 6.0)))
        v_tgt = float(np.min(np.sqrt(v_curve ** 2 + 2.0 * self.a_dec * s)))
        for ob in road.obstacles:
            if ob.distance > -3.0:
                v_tgt = min(v_tgt, math.sqrt(11.0 ** 2 + 2.0 * self.a_dec * max(ob.distance - 12.0, 0.0)))
        v_tgt *= min(self.delay_speed_factor, self.grip_speed_factor)
        # speed the target up gently (it jumps when a corner leaves the preview), slow it down at once
        self.v_ref = min(v_tgt, getattr(self, "v_ref", v) + self.a_acc * vp.control_dt)
        v_tgt = self.v_ref

        err = v_tgt - v
        self.i_err = float(np.clip(self.i_err + err * vp.control_dt, -5.0, 5.0))
        u = self.kp * err + self.ki * self.i_err
        # friction circle: leave grip for cornering by capping throttle at high lateral acceleration
        lat_use = min(abs(obs.ay) / (vp.mu * 9.81), 1.0)
        throttle_cap = max(1.0 - lat_use ** 2, 0.15)
        throttle, brake = (min(u, throttle_cap), 0.0) if u >= 0 else (0.0, min(-u * 0.6, 1.0))
        return Command(steer=steer, throttle=throttle, brake=brake, path=path, path_frame="vehicle",
                       target_speed=v_tgt, debug={"lookahead": ld, "alpha": alpha,
                                                  "rear_slip_deg": rear_slip,
                                                  "grip_speed_factor": self.grip_speed_factor})
