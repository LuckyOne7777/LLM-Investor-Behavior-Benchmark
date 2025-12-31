## Current Direction

LIBB emphasizes transparency, explicit state, and user-controlled execution.  
The system is designed to make behavior observable, modifiable, and debuggable rather than hidden behind abstractions.

These design choices define the current direction of the project.  
They may evolve over time, but they reflect the principles the codebase actively supports today.

The goal is to support rigorous research workflows without enforcing a single way of working.

## Exposed Variables and Functions

All class variables and functions are explicitly exposed.  
Users are free to inspect and modify state such as portfolio values and cash balances.

Name mangling is used to discourage accidental modification of critical internals, not to prevent access.

## User-Controlled Execution and Logs

LIBB does not enforce a fixed execution loop or scheduling model.  
Users define when and how steps are run (e.g., daily vs. weekly workflows).

Data persistence is also user-controlled.  
The default logging structure can be extended, replaced, or bypassed entirely.

## Avoiding Reliance on Existing Infrastructure

The codebase avoids heavy external frameworks and APIs.  
This keeps behavior explicit and allows users to inspect, modify, and extend the system without relying on hidden abstractions.