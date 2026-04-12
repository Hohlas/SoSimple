# Context Handoff

## Current Stage
Этап `triple_barrier_mt4_verdict` завершён. Этап `entry_path_v1_quantile_productization` закрыт ранее (2026-04-12, коммит `0023d92`).

Что зафиксировано:

- **`entry_path_v1_quantile`** — production-ready parallel execution mode:
  - winner `lb_gt_m_q35` (median m/w/correction по 5 сидам)
  - n-boost gate PASS: N=48, PF=8.18, win_rate=0.8125, negative_year_slices=0, same_winner_ratio=1.0
  - MT4 parity 20/20 сделок, win rate 80% exact, PF=11.91 в деньгах (tester лог `20260412.log`)
  - production rule: `ML/reports/entry_path_v1_quantile_selected_rule.json`
  - канонический экспорт: `API.export_entry_path_v1_quantile_signals --rule-path ...`
  - канонический seed: `seed_007`
- **Triple Barrier** — **не production**:
  - в симуляторе `ML/triple_barrier_mt4_execution.py` был баг: `int(outcome)` приводил label в float-конвенции `{1.0=TP, 0.0=SL, 0.5=Timeout}` к целому, SL и Timeout сливались в одну ветку `else → HoldOverTime, pnl=+0.5`. Все прежние прогоны TB давали `losses=0, pf=inf` — это артефакт, а не результат.
  - фикс: `_classify_tb_outcome` с порогами `>=0.75` → TP, `<=0.25` → SL, else → Timeout; патч применён в обеих точках закрытия позиции
  - тесты `tests/test_triple_barrier_mt4_execution.py` переведены с устаревшей `{1, -1, 0}` int-схемы на float; 6/6 зелёные
  - честный прогон `tb_selected_rule.json` (`theta=0.475`, `min_ev=0.1`) на исправленном симуляторе:
    - validation (2019–2022): N=28, PF=4.33, win_rate=57.1%, все годы положительные
    - test (2023–2026): N=69, PF=1.28, win_rate=42.0%, negative years: 2023 (PF=0.55), 2026 (PF=0.00)
  - gate-проверка (унифицированно с quantile: N≥30, PF>2.0, negative_year_slices=0): **fail** (PF и negative years)
  - `tb_selected_rule.json` зафиксирован как frozen исторический артефакт, в MT4 не подключается
  - пересмотр возможен только после накопления forward-данных post-2026-06

## Last Completed Stage
Triple Barrier MT4 Verdict (2026-04-12).

## Next Step
1. Решить, нужен ли composition-трек `entry_path_v1_quantile` + `fav_3_vs_12` (low priority — quantile уже production, composition может быть излишним усложнением).
2. Forward validation для quantile-слоя: прогон на реальных post-2026-04 данных после накопления ~10–15 сделок (ожидаемо 2–3 месяца). До этого quantile остаётся parallel mode, а не единственным.
3. Если composition не даёт прирост, фокус смещается на entry logic / SL-TP / regime analysis как источники PF uplift — направление из `project_ml_status`.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-12-tb-verdict.md` — TB verdict (не production)
- `docs/reports/2026-04-12-quantile-status-decision.md` — quantile production verdict
- `docs/reports/2026-04-11-entry-path-v1-quantile-mt4-parity.md`
- `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/tb_mt4_verdict/` — артефакты TB прогона (validation/test trades, yearly, summary)

## Open Risks
- **TB regime shift**: между validation (2019–2022) и test (2023–2026) PF падает с 4.33 до 1.28. Если 2026-ый catastrophic year — локальный всплеск, решение пересмотрится на forward-данных, но сейчас это "не production" definitively.
- **Quantile low-frequency**: 22 sequential trades на test, PF=3.64. Достаточно для parallel mode, но не для полной замены baseline. Forward validation критична.
- **Label convention risk**: любой новый TB/label simulator должен сравнивать float-пороги, а не `int()`. Убедиться, что все benchmark-скрипты для TB-label прошли аудит после этого фикса.

## Latest Report
`docs/reports/2026-04-12-tb-verdict.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
