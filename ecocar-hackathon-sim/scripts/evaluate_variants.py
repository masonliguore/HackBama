"""Evaluate controller variants on the same held-out generated courses."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
TRACKS = sorted((ROOT / "reliability_tracks" / "heldout").glob("*.yaml"))
VARIANTS = {
    "original": (ROOT / "backups" / "hackbama_final_verified.py", None),
    "deterministic": (ROOT / "controllers" / "hackbama_hybrid.py", ROOT / "experiments" / "ml_off.yaml"),
    "ml": (ROOT / "controllers" / "hackbama_hybrid.py", None),
}

def run_one(name: str, controller: Path, cfg: Path | None, track: Path) -> dict:
    team = f"heldout_{name}_{track.stem}"
    existing = sorted((ROOT / "runs").glob(f"*_{team}_*/summary.json"))
    if existing:
        return json.loads(existing[-1].read_text())
    cmd = [str(PYTHON), "-m", "autocross", "run", "-c", str(controller), "-t", str(track),
           "--backend", "bicycle", "--team", team, "--quiet"]
    if cfg:
        cmd += ["--controller-config", str(cfg)]
    env = dict(os.environ, MPLCONFIGDIR="/tmp/hackbama-ml-mpl")
    subprocess.run(cmd, cwd=ROOT, env=env, check=False)
    files = sorted((ROOT / "runs").glob(f"*_{team}_*/summary.json"))
    if not files:
        return {"error": "missing summary", "track": track.stem, "variant": name}
    return json.loads(files[-1].read_text())

def metrics(rows: list[dict]) -> dict:
    scores = [r.get("score", {}) for r in rows if "score" in r]
    def val(r, *keys, default=0.0):
        x = r
        for k in keys:
            if not isinstance(x, dict): return default
            x = x.get(k)
        return x if isinstance(x, (int, float)) else default
    finished = [val(r, "metrics", "completion", "finished", default=False) for r in rows]
    penalties = [sum(val(r, "metrics", "penalties", k) for k in ("cone_hit", "off_course", "missed_gate", "obstacle_hits")) for r in rows]
    times = [val(r, "metrics", "completion", "time_s") for r in rows]
    path_err = [val(r, "metrics", "deviation", "path_err_mean_m") for r in rows]
    return {"courses": len(rows), "finished": sum(bool(x) for x in finished),
            "zero_penalty": sum(p == 0 for p in penalties),
            "finish_rate": sum(bool(x) for x in finished) / len(rows) if rows else 0,
            "mean_time_s": sum(times)/len(times) if times else 0,
            "mean_path_error_m": sum(path_err)/len(path_err) if path_err else 0,
            "total_penalties": sum(penalties)}

def main() -> None:
    all_results = {}
    for name, (controller, cfg) in VARIANTS.items():
        rows = [run_one(name, controller, cfg, track) for track in TRACKS]
        all_results[name] = {"summary": metrics(rows), "rows": rows}
        print(name, json.dumps(all_results[name]["summary"], sort_keys=True), flush=True)
    out = ROOT / "experiments" / "heldout_variant_results.json"
    out.write_text(json.dumps(all_results, indent=2))

if __name__ == "__main__":
    main()
