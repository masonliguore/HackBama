# HackBama rules

- Reliability first; mean score second.
- Preserve and hash the known-good controller before experiments.
- Never modify official simulator, scorer, physics, vehicle, or track files to improve results.
- Never hard-code public-course coordinates.
- Use paired comparisons with identical seeds/configuration.
- Keep development, validation, and untouched holdout sets separate.
- Prefer minimal explainable changes.
- Revert regressions.
- Never fabricate tests or results.
- Keep runtime comfortably below the official deadline.
- ML must show held-out controller-level benefit before deployment.
- Keep the final submission compatible with the official API/environment.
