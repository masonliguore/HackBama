"""Read saved final-run telemetry and render presentation stills; no simulation changes."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autocross.api import Observation, VehicleParams  # noqa: E402
from autocross.geometry import body_to_world  # noqa: E402
from autocross.perception import RoadModelSensor  # noqa: E402
from autocross.track import load  # noqa: E402
from submission.hackbama import HackBamaController  # noqa: E402


OUT = ROOT / "demo_assets"
VALIDATION = ROOT / "runs/v7_cycle_20261017/validation"
DEVELOPMENT = ROOT / "runs/v7_cycle_20261017/development"
OFFICIAL = ROOT / "runs/20261017-162835_selftest"


def rows_for(run_dir):
    with (run_dir / "telemetry.csv").open(newline="") as stream:
        return list(csv.DictReader(stream))


def published_path(run_dir, station, lead=14.0):
    """Replay the frozen submission to recover one unlogged published path."""
    summary = json.loads((run_dir / "summary.json").read_text())
    tr = load(summary["track"]["path"])
    vp = VehicleParams(**summary["vehicle"])
    sensor = RoadModelSensor(tr, summary["config"]["road_model"], np.random.default_rng(0))
    controller = HackBamaController()
    controller.on_start(None, vp)
    rows = rows_for(run_dir)
    x0, y0, yaw0 = tr.spawn_pose()
    chosen = None
    best = float("inf")
    for j in range(0, len(rows), 2):
        prev = rows[j - 1] if j else None
        val = lambda key, initial=0.0: float(prev[key]) if prev else initial
        x, y, yaw = val("x", x0), val("y", y0), val("yaw", yaw0)
        road = sensor.measure(x, y, yaw, val("progress"))
        obs = Observation(val("t"), j // 2, x, y, yaw, val("vx"), val("vy"),
                          val("yaw_rate"), val("ax"), val("ay"), val("speed"),
                          val("app_steer"), val("app_throttle"), val("app_brake"),
                          val("progress"), 0, True, road=road)
        cmd = controller.step(obs)
        distance = station - obs.progress
        if 0 < distance < road.range_m and abs(distance - lead) < best and cmd.path is not None:
            best = abs(distance - lead)
            chosen = (body_to_world(cmd.path, x, y, yaw), road.preview_s.copy(),
                      obs.progress, obs.speed, cmd.target_speed)
        if obs.progress > station + 2:
            break
    if chosen is None:
        raise ValueError(f"No published path near station {station} in {run_dir}")
    return chosen


def segment_plot(run_dir, gids, output_name, title, *, show_plan=False, compare_dir=None):
    summary = json.loads((run_dir / "summary.json").read_text())
    tr = load(summary["track"]["path"])
    stations = [float(tr.obstacles[gid]["s"]) for gid in gids]
    low, high = min(stations) - 25, max(stations) + 25
    grid = np.arange(low, high + .01, .25)
    center, heading, _, wl, wr, _ = tr.sample(grid)
    normal = np.column_stack((-np.sin(heading), np.cos(heading)))
    left = center + normal * wl[:, None]
    right = center - normal * wr[:, None]

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.plot(*left.T, color="#4d6d93", lw=2, label="road boundaries")
    ax.plot(*right.T, color="#4d6d93", lw=2)
    ax.plot(*center.T, color="#929aa3", lw=1.5, ls="--", label="centerline")
    obs_pts = tr.obstacle_cones[np.isin(tr.obstacle_gid, gids)]
    ax.scatter(*obs_pts.T, c="#e87722", edgecolors="#5b2c06", marker="^", s=90,
               zorder=7, label="obstacle cones")
    rows = rows_for(run_dir)
    progress = np.array([float(row["progress"]) for row in rows])
    traj = np.array([[float(row["x"]), float(row["y"])] for row in rows])
    mask = (progress >= low) & (progress <= high)
    ax.plot(*traj[mask].T, color="#159764", lw=3.5, label="V7 actual trajectory", zorder=5)

    if compare_dir is not None:
        old = rows_for(compare_dir)
        old_progress = np.array([float(row["progress"]) for row in old])
        old_traj = np.array([[float(row["x"]), float(row["y"])] for row in old])
        old_mask = (old_progress >= low) & (old_progress <= high)
        ax.plot(*old_traj[old_mask].T, color="#c94b52", lw=2, ls=":",
                label="V6 actual trajectory", zorder=4)

    if show_plan:
        path, preview, at_progress, speed, target = published_path(run_dir, stations[0])
        # The published path is vehicle-relative at the selected observation.
        visible = preview <= min(35, high - at_progress)
        ax.plot(*path[visible].T, color="#173ea2", lw=2.5, ls="-.",
                label=f"V7 published path ({speed:.1f} m/s; target {target:.1f})", zorder=6)
        ax.scatter(path[0, 0], path[0, 1], s=75, c="#173ea2", marker="o", zorder=7)

    points = np.vstack((center, left, right))
    pad = 6
    ax.set_xlim(points[:, 0].min() - pad, points[:, 0].max() + pad)
    ax.set_ylim(points[:, 1].min() - pad, points[:, 1].max() + pad)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=.15)
    fig.tight_layout()
    output = OUT / output_name
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def main():
    OUT.mkdir(exist_ok=True)
    normal = OFFICIAL / "practice_basic_bicycle/report.png"
    (OUT / "normal_clean.png").write_bytes(normal.read_bytes())
    print(OUT / "normal_clean.png")
    print(segment_plot(OFFICIAL / "practice_obstacles_bicycle", [0],
                       "single_obstacle_bypass.png", "Single obstacle bypass — official clean run"))
    print(segment_plot(VALIDATION / "v7/4014", [0, 1],
                       "tight_s_weave.png", "Tight opposite-side obstacle pair — V7 clean run"))
    print(segment_plot(DEVELOPMENT / "v7/3033", [3, 4],
                       "visible_s_weave.png", "Opposite-side S-weave — V7 clean run"))
    print(segment_plot(VALIDATION / "v7/4003", [0],
                       "narrow_fallback.png", "Narrow-road fallback — V7 clean, V6 cone hit",
                       show_plan=True, compare_dir=VALIDATION / "v6/4003"))


if __name__ == "__main__":
    main()
