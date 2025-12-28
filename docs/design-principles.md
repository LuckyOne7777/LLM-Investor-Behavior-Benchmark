# Design Principles

## Current Direction

LIBB's direction emphasizes transparency,
explicit state, and user-controlled execution.

This direction is not intended to be final. Alternative
approaches, abstractions, or philosophies may be explored as the project
evolves, and differing perspectives are welcome.

Some of these choices emerged organically during development rather than
from a fixed plan, but they reflect a direction the project intentionally
continues to support.


If you disagree with any of these choices or have a strong alternative
idea, feel free to reach out. Anyone interested enough to read the design
philosophy deserves to have their perspective heard.

The goal is to support rigorous research, not to enforce a single way of
working.

---

## Exposed Variables and Functions

All class variables and functions are explicitly exposed, allowing users
to freely edit variables such as portfolio and cash.

In the future, name mangling may be introduced for deeper system
functions and variables where appropriate.

---

## User-Controlled Execution and Logs

LIBB does not enforce a fixed execution loop or scheduling model.
Instead, users are responsible for defining how and when different
steps are run (e.g., daily vs. weekly workflows).

LIBB also allows custom data persistence, enabling users to expand or
move away from the default *Daily Updates* and *Deep Research* output
logging structure.

---

## Avoiding Reliance on Existing Infrastructure

To maintain maximum control and transparency, the codebase intentionally
avoids heavy external frameworks orAPIs. This design allows both
users and project developers to freely inspect, modify, and extend all
aspects of LIBB without being constrained by hidden abstractions.
