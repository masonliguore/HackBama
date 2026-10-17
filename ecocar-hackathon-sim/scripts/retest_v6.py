"""Compare V6 against the preserved V4 validation courses and perturbations."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from autocross.config import load_sim_config
from autocross.runner import run

from final_validate_submission import aggregate, collect


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "runs/final_validation_20261017_151905"
CONTROLLER = ROOT / "controllers/hackbama_v6.py"
OUT = ROOT / "runs" / f"v6_retest_{datetime.now():%Y%m%d_%H%M%S}"
PERTURBATIONS = {
    "nominal": {}, "friction_90": {"friction_scale": .9},
    "friction_80": {"friction_scale": .8},
    "delay_2": {"actuation_delay_steps": 2},
    "friction_90_delay_2": {"friction_scale": .9, "actuation_delay_steps": 2},
    "start_offset": {"start_lateral_offset": .6},
    "steering_bias": {"steer_bias": .02},
    "heavy_vehicle": {"mass_scale": 1.15},
}


def main():
    if not (BASE / "report.json").exists():
        raise FileNotFoundError("preserved V4 batch is required for a matched retest")
    baseline = json.loads((BASE / "report.json").read_text())
    tracks = [BASE / "tracks" / f"track_{seed}.yaml" for seed in range(2000, 2050)]
    if not all(p.exists() for p in tracks):
        raise FileNotFoundError("one or more preserved tracks are missing")
    cfg = load_sim_config()
    cfg["output"]["plot"] = False
    OUT.mkdir(parents=True)
    source_hash = hashlib.sha256(CONTROLLER.read_bytes()).hexdigest()
    unseen = []
    for i, path in enumerate(tracks):
        seed = 2000 + i
        variant = baseline["unseen_rows"][i]["variant"]
        result = run(cfg, str(CONTROLLER), str(path), backend="bicycle",
                     out_dir=OUT / "unseen" / str(seed), verbose=False)
        row = collect(result, seed, "unseen", variant)
        unseen.append(row)
        print(f"unseen {i+1}/50 seed {seed}: "
              f"{'finish' if row['finished'] else 'DNF'}, {row['cones']}/{row['off_course']}/{row['missed_gates']}",
              flush=True)
        (OUT / "unseen_progress.json").write_text(json.dumps(unseen, indent=2))
    robust = []
    for path in tracks[:5]:
        seed = int(path.stem.split("_")[1])
        for name, perturb in PERTURBATIONS.items():
            result = run(cfg, str(CONTROLLER), str(path), backend="bicycle", perturb=perturb,
                         out_dir=OUT / "robustness" / f"{seed}_{name}", verbose=False)
            row = collect(result, seed, "robustness", name)
            robust.append(row)
            print(f"robust {len(robust)}/40 {seed} {name}: "
                  f"{'finish' if row['finished'] else 'DNF'}, {row['cones']}/{row['off_course']}/{row['missed_gates']}",
                  flush=True)
            (OUT / "robust_progress.json").write_text(json.dumps(robust, indent=2))
    after_hash = hashlib.sha256(CONTROLLER.read_bytes()).hexdigest()
    if after_hash != source_hash:
        raise RuntimeError("V6 controller changed during the comparison")
    report = {
        "controller": str(CONTROLLER), "sha256": source_hash,
        "v4_sha256": "c911e116540a7c3fa78b39fb60d3c75ae4cb151310504474ea63e8199b92ec0d",
        "unseen": aggregate(unseen),
        "robustness": {key: aggregate([r for r in robust if r["variant"] == key]) for key in PERTURBATIONS},
        "unseen_rows": unseen, "robustness_rows": robust,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2))
    print(OUT, flush=True)


if __name__ == "__main__":
    main()
