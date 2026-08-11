# Брейншторм новых направлений для SoSimple
**Дата:** 2026-08-10
**Источник контекста:** docs/audit/retrospective.md (полное чтение)
**Порог успеха:** PF >= 1.3 на OOS с bootstrap CI (нижняя граница > 1.0)

---

## Методология

Двухфазный брейншторм:
1. **Расхождение** — максимум идей без самоцензуры (18 идей).
2. **Схождение** — отбор через накопленные ограничения из ретроспективы.

Каждая идея содержит: суть, какой тупик обходит, дешёвый эксперимент для фальсификации, риск переупаковки закрытого направления.

---

## ФАЗА 1: РАСХОЖДЕНИЕ — 18 идей

### Идея 1. Amplitude Tail Trading

**Суть:** Модель предсказывает не направление, а распределение амплитуды следующего движения. Торговля — только когда P(amplitude > cost_threshold) > 0.75. Вход — в сторону предсказанного направления, но только при «крупном» движении.

**Какой тупик обходит:** already-moved (amplitude устойчивее direction: Spearman 0.34->0.44 vs 0.02 для direction), low R² (таргетим хвост распределения, а не среднее).

**Дешёвый эксперимент:** Обучить quantile regression (XGBoost) на live-safe признаках, таргет — |ret_next_open|. Отфильтровать сделки где predicted P75 > медиана. Метрика: PF подвыборки. Убивает: PF < 1.0 на подвыборке.

**Риск переупаковки:** Ретроспектива рекомендует amplitude-based, но конкретной системы не строила. Не переупаковка.

---

### Идея 2. Regime-Gated Rules

**Суть:** Не ML для direction, а ML для классификации текущего режима (тренд/флэт/шок). Внутри каждого режима — простые фиксированные правила. ML отвечает на вопрос «когда», а не «куда».

**Какой тупик обходит:** regime drift (делает его центральным объектом), time-only dominance (правила внутри режима могут быть не calendar-driven).

**Дешёвый эксперимент:** Change-point detection (Bocconi/CUSUM) на волатильности -> 2-3 режима. Простые правила (momentum/mean-reversion) внутри каждого. Убивает: regime detection не устойчив на OOS.

**Риск переупаковки:** Walk-forward (секция 2.8) — это неявная версия. Отличие: явная модель режима, не периодическое переобучение.

---

### Идея 3. Time-Effect Decomposition

**Суть:** Time-only dominance (85.9% ML PF от calendar) — это не шум, а сигнал с неизвестным механизмом. Декомпозировать: session liquidity, rollover, news-schedule, market-maker behavior. Понять механизм -> использовать его осознанно.

**Какой тупик обходит:** time-only dominance (превращает проблему в источник альфы).

**Дешёвый эксперимент:** Decompose time-feature importance: hour, weekday, month, session. Проверить стабильность каждого компонента на rolling windows. Убивает: компоненты нестабильны (исчезают на 2023+).

**Риск переупаковки:** Fixed11 был time_only, но не декомпозировал механизм. Не переупаковка, если найдётся устойчивый механизм.

---

### Идея 4. Limit-Order Entry/Exit Optimization

**Суть:** Расширить limit-order BUY (PF=1.53, spread 0.20) до полной системы: limit entry + limit TP + time-based stop. Оптимизация исполнения, а не предсказания.

**Какой тупик обходит:** execution contract (использует готовую MT5 infra), low R² (не нужна точность направления, нужна точность исполнения).

**Дешёвый эксперимент:** Backtest limit-order variants (TP/SL ratios) на live-safe signals. Убивает: PF < 1.0 при spread > 0.30.

**Риск переупаковки:** Расширение секции 2.7, не переупаковка — добавляет exit-оптимизацию.

---

### Идея 5. Cross-Instrument Lead-Lag

**Суть:** XAGUSD, DXY, US10Y движутся раньше XAUUSD. Использовать завершённые бары кросс-инструментов как признаки.

**Какой тупик обходит:** already-moved (сигнал от другого инструмента — не already-moved для XAUUSD), low R² (дополнительный источник информации).

**Дешёвый эксперимент:** Cross-correlation XAGUSD->XAUUSD на lag 1-5 баров. Проверить стабильность на rolling OOS. Убивает: корреляция нестабильна после 2022.

