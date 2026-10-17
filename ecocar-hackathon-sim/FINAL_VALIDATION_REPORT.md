# Final V4 engineering validation — 17 October 2026

## 1. Submission identity

- File: `submission/hackbama.py`, class `HackBamaController` (V4).
- SHA-256: `c911e116540a7c3fa78b39fb60d3c75ae4cb151310504474ea63e8199b92ec0d`.
- `submission/hackbama.py` and `controllers/hackbama_v4.py` are byte identical.
- The controller was **not changed** during this validation. The untracked
  `controllers/hackbama_v5_candidate.py` predates this audit and was not used.

## 2. Static audit

**Confirmed bugs:**

1. `tight_pair_dist` holds one distance, so a second tight pair overwrites the
   first. The earlier pair loses its 3.5 m/s limit and reduced lookahead. An
   unrelated obstacle within 8 m of the stored distance can inherit the small
   0.15 m clearance. Pair-specific bump shortening still works.
2. For overlapping lateral intervals, the gap branch can replace the true
   interval distance of zero with a positive endpoint distance. A sufficiently
   wide overlap can therefore fail the tight-pair test.
3. `on_start` resets the integral and grip state but leaves `v_ref` from a prior
   run on a reused controller object. The official harness creates a new
   controller process per run, so this does not affect its normal lifecycle.

**Potential risks:** input arrays marked `valid=True` but shorter than two
samples or of inconsistent lengths can raise in `gradient`, interpolation or
indexing. The official `RoadModelSensor` marks previews with fewer than two
samples invalid and constructs the arrays together. Finite positive vehicle
parameters and monotone preview stations are assumed by the published sensor.

**Known design limitations:** road-preview curvature is used for speed planning
instead of the final offset path; 80% friction can exceed available grip on the
public loop; very short opposite-side obstacle sequences can exceed Pure
Pursuit tracking ability. If no nominal bypass candidate exists, V4 leaves the
path on the centerline and retains an 11 m/s obstacle speed cap; it does not
crash or produce invalid output. This is especially consequential on 5 m roads
with wide edge obstacles.

**Not issues under the official API:** `np.gradient` has at least two preview
points when `road.valid` is true; `np.interp` receives sorted preview stations;
`searchsorted` is clipped to the preview length; returned paths use the vehicle
frame and the road arrays are copied before modification. Steering and pedals
are clipped to their API bounds and pedals are mutually exclusive. An invalid
road preview returns full brake and omits `target_speed`, which the API
explicitly permits as an optional field.

## 3. New tests added

At the time of this audit, `tests/test_submission_validation.py` directly
imported the exact submission file. It covers zero, one, two, three and
multiple obstacles; side placement;
behind/current/horizon distances; separation thresholds including 8 m and the
20 m bump length; analytical interval geometry; multiple tight pairs; no
feasible bypass; road-data immutability; invalid empty previews; state reset;
bitwise command determinism; and 5,000 seeded randomized steps. The passing
case for two pairs confirms that both bumps shorten. Four regression assertions
fail on the unchanged V4 source. The repository's preexisting 63 tests pass;
the new file has 41 passing and four failing test cases.

**Later V6 note:** After this audit, the test file was made selectable and now
defaults to the separate V6 candidate. Set
`HACKBAMA_CONTROLLER_PATH=submission/hackbama.py` to reproduce the V4 failures
recorded here. The results in this report remain the original V4 results.

`scripts/final_validate_submission.py` generated 50 new tracks, ran the exact
submission on each, and ran eight supported perturbations on five of those
tracks. Track seeds are 2000–2049, disjoint from the documented development
sets; all 50 generated tracks pass `Track.validate()`.

## 4. Bugs found and regression evidence

| Root cause | Deterministic reproduction | Observed V4 result | Status |
|---|---|---|---|
| One `tight_pair_dist` for two pairs | Pairs at 10/13 m and 30/33 m | First pair keeps 11.0 m/s target instead of at most 3.5 m/s | Unfixed |
| Distance-based tight membership | Pair at 10/13 m; unrelated same-side obstacle at 4 m | Unrelated bypass is 0.43 m instead of 1.08 m | Unfixed |
| Wrong interval gap on overlap | Intervals `[-2,4]` and `[-4,2]` m | True gap 0; controller misses tight speed rule (8.221 m/s first-step target) | Unfixed |
| Stale `v_ref` after `on_start` | Reuse controller at 12 m/s, restart at 8 m/s | Target 12.442 m/s rather than fresh object's 8.221 m/s | Unfixed |

These are software/logic defects, not tuning proposals. The tight-pair fix
would materially change obstacle-path clearance and speed. The controller was
left byte unchanged so the measured V4 results retain their identity. No fix
or post-fix regression claim is made.

