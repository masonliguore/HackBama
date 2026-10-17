"""Reconstruct V6's published paths around first cone hits; diagnostic only."""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

from autocross.api import Observation, VehicleParams
from autocross.perception import RoadModelSensor
from autocross.track import load
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controllers.hackbama_v6 import HackBamaController


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "runs/v6_retest_20261017_153913"
OUTPUT = ROOT / "runs/v6_cone_analysis.json"


def footprint_clearance(path, stations, cones, half_l, half_w):
    """Minimum signed cone clearance from oriented, sampled vehicle footprint."""
    grid = np.arange(0, min(float(stations[-1]), 40.0) + 0.001, 0.2)
    px = np.interp(grid, stations, path[:, 0])
    py = np.interp(grid, stations, path[:, 1])
    hd = np.arctan2(np.gradient(py), np.gradient(px))
    dx = cones[:, None, 0] - px[None, :]
    dy = cones[:, None, 1] - py[None, :]
    forward = dx * np.cos(hd) + dy * np.sin(hd)
    lateral = -dx * np.sin(hd) + dy * np.cos(hd)
    ex = np.abs(forward) - half_l - 0.1
    ey = np.abs(lateral) - half_w - 0.1
    signed = np.where((ex <= 0) & (ey <= 0), np.maximum(ex, ey),
                      np.hypot(np.maximum(ex, 0), np.maximum(ey, 0)))
    return float(signed.min())


