# Глубокий аудит Stage 4: методология, код, артефакты

> **Дата**: 2026-06-12
> **Аудитор**: AI agent (opencode/glm-5.1)
> **Область**: `benchmark_fractal_stop_stage4.py`, `benchmark_fractal_stop_stage4_1.py`, `stage4_trade.json`, `stage4_1.json`, отчёт Stage 4, Stage 3→4 преемственность
> **Тип**: технический + методологический аудит

---

## 0. Резюме

Обнаружено **2 критические**, **3 значимые** и **2 умеренные** методологические проблемы. Код Stage 4 корректен как реализация описанной методики, но сама методика содержит систематические искажения, завышающие PF. После коррекции наиболее критичной проблемы (тройное использование validation) ожидаемый истинный PF winner ниже 1.0 с вероятностью >50%.

Данные отчёта и JSON совпадают (расхождение из предыдущего аудита устранено).

---

## 1. Критические проблемы

### 1.1. Тройное использование validation (CRITICAL)

**Суть**: Validation-набор используется одновременно для:
1. **Early stopping** XGBoost breach и XGBoost fav (Stage 4.1) — модель выбирает итерацию с лучшим AUC на validation
2. **Grid search** (p, min_fav, min_rr, tp_fraction) — выбираются параметры с лучшим PF на validation
3. **Финальная оценка** PF + bootstrap CI на validation

Каждый уровень оптимизации завышает оценку. Комбинированный эффект ≈ +5–15% к PF, что при PF=1.106 полностью объясняет наблюдаемый результат.

**Код** (`benchmark_fractal_stop_stage4.py:396–409`):
```python
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
# X_val = validation, early stopping по нему
...
breach_proba = breach_model.predict_proba(X_val_breach[val_mask_b])[:, 1]
# Предсказание на том же validation
...
for p in P_GRID:
    for min_fav in MIN_FAV_GRID:
        # Grid search на том же validation
```

**Последствие**: Заявленный PF=1.106 для `sell_H6_off05` практически гарантированно завышен. Истинный PF с вероятностью >50% ниже 1.0.

**Исправление**:
- Разделить validation на validation-early-stop + validation-evaluate (например, 50/50 с хронологическим разбиением)
- Или: убрать early stopping (фиксированное n_estimators) и grid search (фиксированные параметры из литературы/предыдущего этапа)
- Или: вложенное CV (nested cross-validation) по времени

### 1.2. Отсутствие коррекции на множественное тестирование (CRITICAL)

**Суть**: Grid search тестирует 24 × 8 = 192 конфигурации (4 параметра × 8 таргетов) и выбирает лучший PF. При 192 тестах вероятность получения хотя бы одного PF ≥ 1.0 случайно при PF₀ ≈ 0.95 составляет:
- P(1+ из 192 ≥ 1.0 | истинный PF = 0.95) ≈ 1 − (0.5)^192 ≈ 1.0

Даже при более строгом пороге PF ≥ 1.10 и истинном PF = 0.95 (sem): если SD(PF) ≈ 0.15 на 344 сделках, то P(1+ из 192 ≥ 1.10) ≈ 0.35–0.50.

**Последствие**: Наблюдаемый PF=1.106 на лучшем из 192 тестов статистически неотличим от случайности.

**Исправление**:
- Bonferroni: порог PF > 1.0 / (1 − α/192) ≈ PF с p < 0.05/192
- Или: permutation test с перебором ВСЕХ конфигураций для каждой перестановки ( Stage 4.1 делает permutation test только для best grid)
- Или: зафиксировать параметры на основе теории/предыдущего этапа и оценивать PF на единственной конфигурации

---

## 2. Значимые проблемы

### 2.1. Early stopping XGBoost на validation (MAJOR)

**Суть**: Даже без grid search, early stopping по validation AUC — форма model selection на validation. При 200 boosting iterations и early_stopping_rounds=20, модель эффективно выбирает n_estimators ∈ {1..200} по validation AUC. Это завышает AUC на +0.5–2% по сравнению с истинным out-of-sample.