## 5. Fuzz/property results

- Seed `20261017`: 3,000 independently constructed API-valid observations.
- Seed `20261018`: 20 stateful sequences of 100 steps (2,000 more steps).
- Zero exceptions or nonfinite commands; zero out-of-range steering or pedals;
  zero simultaneous throttle and brake; finite nonnegative targets and paths.
- Straight-road path offsets remained inside the sampled width allowance.
- No randomized failure required a new regression seed. The four deterministic
  failures above are separate from the fuzz results.

## 6. New unseen evaluation

Bicycle backend, official simulator/scoring, seeds 2000–2049. Ten each of
normal (5.5 m), longer technical mix (5.5 m), obstacle-heavy (eight groups,
5.5 m), narrow (5.0 m), and wide (6.5 m) generated courses.

| Metric | Result |
|---|---:|
| Runs / finishes / clean | 50 / 50 / 32 (64%) |
| Cone hits / off-course / missed gates | 58 / 0 / 0 |
| Controller errors / invalid commands / overruns | 0 / 0 / 0 |
| Technical score mean / median / p10 / worst (of 75) | 63.26 / 65.66 / 55.77 / 51.41 |
| Completion time mean / median | 39.08 / 38.18 s |
| Maximum published-path error | 1.076 m |
| Aggregate step p99 / maximum | 4.67 / 40.90 ms |

The highest p99 among individual unseen runs was 13.41 ms.

Clean by variant: normal 9/10, longer technical mix 9/10, obstacle-heavy
4/10, narrow 1/10, wide 9/10. All recorded penalties were obstacle-cone hits.
The category below is a **likely cause inferred from track geometry**, not a
confirmed cause from an instrumented controller replay. Times and progress are
the first penalty event in each run. Complete event records and telemetry are
in `runs/final_validation_20261017_151905/`.

| Seed | Variant | Cones | First failure time / progress | Likely category |
|---:|---|---:|---|---|
| 2003 | narrow | 4 | 14.75 s / 161.3 m | No feasible nominal bypass |
| 2006 | technical | 1 | 41.80 s / 426.1 m | Tight opposite-side sequence |
| 2007 | obstacle-heavy | 3 | 10.18 s / 84.8 m | Tight opposite-side sequence |
| 2008 | narrow | 4 | 12.68 s / 126.3 m | No feasible nominal bypass |
| 2013 | narrow | 6 | 12.10 s / 140.9 m | No feasible nominal bypass |
| 2017 | obstacle-heavy | 1 | 29.52 s / 279.8 m | Tight opposite-side sequence |
| 2018 | narrow | 2 | 26.87 s / 262.6 m | No feasible nominal bypass |
| 2019 | wide | 1 | 25.12 s / 235.9 m | Tight opposite-side sequence |
| 2023 | narrow | 5 | 6.90 s / 76.5 m | No feasible nominal bypass |
| 2027 | obstacle-heavy | 4 | 30.87 s / 305.0 m | Tight opposite-side sequence |
| 2032 | obstacle-heavy | 2 | 30.15 s / 320.7 m | Tight opposite-side sequence |
| 2033 | narrow | 5 | 7.18 s / 67.2 m | No feasible nominal bypass |
| 2035 | normal | 2 | 31.27 s / 296.2 m | Tight opposite-side sequence |
| 2037 | obstacle-heavy | 3 | 20.97 s / 187.3 m | Tight opposite-side sequence |
| 2038 | narrow | 7 | 19.15 s / 223.0 m | No feasible nominal bypass |
| 2042 | obstacle-heavy | 2 | 18.63 s / 230.6 m | Obstacle bypass tracking |
| 2043 | narrow | 2 | 22.42 s / 243.7 m | No feasible nominal bypass |
| 2048 | narrow | 4 | 13.90 s / 146.6 m | No feasible nominal bypass |

## 7. Robustness results

Five generated tracks (seeds 2000–2004) under eight supported conditions.
Every run finished, with no off-course event, missed gate, controller error,
invalid command or compute overrun.

| Perturbation | Clean / 5 | Cones | Mean technical / 75 | Mean time | Penalized seeds (cones) |
|---|---:|---:|---:|---:|---|
| Nominal | 4 | 4 | 65.09 | 39.45 s | 2003 (4) |
| 90% friction | 4 | 4 | 64.74 | 39.48 s | 2003 (4) |
| 80% friction | 3 | 5 | 62.69 | 39.56 s | 2001 (1), 2003 (4) |
| 2-step delay | 3 | 7 | 51.99 | 52.00 s | 2000 (1), 2003 (6) |
| 90% friction + delay | 3 | 7 | 52.01 | 52.01 s | 2000 (1), 2003 (6) |
| 0.6 m starting lateral offset | 4 | 4 | 65.08 | 39.44 s | 2003 (4) |
| 0.02 steering bias | 4 | 5 | 64.59 | 39.48 s | 2003 (5) |
| 15% additional mass | 4 | 4 | 65.10 | 39.42 s | 2003 (4) |

