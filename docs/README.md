# How to Read This Repository

This project is a stateful trading system designed for daily execution and research.
It prioritizes explicit state, filesystem-backed persistence, and simple orchestration
over abstract frameworks.

If you are new here, check out the main `README.md` and **do not start by reading the code**.
Start with the documents below.

This folder is best read in the recommended order rather than file-by-file.


---

## Recommended Reading Order

### 1. Design Intent (Optional)
These documents explain *why* the system looks the way it does.

- `design-principles.md` — Core philosophy and tradeoffs

---

### 2. How a Run Works
Main ideas and caveats for execution.

- `important-constraints.md` — Current design boundaries
- `workflow.md` — End-to-end lifecycle of a single run

---

### 3. What the System Can Do
These describe the major capabilities at a high level.

- `capabilities/`
  - `accessing-state.md`
  - `file-interaction.md`
  - `metrics.md`

---

### 4. Reading the Code
Once the above is clear, start here:

- `user_side/*` - For an example workflow
- `libb/model.py` — Central orchestrator (`LIBBModel`)
- `libb/execution/` — Order processing and portfolio mutation
- `libb/metrics/` — Metrics and analysis modules

---

## Contributing

If you plan to contribute or extend the system, read:

- `short-term-roadmap.md` — What’s intentionally missing or evolving
- `contributing.md` - Overview for contribution
