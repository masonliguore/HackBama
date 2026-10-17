# HackBama EcoCAR Autonomous Autocross Controller

A reliability-first autonomous driving controller developed for the
HackBama EcoCAR autonomous-autocross challenge.

The final controller combines **obstacle-aware trajectory planning**,
**adaptive obstacle avoidance**, **Pure Pursuit steering**, and **PI
longitudinal control**. Development focused on one rule: **keep a change
only when testing shows that it improves reliability without introducing
a regression.**

## Final Controller

The final V7 controller keeps the overall architecture simple and
deterministic:

``` text
Live Road + Vehicle Observation
            |
            v
Obstacle-Aware Trajectory Planner
            |
            +----> Adaptive tight-pair / narrow-road handling
            |
            v
Curvature + Braking Speed Planner
            |
            +----------------------+
            |                      |
            v                      v
   Pure Pursuit Steering      PI Speed Control
                              Throttle / Brake
            |                      |
            +----------+-----------+
                       |
                       v
                  Vehicle Command
```

### Main components

-   **Trajectory planning:** starts from the perceived road centerline
    and creates smooth lateral offsets around obstacles.
-   **Adaptive obstacle handling:** changes clearance and path shape for
    constrained obstacle configurations.
-   **Tight-pair S-weave:** handles closely spaced opposite-side
    obstacles with shorter avoidance features, reduced lookahead, and a
    lower target speed.
-   **V7 narrow-road fallback:** when the preferred obstacle clearance
    cannot fit on either side, the controller searches for a narrower
    positive-clearance bypass instead of continuing through the
    obstacle.
-   **Pure Pursuit steering:** follows the published path using a
    speed-adaptive lookahead.
-   **Speed planning:** limits speed using road curvature, braking
    distance, preview limits, and obstacle-specific caps.
-   **PI longitudinal control:** converts target-speed error into
    throttle or brake commands.

## Why V7 Was Needed

During final validation, the dominant remaining failure was not a
tracking or steering problem. It was a planner edge case.

Earlier versions normally requested a generous obstacle clearance. On
narrow roads, both preferred bypasses could be rejected even when a
smaller safe gap still existed. The old behavior then left the path
close to the centerline, which could send the vehicle directly through
the obstacle.

V7 preserves the normal planner whenever a preferred bypass exists.
**Only when the normal candidate list is empty**, it:

1.  checks both sides using a smaller positive obstacle gap,
2.  preserves a minimum road-boundary margin,
3.  selects a feasible narrow bypass,
4.  reduces approach speed for the maneuver.

This was a localized change rather than a planner rewrite.

## Validation Results

### Official bicycle selftest

  Metric                            Final V7
  -------------------------- ---------------
  Courses finished                 **5 / 5**
  Cone hits                            **0**
  Off-course events                    **0**
  Missed gates                         **0**
  Controller errors                    **0**
  Invalid/clipped commands             **0**
  Compute overruns                     **0**
  Mean technical score         **66.4 / 75**

### Untouched 50-course validation

The V7 candidate was frozen before evaluating seeds 4000--4049.

  Metric                                          V6              V7
  -------------------------------------- ----------- ---------------
  Finished                                   50 / 50     **50 / 50**
  Clean runs                                 28 / 50     **30 / 50**
  Cone hits                                       88          **50**
  Mean technical score                         61.84       **62.56**
  10th-percentile score                        53.75       **54.64**
  Worst score                                  47.05       **48.24**
  Errors / invalid commands / overruns     0 / 0 / 0   **0 / 0 / 0**

The improvement was concentrated where expected: on the narrow-course
family, cone hits fell from **56 to 18**.

### Robustness testing

Five representative new tracks were tested under eight conditions each:

-   nominal
-   90% friction
-   80% friction
-   two-step actuation delay
-   90% friction + delay
-   0.6 m starting lateral offset
-   0.02 steering bias
-   15% additional mass

Across the 40 matched runs:

  Metric                                                           V6            V7
  --------------------------------------------------------- --------- -------------
  Cone hits                                                        34         **2**
  Clean runs                                                  30 / 40   **38 / 40**
  Finishes                                                    40 / 40   **40 / 40**
  Off-course / missed gates / errors / invalid / overruns           0         **0**

## Example Behaviors

### Normal clean run

The controller tracks the course while the target-speed planner slows
for higher-curvature sections and accelerates on straights.

![Normal clean run](normal_clean.png)

### Single-obstacle bypass

For an isolated obstacle, the planner creates a smooth offset around the
cone group and returns toward the centerline.

![Single obstacle bypass](single_obstacle_bypass.png)

### Tight opposite-side obstacle handling

Closely spaced obstacles on opposite sides require a constrained
S-shaped path. The controller adapts its avoidance behavior rather than
applying one fixed obstacle rule.

![Tight opposite-side obstacle pair](tight_s_weave.png)

![Opposite-side S-weave](visible_s_weave.png)

### V7 narrow-road fallback

This comparison shows the failure mode that motivated V7. V6's
preferred-clearance logic could leave no valid bypass candidate. V7 uses
the remaining safe road width and publishes a narrow bypass instead.

![V7 narrow-road fallback](narrow_fallback.png)

## Development Method

The controller was developed experimentally rather than by accumulating
features.

For each proposed change:

1.  reproduce a failure,
2.  identify the first causal divergence,
3.  form a hypothesis,
4.  make the smallest relevant change,
5.  test the targeted case,
6.  run regression and unseen-course testing,
7.  keep or revert the change based on measured results.

Several ideas were tested and rejected when they did not improve
reliability, including curvature feedforward, generic grip estimation,
alternative speed-profile approaches, and an ML risk estimator.

The final controller intentionally does **not** use machine learning. In
testing, the learned risk gate added complexity without improving
held-out controller reliability.

## Known Limitations

The final controller is intentionally not presented as perfect.

-   Speed planning primarily uses **road-preview curvature**, while the
    final obstacle-offset path can demand greater curvature.
-   Extremely constrained multi-obstacle sequences can still create
    paths that are difficult for Pure Pursuit to track.
-   Some remaining cone hits come from overlapping avoidance geometry,
    tracking error, or local speed-planning limitations.
-   CARLA validation was unavailable in the final development
    environment; the reported official selftest results are from the
    bicycle backend.

A logical next step would be to use curvature of the **actual published
trajectory** in the speed planner and investigate model-predictive
tracking for highly constrained obstacle sequences.

## Running the Controller

From the repository root, run the official bicycle selftest with:

``` bash
MPLCONFIGDIR=/tmp/hackbama-mpl .venv/bin/python -m autocross selftest -c submission/hackbama.py
```

Run the regression suite with:

``` bash
HACKBAMA_CONTROLLER_PATH=submission/hackbama.py .venv/bin/pytest tests -q
```

Verify the frozen submission with:

``` bash
sha256sum submission/hackbama.py
```

Expected V7 SHA-256:

``` text
3f134c590bbcb3ec66bdeb5542087f57c5dcb13e720e3c90528645c9c06d2ee3
```

## Final Takeaway

The project demonstrates a reliability-first approach to autonomous
control:

> **Use the simplest controller that works, measure its failures, and
> add complexity only when the data justifies it.**

V7's most important improvement came from a small, targeted fallback for
a clearly identified planner failure---not from a wholesale controller
rewrite.