**Риск переупаковки:** Секция 2.3 cross-instrument показала «selective transfer». Но тот тест был на ML-сигналах, не на raw lead-lag признаках. Частичный риск.

---

### Идея 6. Ensemble Agreement Meta-Filter

**Суть:** Обучить 5-7 разнородных моделей (XGBoost, RF, Transformer, linear, KNN). Торговать только когда >= 4/7 согласны с направлением. Фильтр уверенности.

**Какой тупик обходит:** low R² (разные модели ловят разные паттерны), малые выборки (фильтр сокращает N, но повышает качество).

**Дешёвый эксперимент:** Обучить 5 моделей на live-safe features. Измерить PF при agreement >= 3/5, 4/5, 5/5. Убивает: PF не растёт с agreement.

**Риск переупаковки:** Не делали. Но если все модели учат already-moved, agreement усилит already-moved.

---

### Идея 7. Mutual Information Upper Bound

**Суть:** Перед обучением — оценить MI между признаками и таргетом. Если MI низкий, никакая модель не поможет. Жёсткий go/no-go.

**Какой тупик обходит:** low R² (может показать, что предсказуемость фундаментально ограничена).

**Дешёвый эксперимент:** KSG MI estimator для каждого признака vs target. Суммарный MI — upper bound. Убивает: MI ~ 0 для всех признаков.

**Риск:** Не торговая идея, а диагностическая. Но может сэкономить месяцы.

---

### Идея 8. Conformal Anomaly Detection for Regime Change

**Суть:** Conformal prediction non-conformity scores — не для фильтрации сделок, а для детекции смены режима. Когда scores резко растут — режим изменился, модель не торгует.

**Какой тупик обходит:** regime drift (детектирует момент смены), already-moved (non-conformity может сигнализировать о structural break).

**Дешёвый эксперимент:** Обучить conformal model на 2017-2022. Мониторить non-conformity на 2023-2026. Убивает: non-conformity не коррелирует с режимом.

**Риск переупаковки:** Conformal prediction (секция 2.1) уже пробовали для фильтрации, но не для regime detection.

---

### Идея 9. Event-Driven Volatility Injection

**Суть:** Торговля только вокруг NFP, FOMC, CPI — известных volatility injection points. Простая модель: предсказать amplitude expansion relative to average.

**Какой тупик обходит:** low R² (события — экзогенный шок, не требует предсказания эндодинной динамики), already-moved (event — exogenous).

**Дешёвый эксперимент:** Измерить average amplitude в event windows vs non-event. Если ratio > 2 — стоит моделировать. Убивает: event effect исчез или нестабилен.

**Риск:** Нужен внешний календарь событий. Не делали.

---

### Идея 10. Amplitude x Session Composition

**Суть:** Amplitude устойчивее direction. Session (time) доминирует. Комбинация: предсказывать amplitude x session interaction. Торговать в сессиях с предсказанной высокой амплитудой.

**Какой тупик обходит:** already-moved (amplitude, не direction), time-only dominance (не время как признак, а время как модификатор amplitude).

**Дешёвый эксперимент:** Train amplitude model с session interaction features. Убивает: interaction не значим.

**Риск:** Может оказаться Fixed11-подобным.

---

### Идея 11. Drawdown-Aware Position Sizing

**Суть:** Не предсказывать направление, а предсказывать вероятность просадки. Размер позиции обратно пропорционален риску.

**Какой тупик обходит:** direction-only (это не alpha, а risk management).

**Дешёвый эксперимент:** Не имеет смысла без alpha-источника.

**Риск:** Не генерирует альфу, только управляет риском. Не самостоятельная идея.

---

### Идея 12. Fractal Pattern Sequence Model

**Суть:** Последовательности фрактальных структур (не значения, а порядок паттернов) как вход для sequence model.

**Какой тупик обходит:** already-moved (порядок паттернов — не то же самое, что уже произошедшее движение).

**Дешёвый эксперимент:** Кодировать фрактальные паттерны как символы, обучить sequence classifier. Убивает: AUC < 0.55.

**Риск переупаковки:** Fractal sequence Transformer (секция 2.10) уже дали direction val_eval=0.0050. **Переупаковка — отсеяна.**

---

### Идея 13. News NLP Signal

