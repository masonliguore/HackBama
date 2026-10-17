"""Generate fixed, disjoint train/tune/evaluation track sets."""
from __future__ import annotations

from pathlib import Path

from autocross.track import save
from autocross.trackgen import generate_open


ROOT = Path(__file__).resolve().parents[1]
SETS = {"train": range(100, 112), "tune": range(200, 206), "heldout": range(300, 320)}


def main() -> None:
    for split, seeds in SETS.items():
        out = ROOT / "reliability_tracks" / split
        out.mkdir(parents=True, exist_ok=True)
        for seed in seeds:
            path = out / f"track_{seed}.yaml"
            if path.exists():
                continue
            spec = generate_open(seed, target_length=520.0, width=5.5, n_obstacles=4)
            spec["name"] = f"reliability_{split}_{seed}"
            save(spec, path)
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
