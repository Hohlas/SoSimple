# pred_adv12 Cap Filter for entry_path_v1_quantile — Skeleton Plan

> **Status:** Skeleton — pending dedicated /writing-plans pass
> **Shortlist rank:** 3 of 3 (STRONG)
> **Discovery source:** `docs/reports/2026-04-13-pf-uplift-discovery.md`

## Goal

Добавить non-retraining фильтр над existing predictions: торговать quantile-отобранный сигнал только если `pred_adv_12_atr ≤ threshold`. Threshold определяется из quantile (Q75) на validation split. Probe (Q75=0.0313): N=37 (-23%), PF=12.75 (+4.57 над baseline 8.18), negative_year_slices=0.

Path-dependent confirmation: MAE low_adv=0.35ATR vs high_adv=1.38ATR (4x), MFE/MAE ratio 10x vs 1.2x — когда модель предсказывает большой adverse, OHLC траектория это подтверждает.

## Non-goals

- Не переобучать модели.
- Не изменять quantile rule или session filter.
- Не оптимизировать threshold на test (threshold фиксируется на validation).
- Не использовать pred_adv для exit logic — только для entry filter.
- Не вводить MA/EMA.

## Read First

- `ML/reports/pf_uplift_discovery/baseline_numbers.json`
- `ML/reports/pf_uplift_discovery/probe_f__pred_adv12___q75_.json`
- `ML/reports/pf_uplift_discovery/trade_enriched.csv` (pred_adv12, mae_atr)
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv`
- `API/export_entry_path_v1_quantile_signals.py`

## Expected Gate

Совместимый с n-boost gate:
- N_trades ≥ 30 (N=37, проходит)
- PF > 2.0
- negative_year_slices = 0
- Threshold зафиксирован на validation split Q75 pred_adv_12_atr (не на test)

## Collision Notes

- Не пересекается с quantile rule lb_gt_m_q35 (разные dimensions: lb использует q-interval, pred_adv — adverse excursion prediction).
- Не пересекается с fav_3_vs_12 composition (закрыт, и это другой feature: adv, не fav).
- Pred_adv_12 column уже существует в quantile predictions CSV — не требует ни переобучения, ни новых экспортов.
- Можно комбинировать с session filter или early timeout в будущем composition-плане.

## Tasks

TBD — to be filled in dedicated /writing-plans pass.

Ожидаемые шаги:
1. Зафиксировать threshold: Q75 pred_adv_12_atr на baseline_selected validation rows
2. Gate-прогон на frozen test с зафиксированным threshold
3. Multi-seed robustness: те же 5 seeds
4. Экспорт: добавить pred_adv_cap в `export_entry_path_v1_quantile_signals.py`
5. Убедиться, что pred_adv_12_atr доступен в quantile CSV и в production rule
6. MT4 parity-check
7. Verdict и документация