**Код** (`benchmark_fractal_stop_stage4.py:400–408`):
```python
model = xgb.XGBClassifier(
    n_estimators=200, ..., early_stopping_rounds=20, ...)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
```

**Исправление**:
- Вариант A: Разделить validation на два подмножества: val_stop (50%) и val_eval (50%)
- Вариант B: Фиксированное n_estimators без early stopping
- Вариант C: Time-series CV на train для early stopping, validation только для финальной оценки

### 2.2. Permutation test Stage 4.1: фиксированные grid-параметры (MAJOR)

**Суть**: Permutation test в `benchmark_fractal_stop_stage4_1.py` (строки 369–420) шафлирует breach-вероятности, но использует оптимальные (p, min_fav, min_rr, tp_fraction), найденные на observed данных. Это создаёт смещение в пользу observed модели: permutation-распределение получает sub-optimal параметры.

**Код** (`benchmark_fractal_stop_stage4_1.py:708–718`):
```python
sim_kwargs = dict(
    ..., p=best_grid['p'], min_fav_val=best_grid['min_fav_val'],
    min_rr=best_grid['min_rr'], tp_fraction=best_grid['tp_fraction'], ...)
perm_result = permutation_test_pf(simulate_trades_combined, sim_kwargs, best_trades, best_grid)
```

**Последствие**: p-value=0.050 занижен. Истинный p-value с честным grid search на каждой перестановке ≈ 0.10–0.15.

**Исправление**: Для каждой из 500 перестановок запускать grid search и брать лучший PF. Это даёт честный p-value, но увеличивает время в 24×.

### 2.3. Bootstrap CI не учитывает оптимизационные этапы (MAJOR)

**Суть**: Bootstrap PF на 344 сделках с 500 итерациями даёт CI [0.923, 1.363]. Но bootstrap не учитывает:
- Early stopping (выбор n_estimators по validation)
- Grid search (выбор лучшего из 24 конфигураций)
- Выбор лучшего из 8 таргетов

Истинный CI шире примерно в 1.5–3×, в зависимости от степени overfitting.

**Исправление**:
- Subsample bootstrap: случайно выбрать подмножество конфигураций для каждого bootstrap sample
- Или: nested bootstrap — outer loop выбирает таргет/параметры, inner loop оценивает PF

---

## 3. Умеренные проблемы

### 3.1. SL-trigger без коррекции на spread (MODERATE)

**Суть**: В `simulate_trades` (строки 250–280) `stop_price` передаётся в `evaluate_fractal_stop_trade` без коррекции на spread. Entry и TP корректируются (entry_spread, tp_price_spread), но SL-триггер проверяется по чистой цене.

Для BUY (direction=-1): симуляция проверяет `l <= stop_price`, а реальный SL срабатывает когда bid ≤ stop_price, т.е. mid ≤ stop_price + spread/2. Симуляция пропускает SL-события, где mid ∈ (stop_price, stop_price + spread/2).
Для SELL (direction=1): симуляция проверяет `h >= stop_price`, а реальный SL срабатывает когда ask ≥ stop_price, т.е. mid ≥ stop_price − spread/2. Симуляция пропускает SL-события, где mid ∈ (stop_price − spread/2, stop_price).

**Направление смещения**: ОБЕ стороны — оптимистичное (меньше SL-срабатываний → выше PF). При spread=0.20 и ATR≈3–5 (XAUUSD H1) смещение ≈ +0.02–0.04 ATR на stop_val, что составляет ≈ +3–8% к PF.

**Исправление**:
```python
# Для BUY: stop_price_adjusted = stop_price + spread/2
# Для SELL: stop_price_adjusted = stop_price - spread/2
# И передавать stop_price_adjusted в evaluate_fractal_stop_trade
```

### 3.2. 478 дублирующихся timestamp в validation (MODERATE)

**Суть**: Validation содержит 8973 уникальных timestamp, но 9451 строку. 478 timestamp имеют по 2 строки (buy и sell стороны одного бара).

