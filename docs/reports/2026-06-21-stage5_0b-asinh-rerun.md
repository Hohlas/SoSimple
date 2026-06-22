# Stage 5.0b Asinh Rerun

> **Дата**: 2026-06-21
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Выполнить отдельный Stage 5.0b rerun для Transformer с заранее зафиксированным `asinh`, обязательными проверками перед обучением и честным сравнением с baseline без объявления trading winner.
> **Related plan/spec**: `docs/superpowers/plans/2026-06-21-stage5_0b-asinh-rerun.md`

## Context

После проверки распределения признаков Stage 5.0a (`docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`) был нужен отдельный Stage 5.0b-прогон, где `asinh` фиксируется до обучения, holdout 2023-2026 используется только для раскрытия результата, а решение о возможном продолжении принимается только по `val_stop`.

## What Was Done

Добавлен отдельный CLI `--stage5-0b-asinh-rerun`, заморожены confirmatory и diagnostic profile sets, включён transform-aware training path с `transform_variant="asinh"`, отключён dynamic corridor `seq_len` для Stage 5.0b, а в JSON добавлены обязательные проверки, baseline-метрики и summary target-контрактов для sell/buy.

Запущен реальный single-seed rerun на CPU через:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed
```

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
- `ML/reports/stage5_0b_asinh_rerun.json`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- `CHANGELOG.md`

## Verification

- `./.venv/bin/python -m pytest tests/ -q` -> `777 passed, 29 warnings`
- `PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed` -> completed, JSON written to `ML/reports/stage5_0b_asinh_rerun.json`
- `PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed --target buy_stop_broken_H6_off05_flag --all-profiles-confirmatory --no-multiseed-gates` -> completed, JSON written to `ML/reports/stage5_0b_asinh_rerun_buy_stop_broken_H6_off05_flag.json`

## Results

### Setup

- Target: `sell_stop_broken_H6_off05_flag`
- Transform: `asinh`
- Scaler: train-only `StandardScaler`
- Dynamic corridor `seq_len`: disabled
- Holdout: 2023-2026, disclosure only
- Trading winner: not declared
- Seed: `42`; устойчивость по нескольким запускам не проверялась

### Decision Policy

Multi-seed candidate only if confirmatory profile passes predefined `val_stop` rules:

- `val_auc >= max(xgb_base_raw_plus_time + 0.01, xgb_time_only + 0.03)`
- `val_lift_30 <= min(xgb_base_raw_plus_time, xgb_time_only)`
- `normalized_distribution_audit.status != "ERROR"`
- profile role = confirmatory only

### Mandatory Checks

- OHLC verification status: `PASS`
- Label sanity status: `SANITY_ONLY`
- Label positive rate (holdout disclosure): `0.406450187762315`
- XGBoost `base_raw_plus_time` val AUC: `0.6631095529328142`
- XGBoost `base_raw_plus_time` val lift_30: `0.5538852868484367`
- XGBoost `time_only` val AUC: `0.6314223730333846`
- XGBoost `time_only` val lift_30: `0.6962245225748507`

### Confirmatory Candidates

| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 | multi_seed |
|---|---:|---:|---:|---:|---|
| `all100_relative_price_time` | 0.6718975762793974 | 0.5043759874653363 | 0.6373443593145742 | 0.646786754818467 | False |
| `nearest40_relative_price_time` | 0.6337113367167122 | 0.6467152231917502 | 0.5951951626996327 | 0.7627373215086124 | False |
| `corridor_5atr_relative_price_atr_full` | 0.6146827394791232 | 0.6683755416718566 | 0.6062987451659358 | 0.7120089485816739 | False |
| `corridor_10atr_relative_price_atr_full` | 0.6161995481306445 | 0.6312435671345312 | 0.6142567474636332 | 0.7029503105590061 | False |

### Diagnostic Controls

| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---|---:|---:|---:|---:|
| `all100_relative_price_no_time` | 0.61973109965454 | 0.649809554403194 | 0.6094142894127927 | 0.6975151277454056 |
| `nearest40_relative_price_no_time` | 0.563133986879711 | 0.8354694270898207 | 0.5497749834145078 | 0.8786878881987578 |
| `all100_absolute_price_atr_scaled_time_asinh` | 0.6672908253173768 | 0.5631682804827681 | 0.6447599957929483 | 0.6485984824230006 |
| `corridor_5atr_price_unit_atr_full` | 0.6215403752461905 | 0.6931301913634069 | 0.6104815253798482 | 0.6938916725363385 |
| `corridor_10atr_price_unit_atr_full` | 0.6122856212040118 | 0.6652812104604129 | 0.6132591907897931 | 0.7083854933726067 |

### Distribution Audit

Проверка распределения признаков после `asinh` и нормализации выполнена перед обучением. Для всех 9 sell-профилей статус `OK`, критических флагов `0`.

| Profile | role | audit_status | flags |
|---|---|---|---:|
| `all100_relative_price_time` | confirmatory | OK | 0 |
| `nearest40_relative_price_time` | confirmatory | OK | 0 |
| `corridor_5atr_relative_price_atr_full` | confirmatory | OK | 0 |
| `corridor_10atr_relative_price_atr_full` | confirmatory | OK | 0 |
| `all100_relative_price_no_time` | diagnostic_control | OK | 0 |
| `nearest40_relative_price_no_time` | diagnostic_control | OK | 0 |
| `all100_absolute_price_atr_scaled_time_asinh` | diagnostic_control | OK | 0 |
| `corridor_5atr_price_unit_atr_full` | diagnostic_control | OK | 0 |
| `corridor_10atr_price_unit_atr_full` | diagnostic_control | OK | 0 |

### Corridor Stats

Коридорные профили не меняли `seq_len` на лету в Stage 5.0b; ниже показано, сколько фракталов фактически попадало в коридор. Статус всех corridor-профилей: `OK`.

| Profile | train median/p80 | val_stop median/p80 | holdout median/p80 |
|---|---:|---:|---:|
| `corridor_5atr_relative_price_atr_full` | 42 / 55 | 40 / 50 | 38 / 51 |
| `corridor_10atr_relative_price_atr_full` | 65 / 77 | 61 / 70 | 62 / 73 |
| `corridor_5atr_price_unit_atr_full` | 42 / 55 | 40 / 50 | 38 / 51 |
| `corridor_10atr_price_unit_atr_full` | 65 / 77 | 61 / 70 | 62 / 73 |

### Target Contracts

Sell target `sell_stop_broken_H6_off05_flag`:

- train: `n_non_null=25672`, `null_rate=0.0`, `positive_rate=0.3885945777500779`
- val_stop: `n_non_null=2832`, `null_rate=0.0`, `positive_rate=0.3806497175141243`
- holdout: `n_non_null=4527`, `null_rate=0.0`, `positive_rate=0.406450187762315`

Buy candidate columns were discovered and summarized for disclosure. For all detected `buy_stop_broken_*_flag` columns in this rerun, every split had `n_non_null=0` and `null_rate=1.0`, so buy remained contract-only and was not trained.

### Additional Buy Target Check

Позднее выяснено, что `buy_stop_broken_*_flag` были пустыми не в исходных CSV, а после загрузки Stage 5. Причина: загрузчик безусловно фильтровал строки по `sell_stop_broken_H6_off05_flag`, поэтому в обучающем наборе оставались только строки, применимые к sell-цели. После исправления загрузки на фильтрацию по выбранной цели выполнен отдельный проверочный прогон для `buy_stop_broken_H6_off05_flag`.

Этот прогон не переопределяет исходное решение Stage 5.0b по sell-цели. Buy-прогон является диагностическим: пороги автоматического отбора были отключены, а все 9 профилей были рассмотрены как основные кандидаты только для сравнения. Это более мягкая политика, чем исходный sell-прогон с 4 заранее выбранными основными профилями и 5 проверочными профилями.

Фикс загрузки не изменил sell-результаты: при sell-цели новая фильтрация по выбранной цели совпадает со старой фильтрацией по `sell_stop_broken_H6_off05_flag`; число train-строк осталось `25672`.

Проверка распределения признаков для buy-прогона также дала `OK` и `0` критических флагов для всех 9 профилей.

Buy target `buy_stop_broken_H6_off05_flag`:

- train: `n_non_null=22745`, `null_rate=0.0`, `positive_rate=0.37014728511760825`
- val_stop: `n_non_null=2580`, `null_rate=0.0`, `positive_rate=0.374031007751938`
- holdout: `n_non_null=4125`, `null_rate=0.0`, `positive_rate=0.3575757575757576`
- OHLC verification: `PASS`, `50/50` matched

XGBoost comparison for buy:

| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---|---:|---:|---:|---:|
| `base_raw_plus_time` | 0.6894008566066187 | 0.538860103626943 | 0.6552051167252958 | 0.5787649178575832 |
| `no_time` | 0.6489221835448115 | 0.5872193436960276 | 0.629778317876559 | 0.6533713330501624 |
| `time_only` | 0.6422621472914227 | 0.5906735751295337 | 0.6233330348576911 | 0.6963265417974048 |

Transformer results for buy:

| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---|---:|---:|---:|---:|
| `all100_relative_price_time` | 0.6761776736874189 | 0.5112262521588946 | 0.6462247521586185 | 0.6217201266048258 |
| `all100_absolute_price_atr_scaled_time_asinh` | 0.6752395771507405 | 0.5423143350604491 | 0.6435071314358811 | 0.626241727525588 |
| `nearest40_relative_price_time` | 0.6290007860247999 | 0.6666666666666667 | 0.6094528941477454 | 0.7709329569899839 |
| `all100_relative_price_no_time` | 0.6216307608399236 | 0.6286701208981001 | 0.6153569555484489 | 0.6827617390351177 |
| `corridor_5atr_price_unit_atr_full` | 0.6187446061053272 | 0.6355785837651122 | 0.5975567636712504 | 0.7211953468615978 |
| `corridor_5atr_relative_price_atr_full` | 0.6172922247710101 | 0.6390328151986183 | 0.5983950111928367 | 0.7257169477823602 |
| `corridor_10atr_relative_price_atr_full` | 0.6153056673992204 | 0.6217616580310881 | 0.5946971538215542 | 0.7031089431785483 |
| `corridor_10atr_price_unit_atr_full` | 0.6137012143281092 | 0.614853195164076 | 0.5939629037416053 | 0.7144129454804543 |
| `nearest40_relative_price_no_time` | 0.5545889411123053 | 0.8462867012089811 | 0.5420832747041893 | 0.8930161818505679 |

Если применить к buy ту же AUC-логику, что и к sell, порог был бы `max(0.6894 + 0.01, 0.6423 + 0.03) = 0.6994`. Лучший buy Transformer дал `0.6762`, разрыв `0.0232`. Это заметно хуже sell-разрыва `0.0012`, поэтому buy-дополнение не усиливает вывод в пользу Transformer.

Buy и sell считаются на разных строках: sell train `25672`, buy train `22745`. Их AUC/lift нельзя напрямую сравнивать как одну и ту же задачу; корректнее сравнивать каждый Transformer с XGBoost на той же цели и тех же строках.

## Conclusions

Stage 5.0b stays `DIAGNOSTIC_ONLY`. Ни один confirmatory profile не прошёл multi-seed policy. Лучший confirmatory профиль `all100_relative_price_time` не прошёл AUC-порог: `0.6719` против требуемых `0.6731`. Разрыв `0.0012` мал и в single-seed режиме не должен трактоваться как устойчивый сигнал. Профиль прошёл lift gate (`0.5044 <= 0.5539`), но правила требуют одновременное выполнение всех условий.

Diagnostic control `all100_absolute_price_atr_scaled_time_asinh` выглядит близко к confirmatory лидеру по AUC, но это не winner и не основание менять решение Stage 5.0b. Это только отдельная гипотеза для нового плана.

Дополнительный buy-прогон подтвердил, что buy-цель пригодна после фильтрации по выбранной целевой колонке. По AUC лучший Transformer (`all100_relative_price_time`, `val_auc=0.6762`) уступил лучшему XGBoost (`base_raw_plus_time`, `val_auc=0.6894`). По `val_lift_30` Transformer лучше (`0.5112` против `0.5389`; меньше лучше), но общего превосходства Transformer над XGBoost нет.

Главная новая гипотеза: `all100_absolute_price_atr_scaled_time_asinh` повторно оказался рядом с лидером на двух целевых. Для sell: `0.6673` против лидера `0.6719`; для buy: `0.6752` против лидера `0.6762`. Это не победитель текущего Stage 5.0b, но наиболее обоснованный кандидат для нового заранее зафиксированного прогона.

## Limitations / Open Questions

- Holdout 2023-2026 приведён только для disclosure; он не использовался в выборе.
- Прогон один seed (`42`); multi-seed продолжение не открыто.
- Перенос в holdout слабее, чем в `val_stop`: у sell `lift_30` ухудшается с `0.5044` до `0.6468`, у buy с `0.5112` до `0.6217`. Это сигнал возможного сдвига режима между годами, а не основание менять решение Stage 5.0b.
- Первоначальный sell-прогон не обучал buy-цель из-за фильтрации по sell-таргету. Отдельный buy-прогон после исправления загрузки показал непустую buy-цель, но тоже не дал превосходства Transformer над XGBoost по AUC.

## Next Step

Multi-seed continuation для Stage 5.0b не открывать. Если нужно развивать ветку дальше, оформить отдельный план для `all100_absolute_price_atr_scaled_time_asinh` как заранее выбранного основного кандидата, не переопределяя задним числом frozen confirmatory policy Stage 5.0b.

## Related Materials

- `ML/reports/stage5_0b_asinh_rerun.json`
- `ML/reports/stage5_0b_asinh_rerun_buy_stop_broken_H6_off05_flag.json`
- `docs/ML/benchmark_stage5_transformer_breach.py.md`
- `docs/reports/2026-06-20-stage5_0a-feature-distribution-audit.md`
- `docs/superpowers/plans/2026-06-21-stage5_0b-asinh-rerun.md`
