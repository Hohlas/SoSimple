# Direct Direction Chain Audit

> **Date**: 2026-05-18
> **Status**: Completed
> **Goal**: Независимо проверить слабый результат direct-direction ветки, найти корневые причины и определить следующий план без подбора по test.
> **Related plan/spec**: `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`
> **Related commit**: pending

## Context

Этап `2026-05-15-direct-direction-improvement` дал общий frozen test PF `1.226` и sequential PF `1.537`, но результат неудовлетворителен для production: SELL PF на frozen test равен `0.618`, есть отрицательные годы `2022` и `2023`, а итог не проходит новый критерий пользователя `PF > 2.0`.

Аудит выполнялся как read-only исследование цепочки:

- raw/export contract `Nero.csv`;
- сортировка, labeling, rowwise normalization, split;
- построение fractal-level признаков и target-ов;
- выбор модели, winner selection, validation/test discipline;
- прошлые решения проекта: entry_path, quantile, live-safe audit, candidate-source audit, Triple Barrier.

## What Was Done

Прочитаны обязательные источники:

- `AGENTS.md`;
- `CONTEXT_HANDOFF.md`;
- `docs/DATA_FLOW.md`;
- `CHANGELOG.md` первые 300 строк;
- `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`;
- `docs/reports/2026-05-15-direct-direction-improvement.md`;
- `wiki/index.md`;
- `knowledge-rag` по direct-direction, live-safe, candidate-source и entry_path.

Дополнительно проверены:

- `ML/reports/entry_path_v1_direct_direction_improvement/*.md`;
- `ML/reports/entry_path_v1_binary_direction/summary.json`;
- `ML/reports/entry_path_v1_binary_direction/frozen_test.json`;
- `ML/reports/entry_path_v1_binary_direction/validation_grid.csv`;
- `ML/reports/entry_path_v1_binary_direction/frozen_test_grid.csv`;
- `processing/normalize.py`;
- `ML/fractal_level_feature_builder.py`;
- `ML/benchmark_entry_path_binary_direction.py`;
- `ML/benchmark_entry_path_score_direction.py`;
- wiki-страницы execution-треков.

## Changed Files

Добавлены audit artifacts:

- `ML/reports/direct_direction_chain_audit/minimal_repro_checks.json`;
- `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md`;
- `docs/audit/2026-05-18-codex-direct-direction-chain-rebuild.md`.

Код не менялся.

## Verification

Минимальные воспроизводимые проверки сохранены в:

`ML/reports/direct_direction_chain_audit/minimal_repro_checks.json`

Ключевые проверки:

1. `summary.json` E1 выбирает HGB one-sided winner, а frozen test запущен для RF.
2. Frozen SELL убыточен почти по всем годам уже использованного test artifact.
3. Изменение только top-level `up_*/dn_*` меняет нормализованные `fractal1.Up/Dn`.

## Results

### 1. Главная доказанная ошибка: target-dependent normalization

`processing/normalize.py` нормализует фрактальные `Up/Dn` в общем пуле с top-level target columns `up_3..dn_48`. Минимальная проверка показала:

```text
top_level_only_changed=True
fractal1_equal=False
changed_fields=up_12,dn_12,up_24,dn_24,up_48,dn_48
```

Следствие: даже если top-level targets не подаются в модель напрямую, они могут влиять на масштаб фрактальных `Up/Dn` признаков. Для direct-direction моделей, построенных из уже нормализованных `DATA/Nero_*_labeled.csv`, это делает feature provenance небезопасным.

### 2. Неверные единицы расстояния в fractal-level features

`ML/fractal_level_feature_builder.py` считает:

```text
(fractal.price - fractal0.price) / ATR
```

Но в split CSV `price` уже rowwise min-max normalized, а `ATR` остаётся в сырой шкале. Это ломает физический смысл `raw_distance_atr`, nearest-k и zone features. Особенно это объясняет слабость `zones`: зоны строятся на искажённой геометрии.

### 3. A/C targets названы ATR, но используют normalized up/dn

`ML/entry_path_direct_direction_targets.py` строит `buy_fav_*_atr` и `sell_fav_*_atr` из top-level `up/dn` split CSV. Эти значения уже нормализованы, а не выражены в ATR. Target D по OHLC менее затронут, но вся A/C часть target grid не может считаться корректной без пересчёта из raw или OHLC.

### 4. Выбор winner не воспроизводится автоматически

`ML/reports/entry_path_v1_binary_direction/summary.json` содержит winner:

```text
D_hgb_buy0.30_sell0.60_m0.05_standalone
one_sided_candidate=True
buy_sell_balance=0.0896
```

Frozen test запущен для:

```text
D_rf_buy0.40_sell0.60_m0.10
```

Код `pick_validation_winner()` не исключает `one_sided_candidate`, не требует `negative_years == 0` и сортирует по `validation_pf` раньше `validation_sequential_pf`, хотя план требовал выбрать winner после gates. Это не доказывает, что RF frozen PF неверен, но доказывает, что selection layer не является механически воспроизводимым.

### 5. SELL weakness реальна, но её нельзя лечить test-порогами

Frozen RF:

| Side | PF | Trades |
|---|---:|---:|
| BUY | 1.904 | 1202 |
| SELL | 0.618 | 843 |

SELL на frozen artifact убыточен почти по всем годам. Но использовать test для подбора SELL-фильтра нельзя. Любая SELL repair гипотеза должна заново проходить validation-only selection и один финальный frozen test.

### 6. E5 score-direction conclusion частично недоказан

`benchmark_entry_path_score_direction.py` выбирает строки по BUY confidence, а затем иногда назначает SELL. Это асимметричная логика. Поэтому вывод “SELL исчезает при высоких thresholds” может быть артефактом правила отбора, а не свойством данных.

## Conclusions

Текущий результат слабый не потому, что “порог плохо подобран”. Цепочка содержит более глубокие проблемы:

1. feature source смешивает current-row фракталы с target-dependent normalization;
2. геометрия уровня считается в неверных единицах;
3. часть target families использует normalized values как ATR values;
4. winner selection не соответствует формальным gates;
5. SELL провал подтверждён, но не должен чиниться по test.

Общий вывод: текущую direct-direction ветку нужно не тюнить, а пересобрать от raw/current-row feature source.

## Limitations / Open Questions

- Аудит не запускал новые validation-matrix эксперименты.
- Test split не использовался для подбора новых гипотез, порогов или моделей.
- Для полного proof нужны raw-vs-labeled parity checks на реальных строках и новый validation-only benchmark.
- Wiki ingest для отчёта `2026-05-15-direct-direction-improvement.md` и этого отчёта ещё нужно выполнить после принятия направления работ.

## Next Step

Исполнить план:

`docs/audit/2026-05-18-codex-direct-direction-chain-rebuild.md`

Первый gate: доказать и исправить feature provenance. До этого запрещено запускать новые model sweeps как основание для выбора production-кандидата.

## Related Materials

- `docs/reports/2026-05-15-direct-direction-improvement.md`
- `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md`
- `ML/reports/entry_path_v1_binary_direction/frozen_test.json`
- `ML/reports/direct_direction_chain_audit/minimal_repro_checks.json`
- `wiki/research/execution-tracks-live-safe-audit.md`
- `wiki/research/execution-tracks-reconciliation-plus-audit.md`