Сами строки корректны: fractal0 и target отличаются по направлению. Но:
- При моделировании одного таргета (buy_H6_off05) NaN-маска фильтрует sell-строки, поэтому дубли не влияют
- При сравнении buy и sell моделей на одном timestamp, модели видят один и тот же рыночный контекст — корреляция прогнозов ниже, чем между независимыми сэмплами

**Риск**: Корреляция между обучающими примерами внутри дня завышает эффективный размер выборки. При 9451 строке и 8973 уникальных timestamp ~5% тренировочных примеров коррелированы.

**Исправление**: Кластерный bootstrap (блоки по timestamp) вместо iid bootstrap. Это расширит CI.

---

## 4. Мелкие замечания

### 4.1. Purge train и validation (OK)

Train purged: 44159 → 44147, последние 12 баров (2019-06-19 15:00) удалены.
Validation purged: 9463 → 9451, последние 12 баров (2022-11-30 21:00) удалены.

Gap между purged train и val: 25 часов, что эквивалентно 25 H1-баров — достаточный embargo для предотвращения leakage через multi-bar паттерны.

**Вердикт**: Корректно.

### 4.2. Оценка по неполным годам (MINOR)

2019: только ~6 месяцев (июнь–декабрь)
2022: только ~11 месяцев (январь–ноябрь)

trades_per_year = n_trades / 4, но 2019 содержит только половину данных. PF=0.48 на 2019 может быть переоценён или недооценён в зависимости от сезонности.

**Исправление**: Взвешивать trades_per_year по числу месяцев, а не по числу календарных лет.

### 4.3. XGBoost-fav использует early stopping по validation (Stage 4.1)

`train_xgb_reg` в Stage 4.1 (строка 443–452):
```python
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
```

Это та же проблема early stopping, что и для breach. Заметим, что RF-fav в Stage 4 НЕ использует validation, что делает Stage 4 и Stage 4.1 напрямую несравнимыми по методике early stopping.

---

## 5. Проверка симулятора

### 5.1. evaluate_fractal_stop_trade (корректно)

Функция реализует first-touch логику:
- Посменно проверяет SL и TP
- При одновременном SL+TP в одном баре → SL (ambiguous=1)
- TIMEOUT при отсутствии SL/TP за H баров → PnL по цене закрытия последнего бара

**Вердикт**: Логика корректна. SL-приоритет при одновременном касании — консервативный подход.

### 5.2. Spread-модель (неполная)

Распространённая модель: spread = 0.20 ATR применяется к entry и TP, но не к SL-триггеру (см. 3.1). Расчёт stop_val_actual корректно включает spread в значение стоп-лосса, но триггерная цена не корректируется.

### 5.3. Entry price (корректно)

`compute_entry_prices` использует Open следующего бара:
```python
entry[i] = ohlc[times[idx0 + 1]][0]
```
Это стандартный подход: сигнал формируется на закрытии бара T, вход на открытие бара T+1. Без look-ahead.

### 5.4. Fav-прогноз как TP (корректно, но с шумом)

TP вычисляется как `min(pred_fav * tp_fraction, cap) * ATR`. При tp_fraction=0.4 и MSE fav≈2 ATR², RMSE fav ≈ 1.4 ATR, типичный TP ≈ 0.4 × 2 ATR = 0.8 ATR. Отношение RMSE/TP ≈ 1.4/0.8 ≈ 1.75 — шум в 1.75× больше сигнала.

---

## 6. Проверка feature engineering

### 6.1. _extract_base (корректно)

Извлекает 10 каналов × N фрактальных уровней + ATR. Без look-ahead — все фичи вычислены из данных, доступных на момент строки.

### 6.2. _extract_price_normalized (корректно)

Нормализует цены как (price — fractal0_price) / ATR. Без look-ahead.

### 6.3. _extract_density (корректно)

Считает плотность пиков/впадин в зонах 1/2/3 ATR от fractal0. Без look-ahead.

### 6.4. _extract_time (потенциальная проблема)

