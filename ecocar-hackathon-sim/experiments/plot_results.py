"""Create a compact evidence plot from the official selftest telemetry."""
from pathlib import Path
import csv
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1] / "runs" / "20261017-115525_selftest"
fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=False)
for course in ("practice_technical", "practice_obstacles"):
    with (root / f"{course}_bicycle" / "telemetry.csv").open() as f:
        rows = list(csv.DictReader(f))
    keys = rows[0]
    t = [float(r.get("time_s", i * 0.05)) for i, r in enumerate(rows)]
    speed_key = "speed" if "speed" in keys else "v"
    speed = [float(r[speed_key]) for r in rows]
    axes[0].plot(t, speed, label=course)
    if "path_error" in keys:
        axes[1].plot(t, [float(r["path_error"]) for r in rows], label=course)
axes[0].set_ylabel("speed (m/s)")
axes[1].set_ylabel("path error (m)")
axes[1].set_xlabel("time (s)")
for ax in axes:
    ax.grid(alpha=0.25)
    ax.legend()
fig.suptitle("HackBama verified submission telemetry")
fig.tight_layout()
fig.savefig(Path(__file__).resolve().parent / "verified_telemetry.png", dpi=150)
