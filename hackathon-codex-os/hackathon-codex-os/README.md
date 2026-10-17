# Hackathon Codex OS

A small Codex-native solo hackathon operating system inspired by the design patterns in [Everything Claude Code](https://github.com/affaan-m/ECC), but independently authored for fast solo execution.

## Quick start (Windows PowerShell, macOS, Linux)

1. Install Git, Node.js LTS, Python 3.11+, and the Codex CLI (`npm install -g @openai/codex`). Sign in with `codex login` if required.
2. Extract this ZIP. Open a terminal inside `hackathon-codex-os`.
3. Start `codex` and say: **Use the hackathon-orchestrator skill. Help me select and build a winning project for [event], [theme], [hours], [rules], [judging rubric]. Start by evaluating three feasible ideas.**
4. Fill in `HACKATHON.md` as soon as you have the event rules; if the rules are not known, ask Codex to mark assumptions until verified.
5. Use `/skills` or explicitly ask Codex to use a named skill in `.agents/skills/` if a skill is not auto-selected.
6. Run `python scripts/preflight.py` to audit the repo and `python scripts/demo_check.py` to verify submission deliverables.

## What is included

- `AGENTS.md`: Codex persistent operating instructions.
- `.agents/skills/`: Codex-native skills for track strategy, architecture, simulation, build, design, QA/security and pitch.
- `agents/`: specialist role reference cards (not automatic background agents).
- `HACKATHON.md`, `DECISIONS.md`, `PLAN.md`, `DEMO.md`: persistent project context and progress.
- `scripts/`: offline preflight and demo readiness checks.
- `templates/`: judging, idea selection and submission templates.
- `.github/workflows/`: optional Python-focused smoke checks on pushes.
- `templates/engineering-dashboard/`: reusable Python/Streamlit example.
- `templates/engineering-web/`: React/TypeScript/Vite sample engineering interface.
- `HACKATHON_LAUNCH.md`, `CHALLENGE_INTAKE.md`, `START_HACKATHON.md`: event launch toolkit.
- `PREPARATION_STATUS.md`: environment inventory, verification evidence, and remaining host actions.

## Reusable templates and deployment

See [HACKATHON_LAUNCH.md](HACKATHON_LAUNCH.md) for launch commands and the 12-hour playbook. The Python example uses a local numerical model with simulated inputs. The web dashboard is client-side and needs no backend. Deployment steps and prerequisites are in [DEPLOYMENT.md](DEPLOYMENT.md). Neither app has been published or connected to an external account.

## Working method

**Research -> choose -> vertical slice -> verify -> polish -> demo -> submit.**

Project-specific application code should live under `app/` or the structure agreed in `PLAN.md`. The bundle intentionally doesn't impose a frontend stack before event rules and project choice are known.

## References and limitations

This is not a verbatim copy or a complete port of ECC. ECC itself has Codex support. Original ECC is licensed separately; review its license and any content before reusing files. Codex skills use `SKILL.md` directories, and Codex reads `AGENTS.md`. Specialist roles here are instructions, not guaranteed native parallel subagents. No networked services, accounts, cloud deployment, or API keys are configured automatically. Do not assume rules permit AI tools or starter code; check the event rules.
