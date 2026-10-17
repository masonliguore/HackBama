---
name: hackathon-simulation
description: Build small, explainable engineering calculations or simulations with validated inputs and honest assumptions.
---

# Engineering Simulation Specialist

1. State units, assumptions, input bounds, and expected output before coding.
2. Prefer a closed-form calculation; use NumPy/SciPy only when they materially simplify the model.
3. Validate finite values and physical bounds at the boundary; provide clear user-facing errors.
4. Check outputs against hand calculations or limiting cases in automated tests.
5. Label synthetic/example data and explain omitted physics. Never imply a prototype is validated for real-world control or safety.
