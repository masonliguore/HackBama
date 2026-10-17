# Reliability-first hybrid controller plan

| Stage | Acceptance check | Status |
|---|---|---|
| Preserve original | Hash and byte-identical backup recorded | complete |
| Reproduce original | Official bicycle selftest, all five public courses | complete |
| Deterministic hardening | Defensive inputs, constrained path candidates, planned-path speed | complete; retained as experiment |
| ML study | Grouped train/validation split and embedded NumPy inference | complete; model retained for future work |
| Common evaluation | Original vs deterministic vs hybrid on identical 20-course held-out set | complete |
| Final selection | Reliability policy applied; preserved controller remains submission | complete |
| Judge evidence | Failure report, architecture, Q&A, four-minute outline | complete |

Owner: Codex. Rollback: `backups/hackbama_final_verified.py`. The official simulator,
scoring configuration, public tracks, and physics remain unmodified.
