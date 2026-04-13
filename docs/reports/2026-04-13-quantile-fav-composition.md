# Quantile × fav_3_vs_12 Composition Verdict

> **Date**: 2026-04-13
> **Status**: Completed — **CLOSED — gate fail**
> **Goal**: Проверить, усиливает ли фиксированный фильтр `fav_3_vs_12 <= 0.653` уже production-ready правило `entry_path_v1_quantile` (`lb_gt_m_q35`)
> **Related plan/spec**: `docs/superpowers/plans/2026-04-13-quantile-fav-composition.md`
> **Rule**: `ML/reports/entry_path_v1_quantile_selected_rule.json`

## Короткий итог

После пересборки правильного источника `pred_fav_3 / pred_fav_12` на тех же активных строках, что и `quantile`, composition больше не является пустым артефактом данных. Итог стал честным и содержательным:

- `quantile_only` на test: `N=48`, `PF=8.178675196069868`
- `composition` на test: `N=47`, `PF=7.860844837655267`
- composition почти не режет сделки (`47/48` survived), но получает один отрицательный годовой срез (`2023`, PF=`0.47526255177309695`)
- из-за этого общий gate не пройден: **`gate_fail`**

Значит проблема не в несовместимости источников, а в самой идее composition: дополнительный фильтр почти ничего не отбирает, но ухудшает yearly stability.

## Источники

- `docs/reports/2026-04-04-archetype-filter-bridge.md`
- `docs/reports/2026-04-12-quantile-status-decision.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/quantile_fav_composition/updn_active_source/{validation,test}_active_updn_predictions.csv`
- `ML/reports/quantile_fav_composition/{validation_metrics,test_metrics,intersection_diagnostic,n_boost_composition}.json`
- `ML/reports/quantile_fav_composition/yearly_breakdown_test.csv`

## Method

1. `quantile` side:
   - `seed_007` predictions from `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_{validation,test}_predictions.csv`
2. Baseline score side:
   - resolved exactly as production exporter does, from `baseline_rule_path` inside `ML/reports/entry_path_v1_quantile_selected_rule.json`
3. `fav_3_vs_12` side:
   - not from external research CSV anymore
   - rebuilt from `transformer_updn_best.pt` on the same active rows of `DATA/Nero_{validation,test}_labeled.csv`
   - exported into `ML/reports/quantile_fav_composition/updn_active_source/`
4. Alignment rule:
   - active row order in `quantile` and in labeled validation/test was verified to match one-to-one
   - therefore `pred_fav_3` / `pred_fav_12` were attached by active-row order, not by ambiguous many-to-many merge on `(time, signal)`
5. Threshold:
   - `fav_3_vs_12 <= 0.653` taken **as-is** from the 2026-04-04 report
   - no threshold tuning

## Verification

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_fav_composition.py -q
/home/hohla/git/SoSimple/.venv/bin/python -m ML.export_updn_active_predictions \
  --output-dir /home/hohla/git/SoSimple/.worktrees/quantile-fav-composition/ML/reports/quantile_fav_composition/updn_active_source
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_fav_composition \
  --rule-path /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_selected_rule.json \
  --seed-dir /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness/seed_007 \
  --updn-active-dir /home/hohla/git/SoSimple/.worktrees/quantile-fav-composition/ML/reports/quantile_fav_composition/updn_active_source \
  --output-dir /home/hohla/git/SoSimple/.worktrees/quantile-fav-composition/ML/reports/quantile_fav_composition
