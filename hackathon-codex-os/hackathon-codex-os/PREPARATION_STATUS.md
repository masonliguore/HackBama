# Preparation status

Last verified: 2026-10-16 (America/Chicago), in WSL2 Ubuntu.

## Environment inventory

| Item | Observed | Status |
|---|---|---|
| Host | WSL2 Linux x86_64; PowerShell interop still errors with `UtilBindVsockAnyPort` | Windows-side tool inventory not verified |
| Python | System Python 3.10.12; project `.venv` Python 3.10.12 | Available; dashboard uses its isolated environment |
| pip | System `python3 -m pip` is absent; dashboard `.venv` has pip 22.0.2 | Dashboard environment ready |
| Python packages | NumPy 2.2.2, pandas 2.2.3, SciPy 1.15.1, Plotly 6.0.0, Streamlit 1.41.1, pytest 8.3.4 | Installed in dashboard `.venv` |
| Node / npm | Node v24.22.0; npm 11.19.1 | Available |
| Git | 2.34.1 | Repository initialized; user.name/email still unset in WSL Git config |
| Codex CLI | `codex-cli 0.162.0-alpha.17.2` | Available; `codex login status` reports logged in using ChatGPT |
| VS Code CLI | 1.142.0 | Available; extension list cannot reach WSL VS Code server socket (`EPERM`) |
| GitHub CLI | `gh` not found | GitHub authentication/repository access not verified |

## Requested checks

| Check | Result |
|---|---|
| Python virtual environment | **Pass**: project `.venv` isolation and pip verified |
| Python dependency imports | **Pass**: all six requested packages imported; versions above |
| Streamlit application starts | **Pass**: started locally and returned HTTP 200 (1,837-byte response) |
| Engineering calculation tests | **Pass**: `pytest -q` → 5 passed |
| React development server | **Pass**: Vite 6.4.4 started at `http://127.0.0.1:5173/`; HTTP 200 after final dependency update |
| React production build | **Pass**: clean `npm ci && npm run build`; Vite completed. Warning: generated JS chunk is ~4.99 MB (~1.54 MB gzip) |
| JavaScript dependency audit | **Pass**: `npm audit` → 0 vulnerabilities after updating Vite and Plotly |
| npm install scripts | Warning only: npm 11 reports `es5-ext` and `esbuild` install scripts not covered by `allowScripts`; clean install and build still passed |
| Git repository | **Pass**: local repository, clean status after latest prep commit |
| No secrets tracked | **Pass**: tracked env/token/secret-name and credential-pattern scans found no credentials; `.env.example` is the only tracked env file |
| Codex instructions and skills | **Pass**: AGENTS.md plus eight `.agents/skills/*/SKILL.md` files are present and discoverable |
| Local config parsing / preflight | **Pass**: Python compilation, JSON parsing, and `python3 scripts/preflight.py` |
| Demo readiness checklist | Partial: `python3 scripts/demo_check.py` reports 2/8 complete; rehearsal, event rules, submission, and deployment checks remain event-dependent |

## Remaining actions

1. If GitHub repository access is needed, install `gh`, authenticate, and confirm access. No remote repository was created.
2. Set your personal Git `user.name` and `user.email` in WSL before future commits; the preparation commits used a one-command temporary identity without changing persistent Git configuration.
3. Check the Codex VS Code extension from the Windows VS Code UI or after restoring the WSL VS Code server socket. PowerShell interop remains unavailable from this WSL session.
4. When challenge statements/rules are released, complete `CHALLENGE_INTAKE.md` and confirm AI, starter-code, deployment, and submission requirements.
5. Rehearse the demo and complete the remaining checklist in `DEMO.md`. No cloud account was connected and nothing was published.

## Repository record

Initial baseline: `9a341c1`. The latest preparation status, lockfile, and security fixes are in the current follow-up commit; inspect with `git log -2 --oneline`.
