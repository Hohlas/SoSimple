# Status Template

Use this as the default shape for `status.md` or the repo's equivalent live-log file.

## Principles

- Make resume trivial for the next run.
- Keep `Next` aligned with the first unfinished milestone in the plan.
- Record assumptions and decisions separately.
- Keep blockers compact and actionable.
- Make smoke commands and demo checks copy-pasteable.

## Recommended Skeleton

````md
# Status

## Snapshot
- Current phase: <phase or milestone>
- Plan file: <path>
- Status: <green / yellow / red>
- Last updated: <YYYY-MM-DD>

## Done
- <completed item>

## In Progress
- <current work item or `none`>

## Next
- <exact next milestone / task>

## Decisions Made
- <decision> - <reason>

## Assumptions In Force
- <assumption>

## Commands
```sh
<smoke or validation command>
```

## Current Blockers
- None

## Audit Log
| Date | Milestone | Files | Commands | Result | Next |
| --- | --- | --- | --- | --- | --- |
| <YYYY-MM-DD> | <milestone> | <paths> | `<cmd>` | <pass/fail> | <next> |

## Smoke / Demo Checklist
- [ ] <core user path works>
- [ ] <startup/build path works>
- [ ] <primary regression checks run>
````

## Update Rules

- Never delete useful history from the audit log unless it is clearly stale and migrated elsewhere.
- When a milestone is completed, update `Done`, clear `In Progress`, and advance `Next`.
- When validations fail, log the failing command and keep the status on the current milestone.
- When the plan changes, note the reason in `Decisions Made` or the audit log.
