# Accessing State

LIBB intentionally exposes all internal state through the `LIBBmodel` object.

There is no abstraction layer between the user and the model state. This design
allows maximum flexibility when constructing prompts, reports, and custom
workflows.

All state access is explicit and user-controlled.

---

## Passing the Model Object

To access internal variables, pass the `LIBBmodel` instance directly into
user-defined functions.

This is the recommended pattern for prompt construction and report generation.

```python

def create_daily_prompt(libb):
portfolio = libb.portfolio
starting_cash = libb.STARTING_CASH
today = libb.date
...
```

Any attribute stored on the `LIBBmodel` instance may be accessed in this way.

---

## Read vs Write Responsibility

LIBB does not enforce read-only protections on internal variables.

Users are free to inspect, modify, or overwrite class attributes directly.
This freedom comes with responsibility.

**There are no error checks preventing you from mutating critical state.**

Overwriting core variables may silently break the workflow.

Examples of high-risk attributes include (but are not limited to):

- `portfolio`
- `cash`
- `date`
- processed data structures created by `process_portfolio()`

Only modify internal state if you explicitly understand the downstream effects.

---

## Intended Usage

State access is primarily intended for:

- prompt construction
- report generation
- conditional logic based on portfolio state
- custom extensions outside the core workflow

State mutation should be treated as an advanced operation.

---

## Design Intent

LIBB prioritizes transparency over safety.

Rather than hiding state behind getters or enforcing rigid interfaces, LIBB
assumes the user understands the system they are operating.

This makes LIBB suitable for research, experimentation, and audit-driven
workflows where explicit control is preferred over guardrails.
