---
name: project_ml_status
description: Долговечный статус ML: production regression_updn + quantile parallel execution, PF-оптимизация через entry logic и filtering
type: project
originSessionId: 98fd8647-310f-41a6-a55c-4f19ad140a3e
---
## Production опора и устойчивое направление

- Production-модель: `regression_updn` с 10 таргетами, Transformer checkpoint `ML/checkpoints/transformer_updn_best.pt`.
- Production-опора в MT4 использует существующий ML-сигнал, а не смену архитектуры.
- **С 2026-04-12**: `entry_path_v1_quantile` подтверждён как **parallel execution mode** в MT4. Winner `lb_gt_m_q35` (median m/w/correction по 5 сидам) прошёл n-boost gate (N=48, PF=8.18, same_winner_ratio=1.0) и MT4 parity-check (20/20 сделок, win rate 80% exact).
- Production rule: `ML/reports/entry_path_v1_quantile_selected_rule.json`. Экспорт в MT4: `API.export_entry_path_v1_quantile_signals --rule-path ...`. Канонический seed для экспорта — `seed_007`.
- Устойчивое направление исследований: улучшать PF через монетизацию сигнала, entry logic, filtering, SL/TP и regime analysis.

## Долговечные выводы

- Бакет `ratio_12=3-4` слабый и опасный.
- Простые short-horizon directional filters в ratio-threshold форме не дают полезного сигнала.
- Перед изменениями EA нужна path-dependent OHLC диагностика, а не только aggregate metrics.
- **TB-слой** (`tb_selected_rule.json`, `theta=0.475`) **не production**: gate_fail на test (N=69, PF=1.28, negative years 2023 и 2026). Validation смотрелся здоровым (PF=4.33), но не обобщается. Пересмотр возможен только после накопления forward-данных post-2026-06. Подробности: `docs/reports/2026-04-12-tb-verdict.md`.
- **Label convention в `Nero_*_labeled.csv`** — float: `1.0`=TP, `0.0`=SL, `0.5`=Timeout (источник: `processing/label_signals.py:919`). Любой simulator/benchmark по TB-label должен сравнивать по float-порогам, а не через `int(...)` — иначе SL и Timeout сливаются и `losses=0` будет артефактом.

## Опорные документы

- `docs/reports/2026-04-12-tb-verdict.md` — TB gate_fail verdict (не production)
- `docs/reports/2026-04-12-quantile-status-decision.md` — production verdict для quantile-layer
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- `docs/superpowers/plans/2026-04-11-quantile-status-decision.md`
- `API/signal_research.py`
