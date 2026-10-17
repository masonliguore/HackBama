# HackBama EcoCAR Project

Reliability on unseen courses is the primary objective. Avoid controller errors, invalid commands, overruns, DNFs, missed gates, off-course events, and cone hits.

Use the `ecocar-reliability` skill for controller changes, failure analysis, ML experiments, and submission decisions.

Read the official rules/API/scoring code before assuming constraints. Preserve the verified submission before modifying it.

Work by: reproduce failure -> inspect telemetry -> state hypothesis -> minimal fix -> regression test -> paired evaluation -> keep/revert.

Do not make broad speculative rewrites. Do not modify official simulator/scoring/physics/track files to improve results.

ML is desired only if it measurably improves held-out reliability. Prefer learned grip/stability estimation or short-horizon risk prediction; deterministic physical constraints retain final authority.