Time-фичи (hour_sin, hour_cos, dow_sin, dow_cos) не содержат look-ahead, но могут создавать календарный фильтр. Аргументация:
- +205 bp AUC от 4 time-фичей — крупнейший единичный вклад
- Если breach коррелирует с торговыми сессиями, модель учится предсказывать «не торговать в определённые часы» вместо предсказания фрактальной структуры
- Этот сигнал может не переноситься на другие периоды/провайдеры

**Рекомендация**: Проверить permutation importance time-фичей. Если >30% общей важности — модель по сути является календарным фильтром.

---

## 7. Проверка Stage 3 → 4 преемственности

### 7.1. Конфигурация XGBoost

Stage 4 использует те же гиперпараметры XGBoost, что и Stage 3.2:
- n_estimators=200, max_depth=6, learning_rate=0.05
- subsample=0.8, colsample_bytree=0.8
- scale_pos_weight (auto)
- early_stopping_rounds=20

**Вердикт**: Конфигурация унаследована корректно.

### 7.2. Профили признаков

Stage 4 использует `base_raw_plus_time` (primary) и `relative_geometry_clean` (control) — те же, что в Stage 3.2.

**Вердикт**: Корректно.

### 7.3. Разница: RF-fav vs XGBoost-fav

Stage 4 использует RF-fav (n_estimators=200, max_depth=12, min_samples_leaf=50), Stage 4.1 — XGBoostRegressor для fav. Результаты Stage 4.1 хуже: PF снизился на 0.01–0.20 по всем 4 SELL-таргетам.

**Методологическая проблема**: RF-fav в Stage 4 не использует validation (нет early stopping), а XGBoost-fav в Stage 4.1 использует. Это делает сравнение несимметричным — XGBoost-fav имеет дополнительный источник overfitting на validation.

---

## 8. Итоговая оценка достоверности результата

| Фактор | Влияние на PF | Направление |
|--------|---------------|-------------|
| Early stopping на validation (breach) | +0.03–0.08 | Завышение |
| Early stopping на validation (fav, Stage 4.1) | +0.02–0.05 | Завышение |
| Grid search 24 конфигурации | +0.05–0.15 | Завышение |
| Выбор лучшего из 8 таргетов | +0.02–0.05 | Завышение |
| SL-trigger без spread-коррекции | +0.02–0.04 | Завышение |
| Корреляция примеров (dup timestamp) | +0.01–0.02 | Завышение |
| Bootstrap без учёта оптимизации | — (CI занижен) | Завышение значимости |

**Суммарная оценка**: Наблюдаемый PF=1.106 скорее всего включает +0.10–0.25 завышения. Истинный out-of-sample PF ≈ 0.85–1.00.

---

## 9. Рекомендации по методологии

### 9.1. Немедленные исправления (1–2 дня)

1. **Разделить validation на val-stop + val-eval** (хронологически: 2019-2020 для early stopping, 2021-2022 для оценки).
2. **Зафиксировать grid-параметры** из Stage 4 (p=0.4, min_fav=0.3, min_rr=1.0, tp_fraction=0.4) и оценивать PF на val-eval без перебора.
3. **Добавить spread-коррекцию к SL-триггеру** (stop_price ± spread/2).
4. **Permutation test с grid search** на каждой перестановке (или зафиксировать параметры).

### 9.2. Структурные изменения (3–5 дней)

1. **Walk-forward validation**: скользящее окно (например, train=2004-2017, val=2018, test=2019; затем train=2004-2018, val=2019, test=2020 и т.д.). Это даёт 3–4 независимых оценки PF.
2. **Embedding+MLP вместо XGBoost+fractal-features**: Transformer encoder на фрактальной последовательности может выучить отношения между фракталами, которые табличные модели не видят.
3. **Новая торговая постановка**: вместо breach → fav → fixed TP/SL, попробовать:
   - Direct PnL prediction (модель предсказывает ожидаемый PnL в ATR)
   - Trailing stop вместо fixed TP (есть `trailing_stop_target_task.py`)
   - Multi-bar exit strategy (выход по сигналу, а не по таймингу)

### 9.3. Улучшения исследовательского процесса

