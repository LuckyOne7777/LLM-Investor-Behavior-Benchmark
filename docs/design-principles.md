# Design Principles

## Current Direction

LIBB reflects a particular set of design choices and priorities at its
current stage of development. These choices emphasize transparency,
explicit state, and user-controlled execution.

This direction is not intended to be prescriptive or final. Alternative
approaches, abstractions, or philosophies may be explored as the project
evolves, and differing perspectives are welcome.

If you disagree with any of these choices, or have a strong alternative idea, feel free to reach out.
Anyone interested enough to read the design philosophy deserves to have their perspective heard.

The goal is to support rigorous research, not to enforce a single way of
working.

## Exposed Variables and Functions

All class variables and functions are explicitly exposed, allowing users to freely edit varibles such as portfolio and cash. 
In the future, however, I will most likely incorporate name mangling for deep system functions and variables. 

---

## User-Controlled Execution and Logs

LIBB does not enforce a fixed execution loop or scheduling model.
Instead, users are responsible for defining how and when different
steps are run (e.g., daily vs. weekly workflows).

LIBB also freely allows custom data saving, 
enabling users to expand or move away from the basic *Daily Updates/Deep Research* output log setup.

---

## Avoiding Reliance on Existing Infrastructure

To maintain maximum control and transparency, the codebase intentionally
avoids heavy external frameworks or APIs. This design allows both
users and project developers to freely inspect, modify, and extend all
aspects of LIBB without being constrained by hidden abstractions.
