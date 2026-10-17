# Final targeted cone-hit development cycle — 17 October 2026

## Controller identity and method

- V6 baseline: `controllers/hackbama_v6.py`, SHA-256 `527825cd9955b1570711a6e7ab1bf81f34f8f57dba4bc08ed3aa9719f45ed91f`.
- Frozen V7 candidate: `controllers/hackbama_v7_candidate.py`, SHA-256 `3f134c590bbcb3ec66bdeb5542087f57c5dcb13e720e3c90528645c9c06d2ee3`.
- `submission/hackbama.py` was **not modified**; it remains the V4 submission at SHA-256 `c911e116540a7c3fa78b39fb60d3c75ae4cb151310504474ea63e8199b92ec0d`.
- The old 2000–2049 batch was used only for diagnosis and a targeted retest. Development seeds 3000–3049 and final validation seeds 4000–4049 are distinct. V7 was frozen before validation.

The diagnostic replay reconstructs each V6 road model and controller step from saved telemetry. Across the 17 penalized courses, its maximum logged-versus-replayed steering or target-speed difference is below 0.003. It evaluates each physical obstacle cone against the *published path's oriented vehicle rectangle* (vehicle length 4.79 m, width 2.16 m, plus the simulator's 0.10 m cone margin), sampling the path every 0.20 m. The diagnostic values below are from about 0.5 s before the first hit; the full approximately 2 s before/1 s after windows, including speed, target speed, offset, widths, margins, steering, throttle, brake, lookahead, curvature, acceleration, yaw rate and rear slip, are in `runs/v6_cone_analysis.json`. Negative planned clearance means the published vehicle footprint overlaps the cone.

## 1. First-hit taxonomy

All 17 first hits were unmapped obstacle cones. Group IDs refer to physical obstacle groups, not map boundary cones.

| Seed | Group | First hit (s) | Primary cause | Planned footprint clearance (m) | Planned / actual offset (m) | Speed (m/s) |
|---:|---:|---:|---|---:|---:|---:|
| 2003 | 1 | 14.75 | I: no feasible preferred bypass | -0.98 | -0.02 / +0.08 | 11.2 |
| 2006 | 2 | 41.80 | C: tracking lag | +0.04 | -0.41 / -0.15 | 3.3 |
| 2007 | 0 | 10.18 | C: tracking lag | +0.04 | -0.36 / -0.13 | 3.3 |
| 2008 | 0 | 12.68 | I: no feasible preferred bypass | -0.76 | 0.00 / +0.40 | 9.6 |
| 2013 | 0 | 12.10 | I: no feasible preferred bypass | -0.96 | +0.02 / +0.38 | 10.7 |
| 2018 | 2 | 26.87 | I: no feasible preferred bypass | -0.89 | -0.01 / -0.10 | 11.6 |
| 2019 | 2 | 25.12 | F: overlapping short bumps | -0.13 | +0.26 / +0.03 | 3.2 |
| 2023 | 0 | 6.90 | I: no feasible preferred bypass | -0.69 | 0.00 / +0.14 | 11.6 |
| 2027 | 3 | 30.87 | C: tracking lag | +0.04 | -0.57 / -0.26 | 3.2 |
| 2032 | 3 | 30.15 | F: overlapping short bumps | -0.27 | +0.59 / +0.29 | 3.2 |
| 2033 | 0 | 7.18 | I: no feasible preferred bypass | -0.82 | 0.00 / -0.07 | 10.7 |
| 2035 | 1 | 31.27 | F: overlapping short bumps | -0.38 | -0.50 / -0.27 | 3.2 |
| 2037 | 1 | 20.97 | F: overlapping short bumps | -0.43 | -0.51 / +0.11 | 3.3 |
| 2038 | 1 | 19.15 | I: no feasible preferred bypass | -0.82 | 0.00 / -0.18 | 11.3 |
| 2042 | 4 | 18.63 | J: path/road curvature speed mismatch | +0.54 | -1.25 / +0.40 | 11.0 |
| 2043 | 3 | 22.42 | I: no feasible preferred bypass | -0.60 | 0.00 / +0.01 | 11.3 |
| 2048 | 2 | 13.90 | I: no feasible preferred bypass | -0.75 | +0.01 / +0.39 | 10.8 |

Counts: **I 9, F 4, C 3, J 1**. By subsystem, **13 planner**, **3 tracker**, **1 speed planner**, **0 demonstrably unavoidable**.

## 2. Dominant cause and discriminating evidence