```

Result:
- tests `5/5` green
- `quantile_only` control numbers still match exactly

## Validation Results

| Mode | N | win_rate | PF | mean_pnl_atr |
|---|---:|---:|---:|---:|
| baseline | 50 | 0.7000 | 4.13304811852324 | 1.9807665944000001 |
| quantile_only | 32 | 0.8125 | 11.240091883688192 | 2.78801166625 |
| fav_only | 46 | 0.6956521739130435 | 4.441840272353088 | 2.0097994004347832 |
| composition | 28 | 0.8214285714285714 | 21.852917603463066 | 2.9510291435714286 |

## Test Results

| Mode | N | win_rate | PF | mean_pnl_atr |
|---|---:|---:|---:|---:|
| baseline | 72 | 0.7638888888888888 | 6.119613175138209 | 2.7351757769444447 |
| quantile_only | 48 | 0.8125 | 8.178675196069868 | 2.7264873945833337 |
| fav_only | 70 | 0.7571428571428571 | 5.760264955825677 | 2.6158550562857137 |
| composition | 47 | 0.8085106382978723 | 7.860844837655267 | 2.6612162540425532 |

Главное наблюдение: composition почти полностью совпадает с `quantile_only`, но чуть хуже по PF и по yearly stability.

## Year By Year

| year | mode | N | wins | losses | PF |
|---:|---|---:|---:|---:|---:|
| 2022 | baseline | 7 | 0 | 7 | 0.0 |
| 2022 | composition | 2 | 0 | 2 | 0.0 |
| 2022 | fav_only | 7 | 0 | 7 | 0.0 |
| 2022 | quantile_only | 2 | 0 | 2 | 0.0 |
| 2023 | baseline | 14 | 10 | 4 | 2.480711916766149 |
| 2023 | composition | 5 | 3 | 2 | 0.47526255177309695 |
| 2023 | fav_only | 12 | 8 | 4 | 1.6472203807789745 |
| 2023 | quantile_only | 6 | 4 | 2 | 1.3861029438118457 |
| 2024 | baseline | 18 | 13 | 5 | 9.079996341667135 |
| 2024 | composition | 16 | 11 | 5 | 7.28632420955386 |
| 2024 | fav_only | 18 | 13 | 5 | 9.079996341667135 |
| 2024 | quantile_only | 16 | 11 | 5 | 7.28632420955386 |
| 2025 | baseline | 28 | 28 | 0 | null |
| 2025 | composition | 24 | 24 | 0 | null |
| 2025 | fav_only | 28 | 28 | 0 | null |
| 2025 | quantile_only | 24 | 24 | 0 | null |
| 2026 | baseline | 5 | 4 | 1 | 24.40236817496082 |
| 2026 | fav_only | 5 | 4 | 1 | 24.40236817496082 |

По gate rule учитываются только годы с достаточным числом сделок. У composition появился один отрицательный годовой срез: **2023**, `N=5`, `PF=0.47526255177309695`.

## Intersection Diagnostic

Из `intersection_diagnostic.json`:

- `n_quantile = 48`
- `n_fav = 70`
- `n_intersection = 47`
- `intersection_over_quantile = 0.9791666666666666`
- `intersection_over_fav = 0.6714285714285714`
- `trades_lost_from_quantile = 1`
- `n_baseline_rows_with_fav_feature = 72`

Это важный вывод: после правильной пересборки данных composition перестал быть sparse-case. Наоборот, фильтр `fav_3_vs_12` почти не сокращает quantile universe. Он отрезает всего одну сделку из `48`, то есть практически не добавляет нового отбора.

## Verdict Rubric

- `PROMOTE-candidate`:
  1. `n_boost_composition.verdict == gate_pass`
  2. composition `N >= 70%` of quantile_only `N`
  3. composition `PF >= 1.15 * quantile_only PF`
  4. composition `negative_year_slices <= quantile_only negative_year_slices`
- `CLOSED — no uplift`:
  gate passes, but (2) or (3) fails
- `CLOSED — gate fail`:
  composition `gate_fail`
- `INCONCLUSIVE`:
  composition `gate_inconclusive`

Observed gate:

```json
{
  "verdict": "gate_fail",
  "n_trades": 47,
  "pf": 7.860844837655267,
  "negative_year_slices": 1,
  "reasons": [
    "negative_year_slices=1 > 0"
  ]
}
```

## Verdict

**CLOSED — gate fail.**

Теперь это честный отрицательный verdict. Composition не только не улучшает `quantile`, но и ломает one-negative-year guard, который `quantile_only` проходил.

## Practical Meaning

Простой смысл результата:

- идея composition проверена честно
- дополнительный фильтр почти ничего не отбирает
- при этом он ухудшает устойчивость по годам
- значит усложнение не оправдано

Иными словами: `entry_path_v1_quantile` уже делает почти весь полезный отбор сам, а `fav_3_vs_12` поверх него добавляет шум, а не качество.

## Next Step

1. Закрыть направление composition.
2. Не возвращаться к нему без нового сильного основания.
3. Сместить исследовательский фокус обратно на:
   - entry logic
   - SL/TP
   - regime analysis

## Related Materials

- `ML/benchmark_quantile_fav_composition.py`
- `ML/export_updn_active_predictions.py`
- `tests/test_benchmark_quantile_fav_composition.py`
- `ML/reports/quantile_fav_composition/updn_active_source/validation_active_updn_predictions.csv`
- `ML/reports/quantile_fav_composition/updn_active_source/test_active_updn_predictions.csv`