**Суть:** NLP-обработка новостей для sentiment/tone signal.

**Какой тупик обходит:** already-moved (news — exogenous).

**Дешёвый эксперимент:** Не требует ML-пайплайна, но требует внешний data source.

**Риск:** Качественных бесплатных данных для XAUUSD нет. Infrastructure overhead не оправдан на этапе поиска alpha. **Отсеяна — невыполнимо.**

---

### Идея 14. Multi-Timeframe Confirmation

**Суть:** H4/D1 контекст как фильтр для H1 entries. Не prediction, а confirmation.

**Какой тупик обходит:** low R² (дополнительный контекст), already-moved (H4 bar закрылся, это не future data для H1).

**Дешёвый эксперимент:** Добавить H4/D1 features к live-safe model. Убивает: PF не улучшается.

**Риск:** H4 features могут быть already-moved для H1.

---

### Идея 15. Adversarial Validation for OOS Detection

**Суть:** Classifier: отличить train от test distribution. Если sample — «test-like», не торговать.

**Какой тупик обходит:** regime drift (прямо детектирует distributional shift).

**Дешёвый эксперимент:** Train classifier (train vs test). Использовать P(test-like) как фильтр. Убивает: фильтр не улучшает PF.

**Риск переупаковки:** Не делали, но близко к conformal anomaly (идея 8).

---

### Идея 16. Bootstrap Power Analysis

**Суть:** Перед каждым экспериментом — считать, какой minimum PF detectable при данном N. Если N < threshold — эксперимент бессмыслен.

**Какой тупик обходит:** малые выборки (мета-методологическое решение).

**Дешёвый эксперимент:** Power curve: N vs minimum detectable PF. Убивает: все текущие системы ниже порога.

**Риск:** Не генерирует альфу, но предотвращает ложные выводы.

---

### Идея 17. Synthetic Data Augmentation (GAN/Bootstrap)

**Суть:** Генерация синтетических тренировочных данных для увеличения выборки.

**Какой тупик обходит:** малые выборки.

**Дешёвый эксперимент:** Time-series bootstrap (block bootstrap) -> train on augmented -> test on real OOS. Убивает: synthetic data не улучшает OOS.

**Риск:** GAN для time series — research-grade, нестабильно. Block bootstrap — проще, но не создаёт новых паттернов.

---

### Идея 18. Signal-to-Noise Ratio Mapping

**Суть:** Не предсказывать направление, а предсказывать, в каких окнах SNR достаточно высок для торговли. «Не торгуй, когда не можешь».

**Какой тупик обходит:** low R² (признаёт, что предсказуемость не постоянна), малые выборки (фильтрует до достаточного N).

**Дешёвый эксперимент:** Rolling R² как proxy for SNR. Торговать когда rolling R² > threshold. Убивает: rolling R² не предсказуем.

**Риск переупаковки:** Близко к regime detection (идея 2), но проще.

---

## ФАЗА 2: СХОЖДЕНИЕ — отбор через ограничения

### Фильтры отбора

- **F1:** Не переупаковка закрытого (секция 8 ретроспективы)
- **F2:** Live-safe (не future-derived)
- **F3:** Обходит хотя бы один накопленный constraint
- **F4:** Дешёвый эксперимент реально выполним

### Таблица отбора

| # | Идея | F1 | F2 | F3 | F4 | Итог |
|---|------|----|----|----|----|------|
| 1 | Amplitude Tail Trading | PASS | PASS | PASS | PASS | **A** |
| 2 | Regime-Gated Rules | PASS | PASS | PASS | PASS | **A** |
| 3 | Time-Effect Decomposition | PASS | PASS | PASS | PASS | **A** |
| 4 | Limit-Order Entry/Exit | PASS | PASS | PASS | PASS | **A** |
| 5 | Cross-Instrument Lead-Lag | PARTIAL | PASS | PASS | PASS | **B** |
| 6 | Ensemble Agreement | PASS | PASS | PASS | PASS | **B** |
| 7 | MI Upper Bound | PASS | PASS | PASS | PASS | **A** (диагностика) |
| 8 | Conformal Anomaly | PASS | PASS | PASS | PASS | **B** |
| 9 | Event-Driven Vol | PASS | PASS | PASS | PARTIAL | **B** |
| 10 | Amplitude x Session | PARTIAL | PASS | PASS | PASS | **B** |
| 12 | Fractal Pattern Seq | FAIL | — | — | — | Отсеяна |
| 13 | News NLP | PASS | PASS | PASS | FAIL | Отсеяна |
| 14 | Multi-Timeframe | PARTIAL | PASS | PASS | PASS | **B** |
| 15 | Adversarial Validation | PASS | PASS | PASS | PASS | **B** |
| 16 | Bootstrap Power | PASS | PASS | PASS | PASS | **A** (диагностика) |
| 17 | Synthetic Data | PASS | PASS | PARTIAL | PASS | **C** |
| 18 | SNR Mapping | PARTIAL | PASS | PASS | PASS | **B** |