The dominant general failure is the `if not candidates: continue` path. V6 demands 0.80 m beyond half the vehicle width on ordinary obstacles. On a narrow road, this can reject both preferred bypasses even though a smaller positive cone gap and boundary gap exist. It then publishes approximately the centerline through the obstacle at 9.6–11.6 m/s. All nine category-I first-hit paths intersect the physical cone footprint by 0.60–0.98 m. Their available *minimum-clearance* width beyond the 0.10 m cone margin ranges from 0.44 to 0.82 m; a deterministic narrow bypass is geometrically possible.

As a successful-run control, a station-geometry reconstruction over **all obstacle groups** in the original 50 courses found 21 groups with no V6 preferred candidate; **21/21 were hit**. Of 249 groups with a preferred candidate, **234 passed** and 15 were hit. The track-level reconstruction approximates the instantaneous road-model decision, while the replay confirms the empty candidate list at every category-I first hit. The no-candidate condition therefore distinguishes a high-risk obstacle group from normal obstacle exposure.

## 3. Other mechanisms examined

- **Planner versus tracker:** A negative planned footprint clearance defines the 13 planner cases. The three C cases have a small positive planned clearance (+0.04 m) but are 0.23–0.31 m short of their intended lateral offset at about 3.2–3.3 m/s. Steering does not saturate. Their lookahead/half-bump ratios are 0.24–0.56; this does not support a general claim that long Pure Pursuit lookahead causes most hits.
- **Multi-obstacle sequences:** The four F cases occur in tight sequences whose opposing bumps are shortened to about 3 m. Their published footprints already overlap the cones by 0.13–0.43 m, despite the tight-pair 3.5 m/s cap. A different local side choice might help some sequences, but these data do not isolate one reliable side-selection rule. No global planner was added.
- **Path curvature versus road curvature:** Seed 2042 publishes a clearing path (+0.54 m) but is 1.65 m from the intended offset at 11.0 m/s. Maximum local road/path curvature is about 0.026/0.312 m⁻¹. The existing lateral-acceleration assumption implies an approximate path-safe speed of 4.4 m/s. This supports a speed-planning concern for that case, not a batch-wide speed change. The tight-pair failures already approach at only about 3.2 m/s and often have colliding published paths.
- **Trackability:** First-hit steering never saturates in the sampled two-second approaches. The short tight-pair bumps have lookahead/half-length ratios around 0.5–0.7 in the four F cases; they create sharp path curvature, but geometry fails before a tracker-only change could solve them. No evidence justified replacing Pure Pursuit.

## 4. One candidate fix and experimental log

**Hypothesis:** When V6's preferred 0.80 m obstacle gap admits no candidate, a narrower positive-clearance pass can avoid the cone without crossing the road boundary.

**Change:** V7 first preserves V6's preferred candidates. Only if that list is empty, it tests a 0.10 m cone gap and 0.22 m lateral boundary margin on each side. For a feasible side, it places the target halfway through the available remaining width and caps that obstacle's approach at 6.0 m/s. If neither side meets the minimum, it retains V6's behavior. This adds 14 net lines, with no new sensor, map, planner architecture, or Pure Pursuit change.

**Targeted result:** On the nine diagnosed category-I courses, cone totals fell **39 → 11**; all nine improved and three became clean. The other eight diagnosed courses were unchanged. Across all 17 inspected courses, cones fell **56 → 28**. These seeds were already inspected and were **not** used as final evidence.

**Fresh development, seeds 3000–3049:** 50/50 finished for each version. V6 had **137 cones, 16 clean**; V7 had **71 cones, 20 clean**. Twenty-one courses improved, none gained cone hits. Mean score 59.31 → 60.31; p10 52.98 → 53.22; worst 44.15 → 47.98. Zero off-course, missed gates, errors, invalid commands, or overruns for either version.

**Decision:** Keep this single change for frozen validation. Other possible changes (multi-obstacle side selection, path-curvature speed limiting) were not implemented because they address fewer first hits and would add independent regression risk. No unsuccessful edits were accumulated.

## 5. Frozen, untouched final validation

Generated seeds **4000–4049** were first evaluated after V7's SHA-256 was frozen. The same track, config and bicycle backend were used for each paired V6/V7 run. Each course family has ten tracks.

