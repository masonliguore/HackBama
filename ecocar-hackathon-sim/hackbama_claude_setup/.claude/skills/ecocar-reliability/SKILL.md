---
name: ecocar-reliability
description: Reliability-first workflow for HackBama EcoCAR controller diagnosis, modification, ML experiments, evaluation, and submission decisions.
---

# EcoCAR Reliability

## Mission
Maximize unseen-course reliability first, then technical score. The verified controller remains champion until a candidate clearly beats it.

## Baseline architecture
Describe the current controller accurately: obstacle-aware path planning, speed-adaptive Pure Pursuit lateral control, PI longitudinal control, and curvature/braking-aware speed planning. Do not claim ML is deployed unless submission code actually uses it.

## Workflow
For every meaningful change:
1. Preserve/hash champion.
2. Reproduce the failure.
3. Inspect telemetry around the first failure.
4. State: "failure X occurs because Y; change Z should address Y."
5. Make the smallest justified change.
6. Run targeted reproduction.
7. Run regressions.
8. Run paired evaluation on identical seeds/configuration.
9. Keep or revert from evidence.
10. Log hypothesis -> change -> result -> keep/revert.

Do not perform broad rewrites before diagnosing a failure.

## Failure analysis
Inspect where available: penalty type/time, speed and target speed, planned/actual path, boundaries, obstacles/bypass side, road and planned-path curvature, lateral/heading error, yaw rate, lateral acceleration, slip, steering, throttle/brake, boundary clearance, and saturation.

Classify the mechanism: planning, clearance, infeasible curvature, entry speed/braking, tracking, steering saturation/delay, grip instability, boundary clipping, obstacle/corner interaction, preview limitation, or another telemetry-supported cause.

## Priority
1. Exceptions, invalid outputs, overruns
2. DNF, missed gate, off-course
3. Cone hits
4. Tail risk/worst cases
5. Tracking/physical realism
6. Completion time/mean score

Never trade materially worse tail reliability for a small mean-score gain.

## ML policy
ML must earn deployment. Prefer:
- online grip/stability estimation
- short-horizon failure-risk prediction
- ranking already-feasible trajectories

Split data by complete run/track/seed, never adjacent frames. Compare ML to simple deterministic thresholds. Measure false negatives and held-out performance. Then A/B test the actual controller with ML enabled vs disabled.

ML is advisory only. Validate inputs/outputs, bound runtime, fail safely, preserve deterministic fallback, and never allow ML to override physical feasibility or increase a physics-derived safe-speed ceiling.

## Testing
Maintain development, validation, and untouched final holdout sets. Test nominal, obstacle-heavy, technical/high-curvature, narrow, reduced-friction, delay, friction+delay, start-offset, and steering-bias scenarios when supported.

Report completion, zero-penalty rate, cones, off-course, missed gates, errors, invalid commands, overruns, worst/10th-percentile/mean score, mean time, max path error, and p99/max runtime.

## Submission gate
Replace champion only if public selftests remain clean, there are zero controller/runtime errors, targeted failures improve, important regressions do not appear, held-out reliability improves, and runtime remains safe.

## Judge answer
Until architecture changes:
"We use an obstacle-aware trajectory planner with speed-adaptive Pure Pursuit for lateral control and a PI controller for longitudinal control, with curvature- and braking-aware speed planning."
