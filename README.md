# LLM Investor Behavior Benchmark (LIBB)

## What Is LIBB?

LIBB is an open-source research framework designed to automatically manage portfolio state and compute key metrics,
while still giving users flexibility over the system.

## Why LIBB Exists
This project originally began as a generic benchmark for LLM-based trading in U.S. equities. While surveying existing LLM trading projects (including my own), I noticed a consistent lack of rigorous sentiment, behavioral, and performance metrics; most projects reported little more than an equity curve.

This raised a fundamental question: ***“Why isn’t LLM trading held to the same analytical standards as the rest of finance?”***

Since then, the project has evolved into a high-quality, easy-to-use research framework designed to support more rigorous evaluation of LLM-driven trading systems. The long-term goal is to provide a shared foundation for this work and, ultimately, to establish a community standard for this type of research.

## Features

- **Persistent portfolio state**  
  All portfolio data is explicitly stored on disk, enabling inspection,
  reproducibility, and post-hoc analysis across runs.

- **Sentiment analysis metrics**  
  Built-in support for sentiment analysis, with results persisted as
  first-class research artifacts.

- **Performance tracking (in progress)**  
  Infrastructure for performance metrics is included, with ongoing
  integration into the core model workflow. Behavioral analytics is still being devolopped.

- **Reproducible run structure**  
  Each model run follows a consistent on-disk directory layout, making
  experiments easy to reproduce, compare, and archive.

- **Flexible execution workflows**  
  Execution logic remains fully user-controlled, allowing researchers
  to integrate custom strategies, models, or data sources.

## How It Works

LIBB operates as a file-backed execution loop where portfolio state,
analytics, and research artifacts are explicitly persisted to disk.

For each run, the framework:

1. Loads and processes existing portfolio state
2. Recieves inputs (e.g., via an LLM)
3. Computes and stores analytical signals (such as sentiment) via explicit user calls
4. saves execution instructions (orders) by passing JSON block
5. Persists all outputs for inspection and reuse

Execution scheduling (e.g., daily vs. weekly runs) and model orchestration
are intentionally left to the user, preserving flexibility while
maintaining a consistent on-disk state.

## Research Directions

LIBB is an exploratory research framework, and its development is driven
by ongoing questions rather than a fixed roadmap.

Areas of current interest include:

- Deeper integration of performance analytics into the core workflow
- Behavioral analysis derived from trading decisions and execution patterns
- Expansion of sentiment analytics across multiple data sources
- Improved tooling for comparing runs and strategies over time
- General design improvements for efficiency and code quality

To see the current roadmap for major features, check out: roadmap.md

These directions reflect current research interests and may evolve,
change, or be abandoned as the project develops.
