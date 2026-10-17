# Execution Plan

## Current stage
Preparation complete; challenge intake pending event release

## Problem / target user / one-sentence value proposition
Reusable Streamlit engineering dashboard and React/Vite engineering interface. The challenge-specific project remains TBD until official rules and judging criteria are available.

## Single demo-critical flow
Python/Streamlit: `cd templates/engineering-dashboard && python -m pip install -r requirements.txt && streamlit run app.py`. React: `cd templates/engineering-web && npm ci && npm run dev` (lockfile and host checks pending Node/npm availability).

## Stack and launch commands
TBD

## Tasks (copy rows as needed)
| Priority | Task | Acceptance check | Status | Owner |
|---|---|---|---|---|
| P0 | Verify contest rules | Sources recorded in HACKATHON.md | TODO | Human/Codex |
| P0 | Pick idea | Compare 3 ideas against rubric and risk | TODO | Human/Codex |
| P0 | Make minimal end-to-end flow | Run it and observe expected result | TODO | Codex |
| P0 | Verify demo and fallback | Complete 3 clean rehearsals | TODO | Human |
| P0 | Submit | Confirm all submission fields accepted | TODO | Human |

| Priority | Task | Acceptance check | Status | Owner |
|---|---|---|---|---|
| P0 | Prepare reusable engineering dashboard | App starts and calculation tests pass | BLOCKED: pip/venv missing | Codex + host setup |
| P0 | Prepare reusable web dashboard | Dev server and production build succeed | BLOCKED: Node/npm missing | Codex + host setup |
| P1 | Check GitHub access and deployment | CLI/account status and project access verified | BLOCKED: gh and deployment accounts unavailable | Human |

## Risks / external blockers
Python 3.10.12/Git/Codex CLI/VS Code CLI present under WSL2 Ubuntu 22.04. Codex is logged in. `python3-venv`, pip, Node/npm, and `gh` are absent. Windows interop and VS Code server extension listing fail; details in PREPARATION_STATUS.md.

## Last known working state
TBD

## Next action
Install/enable Python venv and Node/npm in this WSL environment, then rerun blocked checks; complete challenge intake when official rules are released.
