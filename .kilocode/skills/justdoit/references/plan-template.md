# Plan Template

Use this as the default shape for `plans.md` or the repo's equivalent plan file.

## Principles

- Keep milestones dependency-ordered.
- Keep milestones small enough for one execution loop.
- Every milestone must have an observable done condition.
- Every milestone must have validation commands or an explicit validation assumption.
- If a task changes behavior, reflect the needed tests in the milestone.

## Recommended Skeleton

````md
# Plans

## Source
- Task: <one-line task statement>
- Canonical input: <PRD / issue / user request / note>
- Repo context: <repo or package area>
- Last updated: <YYYY-MM-DD>

## Assumptions
- <explicit assumption>

## Validation Assumptions
- <only if real repo commands are missing>

## Milestone Order
| ID | Title | Depends on | Status |
| --- | --- | --- | --- |
| M1 | <title> | - | [ ] |
| M2 | <title> | M1 | [ ] |

## M1. <Milestone title> `[ ]`
### Goal
- <what becomes true after this milestone>

### Tasks
- [ ] <task 1>
- [ ] <task 2>

### Definition of Done
- <observable result>
- <user-visible or repo-visible outcome>

### Validation
```sh
<command 1>
<command 2>
```

### Known Risks
- <risk>

### Stop-and-Fix Rule
- If validation fails, fix the failure before moving to the next milestone.

## M2. <Milestone title> `[ ]`
...
````

## Adaptation Rules

- If the repo already uses `PLAN.md`, `plans.md`, or a different path, keep that convention.
- If the task is large, use phases first, then milestones inside the active phase.
- If later milestones depend on unresolved product choices, keep them coarse and state the dependency explicitly.
- If the plan already exists, preserve completed milestones and only rewrite affected sections.
