# Regression Up/Dn Ratio Audit

> **Дата**: 2026-07-01
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить построчно, как предсказанное отношение `up_h/dn_h` совпадает с реальным отношением от цены фрактала, и где оно теряет торговый смысл при входе на следующем `open`.
> **Related plan/spec**: внеплановый EDA после обнаружения ошибки шкалы в торговой проверке

## Context

`Regression Up/Dn target foundation` показал сильную предсказуемость `up_h/dn_h`, но затем была найдена ошибка шкалы: `TP/SL` строились из нормализованных `pred_up_h/pred_dn_h`. После этого остался отдельный методический вопрос: модель может хорошо предсказывать движение от цены фрактала, а торговый симулятор проверяет уже другой объект — движение от следующего `open` после строки сигнала.

Этот этап не выбирает торгового кандидата и не подбирает прибыльное правило. Уровень этапа: **диагностический EDA**.

## What Was Done

Добавлен скрипт [`ML/baseline/analyze_regression_updn_ratio_audit.py`](../../ML/baseline/analyze_regression_updn_ratio_audit.py), который:

- повторяет фактический контракт `structure_full` / `xgboost_depth3`;
- обучает модели на `train_core` (`<= 2020`);
- оценивает только `val_stop` (`2021-2022`);
- денормализует реальные и предсказанные `up/dn` через `DATA/Nero_XAUUSD_*_updn_params.npy`;
- сохраняет построчную таблицу сравнения:
  - реальное `up/dn` от цены фрактала;
  - предсказанное `up/dn`;
  - `actual_log_ratio`;
  - `pred_log_ratio`;
  - движение от следующего `open` по OHLC;
  - расстояние между `entry_open` и ценой `fractal0`.

Важная техническая находка: быстрый сборщик признаков сверяется с существующим runner-ом на малой выборке. При этой сверке выяснилось, что `structure_full` в старом пути фактически даёт нулевое значение для `shift`, хотя контракт декларирует `shift`. Ratio audit воспроизводит именно фактическое поведение старого runner-а, чтобы числа были сопоставимы.

## Changed Files

- `ML/baseline/analyze_regression_updn_ratio_audit.py`
- `ML/reports/regression_updn_ratio_audit.json`
- `ML/reports/regression_updn_ratio_audit_predictions.csv`
- `ML/reports/regression_updn_ratio_audit_structure_full_features.npz`
- `docs/reports/2026-07-01-regression-updn-ratio-audit.md`

## Verification

Команды:

```bash
./.venv/bin/python -m py_compile ML/baseline/analyze_regression_updn_ratio_audit.py
./.venv/bin/python ML/baseline/analyze_regression_updn_ratio_audit.py --force-features
./.venv/bin/python ML/baseline/analyze_regression_updn_ratio_audit.py
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python statistics/data_contract_smoke_check.py \
  --train DATA/Nero_XAUUSD_train_labeled.csv \
  --val DATA/Nero_XAUUSD_validation_labeled.csv \
  --test DATA/Nero_XAUUSD_test_labeled.csv
```

Наблюдения:

- полный прогон с построением признаков завершён за `100.104` сек.;
- повторный прогон с кешем признаков завершён за `81.179` сек.;
- `feature_meta.status = PASS`;
- `max_abs_diff_vs_reference = 0.0` на контрольной выборке;
- итоговая таблица содержит `45 846` строк: `5094 rows × 3 horizons × 3 seeds`;
- CSV и JSON согласованы по числу строк.
- полный набор тестов: `1012 passed, 30 warnings`;
- `statistics/data_contract_smoke_check.py` снова падает на старом ожидании `target_buy_H6_val`; это общий data-contract долг текущих XAUUSD CSV, а не ошибка нового ratio audit.

## Results

### Main Ratio Quality

Медианы по 3 seed на `val_stop`:

| Horizon | Direction agreement vs real fractal Up/Dn | `pred_log_ratio` vs `actual_log_ratio` Spearman | Edge Spearman | Up MAE price | Dn MAE price |
|---:|---:|---:|---:|---:|---:|
| H3 | `0.8950` | `0.7881` | `0.8191` | `2.102` | `2.138` |
| H6 | `0.8106` | `0.7212` | `0.6940` | `3.514` | `3.522` |
| H12 | `0.7291` | `0.6264` | `0.5624` | `5.438` | `5.468` |

Вывод: отношение `up/dn` действительно предсказывается. Самая сильная точка — H3.

### Predicted Ratio Buckets

Корзины по предсказанному отношению `up/dn`, H3:

| Bucket | Median predicted log-ratio | Median actual log-ratio | Direction agreement | Actual `up > dn` |
|---:|---:|---:|---:|---:|
| 1 | `-1.871` | `-22.803` | `0.944` | `0.056` |
| 2 | `-1.294` | `-22.110` | `0.875` | `0.125` |
| 3 | `-0.671` | `-0.336` | `0.796` | `0.441` |
| 4 | `1.539` | `22.032` | `0.900` | `0.900` |
| 5 | `2.399` | `22.777` | `0.958` | `0.958` |

Это сильный результат именно для движения **от цены фрактала**. Крайние корзины почти однозначно отделяют `up > dn` от `dn > up`.

### Extreme Signal Check

Если брать только самые сильные 10% по `abs(pred_log_ratio)`:

| Horizon | Threshold `abs(pred_log_ratio)` | Rows per seed | Agreement vs real fractal Up/Dn | Agreement vs next-open move |
|---:|---:|---:|---:|---:|
| H3 | `2.477` | `510` | `0.961` | `0.507` |
| H6 | `1.779` | `510` | `0.942` | `0.502` |
| H12 | `1.347` | `510` | `0.922` | `0.526` |

