# Test Plan Template

Use this as the default shape for `test-plan.md` or the repo's equivalent validation file.

## Principles

- Tie test coverage to the actual milestones and behavior changes in the plan.
- Prefer runnable checks over vague test intentions.
- Separate smoke checks from deeper regression coverage.
- Make release and demo gates explicit.
- Record what is intentionally not covered yet.

## Recommended Skeleton

````md
# Test Plan

## Source
- Task: <one-line task statement>
- Plan file: <path>
- Status file: <path>
- Repo context: <repo or package area>
- Last updated: <YYYY-MM-DD>

## Validation Scope
- In scope: <behaviors, flows, components, APIs>
- Out of scope: <deferred or non-applicable areas>

## Environment / Fixtures
- Data fixtures: <seed data, mocks, sample inputs>
- External dependencies: <APIs, queues, services, browsers, devices>
- Setup assumptions: <env vars, local services, accounts>

## Test Levels

### Unit
- <what must be covered>

### Integration
- <critical integrations or contracts>

### End-to-End / Smoke
- <core user journeys or CLI/API flows>

## Negative / Edge Cases
- <failure mode>
- <boundary or malformed input>
- <permission / auth / network issue>

## Acceptance Gates
- [ ] `lint`
- [ ] `typecheck`
- [ ] `test`
- [ ] `build`
- [ ] <repo-specific acceptance command>

## Release / Demo Readiness
- [ ] Core scenario works end to end
- [ ] Primary regression checks are green
- [ ] No blocker-level known issue remains
- [ ] Demo steps are reproducible

## Command Matrix
```sh
<command 1>
<command 2>
```

## Open Risks
- <known validation gap>

## Deferred Coverage
- <follow-up test work that is not required for the current slice>
````

## Adaptation Rules

- If the repo already uses `TEST_PLAN.md`, keep that convention.
- If the task is infra-only or docs-only, compress the file but keep explicit acceptance gates.
- If commands are unknown, keep provisional defaults and label them as assumptions.
- If a milestone adds or changes behavior, reflect the new checks here before considering the milestone complete.
