# NY Session Filter for entry_path_v1_quantile — Skeleton Plan

> **Status:** Skeleton — pending dedicated /writing-plans pass
> **Shortlist rank:** 1 of 3 (STRONG)
> **Discovery source:** `docs/reports/2026-04-13-pf-uplift-discovery.md`

## Goal

Добавить фильтр по торговой сессии в production execution path `entry_path_v1_quantile`: исключить открытие позиций в NY-сессии (приблизительно 19:00–00:00 broker time), сохранив только Asia и Overlap входы.

Probe показал: N=34 (drop 29%), PF=20.28 (+12.1 над baseline 8.18), negative_year_slices=0.

## Non-goals

- Не переобучать модели.
- Не вводить MA/EMA или любые MA-derived фильтры.
- Не изменять quantile rule (lb_gt_m_q35) или baseline_threshold.
- Не подключать к MT4 до parity-check и dedicated gate.
- Не делать реализацию EA до отдельного implementation-плана.

## Read First

- `ML/reports/pf_uplift_discovery/baseline_numbers.json`
- `ML/reports/pf_uplift_discovery/probe_r__ny_session_exclusi.json`
- `ML/reports/pf_uplift_discovery/trade_enriched.csv`
- `ML/reports/pf_uplift_discovery/regime_crosstab.csv`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `MT/MQL4/Include/lib_ML_Signal.mqh` — точка входа сессионной логики в EA
- `API/export_entry_path_v1_quantile_signals.py` — экспортёр сигналов в MT4

## Expected Gate

Совместимый с n-boost gate (унифицированный стандарт проекта):
- N_trades ≥ 30
- PF > 2.0
- negative_year_slices = 0 (годы с N < 3 игнорируются)
- same_winner_ratio ≥ 0.8 (если multi-seed validation)

Дополнительно: проверить, что session=NY является robustly-tagged (no timezone/DST artifacts).

## Collision Notes

- Не пересекается с quantile filter (lb_gt_m_q35) — ортогональное измерение.
- Пересекается с vol_q4 exclusion (тоже STRONG): если реализовывать оба — composition-style план, а не два отдельных.
- Phase A spec (2026-03-27) не упоминает session filter.

## Tasks

TBD — to be filled in dedicated /writing-plans pass.

Ожидаемые шаги (не финальные):
1. Верифицировать определение broker time → UTC → session bucket (проверить DST для MT4 broker)
2. Ретроспективный gate-прогон на train/validation/test со строгим gate
3. Multi-seed robustness проверка (те же 5 seeds)
4. Python-side exporter: добавить session_hour фильтр в `export_entry_path_v1_quantile_signals.py`
5. MT4 parity-check через signal_tracer
6. Verdict и обновление CONTEXT_HANDOFF
