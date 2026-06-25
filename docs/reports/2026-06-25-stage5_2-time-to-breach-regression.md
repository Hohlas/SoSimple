# Stage 5.2 Time-To-Breach Regression

> **Дата**: 2026-06-25
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, можно ли заменить бинарную цель `stop broken / not broken` на регрессию времени до пробоя фрактального стопа.
> **Related plan/spec**: `docs/superpowers/specs/2026-06-25-stage5_2-time-to-breach-regression-design.md`, `docs/superpowers/plans/2026-06-25-stage5_2-time-to-breach-regression.md`

## Context

Stage 5.1 и Stage 5.1b показали, что в структурных фрактальных полях есть диагностический след, особенно в поле `back`, но ветка `H6_off05 stop broken` не была переоткрыта как кандидат. Stage 5.2 проверял другую постановку: не просто "будет пробой или нет", а "через сколько баров будет пробой".

Первый Stage 5.2 прогон был признан невалидным: `reg:pseudohubererror` схлопывал raw-прогнозы в константу вне диапазона, а clipping превращал их в `1.0`. После bugfix objective заменён на `reg:squarederror`, добавлен `pred_summary`, oracle-gate перестал принимать бесконечный binary-oracle как валидное сравнение. Этот отчёт описывает повторный полный прогон после исправления.

Уровень этапа: поисковый. Результат не может стать торговым кандидатом без нового независимого проверочного цикла.

## What Was Done

Добавлена разметка `bars_to_breach`: первое касание уровня стопа в пределах горизонта или значение `H + 1`, если пробоя не было. Для основной проверки использованы цели:

- `sell_bars_to_breach_H6_off05`
- `buy_bars_to_breach_H6_off05`

Повторный прогон Stage 5.2:

- objective: `reg:squarederror`
- 7 профилей: `time_only`, `clock_shift`, `clock_shift_back`, `clock_shift_impulse`, `clock_shift_back_impulse`, `structure_full`, `structure_full_without_back`
- 2 цели: sell и buy
- 3 seed: `42`, `77`, `123`
- всего `42` model-run
- запуск: `--stage5-2-workers 8 --stage5-2-xgb-threads 4`

Также проверены:

- constant baseline: всегда предсказывает censored value `7`
- oracle-preflight через first-touch simulator
- censoring gate
- model gate по Spearman, MAE, AUC, годовой согласованности и приростам над baseline
- structured JSON: `ML/reports/stage5_2_time_to_breach_regression.json`

## Multiple Testing Context

Search budget: `7 профилей × 2 цели × 3 seed = 42` XGBoost-регрессии плюс constant baseline и oracle-preflight.

Коррекция множественного тестирования не применялась. Это допустимо только потому, что этап остаётся `DIAGNOSTIC_ONLY`: результаты нельзя использовать как подтверждение кандидата или как основание для торгового правила.

Выбор winner-а по `2023-2025` запрещён и не выполнялся. `2023-2025` используются только как diagnostic holdout disclosure.

## Changed Files

Код и тесты:

- `processing/label_signals.py` — `BR_TIME_TO_BREACH_COLUMNS` и расчёт первого бара пробоя.
- `processing/label_main.py` — heartbeat для долгой разметки.
- `ML/baseline/benchmark_stage5_transformer_breach.py` — Stage 5.2 pipeline, `reg:squarederror`, `pred_summary`, gate, oracle-preflight, CLI.
- `tests/processing/test_fractal_stop_breach_labels.py` — тесты контракта новой разметки.
- `tests/test_stage5_transformer_breach.py` — тесты профилей, метрик, objective, oracle-gate, runner и CLI.
- `ML/reports/stage5_2_time_to_breach_regression.json` — structured artifact повторного полного прогона.

## Verification

Полный тестовый набор после bugfix:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Результат:

```text
857 passed, 29 warnings in 162.05s
```

Команда rerun:

```bash
./.venv/bin/python -u ML/baseline/benchmark_stage5_transformer_breach.py \
  --stage5-2-time-to-breach-regression \
  --stage5-2-workers 8 \
  --stage5-2-xgb-threads 4
```

Результат:

```text
Stage 5.2: регрессия времени до пробоя завершена
done_runs: 42
total_runs: 42
elapsed_sec: 2983.555
status: DIAGNOSTIC_ONLY
```

Дополнительная проверка JSON:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/stage5_2_time_to_breach_regression.json")
d = json.loads(p.read_text())
assert d["status"] == "DIAGNOSTIC_ONLY"
assert d["progress"]["done_runs"] == d["progress"]["total_runs"] == 42
assert d["progress"]["workers"] == 8
assert d["progress"]["xgb_threads"] == 4
for target in d["targets"]:
    gate = d["gate_results"][target]
    assert gate["censoring_gate"]["pass"] is True
    assert gate["oracle_gate"]["pass"] is False
    assert gate["oracle_gate"]["reason"] == "invalid_oracle_binary_comparison"
    assert gate["model_gate"]["pass"] is False
    best = d["summary"][target]["best_profile"]
    assert best["val_stop"]["spearman_r"] > 0.30
    assert best["val_stop"]["auc_true_ge_4"] >= 0.70
