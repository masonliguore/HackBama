"""Train a compact regularized logistic risk model with a track-grouped split."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["speed", "rear_slip", "lateral", "heading", "demand",
            "ay_use", "boundary", "obstacle", "delay", "yaw_residual"]


def _f(row, key, default=0.0):
    try:
        x = float(row[key])
        return x if math.isfinite(x) else default
    except (KeyError, TypeError, ValueError):
        return default


def load_run(folder: Path):
    summary = json.loads((folder / "summary.json").read_text())
    events = json.loads((folder / "events.json").read_text())
    vp = summary["vehicle"]
    delay = float(summary.get("perturbation", {}).get("actuation_delay_steps", 0.0))
    danger_times = [float(e["t"]) for e in events if e["kind"] in {"cone_hit", "off_course", "missed_gate"}]
    rows = list(csv.DictReader((folder / "telemetry.csv").open()))
    ctrl = [r for r in rows if _f(r, "ctrl_step") > 0.5 and r.get("dbg_planned_curvature") not in (None, "", "nan")]
    unsafe = np.array([abs(_f(r, "dbg_rear_slip_deg")) > 7.0 or _f(r, "boundary_margin", 9.0) < 0.20
                       or _f(r, "path_err") > 0.9 for r in ctrl])
    times = np.array([_f(r, "t") for r in ctrl])
    labels = np.zeros(len(ctrl), dtype=float)
    for i, t in enumerate(times):
        future_state = unsafe[i:min(i + 21, len(unsafe))].any()
        future_event = any(t <= et <= t + 1.0 for et in danger_times)
        labels[i] = float(future_state or future_event)
    X = np.array([[_f(r, "speed"), abs(_f(r, "dbg_rear_slip_deg")), abs(_f(r, "lateral")),
                   abs(_f(r, "dbg_feat_heading_error")), _f(r, "dbg_grip_demand"),
                   _f(r, "dbg_feat_ay_use"), _f(r, "dbg_feat_boundary"),
                   _f(r, "dbg_feat_obstacle"), delay, _f(r, "dbg_feat_yaw_residual")]
                  for r in ctrl], dtype=float)
    return X, labels, summary["track"]["name"]


def metrics(y, p, threshold=0.35):
    pred = p >= threshold
    pos = y > 0.5
    tp = int((pred & pos).sum())
    fn = int((~pred & pos).sum())
    fp = int((pred & ~pos).sum())
    tn = int((~pred & ~pos).sum())
    recall = tp / max(tp + fn, 1)
    return {"observations": len(y), "positive": int(pos.sum()), "positive_fraction": float(pos.mean()),
            "recall": recall, "false_negative_rate": 1.0 - recall,
            "precision": tp / max(tp + fp, 1), "brier": float(np.mean((p - y) ** 2)),
            "confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn}}


def main() -> None:
    loaded = [load_run(p) for p in sorted((ROOT / "runs").glob("*mltrain*/"))
              if (p / "summary.json").exists()]
    groups = sorted({g for _, _, g in loaded})
    validation_groups = set(groups[::4])
    train = [(x, y) for x, y, g in loaded if g not in validation_groups]
    valid = [(x, y) for x, y, g in loaded if g in validation_groups]
    X = np.vstack([x for x, _ in train]); y = np.concatenate([v for _, v in train])
    Xv = np.vstack([x for x, _ in valid]); yv = np.concatenate([v for _, v in valid])
    mean = X.mean(0); scale = X.std(0); scale[scale < 1e-6] = 1.0
    Z = np.clip((X - mean) / scale, -6.0, 6.0)
    Zv = np.clip((Xv - mean) / scale, -6.0, 6.0)
    w = np.zeros(Z.shape[1]); b = 0.0
    pos_weight = min(max((len(y) - y.sum()) / max(y.sum(), 1.0), 1.0), 12.0)
    sample_w = np.where(y > 0.5, pos_weight, 1.0)
    for step in range(2500):
        logits = np.clip(Z @ w + b, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-logits))
        err = (p - y) * sample_w
        lr = 0.08 / (1.0 + step / 900.0)
        w -= lr * ((Z.T @ err) / sample_w.sum() + 0.015 * w)
        b -= lr * float(err.sum() / sample_w.sum())
    pt = 1.0 / (1.0 + np.exp(-np.clip(Z @ w + b, -30.0, 30.0)))
    pv = 1.0 / (1.0 + np.exp(-np.clip(Zv @ w + b, -30.0, 30.0)))
    report = {"architecture": "regularized logistic regression, 10 inputs, 11 parameters",
              "features": FEATURES, "training_courses": len(set(groups) - validation_groups),
              "validation_courses": len(validation_groups), "validation_groups": sorted(validation_groups),
              "mean": mean.tolist(), "scale": scale.tolist(), "weights": w.tolist(), "bias": float(b),
              "train": metrics(y, pt), "validation": metrics(yv, pv)}
    out = ROOT / "experiments" / "risk_model.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