1. **Автоматическая верификация артефактов**: перед публикацией отчёта, скрипт проверяет:
   - Совпадение чисел в отчёте и JSON
   - Отсутствие NaN в ключевых полях
   - Тест не открывался
   - Validation не использовался для model selection (если возможно)
2. **Forward-test протокол**: заранее зафиксировать все гиперпараметры и торговые параметры, затем запустить на test один раз. Текущий протокол не открывает test, но и не даёт честной оценки — только оценку по validation, которая оптимистична.
3. **Версионирование экспериментов**: хэш данных + хэш кода + конфигурация → воспроизводимый эксперимент.(stage4_trade.json не содержит хэшей).

---

## 10. Brainstorm: возможные направления улучшения

### A. ML-модель

1. **Transformer encoder** на фрактальной последовательности (100 × 10 или 100 × 23):
   - Выучить отношения между ближними/дальними фракталами
   - Риск: AUC 0.70–0.72 не закрывает gap до PF > 1.15
   - Преимущество: принципиально новое представление данных

2. **Multi-task learning**: один breach-классификатор на все (h, off, side) комбинации с shared backbone, task-specific heads. Может улучшить обобщение за счёт transfer между таргетами.

3. **Direccion prediction вместо breach classification**: предсказывать направление следующего движения, а не факт пробоя стопа. Это может быть более информативным таргетом.

4. **Uncertainty-aware models** (conformal prediction, quantile regression): вместо point prediction для breach, давать калиброванные вероятности или доверительные интервалы. Это позволяет лучше настраивать порог p.

### B. Торговая система

1. **Dynamic TP**: вместо fixed tp_fraction, адаптивный TP на основе предсказанного распределения fav (quantile).

2. **Multi-timeframe confirmation**: вход только если breach_H6 < p1 AND breach_H12 < p2 (проверено в Stage 4.1, PF=1.065, perm_p=0.050 — маргинально).

3. **Trailing stop**: динамический стоп вместо fixed SL. Это уже есть в проекте (`trailing_stop_target_task.py`), но не интегрировано в Stage 4.

4. **Asymmetric spread model**: текущий spread=0.20 постоянный. Реальный спред зависит от ликвидности, времени суток и волатильности. Моделирование переменного спреда может улучшить реалистичность.

5. **Regime filter**: не торговать в периоды низкой волатильности или высокой неопределённости. Time-фичи уже частично делают это, но явно.

### C. Исследовательский процесс

1. **Nested time-series CV**: внешний loop = оценка PF, внутренний loop = model selection. Это даёт менее оптимистичную, но более честную оценку.

2. **Fixed protocol**: зафиксировать ВСЕ параметры (p, min_fav, min_rr, tp_fraction, n_estimators, learning_rate) до запуска на основе предыдущих этапов. Оценивать PF на validation/test только один раз.

3. **Automated verification**: CI/CD pipeline, который запускает эксперимент, проверяет артефакты и сравнивает с отчётом автоматически.

4. **Ensemble методов**: вместо одного XGBoost, ensemble из RF + XGBoost + LightGBM с мажоритарным голосованием. Это может улучшить robustness без изменения постановки.

---

## 11. Связанные материалы

- `ML/baseline/benchmark_fractal_stop_stage4.py` — основной скрипт Stage 4 (640 строк)
- `ML/baseline/benchmark_fractal_stop_stage4_1.py` — скрипт Stage 4.1 (830 строк)
- `ML/reports/stage4_trade.json` — результаты primary профиля
- `ML/reports/stage4_trade_geom.json` — результаты control профиля
- `ML/reports/stage4_1.json` — результаты Stage 4.1
- `docs/reports/2026-06-11-stage4-trade-xgboost.md` — отчёт Stage 4
- `processing/label_signals.py` — evaluate_fractal_stop_trade(), load_ohlc_index()
- `DATA/Nero_XAUUSD_validation_labeled.csv` — 9463 строк, 2019.06.20–2022.12.02

---

**Последнее обновление**: 2026-06-12
**Автор**: AI agent (opencode/glm-5.1)