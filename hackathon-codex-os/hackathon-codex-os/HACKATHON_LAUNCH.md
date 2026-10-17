# HackBama launch guide

## Launch the templates

### Python / Streamlit

```bash
cd templates/engineering-dashboard
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pytest
streamlit run app.py
```

Open the local URL Streamlit prints (normally `http://localhost:8501`). The chart and inputs use a clearly labeled deterministic simulated engineering example.

### React / TypeScript / Vite

```bash
cd templates/engineering-web
npm ci
npm run dev
```

Production check: `npm run build`. Open the URL Vite prints (normally `http://localhost:5173`). The committed `package-lock.json` locks the transitive dependency tree.

## First 15 minutes: choose a track

1. Minutes 0–3: read both official problem statements, constraints, required integrations, and deadlines; copy exact text and sources to `CHALLENGE_INTAKE.md`.
2. Minutes 3–6: extract each judging criterion and weight; ask organizers about any ambiguous hard rule.
3. Minutes 6–10: propose one small demo idea per track and score both using the matrix below.
4. Minutes 10–13: verify the riskiest assumption for each (data, hardware, API, rules) using a tiny local probe or organizer clarification.
5. Minutes 13–15: choose the best feasible score, record the decision and one-sentence demo path, then start a vertical slice.

### Track comparison scorecard

Rate 1 (poor) to 5 (excellent), multiply by weight / 100. Apply published judging weights to rubric alignment; split the remaining weight as shown. If the rubric is unavailable, mark it provisional.

| Dimension | Weight | Track A (1–5) | Track B (1–5) |
|---|---:|---:|---:|
| Published rubric alignment | 40% |  |  |
| Can build core demo in 6 hours | 20% |  |  |
| Clear, observable demo moment | 15% |  |  |
| Data/integration reliability | 15% |  |  |
| Personal familiarity / credible explanation | 10% |  |  |
| **Weighted total / 5** | **100%** |  |  |

For more than one published criterion, score each criterion with its official weight, and normalize the other dimensions into the remaining weight. A hard-rule violation disqualifies the option regardless of score.

## Stack choice

Start with the tools already installed and familiar. Prefer one frontend and local fixture data. Choose Python/Streamlit for data-heavy engineering calculations and fast iteration; choose React/Vite when interaction, visual polish, or a browser-only experience matters. Add a backend only for a demonstrated requirement. Add a third-party API only when its credentials, terms, network, and demo fallback are verified. Recheck event constraints before committing.

## 12-hour schedule

| Elapsed | Work |
|---|---|
| 0:00–0:15 | Intake, rules, track choice |
| 0:15–0:45 | Pick user/problem, agree on demo and architecture |
| 0:45–1:15 | Scaffold and verify clean launch |
| 1:15–5:30 | Build the smallest end-to-end demo; validate with sample data |
| 5:30–6:00 | Midpoint scope cut; resolve highest-risk assumption |
| 6:00–8:15 | Complete core flow and useful feedback/error states |
| 8:15–9:00 | Automated checks and bug fixing |
| 9:00–9:45 | UI polish and technical explanation |
| 9:45–10:30 | Demo script, presentation outline, screenshots if allowed |
| 10:30–11:15 | Freeze features; clean-start and failure fallback rehearsal |
| 11:15–12:00 | Final demo, submission validation, submit before deadline |

Adjust to event milestones, but reserve the final 25% for verification, rehearsal, and submission.

## Demo readiness

- [ ] The main user journey runs from a clean start using documented commands.
- [ ] Demo data is labeled as simulated or sample; live services are identified accurately.
- [ ] Loading, empty, and error states are understandable.
- [ ] Automated tests pass; critical outputs are checked against known values.
- [ ] No secrets or personal data appear in source, logs, screenshots, or presentation.
- [ ] Demo can run offline or has an offline fixture fallback.
- [ ] Two-minute demo and 30-second hook are rehearsed; capture backup only if rules allow.
- [ ] Claims have evidence; limitations are stated plainly.

## Final submission

- [ ] Confirm team, AI, code reuse, licensing, data, and submission rules.
- [ ] Confirm correct project URL/file, permissions, and required fields.
- [ ] Check README, setup steps, presentation, and required AI disclosures.
- [ ] Check repo status and secrets; preserve a local working copy.
- [ ] Submit before the deadline and verify the confirmation/receipt.

## Failure fallback

- API or credentials fail: switch to bundled sample fixtures and label the simulation; keep the core value demonstrable.
- Deployment fails: run locally, screen-share if permitted, and prepare a short local recording/screenshots if allowed. Never claim a deployment that is not live and checked.
- Internet fails: stop dependency changes, use cached/local dependencies and fixture data; export slides and demo assets locally.
- App fails: use the last known working commit, run the smallest path, and show a recorded/screenshot fallback if the rules permit.