print("stage5_2_rerun_json_consistency_ok")
PY
```

Результат:

```text
stage5_2_rerun_json_consistency_ok
```

## Results

Итоговый статус JSON: `DIAGNOSTIC_ONLY`.

Прогон завершён полностью: `42 / 42`.

### Gate Summary

| Target | Censoring gate | Oracle gate | Model gate | Overall |
|---|---:|---:|---:|---|
| `sell_bars_to_breach_H6_off05` | PASS | FAIL | FAIL | `ORACLE_FAILED` |
| `buy_bars_to_breach_H6_off05` | PASS | FAIL | FAIL | `ORACLE_FAILED` |

Oracle gate падает не потому, что `oracle_time_pf` плохой, а потому что comparison против binary-oracle невалиден: `oracle_binary_pf = inf`, `pf_delta_vs_binary = None`.

Model gate почти проходит по ранжированию, но не проходит из-за MAE-improvement над constant baseline:

- `spearman_ge_0_30`: PASS на обеих целях
- `auc_ge_0_70`: PASS на обеих целях
- `yearly_not_single_year`: PASS на обеих целях
- `mae_le_3`: PASS на обеих целях
- `spearman_delta_*`: PASS на обеих целях
- `mae_improvement_constant_ge_10pct`: FAIL на обеих целях

### Censoring

Доля непробитых уровней в train ниже блокирующего порога `0.70`:

| Target | train censoring | val censoring | holdout censoring |
|---|---:|---:|---:|
| sell | `0.6114` | `0.6194` | `0.5923` |
| buy | `0.6299` | `0.6260` | `0.6441` |

### Oracle Preflight

| Target | oracle_time_pf | oracle_binary_pf | pf_delta_vs_binary | trades | trades/year | yearly PF |
|---|---:|---:|---:|---:|---:|---|
| sell | `1.6520` | `inf` | `None` | `2206` | `1103.0` | 2021 `1.6352`, 2022 `1.6682` |
| buy | `1.7244` | `inf` | `None` | `1997` | `998.5` | 2021 `1.6734`, 2022 `1.7723` |

Критическая оговорка: binary-oracle входит на строках, где `breach_flag == 0`. При таком выборе стоп по определению не пробивается внутри горизонта `H=6`, поэтому SL-исходов нет, а PF становится бесконечным. Следовательно, oracle-preflight показывает только высокий диагностический потолок при знании будущего. Он не доказывает, что регрессия времени до пробоя лучше бинарного знания `breach / no breach`.

Дополнительная оговорка: `998-1103` сделок в год — нереалистично высокая частота. Это не торговый потолок, а diagnostic ceiling.

### Model Results

Повторный прогон устранил аномалию одинаковых метрик. Профили различаются, `pred_summary.std` ненулевой, количество уникальных округлённых прогнозов высокое.

| Target | Profile | val Spearman | val MAE | val AUC `true>=4` | pred std | pred uniq | holdout Spearman | holdout MAE | holdout AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sell | `time_only` | `0.2253` | `1.7444` | `0.6325` | `0.5113` | `115` | `0.1781` | `1.7963` | `0.6251` |
| sell | `clock_shift` | `0.1986` | `1.7928` | `0.6231` | `0.6105` | `2648` | `0.1866` | `1.7938` | `0.6236` |
| sell | `clock_shift_back` | `0.3072` | `1.6942` | `0.7005` | `0.6463` | `2662` | `0.2942` | `1.7139` | `0.6784` |
| sell | `clock_shift_impulse` | `0.2547` | `1.7505` | `0.6666` | `0.6039` | `2651` | `0.2340` | `1.7601` | `0.6434` |
| sell | `clock_shift_back_impulse` | `0.3041` | `1.7076` | `0.6974` | `0.6281` | `2649` | `0.2919` | `1.7243` | `0.6780` |
| sell | `structure_full` | `0.3000` | `1.7348` | `0.6928` | `0.6155` | `2646` | `0.2831` | `1.7487` | `0.6732` |
| sell | `structure_full_without_back` | `0.2706` | `1.7480` | `0.6752` | `0.5839` | `2646` | `0.2426` | `1.7518` | `0.6467` |
| buy | `time_only` | `0.2450` | `1.7160` | `0.6560` | `0.5641` | `118` | `0.1933` | `1.7550` | `0.6269` |
| buy | `clock_shift` | `0.2169` | `1.7417` | `0.6377` | `0.6305` | `2418` | `0.1883` | `1.7576` | `0.6193` |
| buy | `clock_shift_back` | `0.3162` | `1.6681` | `0.6991` | `0.7514` | `2446` | `0.2634` | `1.6896` | `0.6624` |
| buy | `clock_shift_impulse` | `0.2752` | `1.6879` | `0.6723` | `0.6473` | `2439` | `0.2258` | `1.7266` | `0.6347` |
| buy | `clock_shift_back_impulse` | `0.3280` | `1.6434` | `0.7071` | `0.7290` | `2450` | `0.2660` | `1.6920` | `0.6613` |
| buy | `structure_full` | `0.3262` | `1.6632` | `0.7055` | `0.7016` | `2450` | `0.2669` | `1.7104` | `0.6598` |
| buy | `structure_full_without_back` | `0.2982` | `1.6668` | `0.6884` | `0.6302` | `2433` | `0.2409` | `1.7171` | `0.6435` |

Best profiles by validation Spearman:

| Target | Best profile | val Spearman | val AUC | val MAE | holdout Spearman | holdout AUC |
|---|---|---:|---:|---:|---:|---:|
| sell | `clock_shift_back` | `0.3072` | `0.7005` | `1.6942` | `0.2942` | `0.6784` |
| buy | `clock_shift_back_impulse` | `0.3280` | `0.7071` | `1.6434` | `0.2660` | `0.6613` |

Constant baseline остаётся лучше по MAE:

| Target | constant MAE | best model MAE | model MAE improvement |
|---|---:|---:|---:|
| sell | `1.4439` | `1.6942` | `-17.3%` |
| buy | `1.4329` | `1.6434` | `-14.7%` |

Это ключевой компромисс Stage 5.2: модель даёт полезное ранжирование времени до пробоя, но как точечная регрессия проигрывает простой константе `7` по MAE из-за сильной цензуры цели.

## Conclusions

Stage 5.2 после bugfix показывает содержательный сигнал, но не переоткрывает `H6_off05` как кандидата.

Главный положительный результат: `back` снова является главным компактным структурным полем. На sell лучший профиль `clock_shift_back`; на buy лучший `clock_shift_back_impulse`, а `structure_full` почти рядом. Это согласуется со Stage 5.1/5.1b: `back` связан с устойчивостью фрактального уровня.

Главный отрицательный результат: обычная регрессия одного числа `bars_to_breach` плохо согласуется с censored target. Constant baseline `7` выигрывает по MAE, потому что большая доля строк реально не пробивается за `H=6`. Поэтому model gate не проходит, несмотря на Spearman/AUC.

Oracle-preflight не может быть использован как подтверждение time-to-breach advantage: binary-oracle имеет бесконечный PF по построению, а частота сделок oracle-time нереалистично высокая.

Итог: идея времени до пробоя стала перспективной как ранжирование или дискретная/цензурированная постановка, но не как текущая обычная регрессия с MAE-gate.

## Limitations / Open Questions

- Verdict остаётся `DIAGNOSTIC_ONLY`; кандидата нет.
- Oracle comparison невалиден: `oracle_binary_pf = inf`, `pf_delta_vs_binary = None`.
- MAE-gate провален на обеих целях: модель хуже constant baseline `7`.
- `bars_to_breach = 7` означает "не пробит за 6 баров", а не фактический пробой на 7-м баре. Обычная регрессия плохо учитывает такую цензуру.
- `2023-2025` не является независимым frozen test, потому что эта ветка уже многократно использовала эти годы для диагностики.
- Scale contract: Stage 5.2 использует уже нормализованные `DATA/*_labeled.csv`; отдельного scaler внутри Stage 5.2 нет. Фрактальные поля наследуют rowwise normalization из preprocessing.
- Новый JSON содержит `pred_summary`, но не содержит sampled `y_pred`/`y_true`. Для глубокой калибровки это стоит добавить отдельно.
- Up/Dn поля намеренно не включались в стартовые профили Stage 5.2 по итогам Stage 5.1b.

## Validation Split Disclosure

Split соответствует Stage 5.x fixed protocol:

- `train_core`: до `2020`
- `val_stop`: `2021-2022`
- `diagnostic_holdout`: `2023-2025`
- `low_n_disclosure`: `2026`

`val_stop` использовался для model gate и выбора лучшего профиля. `diagnostic_holdout` раскрыт только для диагностики и не использовался для выбора параметров, winner-а или статуса кандидата. Поэтому результат не является frozen-candidate validation.

## Next Step

Не объявлять Stage 5.2 кандидатом.

Допустимые следующие шаги:

- Проверить time-to-breach как дискретную задачу: `fast / medium / no breach` вместо обычной регрессии.
- Проверить несколько бинарных целей `breach_after_k` / `survives_at_least_k`, потому что Spearman/AUC показывают ранжирование, а MAE ломается на цензуре.
- Делать следующий follow-up только на узких профилях: `clock_shift_back`, `clock_shift_back_impulse`, `structure_full`, `structure_full_without_back`.
- Добавить sampled `y_pred`/`y_true` в JSON для калибровки и bucket-анализа.
- Исправить oracle-preflight design: binary-oracle comparison в текущем виде неинформативен.

Запрещено делать дальше:

- Объявлять Stage 5.2 кандидатом.
- Использовать oracle-time PF как торговое подтверждение.
- Использовать `2023-2025` как новое независимое подтверждение.
- Запускать новый широкий перебор по `H6_off05` на тех же годах.

## Related Materials

- `ML/reports/stage5_2_time_to_breach_regression.json`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `processing/label_signals.py`
- `tests/test_stage5_transformer_breach.py`
- `tests/processing/test_fractal_stop_breach_labels.py`
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md`