| Metric | V6 | V7 |
|---|---:|---:|
| Finished | 50/50 | 50/50 |
| Clean | 28/50 (56%) | **30/50 (60%)** |
| Cone hits | 88 (1.76/run) | **50 (1.00/run)** |
| Off-course / missed gates / errors / invalid / overruns | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| Mean technical score | 61.84 | **62.56** |
| Median technical score | 65.25 | 65.25 |
| P10 technical score | 53.75 | **54.64** |
| Worst technical score | 47.05 | **48.24** |
| Mean time | 39.00 s | 39.78 s |
| Maximum path error | 1.273 m | 1.273 m |
| Largest per-run p99 controller step | 4.91 ms | 3.42 ms |
| Largest controller step | 15.15 ms | 11.54 ms |

Nine courses improved their cone count, no course gained cones, and two additional courses became clean. By family, the cone counts were: narrow **56 → 18**, normal 3 → 3, technical 4 → 4, obstacle-heavy 24 → 24, wide 1 → 1. The improvement is specific to the geometry the fallback addresses and repeated on new narrow courses. The slower mean run time is a consequence of the local safety speed cap, not a tuning goal. Raw paired results are in `runs/v7_cycle_20261017/validation/report.json`.

## 6. Robustness comparison

Five representative new tracks (seeds 4000–4004, one from each family) were each run under eight conditions for both controllers: **40 matched perturbation runs per version**. Every run finished; both versions had zero off-course events, missed gates, controller errors, invalid commands and overruns. The table reports total cones and clean courses out of five for each condition.

| Condition | V6 cones / clean | V7 cones / clean |
|---|---:|---:|
| Nominal | 4 / 4 | **0 / 5** |
| 90% friction | 4 / 4 | **0 / 5** |
| 80% friction | 4 / 4 | **0 / 5** |
| Two-step actuation delay | 5 / 3 | **1 / 4** |
| 90% friction plus delay | 5 / 3 | **1 / 4** |
| +0.6 m start offset | 4 / 4 | **0 / 5** |
| +0.02 steering bias | 4 / 4 | **0 / 5** |
| 15% additional mass | 4 / 4 | **0 / 5** |

Total cones were **34 → 2** and clean runs **30/40 → 38/40**. On the narrow representative course, V6 hit four cones in every condition and V7 remained clean in every condition. Other paired courses were unchanged except for the same delay-related cone hit in both versions. Condition-level p10 scores also improved in all eight conditions. Raw results are in `runs/v7_cycle_20261017/robustness/report.json`.

## 7. Official comparison

The final sequential V7 bicycle selftest completed **5/5 public courses clean**, with zero cones, off-course events, missed gates, controller errors, invalid commands or overruns. Mean technical score was **66.4/75**, matching V6; every public course had the same completion time, penalties, deviation and dynamics metrics as V6. Maximum observed V7 controller step was **5.46 ms**. The exact final stdout is in `runs/v7_cycle_20261017/official_selftest_final.txt` and summaries are in `runs/20261017-162052_selftest/`. An earlier concurrent selftest had a transient compute-timing score drop on one course; the isolated recheck resolved it. CARLA was unavailable, so the official comparison is bicycle-model only.

## 8. Complexity assessment

The candidate adds 14 net source lines and keeps the V6 architecture. Its observed reliability gain on targeted and untouched narrow roads is large enough to justify the added fallback. Mean time was 0.78 s longer on the new validation batch; reliability is the criterion for this cycle. The remaining cone hits have other causes and were not used to justify more controller complexity.

## 9. Recommendation

**PROMOTE V7**

V7 meets every stated acceptance gate: official selftest clean and score matched, 112/112 tests passed, zero errors/invalid commands/overruns, direct improvement in the dominant failure mode, lower cone rate and higher clean percentage on a distinct 50-course validation set, better p10 and worst technical scores, and no material robustness regression. The candidate is a recommendation; `submission/hackbama.py` still contains V4.

## 10. Submission instructions after approval

From the repository root, after approving promotion, copy the reviewed bytes to the submission path and validate that **exact file**:

```bash
cp controllers/hackbama_v7_candidate.py submission/hackbama.py
cmp controllers/hackbama_v7_candidate.py submission/hackbama.py
MPLCONFIGDIR=/tmp/mpl-v7-submission .venv/bin/python -m autocross selftest -c submission/hackbama.py
HACKBAMA_CONTROLLER_PATH=submission/hackbama.py .venv/bin/pytest tests -q
sha256sum submission/hackbama.py
```

The final SHA-256 should be `3f134c590bbcb3ec66bdeb5542087f57c5dcb13e720e3c90528645c9c06d2ee3` if the file is a byte copy. Confirm the exact-file selftest and suite are clean, record that hash, then freeze the submission without further edits. Promotion was deliberately **not** performed in this cycle.
