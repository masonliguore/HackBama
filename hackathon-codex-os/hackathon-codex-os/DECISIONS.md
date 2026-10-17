# Decision log

| Date | Decision | Alternatives considered | Reason / tradeoff |
|---|---|---|---|
| 2026-10-16 | Prepare two independent reusable demo templates, one Streamlit and one React/Vite | Preselect a single challenge stack; introduce backend infrastructure | Challenge statements are unreleased. Provide useful generic engineering starters without guessing the track. |
| 2026-10-16 | Use a deterministic constant-force motion example and local simulated data | Live sensor/vehicle data; external API | Works offline when dependencies are available and has transparent assumptions. It is not a real-world validated model. |
| 2026-10-16 | Keep Python dependencies and web direct dependencies pinned | Floating latest dependencies | Reproducible direct requirements; web transitive lockfile still needs npm to generate. |