Seed 2003 is a narrow-obstacle case already penalized in nominal conditions.
The additional friction and delay penalties are expected tracking/grip limits
in this batch; none produced a software exception or invalid command.

## 8. Official selftest

The **exact stdout/stderr** is saved at
`runs/final_validation_20261017_151905/official_selftest.txt`. All five public
bicycle courses finished with zero cones, off-course events and missed gates.
Per-course times, p99 times and technical points: hackathon_test 54.4 s,
2.0 ms, 66.8; practice_basic 33.4 s, 1.8 ms, 68.5; practice_loop 86.8 s,
2.2 ms, 65.0; practice_obstacles 58.6 s, 2.1 ms, 67.0; practice_technical
40.1 s, 1.7 ms, 64.8. Mean technical score: **66.4/75**. CARLA was not
available in this WSL2 environment, so this is bicycle-backend evidence only.
Controller errors, command clipping and overruns were zero; peak controller
memory across these runs was 31.6 MB.

## 9. Runtime and determinism

| Run set | Control steps | Median | p95 | p99 | Maximum | Overruns |
|---|---:|---:|---:|---:|---:|---:|
| Official selftest | 5,684 | 0.89 ms | 1.55 ms | 2.04 ms | 5.54 ms | 0 |
| 50 unseen tracks | 41,143 | 1.37 ms | 2.57 ms | 4.67 ms | 40.90 ms | 0 |

Some unseen runs overlapped with the repository test suite, so their timing
tail includes host contention; all remained below the 50 ms deadline. A
1,000-call `cProfile` run on a four-obstacle observation took 1.184 s total.
The largest cumulative costs were planner logic, NumPy clipping and the path
gradient. No optimization was justified.

Separate fresh-process nominal runs of seeds 2000 and 2003 had identical
trajectory and command telemetry: respectively 1,560 and 1,680 physics rows
matched exactly for position, velocity, progress, pedals, steering, target
speed and path error. Seed 2003 also repeated the same four cone-event times
and progress values. Timing fields were excluded from this comparison.

## 10. Submission compliance

| Requirement | Result | Evidence |
|---|---|---|
| Team filename and class/interface | PASS | Single `hackbama.py` defines `HackBamaController(Controller)` with `on_start` and `step` |
| Correct imports and allowed dependencies | PASS | Python standard library, NumPy, `autocross.api`; fresh isolated Python import succeeded |
| No course-map access or track-specific hardcoding | PASS | Source uses live `Observation.road` and published vehicle parameters; no course names or coordinates |
| No filesystem, network or external model/data dependency | PASS | Source inspection and sandboxed selftest |
| Valid Command fields and vehicle-frame path | PASS | API bounds and finite values in 5,000 fuzz steps; no invalid commands in 90 simulations |
| Runtime and memory budget | PASS | No overruns in 90 simulations; worst step 40.90 ms under 50 ms; official selftest peak memory within 1 GB |
| Self-contained fresh-process copy | PASS | SHA-matched copy in `/tmp` imported with isolated Python and finished seed 2000 cleanly |
| Full regression suite | FAIL | Existing 63 pass; four new deterministic bug regressions fail |
| CARLA verification | NOT RUN | CARLA server/client unavailable in this environment |

Python 3.10.12 on Linux/WSL2; NumPy 2.2.6, PyYAML 6.0.3, pytest 9.1.1,
psutil 7.2.2. No official simulator, scoring, physics, API, vehicle config or
course file was modified.

## 11. Known remaining limitations

The controller lacks a feasible-path fallback for blocked/narrow corridors;
it can drive into an obstacle at up to the 11 m/s obstacle cap. Tight
opposite-side sequences and lower friction can produce cone hits despite valid
commands. Speed is planned from road curvature rather than curvature of the
final obstacle-offset path. The bugs in section 4 are additional confirmed
logic defects and are not treated as mere limitations.

## 12. Final recommendation

Do not freeze this exact V4 file. The deterministic tight-pair membership and
interval-gap regressions remain in the submission, and the new 50-course batch
is only 32/50 clean. Any fix that materially changes bypass behavior should be
evaluated as a new candidate against these preserved tests and tracks before
the submission hash is replaced.
