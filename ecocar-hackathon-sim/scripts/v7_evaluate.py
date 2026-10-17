"""Matched V6/V7 development and frozen-validation runs on generated courses."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from autocross.config import load_sim_config
from autocross.runner import run
from autocross.track import save
from autocross.trackgen import generate_open
from final_validate_submission import aggregate, collect


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/v7_cycle_20261017"
CONTROLLERS = {
    "v6": ROOT / "controllers/hackbama_v6.py",
    "v7": ROOT / "controllers/hackbama_v7_candidate.py",
}
VARIANTS = [
    ("normal", 450, 5.5, 4), ("technical", 550, 5.5, 4),
    ("obstacle_heavy", 450, 5.5, 8), ("narrow", 450, 5.0, 5),
    ("wide", 450, 6.5, 6),
]
PERTURBATIONS = {
    "nominal": {}, "friction_90": {"friction_scale": .9},
    "friction_80": {"friction_scale": .8},
    "delay_2": {"actuation_delay_steps": 2},
    "friction_90_delay_2": {"friction_scale": .9, "actuation_delay_steps": 2},
    "start_offset": {"start_lateral_offset": .6},
    "steering_bias": {"steer_bias": .02},
    "heavy_vehicle": {"mass_scale": 1.15},
}


def course(phase, index):
    seed = (3000 if phase == "development" else 4000) + index
    if phase == "development":
        variant, length, width, obstacles = (("narrow", 450, 5.0, 5) if index % 2 == 0
                                               else ("obstacle_heavy", 450, 5.5, 8))
    else:
        variant, length, width, obstacles = VARIANTS[index % len(VARIANTS)]
    path = OUT / phase / "tracks" / f"track_{seed}.yaml"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save(generate_open(seed, target_length=length, width=width, n_obstacles=obstacles), path)
    return seed, variant, path


def evaluate(phase, count):
    cfg = load_sim_config()
    cfg["output"]["plot"] = False
    phase_out = OUT / phase
    rows = {name: [] for name in CONTROLLERS}
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in CONTROLLERS.items()}
    for index in range(count):
        seed, variant, path = course(phase, index)
        for name, controller in CONTROLLERS.items():
            result = run(cfg, str(controller), str(path), backend="bicycle",
                         out_dir=phase_out / name / str(seed), verbose=False)
            row = collect(result, seed, phase, variant)
            rows[name].append(row)
            print(f"{phase} {index+1}/{count} {name} seed {seed}: "
                  f"{int(row['finished'])} finish, {row['cones']} cones", flush=True)
        (phase_out / "progress.json").write_text(json.dumps(rows, indent=2))
    if hashes != {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in CONTROLLERS.items()}:
        raise RuntimeError("Controller changed during batch")
    report = {"phase": phase, "sha256": hashes, "summary": {name: aggregate(value) for name, value in rows.items()},
              "rows": rows}
    (phase_out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["summary"], indent=2), flush=True)


def robustness():
    cfg = load_sim_config()
    cfg["output"]["plot"] = False
    phase_out = OUT / "robustness"
    rows = {name: [] for name in CONTROLLERS}
    for index in range(5):
        seed, _, path = course("validation", index)
        for variant, perturb in PERTURBATIONS.items():
            for name, controller in CONTROLLERS.items():
                result = run(cfg, str(controller), str(path), backend="bicycle", perturb=perturb,
                             out_dir=phase_out / name / f"{seed}_{variant}", verbose=False)
                row = collect(result, seed, "robustness", variant)
                rows[name].append(row)
                print(f"robustness {name} {seed} {variant}: {row['cones']} cones", flush=True)
        (phase_out / "progress.json").write_text(json.dumps(rows, indent=2))
    report = {name: {variant: aggregate([r for r in value if r["variant"] == variant])
                     for variant in PERTURBATIONS} for name, value in rows.items()}
    (phase_out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


def diagnostic():
    """Retest inspected V6 failures as a targeted check, never as a holdout."""
    cfg = load_sim_config()
    cfg["output"]["plot"] = False
    source = ROOT / "runs/v6_retest_20261017_153913/report.json"
    old_rows = [r for r in json.loads(source.read_text())["unseen_rows"] if r["cones"]]
    rows = []
    for old in old_rows:
        seed = old["seed"]
        track = ROOT / "runs/final_validation_20261017_151905/tracks" / f"track_{seed}.yaml"
        result = run(cfg, str(CONTROLLERS["v7"]), str(track), backend="bicycle",
                     out_dir=OUT / "diagnostic" / str(seed), verbose=False)
        new = collect(result, seed, "diagnostic", old["variant"])
        rows.append({"seed": seed, "before": old, "after": new})
        print(f"diagnostic {seed}: {old['cones']} -> {new['cones']} cones", flush=True)
    path = OUT / "diagnostic/report.json"
    path.write_text(json.dumps(rows, indent=2))
    print(f"Wrote {path}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["development", "validation", "robustness", "diagnostic"])
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()
    if args.phase == "robustness":
        robustness()
    elif args.phase == "diagnostic":
        diagnostic()
    else:
        evaluate(args.phase, args.count)


if __name__ == "__main__":
    main()
