"""Reproducible, read-only V4 evaluation on unseen generated courses."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np

from autocross.config import load_sim_config
from autocross.runner import run
from autocross.track import save
from autocross.trackgen import generate_open


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission/hackbama.py"
OUT = ROOT / "runs" / f"final_validation_{datetime.now():%Y%m%d_%H%M%S}"


def collect(result, seed, kind, variant):
    m = result["metrics"]
    p = m["penalties"]
    events = json.loads((Path(result["out_dir"]) / "events.json").read_text())
    first = next((e for e in events if e["kind"] in ("cone_hit", "off_course", "missed_gate")), None)
    return {
        "seed": seed, "kind": kind, "variant": variant, "track": result["track"]["name"],
        "finished": m["completion"]["finished"], "dnf": m["completion"]["dnf_reason"],
        "time_s": m["completion"]["time_s"], "score": result["score"]["technical_points"],
        "cones": p["cone_hit"], "off_course": p["off_course"], "missed_gates": p["missed_gate"],
        "errors": m["compute"]["errors"], "overruns": m["compute"]["overruns"],
        "clipped_fraction": m["dynamics"]["clipped_cmd_frac"],
        "max_path_error": m["deviation"]["path_err_max_m"], "first_penalty": first,
        "step_p50_ms": m["compute"]["step_ms_p50"],
        "step_p95_ms": m["compute"]["step_ms_p95"],
        "step_p99_ms": m["compute"]["step_ms_p99"],
        "step_max_ms": m["compute"]["step_ms_max"],
        "out_dir": result["out_dir"],
    }


def aggregate(rows):
    scores = np.array([r["score"] for r in rows])
    times = np.array([r["time_s"] for r in rows if r["time_s"] is not None])
    return {
        "runs": len(rows), "finished": sum(r["finished"] for r in rows),
        "clean": sum(r["finished"] and not any(r[k] for k in
                     ("cones", "off_course", "missed_gates", "errors", "overruns")) for r in rows),
        "cones": sum(r["cones"] for r in rows),
        "off_course": sum(r["off_course"] for r in rows),
        "missed_gates": sum(r["missed_gates"] for r in rows),
        "errors": sum(r["errors"] for r in rows), "overruns": sum(r["overruns"] for r in rows),
        "invalid_commands": sum(r["clipped_fraction"] > 0 for r in rows),
        "score_mean": float(scores.mean()), "score_median": float(np.median(scores)),
        "score_p10": float(np.percentile(scores, 10)), "score_worst": float(scores.min()),
        "time_mean_s": float(times.mean()) if len(times) else None,
        "time_median_s": float(np.median(times)) if len(times) else None,
        "max_path_error_m": max(r["max_path_error"] for r in rows),
        "max_run_p99_ms": max(r["step_p99_ms"] for r in rows),
        "max_step_ms": max(r["step_max_ms"] for r in rows),
    }


def main():
    OUT.mkdir(parents=True)
    cfg = load_sim_config()
    cfg["output"]["plot"] = False
    rows = []
    tracks = []
    variants = [
        ("normal", 450, 5.5, 4), ("technical", 550, 5.5, 4),
        ("obstacle_heavy", 450, 5.5, 8), ("narrow", 450, 5.0, 5),
        ("wide", 450, 6.5, 6),
    ]
    for i in range(50):
        seed = 2000 + i
        variant, length, width, obstacles = variants[i % len(variants)]
        spec = generate_open(seed, target_length=length, width=width, n_obstacles=obstacles)
        path = OUT / "tracks" / f"track_{seed}.yaml"
        path.parent.mkdir(exist_ok=True)
        save(spec, path)
        tracks.append(path)
        result = run(cfg, str(SUBMISSION), str(path), backend="bicycle", out_dir=OUT / "unseen" / str(seed),
                     verbose=False)
        row = collect(result, seed, "unseen", variant)
        rows.append(row)
        print(f"unseen {i+1}/50 seed {seed}: {'finish' if row['finished'] else 'DNF'}, "
              f"penalties {row['cones']}/{row['off_course']}/{row['missed_gates']}", flush=True)
        (OUT / "progress.json").write_text(json.dumps(rows, indent=2))
    perturbations = {
        "nominal": {}, "friction_90": {"friction_scale": .9},
        "friction_80": {"friction_scale": .8},
        "delay_2": {"actuation_delay_steps": 2},
        "friction_90_delay_2": {"friction_scale": .9, "actuation_delay_steps": 2},
        "start_offset": {"start_lateral_offset": .6},
        "steering_bias": {"steer_bias": .02},
        "heavy_vehicle": {"mass_scale": 1.15},
    }
    robust = []
    for path in tracks[:5]:
        seed = int(path.stem.split("_")[1])
        for variant, perturb in perturbations.items():
            result = run(cfg, str(SUBMISSION), str(path), backend="bicycle", perturb=perturb,
                         out_dir=OUT / "robustness" / f"{seed}_{variant}", verbose=False)
            row = collect(result, seed, "robustness", variant)
            robust.append(row)
            print(f"robust {len(robust)}/40 {seed} {variant}: "
                  f"{'finish' if row['finished'] else 'DNF'}, {row['cones']}/{row['off_course']}/{row['missed_gates']}",
                  flush=True)
            (OUT / "robust_progress.json").write_text(json.dumps(robust, indent=2))
    report = {"unseen": aggregate(rows), "robustness": {key: aggregate([r for r in robust if r["variant"] == key])
                                                      for key in perturbations},
              "unseen_rows": rows, "robustness_rows": robust}
    (OUT / "report.json").write_text(json.dumps(report, indent=2))
    print(OUT, flush=True)


if __name__ == "__main__":
    main()