Практическая интерпретация:

- для фрактальной цены сигнал очень силён;
- для входа на следующем `open` этот же сигнал почти случайный.

### Entry Mismatch

Связь предсказанного отношения с движением от следующего `open`:

| Horizon | Spearman `pred_log_ratio` vs next-open log-ratio | Direction agreement vs next-open move |
|---:|---:|---:|
| H3 | `-0.011` | `0.493` |
| H6 | `-0.017` | `0.491` |
| H12 | `0.001` | `0.497` |

Даже если оставить только 10% строк с самым близким `entry_open` к цене `fractal0`, связь не восстанавливается:

| Horizon | `abs(entry_open - fractal0_price)` threshold | Rows per seed | Direction agreement vs next-open move | Spearman vs next-open move |
|---:|---:|---:|---:|---:|
| H3 | `1.14` | `511` | `0.477` | `0.029` |
| H6 | `1.14` | `511` | `0.483` | `0.034` |
| H12 | `1.14` | `511` | `0.526` | `0.039` |

Значит, простая идея "войти ближе к фрактальной цене" сама по себе ещё не восстанавливает edge для следующего `open`.

## Conclusions

1. `Regression Up/Dn` не был ложным сигналом на уровне цели. Модель сильно ранжирует `up_h/dn_h` и отношение `up_h/dn_h` от цены фрактала.

2. Старую торговую проверку нельзя использовать как доказательство слабости ratio-сигнала. При этом ratio audit всё равно показывает смену объекта проверки: target измеряет реакцию цены от `fractal0_price`, а симулятор торговал от следующего `open`.

3. Следующий `open` почти полностью разрушает связь между `pred_log_ratio` и будущим движением от точки входа. Для H3 Spearman около `-0.011`, direction agreement около `0.493`.

4. Крайние ratio-сигналы выглядят пригодными как фильтр **зоны/уровня**, но не как немедленная рыночная сделка на следующем баре.

5. Старый `structure_full` имеет дополнительное ограничение: `shift` был заявлен в контракте, но фактически не попал как ненулевой признак через использованный Stage 5 builder. Это не отменяет текущий ratio-вывод, но требует отдельного исправления или disclosure в следующем clean-cycle.

## Limitations / Open Questions

- Это EDA на `val_stop`, не торговый backtest.
- PF, спред и Stop/Profit здесь не проверялись.
- `diagnostic_holdout` и 2026 не использовались для выбора правил.
- Движение от следующего `open` измерено без торговых расходов и без ограничений исполнения.
- Не проверены limit-entry, pullback-entry, retest-entry и вход по касанию фрактальной цены.
- Не проверено, какая часть силы `up_h/dn_h` объясняется уже случившимся движением между ценой фрактала и возможной ценой входа.

## Next Step

Разрешённый следующий шаг — не новый широкий перебор модели, а узкий проверочный план для правил, которые сохраняют смысл фрактальной цены:

1. **Запрещённое правило:** не использовать `pred_up - pred_dn` или `pred_up/pred_dn` как market-entry на следующем `open`. Этот анализ показывает, что связь с next-open move почти нулевая.

2. **Обязательный контроль перед торговым правилом:** измерить "уже случившееся движение".
   - Для `dir=-1` отдельно проверить, не становится ли `up_h > dn_h` лёгкой задачей только потому, что после формирования фрактала цена уже прошла часть пути вверх.
   - Для `dir=1` сделать симметричную проверку вниз.
   - Сравнить `actual_up/actual_dn` от `fractal0_price` с остаточным ходом от возможной цены входа.

3. **Кандидат на проверку A:** `level-retest entry`.
   - BUY/SELL не открывается сразу.
   - Сначала требуется возврат цены к зоне `fractal0_price`.
   - Direction берётся из `pred_log_ratio`.
   - Торговый горизонт начинается от фактического касания/ретеста, а не от строки сигнала.

3. **Кандидат на проверку B:** `fractal-price anchored oracle/preflight`.
   - До ML-торговли проверить потолок механики: если вход считать от `fractal0_price`, даёт ли экстремальный `pred_log_ratio` достаточный raw edge без спреда и затем со спредом.

4. **Кандидат на проверку C:** threshold rule по отношению, не по разности.
   - H3 primary: сильная зона начинается примерно с `abs(pred_log_ratio) >= 2.48`.
   - В обычном отношении это примерно `pred_up/pred_dn >= 11.9` или `<= 0.084`.
   - Этот порог нельзя сразу торговать; его нужно проверять только в entry-механике, привязанной к фрактальной цене.

Что не делать дальше:

- не запускать новый широкий перебор XGBoost/Transformer/профилей;
- не оптимизировать Stop/Profit вокруг next-open market-entry;
- не объявлять ratio-сигнал торговым edge без отдельной проверки entry-механики.

## Related Materials

- [Structured JSON](../../ML/reports/regression_updn_ratio_audit.json)
- [Prediction CSV](../../ML/reports/regression_updn_ratio_audit_predictions.csv)
- [Feature cache](../../ML/reports/regression_updn_ratio_audit_structure_full_features.npz)
- [Audit script](../../ML/baseline/analyze_regression_updn_ratio_audit.py)
- [Regression Up/Dn target foundation](2026-06-30-regression-updn-target-foundation.md)
- Старая торговая проверка удалена как недействительная из-за ошибки шкалы.