---

## ФИНАЛЬНЫЙ РЕЙТИНГ — 6 идей для реализации

### Tier 1: Делать немедленно

#### 1. Amplitude Tail Trading (идея 1)

**Почему первая:** amplitude — единственный устойчивый сигнал из ретроспективы. Tail-фильтр сокращает выборку до «крупных» движений, где PF может быть достаточным.

**Первый шаг:** quantile regression XGBoost, таргет |return_next_open|, live-safe features. Подвыборка: top-25% predicted amplitude. Метрика: PF подвыборки с bootstrap CI.

**Критерий смерти:** PF < 1.0 на top-25% подвыборке.

#### 2. Regime-Gated Rules (идея 2)

**Почему вторая:** regime drift — вторая по важности проблема. Если режим детектируем, простые правила внутри режима могут работать.

**Первый шаг:** CUSUM/Bocconi change-point detection на ATR. 2-3 режима. Внутри каждого — momentum или mean-reversion rule. Метрика: PF внутри режима на OOS 2023-2026.

**Критерий смерти:** детектор режимов не устойчив на OOS (F1 score < 0.6).

#### 3. MI Upper Bound + Bootstrap Power (идеи 7 + 16)

**Почему вместе:** это диагностический контур. MI покажет фундаментальный предел предсказуемости. Power analysis покажет, при каком N эксперимент имеет смысл. Могут спасти месяцы бесплодной работы.

**Первый шаг:** KSG MI estimator для каждого live-safe признака vs direction и amplitude таргеты. Power curve: N vs minimum detectable PF при alpha=0.05, beta=0.8.

**Критерий смерти:** MI ~ 0 для всех признаков -> предсказуемость фундаментально ограничена.

### Tier 2: Делать после Tier 1

#### 4. Time-Effect Decomposition (идея 3)

**Почему:** 85.9% calendar dominance — это либо самый большой источник альфы, либо самая большая иллюзия. Нужно понять механизм.

**Первый шаг:** Partial dependence hour-of-day, day-of-week, month. Rolling stability 2017-2022 vs 2023-2026.

**Критерий смерти:** паттерны 2023-2026 полностью отличаются от 2017-2022.

#### 5. Limit-Order Entry/Exit Optimization (идея 4)

**Почему:** MT5 infra готова, limit BUY PF=1.53. Расширение до полной системы — самый дешёвый путь к production.

**Первый шаг:** Grid search TP/SL ratios для limit-order entries. Spread sensitivity analysis.

**Критерий смерти:** PF < 1.0 при spread > 0.30.

### Tier 3: Исследовать если Tier 1/2 не дали результата

#### 6. Adversarial Validation (идея 15)

**Почему:** если regime drift необратим, нужно знать, когда модель «видит» unfamiliar data и не торгует.

**Первый шаг:** Classifier train vs test (2017-2022 vs 2023-2026). P(test-like) как gate.

**Критерий смерти:** classifier AUC < 0.55 (не отличает режимы).

---

## Ключевое наблюдение

Ретроспектива показывает систематический паттерн: **высокие in-sample метрики -> коллапс на OOS**. Это не методологическая ошибка — это сигнал, что **предсказуемость XAUUSD H1 фундаментально низка** (low R²=0.08-0.18, MI может быть ~0).

Идея 7 (MI Upper Bound) — самая важная диагностика. Если MI покажет, что предсказуемость близка к нулю, это честный ответ, который сэкономит месяцы. Если MI > 0 — значит alpha существует, и идеи 1-2 помогут её извлечь.
