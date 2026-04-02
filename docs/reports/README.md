# Reports

`docs/reports/` holds detailed reports for completed project stages with significant changes. These are the canonical long-form records for work that changes how the project behaves, how results are interpreted, or how the next stage should be handed off.

## When a report is required

Create a report when at least one of these is true:

- code behavior changed in a way that affects results, signals, trading logic, CLI behavior, or data format;
- a tool or research scenario was added or substantially expanded;
- new results were obtained and they led to practical conclusions;
- a bug was fixed that changes how results are interpreted;
- a plan or spec stage was completed and is ready for handoff.

## Naming rule

- Use `YYYY-MM-DD-topic.md`.
- The date must be ISO format.
- Keep `topic` short and descriptive.

## Minimal report structure

Every report has 13 required elements:

1. title line
2. date
3. status
4. goal
5-13. the 9 body sections from `Context` through `Related Materials`

The body starts after the metadata block and uses the same sections:

1. Context
2. What Was Done
3. Changed Files
4. Verification
5. Results
6. Conclusions
7. Limitations / Open Questions
8. Next Step
9. Related Materials

## Header template

```md
# Stage Title

> **Date**: YYYY-MM-DD
> **Status**: Completed
> **Goal**: ...
> **Related plan/spec**: ...
> **Related commit**: pending
```

`Related plan/spec` and `Related commit` are recommended extra header fields. They help with traceability, but they are not part of the 13 required elements.
