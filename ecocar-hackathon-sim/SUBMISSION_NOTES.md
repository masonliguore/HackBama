# HackBama EcoCAR autonomous autocross submission

Submit **`submission/hackbama.py`** as the single-file team controller. It defines
`HackBamaController`, uses only `numpy` and `autocross.api`, and reads the live
`Observation.road` preview. It does not read course files or use network access.
The source is also in `controllers/hackbama.py`; the verified backup is
`backups/hackbama_final_verified.py`.

## Controller

1. **Path planning:** Start from the perceived centerline. For each detected
   obstacle group, compare left and right bypasses against the visible corridor
   and vehicle width. Apply a 20 m half-length cosine shift toward the shorter
   feasible bypass. Combine nearby same-side obstacles by the maximum required
   shift, avoiding a summed shift into the outer cones. Publish this full path
   every control step.
2. **Steering:** Track the published path with speed-adaptive pure pursuit. If
   the vehicle interface reports actuation delay, increase lookahead and reduce
   target speed.
3. **Speed:** Convert preview curvature to a lateral-acceleration speed limit,
   then apply braking-distance constraints to every preview sample. Use a
   conservative limit at the unknown end of the 40 m preview and a lower speed
   through obstacle bypasses. Apply a PI speed controller, with throttle limited
   by the lateral grip currently in use. Throttle and brake are exclusive.

No neural network or pretrained model is used. The controller plans from the
current observation only; it does not use track-specific coordinates.

## Public-course evidence

Official bicycle-backend selftests with the repository's unmodified scoring and
simulation configuration: baseline `runs/20261017-100358_selftest`, submitted
file `runs/20261017-102913_selftest`. All five runs finished. Penalties below
are cone hits; both versions had zero off-course and missed-gate events on these
runs. Path values are mean/maximum error in metres. Scores are **technical
points out of 75**, with no judged innovation points.

| Course | Baseline s | HackBama s | Cones baseline → HackBama | Path error baseline → HackBama | HackBama p99 step ms | Points baseline → HackBama |
|---|---:|---:|---:|---:|---:|---:|
| hackathon_test | 56.0 | 56.6 | 2 → 0 | 0.17/0.57 → 0.18/0.57 | 3.5 | 61.9 → 65.4 |
| practice_basic | 35.9 | 35.1 | 0 → 0 | 0.18/0.59 → 0.19/0.59 | 2.5 | 66.2 → 66.8 |
| practice_loop | 92.9 | 90.8 | 0 → 0 | 0.14/0.58 → 0.15/0.57 | 6.9 | 66.5 → 66.3 |
| practice_obstacles | 61.2 | 61.2 | 3 → 0 | 0.22/0.62 → 0.23/0.62 | 5.2 | 59.5 → 65.5 |
| practice_technical | 39.5 | 41.6 | 4 → 0 | 0.16/0.61 → 0.18/0.60 | 2.5 | 57.5 → 63.5 |

Mean technical score: **62.3 → 65.5/75**. Cone hits: **9 → 0**. The technical
course takes 2.1 s longer; the controller trades that time for eliminating its
four obstacle hits. Path mean error is slightly higher on most courses.

The exact submission file passed:

```bash
MPLCONFIGDIR=/tmp/hackbama-mpl .venv/bin/python -m autocross selftest -c submission/hackbama.py
```

All five submission runs reported zero controller errors, zero compute overruns,
zero clipped commands, and `controller` as the published path source. Maximum
measured p99 step time was 6.9 ms against the 50 ms deadline. The bicycle model
was used; CARLA was not installed on this machine.

## Unfamiliar courses and stress checks

Four new, seeded courses were generated using the official `gen-track` command
and stored under `generated_tracks/`, outside the official `tracks/` directory.
The final controller finished all four with zero cone, off-course, or gate
penalties. Their technical points were 66.1 (seed 42), 66.3 (seed 83), 65.4
(seed 2026), and 66.2 (closed seed 31). Runs are under `runs/*hackbama_candidate2*/`.

A two-step actuator-delay test finished cleanly on `hackathon_test` and
`practice_loop` (runs under `runs/*hackbama_delay_final*/`). A 20% friction
reduction on `practice_loop` still finished but hit 23 boundary cones and scored
4.5/75 (`runs/*hackbama_lowgrip_final*/`). This is the main known robustness
limit. A slower 0.50 lateral-acceleration setting cleared that stress case with
zero penalties, but scored 63.5/75 on the five nominal public courses versus
65.5/75 for the submitted setting. The submitted setting was chosen for the
published nominal evaluation conditions.

The final official robustness batch on the exact submission file produced
**40/40 finishes, 38/40 clean runs, zero controller errors, and zero compute
overruns** (`runs/20261017-103025_hackbama_submission_batch`). The only two
penalized runs were the two seeds of `practice_loop` with 20% reduced friction;
each had 23 cone hits. The two actuator-delay seeds on both batch courses were
clean.

## Four-minute judge presentation outline

- **0:00–0:35 — Challenge:** No prior map, 40 m live road preview, obstacles,
  50 ms control deadline. Explain why completion and penalties matter.
- **0:35–1:30 — Algorithm:** Show the observed centerline, corridor, obstacle
  extents, and the smooth bypass path. Explain that nearby same-side obstacles
  share one shift so the path stays inside the cones.
- **1:30–2:20 — Controls:** Explain curvature speed limits, braking-distance
  preview, end-of-sight caution, adaptive pure pursuit, and grip-aware throttle.
- **2:20–3:10 — Evidence:** Show the public-course table. State nine baseline
  cone hits versus zero for the submission and 62.3 versus 65.5 technical points.
  Point out that the technical run is slower and path error rises slightly.
- **3:10–4:00 — Generalization and limits:** Four generated courses completed
  cleanly; delay stress tests completed cleanly. Disclose the low-grip loop's
  23 cone hits. Close with the single-file submission and selftest result.
