# Documentation Audit — 2026-04-01

Область: все markdown-файлы, отслеживаемые git (`124` файлов).

## Методика
- Проверка структуры: наличие H1/H2, размер файла (line count).
- Проверка ссылок: локальные markdown links (пути и якоря).
- Проверка maintainability: файлы >300 строк как кандидаты на декомпозицию.
- Категоризация: core docs, active docs, plans/specs, archive, skills, memory.

## AGENTS.md — Детальный разбор
- Сильные стороны: codex-first фокус, четкие guardrails по CSV/MT, явные команды быстрого старта.
- Соответствие Codex: высокое (структура короткая, приоритеты ясные, есть ссылка на CLAUDE.md для разделения контекстов).
- Улучшения: добавлен явный приоритет источников и разграничение нормативных/вспомогательных источников контекста.

## Ключевые проблемы в активной документации
- После правок: битые ссылки в активной документации не обнаружены (ACTIVE_BROKEN=0).

## Аудит каждого .md файла

| File | Category | Lines | H1 | Local Links | Broken Links | Quality Flags |
|---|---:|---:|---:|---:|---:|---|
| `.claude/memory/MEMORY.md` | memory | 7 | 1 | 3 | 0 | ok |
| `.claude/memory/feedback_ml_approach.md` | memory | 25 | 0 | 0 | 0 | no-h1 |
| `.claude/memory/project_ml_status.md` | memory | 72 | 0 | 0 | 0 | no-h1 |
| `.claude/memory/user_profile.md` | memory | 13 | 0 | 0 | 0 | no-h1 |
| `.claude/skills/brainstorming/SKILL.md` | claude-skill | 164 | 1 | 0 | 0 | ok |
| `.claude/skills/brainstorming/spec-document-reviewer-prompt.md` | claude-skill | 49 | 1 | 0 | 0 | ok |
| `.claude/skills/brainstorming/visual-companion.md` | claude-skill | 285 | 12 | 0 | 0 | ok |
| `.claude/skills/dispatching-parallel-agents/SKILL.md` | claude-skill | 182 | 1 | 0 | 0 | ok |
| `.claude/skills/executing-plans/SKILL.md` | claude-skill | 70 | 1 | 0 | 0 | ok |
| `.claude/skills/finishing-a-development-branch/SKILL.md` | claude-skill | 200 | 10 | 0 | 0 | ok |
| `.claude/skills/receiving-code-review/SKILL.md` | claude-skill | 213 | 1 | 0 | 0 | ok |
| `.claude/skills/requesting-code-review/SKILL.md` | claude-skill | 105 | 1 | 0 | 0 | ok |
| `.claude/skills/requesting-code-review/code-reviewer.md` | claude-skill | 146 | 1 | 0 | 0 | ok |
| `.claude/skills/subagent-driven-development/SKILL.md` | claude-skill | 277 | 1 | 0 | 0 | ok |
| `.claude/skills/subagent-driven-development/code-quality-reviewer-prompt.md` | claude-skill | 26 | 1 | 0 | 0 | ok |
| `.claude/skills/subagent-driven-development/implementer-prompt.md` | claude-skill | 113 | 1 | 0 | 0 | ok |
| `.claude/skills/subagent-driven-development/spec-reviewer-prompt.md` | claude-skill | 61 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/CREATION-LOG.md` | claude-skill | 119 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/SKILL.md` | claude-skill | 296 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/condition-based-waiting.md` | claude-skill | 115 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/defense-in-depth.md` | claude-skill | 122 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/root-cause-tracing.md` | claude-skill | 169 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/test-academic.md` | claude-skill | 14 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/test-pressure-1.md` | claude-skill | 58 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/test-pressure-2.md` | claude-skill | 68 | 1 | 0 | 0 | ok |
| `.claude/skills/systematic-debugging/test-pressure-3.md` | claude-skill | 69 | 1 | 0 | 0 | ok |
| `.claude/skills/test-driven-development/SKILL.md` | claude-skill | 371 | 1 | 0 | 0 | long>300 |
| `.claude/skills/test-driven-development/testing-anti-patterns.md` | claude-skill | 299 | 1 | 0 | 0 | ok |
| `.claude/skills/using-git-worktrees/SKILL.md` | claude-skill | 218 | 10 | 0 | 0 | ok |
| `.claude/skills/using-superpowers/SKILL.md` | claude-skill | 115 | 1 | 0 | 0 | ok |
| `.claude/skills/using-superpowers/references/codex-tools.md` | claude-skill | 25 | 1 | 0 | 0 | ok |
| `.claude/skills/using-superpowers/references/gemini-tools.md` | claude-skill | 33 | 1 | 0 | 0 | ok |
| `.claude/skills/verification-before-completion/SKILL.md` | claude-skill | 139 | 1 | 0 | 0 | ok |
| `.claude/skills/writing-plans/SKILL.md` | claude-skill | 142 | 2 | 0 | 0 | ok |
| `.claude/skills/writing-plans/plan-document-reviewer-prompt.md` | claude-skill | 49 | 1 | 0 | 0 | ok |
| `.claude/skills/writing-skills/SKILL.md` | claude-skill | 655 | 19 | 0 | 0 | long>300 |
| `.claude/skills/writing-skills/anthropic-best-practices.md` | claude-skill | 1150 | 16 | 15 | 15 | long>300, long>700 |
| `.claude/skills/writing-skills/examples/CLAUDE_MD_TESTING.md` | claude-skill | 189 | 1 | 0 | 0 | ok |
| `.claude/skills/writing-skills/persuasion-principles.md` | claude-skill | 187 | 1 | 0 | 0 | ok |
| `.claude/skills/writing-skills/testing-skills-with-subagents.md` | claude-skill | 384 | 1 | 0 | 0 | long>300 |
| `.codex/skills/csv-processing/SKILL.md` | codex-skill | 91 | 1 | 0 | 0 | ok |
| `.codex/skills/jupyter-processing/SKILL.md` | codex-skill | 70 | 2 | 0 | 0 | ok |
| `.codex/skills/rebuild-module-index/SKILL.md` | codex-skill | 47 | 1 | 0 | 0 | ok |
| `.codex/skills/update-docs-on-code-change/SKILL.md` | codex-skill | 60 | 1 | 0 | 0 | ok |
| `.github/copilot-instructions.md` | github-meta | 15 | 1 | 4 | 1 |  |
| `.kilocode/rules-architect/user_rules.md` | kilocode-rules | 11 | 0 | 0 | 0 | no-h1 |
| `.kilocode/rules-ask/user_rules.md` | kilocode-rules | 11 | 0 | 0 | 0 | no-h1 |
| `.kilocode/skills/csv-processing/SKILL.md` | kilocode-skill | 91 | 1 | 0 | 0 | ok |
| `.kilocode/skills/jupyter-processing/SKILL.md` | kilocode-skill | 70 | 2 | 0 | 0 | ok |
| `.kilocode/skills/rebuild-module-index/SKILL.md` | kilocode-skill | 47 | 1 | 0 | 0 | ok |
| `.kilocode/skills/update-docs-on-code-change/SKILL.md` | kilocode-skill | 60 | 1 | 0 | 0 | ok |
| `.kilocode/skills/update-docs-on-code-change/references/file-mappings.md` | kilocode-skill | 64 | 1 | 0 | 0 | ok |
| `.kilocode/skills/update-docs-on-code-change/templates/file-headers.md` | kilocode-skill | 164 | 22 | 0 | 0 | ok |
| `AGENTS.md` | core-agent | 131 | 6 | 7 | 0 | ok |
| `API/README.md` | module-doc | 33 | 5 | 4 | 0 | ok |
| `CHANGELOG.md` | core-root | 543 | 1 | 12 | 0 | long>300 |
| `CLAUDE.md` | claude-agent | 52 | 1 | 2 | 0 | ok |
| `CONTEXT_HANDOFF.md` | core-root | 174 | 5 | 0 | 0 | ok |
| `ML/README.md` | module-doc | 96 | 8 | 17 | 0 | ok |
| `ML/baseline/reports/baseline_report.md` | module-doc | 135 | 1 | 5 | 0 | ok |
| `ML/reports/architecture_comparison_classification.md` | module-doc | 107 | 1 | 9 | 0 | ok |
| `ML/reports/architecture_comparison_regression.md` | module-doc | 51 | 1 | 9 | 0 | ok |
| `ML/reports/architecture_comparison_regression_updn.md` | module-doc | 51 | 1 | 9 | 0 | ok |
| `ML/reports/evaluate_test_H12.md` | module-doc | 16 | 1 | 0 | 0 | ok |
| `ML/reports/evaluate_test_tb.md` | module-doc | 21 | 1 | 0 | 0 | ok |
| `ML/reports/reproducibility_report_12H.md` | module-doc | 50 | 1 | 0 | 0 | ok |
| `ML/reports/threshold_analysis_12H.md` | module-doc | 77 | 1 | 3 | 0 | ok |
| `ML/reports/threshold_analysis_24H.md` | module-doc | 77 | 1 | 3 | 0 | ok |
| `ML/reports/threshold_analysis_48H.md` | module-doc | 77 | 1 | 3 | 0 | ok |
| `MODULE_INDEX.md` | core-root | 80 | 1 | 54 | 0 | ok |
| `MT/MQL4/README.md` | module-doc | 4 | 1 | 0 | 0 | ok |
| `README.md` | core-root | 23 | 3 | 4 | 0 | ok |
| `docs/DATA_FLOW.md` | docs-active | 518 | 17 | 3 | 0 | long>300 |
| `docs/ML/baseline_experiments.py.md` | docs-active | 43 | 1 | 2 | 0 | ok |
| `docs/ML/conformal_prediction.md` | docs-active | 107 | 2 | 3 | 0 | ok |
| `docs/ML/neural_networks.md` | docs-active | 397 | 16 | 1 | 0 | long>300 |
| `docs/MT/lib_PIC.mqh.md` | docs-active | 136 | 1 | 0 | 0 | ok |
| `docs/MT/ml_signal_integration.md` | docs-active | 79 | 5 | 2 | 0 | ok |
| `docs/MT/trading_strategy.md` | docs-active | 738 | 1 | 7 | 0 | long>300, long>700 |
| `docs/PRD.md` | docs-active | 110 | 1 | 3 | 0 | ok |
| `docs/archive/#QUESTIONS.md` | archive | 91 | 1 | 0 | 0 | ok |
| `docs/archive/03.10_audit_answers/another agents/GLM5/GLM5-architecture_decision.md` | archive | 218 | 1 | 0 | 0 | ok |
| `docs/archive/03.10_audit_answers/another agents/GLM5/GLM5-project_audit_and_plan.md` | archive | 299 | 4 | 0 | 0 | ok |
| `docs/archive/03.10_audit_answers/another agents/kimi-k2.5/kimi_architecture_decision.md` | archive | 292 | 3 | 7 | 7 |  |
| `docs/archive/03.10_audit_answers/another agents/kimi-k2.5/kimi_project_audit_and_plan.md` | archive | 488 | 18 | 23 | 23 | long>300 |
| `docs/archive/03.10_audit_answers/another agents/minimax-m2.5/minimax_architecture_decision.md` | archive | 172 | 6 | 4 | 4 |  |
| `docs/archive/03.10_audit_answers/another agents/minimax-m2.5/minimax_project_audit_and_plan.md` | archive | 342 | 12 | 8 | 8 | long>300 |
| `docs/archive/03.10_audit_answers/audit_reproducibility_analysis.md` | archive | 180 | 5 | 7 | 7 |  |
| `docs/archive/03.10_audit_answers/opus-architecture_decision.md` | archive | 193 | 1 | 2 | 2 |  |
| `docs/archive/03.10_audit_answers/opus-project_audit_and_plan.md` | archive | 441 | 1 | 6 | 6 | long>300 |
| `docs/archive/03.10_audit_answers/walkthrough.md` | archive | 58 | 2 | 14 | 14 |  |
| `docs/archive/0315/plans_Nemotron_free.md` | archive | 81 | 1 | 0 | 0 | ok |
| `docs/archive/0316/Custom Trading Loss Results.md` | archive | 40 | 1 | 3 | 3 |  |
| `docs/archive/0317/MEMORY.md` | archive | 7 | 1 | 3 | 0 | ok |
| `docs/archive/0317/feedback_ml_approach.md` | archive | 21 | 0 | 0 | 0 | no-h1 |
| `docs/archive/0317/project_ml_status.md` | archive | 23 | 0 | 0 | 0 | no-h1 |
| `docs/archive/0317/serialized-foraging-honey.md` | archive | 173 | 1 | 0 | 0 | ok |
| `docs/archive/0317/user_profile.md` | archive | 13 | 0 | 0 | 0 | no-h1 |
| `docs/archive/0317_claude_answer.md` | archive | 132 | 4 | 0 | 0 | ok |
| `docs/archive/0318.md` | archive | 78 | 1 | 0 | 0 | ok |
| `docs/archive/0319_Gemini.md` | archive | 89 | 0 | 2 | 2 | no-h1 |
| `docs/archive/0320_Codex.md` | archive | 5 | 0 | 0 | 0 | no-h1 |
| `docs/archive/signal_tracer/path_ordering_analysis.md` | archive | 47 | 1 | 0 | 0 | ok |
| `docs/archive/signal_tracer/phase_a_results.md` | archive | 110 | 1 | 0 | 0 | ok |
| `docs/archive/signal_tracer/trade_analysis_20260324.md` | archive | 214 | 1 | 0 | 0 | ok |
| `docs/dataset_description.md` | docs-active | 121 | 1 | 0 | 0 | ok |
| `docs/plans/2026-03-22-triple-barrier.md` | plans | 943 | 5 | 1 | 0 | long>300, long>700 |
| `docs/plans/ME13_Diagnostics_Plan.md` | plans | 55 | 2 | 1 | 0 | ok |
| `docs/plans/ml_implementation_plan.md` | plans | 287 | 1 | 15 | 0 | ok |
| `docs/plans/project_refactoring.md` | plans | 80 | 0 | 0 | 0 | no-h1 |
| `docs/processing/label_main.py.md` | docs-active | 53 | 5 | 0 | 0 | ok |
| `docs/processing/label_signals.py.md` | docs-active | 26 | 1 | 0 | 0 | ok |
| `docs/processing/normalize.py.md` | docs-active | 46 | 6 | 0 | 0 | ok |
| `docs/specs/2026-03-22-triple-barrier-design.md` | specs | 284 | 1 | 0 | 0 | ok |
| `docs/statistics/EDA.ipynb.md` | docs-active | 273 | 1 | 3 | 0 | ok |
| `docs/statistics/signal_tracer.py.md` | docs-active | 232 | 5 | 4 | 0 | ok |
| `docs/statistics/statistics.py.md` | docs-active | 138 | 6 | 0 | 0 | ok |
| `docs/superpowers/plans/2026-03-25-updn-denormalization.md` | superpowers | 469 | 5 | 0 | 0 | long>300 |
| `docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md` | superpowers | 585 | 17 | 0 | 0 | long>300 |
| `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md` | superpowers | 211 | 2 | 0 | 0 | ok |
| `docs/superpowers/specs/2026-03-27-pf-improvement-design.md` | superpowers | 287 | 1 | 0 | 0 | ok |
| `processing/README.md` | module-doc | 33 | 3 | 4 | 0 | ok |
| `statistics/README.md` | module-doc | 48 | 6 | 4 | 0 | ok |
| `statistics/reports/EDA_report.md` | module-doc | 1354 | 2 | 23 | 0 | long>300, long>700 |