"""Run the deterministic controller on training tracks under labeled perturbations."""
from __future__ import annotations

import os
import subprocess
import glob
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
SCENARIOS = {
    "nominal": [],
    "lowgrip": ["--perturb", "friction_scale=0.8"],
    "delay": ["--perturb", "actuation_delay_steps=2"],
    "lowgrip_delay": ["--perturb", "friction_scale=0.8", "--perturb", "actuation_delay_steps=2"],
}


def main() -> None:
    env = dict(os.environ, MPLCONFIGDIR="/tmp/hackbama-ml-mpl")
    controller = ROOT / "controllers" / "hackbama_hybrid.py"
    for track in sorted((ROOT / "reliability_tracks" / "train").glob("*.yaml")):
        for scenario, args in SCENARIOS.items():
            team = f"mltrain_{track.stem}_{scenario}"
            if glob.glob(str(ROOT / "runs" / f"*_{team}_*" / "summary.json")):
                continue
            cmd = [str(PYTHON), "-m", "autocross", "run", "-c", str(controller),
                   "-t", str(track), "--backend", "bicycle", "--team", team, "--quiet", *args]
            print(track.stem, scenario, flush=True)
            subprocess.run(cmd, cwd=ROOT, env=env, check=False)


if __name__ == "__main__":
    main()
