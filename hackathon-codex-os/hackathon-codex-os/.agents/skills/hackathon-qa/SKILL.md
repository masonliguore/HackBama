---
name: hackathon-qa
description: Use to run a critical-path QA, robustness, and security audit before a demo.
---

# Hackathon Qa

1. Read DEMO.md and run the documented local setup from clean state if feasible.
2. Test core flow, failure handling, no-internet/demo fallback, missing environment variables, obvious security/privacy risks and mobile layout.
3. Capture commands and results. Don't mark checks passed unless observed.
4. Classify findings P0 demo blocker, P1 serious, P2 cosmetic. Fix P0 first.
5. Run scripts/preflight.py and scripts/demo_check.py; distinguish checklist coverage from functional test verification.
