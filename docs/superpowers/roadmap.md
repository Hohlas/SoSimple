# Post-Bridge Roadmap

## Контекст

Точка остановки после `Archetype × Filter Bridge`:
- `fav_3_vs_12 <= 0.653` — текущий лучший фильтр по связи с winning archetype
- `ratio_3_vs_12 > 4.751` — полезен только как benchmark механики pullback
- следующий этап должен идти уже по новой дисциплине: подбор на `validation`, финальная проверка на `test`
- composition check `entry_path_v1_quantile × fav_3_vs_12` завершён 2026-04-13 с verdict `CLOSED — gate fail`: после честной пересборки источника composition дал `47` test trades vs `48` у quantile, но получил negative year slice в 2023 и therefore не проходит gate
- quantile forward validation scaffold завершён 2026-04-13: benchmark готов, но verdict пока `watch / no_forward_data`, потому что в репозитории нет strictly-forward prediction CSV после production decision

Подробный текущий handoff: [CONTEXT_HANDOFF.md](../CONTEXT_HANDOFF.md)

## Главный порядок выполнения

1. **Validation-first protocol**
   [docs/superpowers/plans/2026-04-07-validation-first-research.md](plans/2026-04-07-validation-first-research.md)
   Сначала фиксируем новую дисциплину проверки, переносим поиск правил на `validation` и повторно ставим на рельсы текущий bridge baseline.

2. **ML exit and position management**
   [docs/superpowers/plans/2026-04-07-ml-exit-and-position-management.md](plans/2026-04-07-ml-exit-and-position-management.md)
   После этого усиливаем текущий `regression_updn` трек без переобучения: выходим умнее, а не только входим.

3. **Triple Barrier hardening**
   [docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md](plans/2026-04-07-triple-barrier-hardening.md)
   Доводим уже начатый parallel-трек до честного финального вердикта.

4. **Outcome-aligned retraining**
   [docs/superpowers/plans/2026-04-07-outcome-aligned-retraining.md](plans/2026-04-07-outcome-aligned-retraining.md)
   Только после этого запускаем более широкий новый трек обучения под торговый исход.

## Как это связано с текущим handoff

Этот roadmap не отменяет `CONTEXT_HANDOFF.md`, а разворачивает его решение в исполнимую последовательность:

- пункт handoff про `fav_3_vs_12 + market` становится стартовым baseline внутри плана `validation-first`
- пункт handoff про улучшение фильтра через replicated spread features тоже входит в первый план
- пункт handoff про `ratio_3_vs_12 + pullback` сохраняется только как benchmark, не как основной путь

## Как это связано со старым Triple Barrier планом

Исходный план:
[docs/superpowers/plans/2026-03-22-triple-barrier.md](plans/2026-03-22-triple-barrier.md)

Статус:
- базовая реализация из плана 2026-03-22 уже сделана
- текущая задача — не повторить запуск сначала, а усилить и проверить трек
- для продолжения использовать новый план hardening, а старый документ держать как исходный implementation record

## Где держать что

- `CONTEXT_HANDOFF.md` — текущая точка остановки, ближайший следующий шаг, риски
- `docs/superpowers/roadmap.md` — общий порядок работ между несколькими планами
- `docs/superpowers/plans/*.md` — детальные исполнимые планы по отдельным направлениям
- `docs/DATA_FLOW.md` — не место для текущего roadmap; этот документ должен оставаться стабильной картой пайплайна, а не рабочим списком исследований

## Composition Status

- `entry_path_v1_quantile × fav_3_vs_12`:
  closed
  verdict report: [2026-04-13-quantile-fav-composition.md](../reports/2026-04-13-quantile-fav-composition.md)

## Standalone Status

- `fav_3_vs_12` as standalone system:
  closed
  verdict report: [2026-04-13-fav-3-vs-12-standalone.md](../reports/2026-04-13-fav-3-vs-12-standalone.md)
  reason: no stable threshold found; best validation PF stayed at `0.1379`, so the feature does not work as an independent second system

## Quantile Forward Status

- `entry_path_v1_quantile` forward validation:
  scaffold ready
  verdict report: [2026-04-13-quantile-forward-validation.md](../reports/2026-04-13-quantile-forward-validation.md)
  current verdict: `watch / no_forward_data`
  next action: collect or generate a strictly newer forward prediction CSV, then run `ML.benchmark_quantile_forward_validation`

## PF Uplift Beyond ML Layer

Discovery: [2026-04-13-pf-uplift-discovery.md](../reports/2026-04-13-pf-uplift-discovery.md)
Status: **SHORTLISTED (3)** — two implementation checks completed; `early_timeout_hold_bars=12` and `NY session exclusion` rejected by canonical validation gate

| Rank | Plan | pf_delta | N_drop | Status |
|------|------|:--------:|:------:|--------|
| 1 | [NY session filter](plans/2026-04-13-ny-session-filter.md) | +12.097 | 29% | Rejected — validation gate fail (`N=24 < 30`) |
| 2 | [Early timeout bar=12](plans/2026-04-13-early-timeout-bar12.md) | +5.552 | 0% | Rejected — validation gate fail (`N=27`, lower mean PnL vs hold24) |
| 3 | [pred_adv12 ≤ Q75 cap](plans/2026-04-13-pred-adv-cap.md) | +4.567 | 23% | Skeleton — TBD |

Candidate #4 (not shortlisted due to limit): vol_q4 exclusion (+2.42 PF, N_drop=12.5%) — first candidate for composition with any of the 3.

Recommended execution order now: pred_adv cap. `Early timeout` and `NY session filter` stay as completed negative verdicts and should not be productized further without new evidence.