def analyze_seed(seed):
    directory = BATCH / "unseen" / str(seed)
    summary = json.loads((directory / "summary.json").read_text())
    events = json.loads((directory / "events.json").read_text())
    hits = [e for e in events if e["kind"] == "cone_hit"]
    if not hits:
        return None
    hit = hits[0]
    tr = load(summary["track"]["path"])
    vp = VehicleParams(**summary["vehicle"])
    cone_index = hit["detail"]["cone"]
    mapped = cone_index < len(tr.cones)
    gid = int(tr.obstacle_gid[cone_index - len(tr.cones)]) if not mapped else None
    cone = tr.all_cones()[0][cone_index]
    sensor = RoadModelSensor(tr, summary["config"]["road_model"], np.random.default_rng(0))
    controller = HackBamaController()
    controller.on_start(None, vp)
    rows = list(csv.DictReader((directory / "telemetry.csv").open()))
    x0, y0, yaw0 = tr.spawn_pose()
    samples = []
    worst_replay_error = 0.0
    for j in range(0, len(rows), 2):
        row = rows[j]
        prev = rows[j - 1] if j else None
        val = lambda key, initial=0.0: float(prev[key]) if prev else initial
        x, y, yaw = val("x", x0), val("y", y0), val("yaw", yaw0)
        road = sensor.measure(x, y, yaw, val("progress"))
        obs = Observation(val("t"), j // 2, x, y, yaw, val("vx"), val("vy"),
                          val("yaw_rate"), val("ax"), val("ay"), val("speed"),
                          val("app_steer"), val("app_throttle"), val("app_brake"),
                          val("progress"), 0, True, road=road)
        cmd = controller.step(obs)
        if cmd.path is None:
            continue
        worst_replay_error = max(worst_replay_error, abs(cmd.steer - float(row["cmd_steer"])),
                                 abs(cmd.target_speed - float(row["target_speed"])))
        if not (hit["t"] - 2.05 <= obs.t <= hit["t"] + 1.05):
            continue
        if j % 10 and abs(obs.t - hit["t"]) > 0.15:
            continue
        d = float(tr.obstacles[gid]["s"] - (tr.spawn_s + obs.progress)) if gid is not None else None
        if tr.closed and d is not None:
            d = (d + tr.length / 2) % tr.length - tr.length / 2
        in_view = gid is not None and d is not None and -3 <= d <= road.range_m
        ob = None
        if in_view:
            group_lat = tr.obstacle_lat[tr.obstacle_gid == gid]
            ob = min(road.obstacles, key=lambda item: abs(item.distance - d), default=None)
            if ob is not None and abs(ob.distance - d) > 1.0:
                ob = None
        clearance = None
        planned_offset = None
        path_kappa = None
        road_kappa = None
        v_safe = None
        no_candidate = None
        tight = None
        bump_half = None
        bypass = None
        if ob is not None:
            physical = tr.obstacle_cones[tr.obstacle_gid == gid]
            body = np.column_stack((np.cos(yaw) * (physical[:, 0] - x) + np.sin(yaw) * (physical[:, 1] - y),
                                    -np.sin(yaw) * (physical[:, 0] - x) + np.cos(yaw) * (physical[:, 1] - y)))
            clearance = footprint_clearance(cmd.path, road.preview_s, body, vp.length / 2, vp.width / 2)
            i = int(np.clip(np.searchsorted(road.preview_s, max(d, 0)), 0, len(road.preview_s) - 1))
            center = road.preview_centerline[i]
            tangent = np.gradient(road.preview_centerline, axis=0)[i]
            normal = np.array([-tangent[1], tangent[0]]) / max(np.linalg.norm(tangent), 1e-6)
            planned = np.array([np.interp(max(d, 0), road.preview_s, cmd.path[:, k]) for k in (0, 1)])
            planned_offset = float((planned - center) @ normal)
            t = max(0.0, d)
            grid = np.arange(max(0.0, t - 8), min(float(road.preview_s[-1]), t + 8) + .001, .25)
            if len(grid) > 4:
                p = np.column_stack([np.interp(grid, road.preview_s, cmd.path[:, k]) for k in (0, 1)])
                p1 = np.gradient(p, grid, axis=0)
                p2 = np.gradient(p1, grid, axis=0)
                curv = (p1[:, 0] * p2[:, 1] - p1[:, 1] * p2[:, 0]) / np.maximum(np.linalg.norm(p1, axis=1) ** 3, 1e-6)
                path_kappa = float(np.max(np.abs(curv)))
                road_kappa = float(np.max(np.abs(np.interp(grid, road.preview_s, road.preview_curvature))))
                v_safe = float(math.sqrt(controller.a_lat / max(path_kappa, 1e-4)))
            wl = float(road.preview_width_left[i])
            wr = float(road.preview_width_right[i])
            left_limit = wl - vp.width / 2 - .22
            right_limit = wr - vp.width / 2 - .22
            tight_ids = set()
            for k, other in enumerate(road.obstacles):
                if other is ob:
                    continue
                sep = abs(other.distance - ob.distance)
                if sep < 8 and (ob.lateral_max + ob.lateral_min) * (other.lateral_max + other.lateral_min) < 0:
                    gap = max(0.0, max(ob.lateral_min, other.lateral_min) - min(ob.lateral_max, other.lateral_max))
                    if gap < vp.width + .5:
                        tight_ids.add(k)
            tight = bool(tight_ids)
            required = vp.width / 2 + (.15 if tight else .8)
            candidates = []
            if ob.lateral_max + required <= left_limit:
                candidates.append(ob.lateral_max + required)
            if ob.lateral_min - required >= -right_limit:
                candidates.append(ob.lateral_min - required)
            no_candidate = not candidates
            if candidates:
                target = min(candidates, key=abs)
                bypass = "left" if target > 0 else "right"
                bump_half = 20.0
                for other in road.obstacles:
                    if other is ob:
                        continue
                    sep = abs(other.distance - ob.distance)
                    if sep < bump_half and (target > 0) != ((other.lateral_min + other.lateral_max) < 0):
                        bump_half = max(sep - .5, 3.0)
        # Physical clearance at the logged vehicle pose nearest the event.
        actual_cone = cone - np.array([x, y])
        longitudinal = actual_cone[0] * math.cos(yaw) + actual_cone[1] * math.sin(yaw)
        lateral = -actual_cone[0] * math.sin(yaw) + actual_cone[1] * math.cos(yaw)
        actual_margin = max(abs(longitudinal) - vp.length / 2 - .1, abs(lateral) - vp.width / 2 - .1)
        samples.append({"t": round(obs.t, 3), "dt_hit": round(obs.t - hit["t"], 3),
                        "progress": obs.progress, "distance": d, "obstacle_visible": ob is not None,
                        "obstacle_interval": [ob.lateral_min, ob.lateral_max] if ob else None,
                        "widths": [wl, wr] if ob else None, "planned_offset": planned_offset,
                        "actual_offset": road.lateral_offset, "heading_error_deg": math.degrees(road.heading_error),
                        "planned_footprint_margin": clearance, "actual_cone_margin": actual_margin,
                        "boundary_margin": float(row["boundary_margin"]), "path_error": float(row["path_err"]),
                        "speed": obs.speed, "target_speed": cmd.target_speed,
                        "lookahead": cmd.debug["lookahead"], "steer": cmd.steer,
                        "steer_saturated": abs(cmd.steer) >= .999, "throttle": cmd.throttle, "brake": cmd.brake,
                        "road_curvature_max": road_kappa, "path_curvature_max": path_kappa,
                        "path_safe_speed": v_safe, "ay": obs.ay, "yaw_rate": obs.yaw_rate,
                        "rear_slip_deg": cmd.debug["rear_slip_deg"], "tight_pair": tight,
                        "no_candidate": no_candidate, "bypass": bypass, "bump_half_length": bump_half})
        if obs.t > hit["t"] + 1.05:
            break
    return {"seed": seed, "variant": summary["track"]["name"], "hit": hit,
            "cone_index": cone_index, "mapped": mapped, "obstacle_gid": gid,
            "cone_position": cone.tolist(), "vehicle_width": vp.width,
            "obstacle_lateral_interval": [float(tr.obstacle_lat[tr.obstacle_gid == gid].min()),
                                          float(tr.obstacle_lat[tr.obstacle_gid == gid].max())] if gid is not None else None,
            "replay_max_command_error": worst_replay_error, "samples": samples}


def main():
    report = json.loads((BATCH / "report.json").read_text())
    seeds = [r["seed"] for r in report["unseen_rows"] if r["cones"]]
    out = [analyze_seed(seed) for seed in seeds]
    OUTPUT.write_text(json.dumps(out, indent=2))
    print(f"Analyzed {len(out)} penalized runs; wrote {OUTPUT}")
    for item in out:
        samples = [s for s in item["samples"] if s["obstacle_visible"] and -.75 <= s["dt_hit"] <= -.25]
        s = min(samples, key=lambda s: abs(s["dt_hit"] + .5)) if samples else None
        print(item["seed"], "gid", item["obstacle_gid"], "t", round(item["hit"]["t"], 2),
              "replay", round(item["replay_max_command_error"], 4),
              "d", round(s["distance"], 1) if s else None,
              "plan", round(s["planned_footprint_margin"], 2) if s else None,
              "nocand", s["no_candidate"] if s else None,
              "offset", round(s["planned_offset"], 2) if s else None,
              "actual", round(s["actual_offset"], 2) if s else None,
              "v", round(s["speed"], 1) if s else None,
              "safe", round(s["path_safe_speed"], 1) if s else None)


if __name__ == "__main__":
    main()
