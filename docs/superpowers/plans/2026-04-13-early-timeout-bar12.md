# Early Timeout hold_bars=12 for entry_path_v1_quantile — Skeleton Plan

> **Status:** Skeleton — pending dedicated /writing-plans pass
> **Shortlist rank:** 2 of 3 (STRONG)
> **Discovery source:** `docs/reports/2026-04-13-pf-uplift-discovery.md`

## Goal

Сократить `ML_HoldBars` с 24 до 12 для quantile execution mode. Probe показал: PF=13.73 (+5.55 над baseline 8.18), N=48 (без изменений), negative_year_slices=0. Path-dependent check: 0 из 37 wins-at-bar-12 перевернулись в losses к bar-24; 2 losses-at-bar-12 восстановились — но это не оправдывает удержание 12 лишних баров.

## Non-goals

- Не переобучать модели.
- Не изменять quantile rule или session filter.
- Не вводить adaptive hold (разные hold для разных сигналов) без отдельного плана.
- Не подключать к production MT4 до dedicated gate и parity-check.

## Read First

- `ML/reports/pf_uplift_discovery/baseline_numbers.json`
- `ML/reports/pf_uplift_discovery/probe_s__early_timeout_hold.json`
- `ML/reports/pf_uplift_discovery/trade_enriched.csv` (mfe_atr, mae_atr по сделкам)
- `MT/MQL4/Include/lib_ML_Signal.mqh` — параметр `ML_HoldBars`
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md` — Phase A.2.4 reference

## Expected Gate

Совместимый с n-boost gate:
- N_trades ≥ 30 (N=48, легко)
- PF > 2.0
- negative_year_slices = 0

Ключевая дополнительная проверка: сравнить `true_ret_12_dir_atr` (proxy для hold=12) с `true_ret_24_dir_atr` на validation split — gate должен быть пройден на validation, затем frozen на test.

## Collision Notes

- Не пересекается с quantile filter (ортогонально).
- Не пересекается с session filter или pred_adv cap.
- Упоминался в Phase A.2.4 как "ранний MARKET-выход при MFE < 0.5ATR за N баров" — это другой вариант (conditional exit). Фиксированный hold=12 проще и имеет probe-данные.
- Реализация в MT4 минимальная: изменить `ML_HoldBars=12` в тестере для quantile signals.

## Tasks

TBD — to be filled in dedicated /writing-plans pass.

Ожидаемые шаги:
1. Проверить true_ret_12_dir_atr на validation set (gate на validation перед test)
2. Multi-seed gate (те же 5 seeds) с hold=12
3. Yearly breakdown для hold=12 на test
4. MT4 parity-check: изменить `ML_HoldBars=12` в тестере, прогнать на quantile signals
5. Сравнение PF(12) vs PF(24) по signal_tracer
6. Verdict и обновление production rule документации
