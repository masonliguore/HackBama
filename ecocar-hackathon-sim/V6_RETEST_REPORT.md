# V6 bug-fix candidate retest — 17 October 2026

## Identity and scope

- Candidate: `controllers/hackbama_v6.py`, class `HackBamaController`.
- Candidate SHA-256: `527825cd9955b1570711a6e7ab1bf81f34f8f57dba4bc08ed3aa9719f45ed91f`.
- Source: byte copy of V4, then three localized bug fixes. The V4 submission
  remains unchanged at SHA-256
  `c911e116540a7c3fa78b39fb60d3c75ae4cb151310504474ea63e8199b92ec0d`.
- The existing untracked `controllers/hackbama_v5_candidate.py` was not used.

## Fixes

1. **Pair membership:** replace one `tight_pair_dist` scalar with a set of
   participating obstacle indices. Only members of an actual close,
   opposite-side pair receive tight clearance and speed limits. The nearest
   ahead member determines reduced lookahead. This fixes both missed earlier
   pairs and unrelated obstacles inheriting tight clearance.
2. **Interval gap:** compute the nonnegative distance between two lateral
   intervals as `max(0, max(lower bounds) - min(upper bounds))`. Overlapping
   intervals therefore have a gap of zero.
3. **State reset:** initialize `v_ref` in `on_start`; use current speed as the
   initial reference on the first step. Reusing a controller object now starts
   with clean speed-controller state.

No tuning constant, speed-planning architecture, or Pure Pursuit logic was
changed. The no-feasible-bypass behavior and other known V4 limitations remain.

## Tests and differential check

- `pytest tests -q`: **112 passed** with V6 as the focused test target.
- The focused suite alone: **49 passed**, including the four V4 regression
  failures and 5,000 seeded randomized steps.
- Running the same focused suite with
  `HACKBAMA_CONTROLLER_PATH=submission/hackbama.py` still gives the same four
  V4 failures (45 passed, four failed), confirming the regression tests
  distinguish the candidate.
- In 1,500 ordinary synthetic one-step cases with zero obstacles, one
  obstacle, or a standard disjoint pair, V4 and V6 returned bitwise identical
  commands and paths.
- A byte-matched V6 copy in `/tmp` imported under isolated Python without
  prior experiment artifacts.

## Official bicycle selftest

All five courses finished with zero cones, off-course events, missed gates,
controller errors, command clipping and overruns. Mean technical score was
**66.4/75**, matching V4. Per-course times and scores were also unchanged.
The exact stdout/stderr is saved in
`runs/v6_validation_20261017/official_selftest.txt`. Maximum controller memory
was 31.7 MB. CARLA was unavailable in this environment.

## Matched 50-course comparison

The candidate was run on exactly the 50 preserved valid generated courses
(seeds 2000–2049) from the V4 final audit. The track files, simulator settings,
and bicycle backend were the same. Raw V6 summaries and events are in
`runs/v6_retest_20261017_153913/`; baseline V4 data are in
`runs/final_validation_20261017_151905/`.

| Metric | V4 | V6 |
|---|---:|---:|
| Finished | 50/50 | 50/50 |
| Clean | 32/50 | **33/50** |
| Cone hits | 58 | **56** |
| Off-course / missed gates / controller errors / invalid commands / overruns | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| Mean technical score / 75 | 63.26 | 63.50 |
| Median / p10 / worst technical score | 65.66 / 55.77 / 51.41 | 65.82 / 56.17 / 51.84 |
| Mean / median time | 39.084 / 38.181 s | 39.085 / 38.181 s |
| Maximum path error | 1.076 m | 1.076 m |

The only cone-count changes were seed **2017: 1 → 0** and seed **2027: 4 → 3**.
No course gained a penalty. V6 still has 17 penalized courses in this batch,
primarily narrow bypasses and tight obstacle sequences. These are not claimed
to be solved by the local bug fixes.

## Matched 40-run perturbation comparison

Five preserved generated courses, eight supported conditions each. All runs
finished. In every condition, V6 matched V4's clean count and cone count;
both had zero off-course events, missed gates, controller errors, invalid
commands and overruns.

| Condition | Clean / 5 | Cones |
|---|---:|---:|
| Nominal | 4 | 4 |
| 90% friction | 4 | 4 |
| 80% friction | 3 | 5 |
| Two-step actuation delay | 3 | 7 |
| 90% friction plus delay | 3 | 7 |
| 0.6 m starting lateral offset | 4 | 4 |
| 0.02 steering bias | 4 | 5 |
| 15% additional mass | 4 | 4 |

## Runtime

| V6 run set | Steps | Median | p95 | p99 | Maximum | Overruns |
|---|---:|---:|---:|---:|---:|---:|
| Official selftest | 5,684 | 0.76 ms | 1.39 ms | 1.72 ms | 3.50 ms | 0 |
| Matched unseen batch | 41,143 | 0.86 ms | 1.49 ms | 1.82 ms | 16.85 ms | 0 |

Runtime distributions from separate batches depend on host load; these values
show the V6 candidate stayed below the official 50 ms deadline. They are not
used to claim an optimization over V4.

## Outcome

V6 passes the bug regressions, the complete test suite, official bicycle
selftest, 50 paired generated courses, and 40 paired robustness runs without
a measured reliability regression. It remains a **separate candidate** in
`controllers/hackbama_v6.py`; `submission/hackbama.py` is still the unchanged
V4 file. A decision to submit V6 requires copying this reviewed candidate to
the submission path and rerunning the exact-file selftest and hash check.
