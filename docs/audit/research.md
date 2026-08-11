# Брейншторм новых направлений для SoSimple

**Дата:** 2026-08-11
**Источник контекста:** `docs/audit/retrospective.md` (прочитана целиком).
**Дополнительные проверки фактов:** `knowledge-rag` (amplitude, regime drift, already-moved, limit-order, MT5 batch, calendar uplift).
**Порог успеха:** PF ≥ 1.3 на строгом OOS с bootstrap CI (нижняя граница > 1.0).

## Методология

Двухфазный брейншторм:

1. **Расхождение** — максимум идей без самоцензуры. Каждая идея помечена как `ФАКТ` (опирается на конкретные числа из ретроспективы), `ГИПОТЕЗА` (требует проверки) или `СПЕКУЛЯЦИЯ` (правдоподобно, но без оснований в данных).
2. **Схождение** — отбор через накопленные ограничения (секция 7 ретроспективы).

Для каждой идеи указаны:
- **Суть** (2–4 предложения).
- **Тупик/ограничение из ретроспективы**, которое обходит (ссылка на секцию).
- **Дешёвый эксперимент для фальсификации** — метрика и результат, убивающий идею.
- **Риск переупаковки** — не является ли это закрытым направлением из секции 8 ретроспективы (direction-only, breach-based trading, Triple Barrier, Fixed11, take/skip).

---

## ФАЗА 1: РАСХОЖДЕНИЕ

### Идея 1. Quantile-Tail Amplitude Selection (功耗-amplitude tail)

**Суть:** Модель предсказывает не направление, а распределение амплитуды будущего движения. Торговля включается только когда P(amplitude > threshold) выше заданного уровня, т.е. предсказанная амплитуда лежит в верхнем квантиле распределения. Стандартная модель предсказывает среднее; quantile regression предсказывает конкретные перцентили; это смещает фокус с труднопредсказуемого sign(next_move) на более устойчивый |next_move|.

**Что обходит:** already-moved (секция 2.10, residual Spearman после вычитания 0.29–0.54 vs 0.02 у direction) — амплитуда устойчивее направления; low R² (секция 7.5, R²=0.10–0.18) — таргетим хвост распределения, а не среднее; малые выборки (секция 7.2) — приложение к tail и без того уменьшает N, но ожидает высокий PF на оставшемся.

**Дешёвый эксперимент:** Обучить XGBoost quantile regression (quantiles 0.10/0.50/0.90) на live-safe признаках, таргет — `max(entry_up_H, entry_dn_H)` для H=6 и H=12. Отфильтровать сделки с `pred_q90 > Q3(actual)`. Метрика: PF подвыборки с bootstrap CI на frozen OOS. **Убивает:** PF < 1.0 на top-25% подвыборке, либо N < 30 на 5+ лет.

**Риск переупаковки:** `ФАКТ`: ретроспектива в секции 8 рекомендует amplitude-based как высокоприоритетное, но конкретной системы не строила. Не переупаковка closed-направления.

---

### Идея 2. Volatility Regime Gating при Live-Safe Baseline

**Суть:** Использоватьstance: вместо ML-предсказания направления — ML-классификация текущего режима волатильности (low/mid/high за ATR-lookback). Торговля внутри каждого режима по простым fixed-правилам. ML отвечает на «когда», а не «куда». Регим волатильности — не направление цены, а уже установленный факт (low leakage).

**Что обходит:** regime drift (секция 2.8, walk-forward: breach работал 2017–2022, перестал 2023–2026) — детектор режима делает drift явным объектом; time-only dominance (секция 7.6) — правила внутри режима уже не calendar-driven; already-moved (секция 2.10) — классификация текущего состояния, не предсказание будущего движения.

**Дешёвый эксперимент:** CUSUM-based change-point detection на rolling 24-bar ATR. 2–3 режима. Простые правила: внутри low-vol — mean-reversion (fade); внутри high-vol — breakout follow. Метрика: PF внутри каждого режима на OOS 2023–2026 (split between known vs unknown regimes). **Убивает:** распределение режимов не устойчиво на OOS (reg-transition F1 < 0.6), либо PF < 1.0 во всех режимах.

**Риск переупаковки:** `ГИПОТЕЗА`: walk-forward (секция 2.8) — это неявная версия regime-awareness. Принципиальное отличие — явная модель режима (детектор), а не периодическое переобучение direction-модели. Не breach-classification; breach-classification (секция 8) закрыта как самостоятельный edge, но здесь breach не используется — режим волатильности не эквивалентен breach.

---

### Идея 3. Time-Effect Decomposition: часы вместо «времени как ML-фичи»

**Суть:** Time-only dominance (no-ML baseline 85.9% ML PF) — это не шум, а сигнал с неизвестным механизмом. Декомпозировать: session liquidity (Asia/London/NY/overlap), rollover, news-schedule, market-maker behavior. Найти устойчивый подсигнал, который зависит от известного бюджета времени, и моделироватьexplicitly, без ML.

**Что обходит:** time-only dominance (секция 7.6) — превращает «проблему» в источник альфы; low R² (секция 7.5) — если механизм calendar-based, не нужна аппроксимация сложной модели.

**Дешёвый эксперимент:** Декомпозировать time-feature importance: час дня, день недели, месяц, сессия. Rolling stability каждого компонента на окнах 2017–2020 / 2021–2022 / 2023–2026. Метрика: коэффициент вариации средней амплитуды / PF per-component между окнами. **Убивает:** паттерны 2023–2026 полностью противоположны 2017–2022 ( instability across all components).

**Риск переупаковки:** `ФАКТ`: Fixed11 (секция 2.11, 11 rules = time_only, calendar dominance 85.9%) — закрыт. Принципиальное отличие — Fixed11 использовал time как ML-фичу без понимания; здесь — декомпозиция и поиск физически-обоснованного механизма. Если механизм не найден — это переупаковка Fixed11; поэтому критерий смерти жёсткий.

---

### Идея 4. Limit-Order BUY с трёх-барьерной структурой выхода

**Суть:** Расширение limit-order BUY (PF=1.53 на spread 0.20, 55.3 сделок/год, 0 neg years) до полной системы с фиксированным TP/SL/time-exit. Определять не направление модели, а параметры исполнения. TP/SL grid по исторической MFE/MAE, time-exit по распаду сигнала. Optimизация исполнения, а не предсказания.

**Что обходит:** execution contract (секция 7.4) — использует готовую MT5 infrastructure; low R² (секция 7.5) — не нужна точность направления; leakage (секция 7.1) — limit-order уже исполнимая конфигурация (live-safe).

**Дешёвый эксперимент:** Расширить существующий limit-order BUY runner до grid (TP ∈ {1,2,3,5,8} ATR × SL ∈ {1,2,3,5} ATR × time-exit ∈ {6,12,24} bars). Ре-evaluate на canonical (spread 0.20) и stress (spread 0.40). Метрика: PF + N + bootstrap CI per config. **Убивает:** PF < 1.0 при spread ≥ 0.30, либо best-config N < 30 сделок на OOS.

**Риск переупаковки:** `ФАКТ`: секция 2.7 limit-order BUY PASS, но точечно (один вход, без выхода). Не direction-only, не breach, не TB (TB тоже barrier-based, но метки другие и попытка prediction-of-crossing). Расширение exit-слоя — принципиально новый элемент.

---

### Идея 5. Conditional Direction при Amplitude-Gate

**Суть:** Двухстадийная архитектура: первый stage — детектор амплитуды (когда предсказано «big move imminent»); второй stage — детектор направления,trained exclusively на подвыборке с крупным движением. Direction непредсказуем на всём множестве (Spearman ~0.02), но возможно предсказуем на хвостах — там, где есть реальный драйвер.

**Что обходит:** already-moved (секция 2.10) — амплитуда residual-movement остаётся ~0.29–0.54; low R² (секция 7.5) — R² низкий на всём множестве, может быть выше на хвостах; directionUNDICTability на full-sample (секция 8 закрыта) — не contradict закрытию, потому что закрывали direction-only на всём множестве.

**Дешёвый эксперимент:** На исторических данных отфильтровать top-25% по actual future amplitude (oracle gate). Обучить direction-модель на фильтрованной выборке. Замер: residual Spearman vs Spearman на full-sample. **Убивает:** residual Spearman на top-25% не выше 0.10 vs 0.0248 на full-sample — нет uplift. Это дешёвый oracle-test; результат «uplift есть» — гипотеза для следующего шага, не доказательство работоспособности.

**Риск переупаковки:** `ГИПОТЕЗА`: направление осталось непредсказуемым на full-sample (секция 8). Принципиально новый элемент — двухстадийная структура с amplitude-gate. Не direction-only, не breach, не TB, не Fixed11, не take/skip. Если oracle-gate не даёт uplift — эквивалентно закрытому direction-only.

---

### Идея 6. Position-Ordinal как Live-Safe фильтр

**Суть:** В MT5 batch (секция 2.12) ordinal 5+ PF=3.205 (N=682, BS CI [2.909, 3.650]), ordinal 1 — PF=1.013. Фильтр нереализуем в live прямым счётом ордеров, но если существует live-safe proxy (продолжительность occupied-state, эквивалентная «5-я позиция в очереди»), edge становится доступным. Поиск прокси = поиск функции от live-safe переменных.

**Что обходит:** single-position policy (секция 7.7, 99.2% OPEN_FAILED) — не требует multi-position; regime drift (секция 7.3) — ordinal — это marker длительного рабочего состояния, которое само зависит от режима.

**Дешёвый эксперимент:** Факторизовать ordinal-1 vs ordinal-5+ сделки через live-safe признаки, доступные в момент решения (ATR, uptime-since-last-fill, fractal count, session). Binary classifier: «это будет ordinal-5+ entry?». Метрика: AUC на OOS. **Убивает:** AUC < 0.60 → нет live-safe proxy, фильтр нереализуем. (Если AUC ≥ 0.60 — переход к торговле на filtered subset с PF > 1.3.)

**Риск переупаковки:** `ГИПОТЕЗА`: секция 2.12 закрыта как MT5-batch direction-trading (no winner). Здесь — не direction ML, а обнаружение состояния, в котором leverage «ордина 5+» сохраняется. Принципиальное отличие — edge уже документирован в test (PF=3.205), но применить его в live сейчас невозможно; идея — сделать edge live-safe научившисьпредсказывать ordinal. Если прогноз ordinal равносилен прогнозу направления — переупаковка; это и проверяет эксперимент.

---

### Идея 7. Framework-first: Mutual Information Upper Bound перед обучением

**Суть:** Перед обучением оценить MI (mutual information) между признаками и target. Если суммарный MI низкий, никакая модель не даст edge — независимо от архитектуры. Это методологический go/no-go, необходимый после того, как все архитектуры (BiLSTM, Transformer, XGBoost, RF, linear) дали Collaps на OOS.

**Что обходит:** low R² (секция 7.5, R²=0.10–0.18) — MI upper bound объяснит, ограничение это данных или метода; малые выборки (секция 7.2) — MI estimate также определит minimum N для detectable edge.

**Дешёвый эксперимент:** KSG (Kraskov-Stögbauer-Grassberger) MI estimator для каждого live-safe признака vs target (direction и amplitude). Суммарный MI — оценка верхнего предела предсказуемости. Параллельно: power curve — N vs minimum detectable PF при α=0.05, β=0.8. **Убивает:** MI ~ 0 для всех live-safe признаков (предсказуемость принципиально ограничена данными) — корректный честный ответ, экономит месяцы.

**Риск переупаковки:** `ФАКТ`: это не торговая идея, а диагностическая. Не пересекается с закрытыми направлениями из секции 8. Скорее — методологический audit до того, как запускать идеи 1–6.

---

### Идея 8. Multi-Position Profitability через Risk-Adjusted Position Sizing

**Суть:** Multi-position исполняет ~9.6× больше сделок, но PF=0.895–0.910 (секция 2.12). Гипотеза (СПЕКУЛЯЦИЯ): убыток происходит от risk-overlap — несколько одновременных позиций имеют correlated SL. Решение — не отказываться от multi-position, а размер каждой новой позиции убывает по текущему暴露лению. Это превращает multi-position из «все-торговать» в «stack с decay».

**Что обходит:** single-position policy (секция 7.7) — позволяет multi-position; execution contract (секция 7.4) — не требует нового timing-контракта, только position-sizing layer.

**Дешёвый эксперимент:** Re-simulate существующий MT5 batch 32 кандидатов с position-sizing rule: размер новой сделки = max(0, 1.0 − 0.2 × (current open positions)). Метрика: PF + drawdown vs constant-position baseline. **Убивает:** PF не улучшается, или улучшение < 0.05 → не размер, а качество сигнала.

**Риск переупаковки:** `ГИПОТЕЗА`: секция 2.12 multi-position probe (PF=0.895–0.910) закрыт как «убыточен в обоих». Принципиально новый элемент — Risk-Adjusted Sizing (документирован close-of-position overlap не проверялся). Если размер не решает — переупаковка.

---

### Идея 9. Calendar News Cycle Overlay

**Суть:** XAUUSD чувствителен к NFP, FOMC, CPI, FOMC minutes. В event windows волатильность расширения, в non-event — сжатие. Идея: торговать только pre-defined risk-event windows; модель предсказывает amplitude expansion relative to rolling baseline. Если event windows stable по амплитуде на OOS — это exogenous alpha source.

**Что обходит:** already-moved (секция 2.10) — event — exogenous; regime drift (секция 7.3) — event windows стабильны структурно, не стационарно-drift; low R² (секция 7.5) — в event-окнах амплитуда должна быть больше и предсказуемей.

**Дешёвый эксперимент:** Использовать public economic calendar (NFP/FOMC/CPI dates). Измерить average amplitude в event windows (±1 час) на 2017–2022 vs 2023–2026. Метрика: ratio event/non-event amplitude + стабильность ratio. **Убивает:** event effect исчез или нестабилен post-2022 → нет источника edge.

**Риск переупаковки:** `ФАКТ`: не пробовали — это не direction-only, не breach, не TB, не Fixed11, не take/skip. Требует внешнего календаря; для XAUUSD public calendar достаточен.

---

### Идея 10. Cross-Instrument Lead-Lag признаки

**Суть:** XAGUSD, DXY, US10Y могут двигаться раньше XAUUSD. На H1 закрытые бары кросс-инструментов — не future data для XAUUSD, но могут сигнализировать о движении XAUUSD с лагом 1–5 баров. Источник информации за пределами own-price already-moved.

**Что обходит:** already-moved (секция 2.10) — сигнал от кросс-инструмента не является уже произошедшим движением самого XAUUSD; low R² (секция 7.5) — дополнительный exogenous источник.

**Дешёвый эксперимент:** Cross-correlation XAGUSD→XAUUSD и DXY→XAUUSD на лагах 1–5 баров. Метрика: cross-correlation на rolling 1y окнах, позволяющих detect stability. **Убивает:** корреляция не превосходит 0.30, либо нестабильна после 2022.

**Риск переупаковки:** `ГИПОТЕЗА`: секция 2.3 cross-instrument (XAGUSD PF=inf, EURUSD failed) — но тот тест был на ML-сигналах в entry_path framework, а не на raw lead-lag признаках. Как признак для обучения на live-safe target — новый элемент.

---

### Идея 11. Adversarial Distribution Gate

**Суть:** Binary classifier: «отличить train-distribution от test-distribution» по live-safe признакам в момент решения. Торговать только когда P(test-like) < threshold — то есть когда текущее состояние «похоже» на обучающее. Auto-detector regime shift.

**Что обходит:** regime drift (секция 7.3) — прямо детектирует distributional shift; low R² (секция 7.5) — gating вместо prediction.

**Дешёвый эксперимент:** Train classifier train(2017–2022) vs test(2023–2026) на live-safe features. Метрика: AUC discriminator. Threshold-gate_PF. **Убивает:** classifier AUC < 0.55 → не различает regimes, либо PF post-gate не лучше random (нет subset, где модель работает).

**Риск переупаковки:** `ФАКТ`: не делали. Не пересекается с закрытыми секцией 8. Не direction ML — meta-gate.

---

### Идея 12. Entropy/Subordination Ranking вместо регрессии

**Суть:** Regression показала R²=0.10–0.18 и Spearman 0.29–0.54 post-already-moved. Вместо предсказания точного значения — rank entries по «ожидаемой utility». Учить модель ranking-loss (NDCG-style) с таргетом — order по MFE − MAE. В best-K subset входить. Это другой свод.metrics — не R², а rank-correlation на top-K.

**Что обходит:** low R² (секция 7.5) — ranking не требует объяснения дисперсии, требует порядка; малые выборки (секция 7.2) — top-K subset компактнее, expected PF выше.

**Дешёвый эксперимент:** LambdaRank / listMLE модель на live-safe features, таргет — `rank(entry_up − entry_dn) per time-window`. Сравнить top-K PF vs random-baseline PF. **Убивает:** top-K улучшение PF не превосходит 0.05 → ranking не несёт сигнала.

**Риск переупаковки:** `ГИПОТЕЗА`: не делали. Архитектура принципиально отличается от regression-in-the-wild (секция 2.1 threshold analysis использовал regression, но без rank loss). Не переупаковка.

---

### Идея 13. Process-Based Synthetic Envelope

**Суть:** Model XAUUSD H1 как stochastic process (GBM + jumps). Обучить параметры процесса на rolling окне, предсказывать выпуски, торговать когда prediction interval не накрывает zero. Гипотеза (СПЕКУЛЯЦИЯ): распределение next-return на H1 имеет асимметричные tail-ratios, которые усиленные волатильностью. Эффективный edge возможен если асимметрия хвостов проходит в OOS.

**Что обходит:** already-moved (секция 2.10) — явная модель процесса, не ML на residuals; low R² (секция 7.5) — R² не целевая метрика, целевая — interval overlap.

**Дешёвый эксперимент:** Оценить GARCH(1,1)+jump-diffusion параметры на rolling. Предсказать 5–95% interval следующего H1-return. Метрика: interval overlap + асимметрия up/down tail. **Убивает:** tail asymmetry не превосходит 5% на OOS → нет trade-able edge.

**Риск переупаковки:** `СПЕКУЛЯЦИЯ`: не пробовали. Гипотеза о tail asymmetry — это гипотеза; если её нет, процесс-based модель даст тот же zero-edge для directional trading. Не переупаковка closed-направлений, но и не гарантированый new-edge.

---

### Идея 14. Calendar-of-Themes: RecurrentOfYear Patterns

**Суть:** Годовые циклы: tax year-end, Indian wedding season, central bank cycle. Гипотеза (СПЕКУЛЯЦИЯ): эти циклы создают recurring patterns в demand for XAUUSD на конкретных месяцах. Это не time-of-day или weekday (Fixed11), а более длинные cycle-时机-проявления. Если паттерны detect-able и OOS-stable, edge не зависит от ML.

**Что обходит:** time-only dominance (секция 7.6) — это другой time-scale, не тот, что доминирует в Fixed11; regime drift (секция 7.3) — cycle-структура структурна.

**Дешёвый эксперимент:** Aggregate monthly average return H1 для XAUUSD по годам на 2010–2026 (public data доступны). Метрика: correlation month-of-year averages между 2010–2018 и 2019–2026. **Убивает:** паттерны не воспроизводятся на second half.

**Риск переупаковки:** `СПЕКУЛЯЦИЯ`: Fixed11 (секция 2.11) использовал «hour/dow» а не «month-of-year». Принципиально новый масштаб времени. Но еслиcycle-of-year не separate от time-of-day dominance — это переупаковка. Проверяется экспериментом.

---

### Идея 15. Ensemble Disagreement как Risk-Gate

**Суть:** Обучить 5 разнородных моделей (XGBoost, RF, HistGB, linear, KNN) на одном target. Торговать only когда не менее 4/5 согласны по направлению. Классический ensemble voting, но цель — не предсказание направления, а сигнал «высокий consensus → high-confidence regime».

**Что обходит:** low R² (секция 7.5) — разные модели ловят разные unstable-паттерны; малые выборки (секция 7.2) — фильтр сокращает N, но повышает качество.

**Дешёвый эксперимент:** 5-fold ensemble на live-safe features. PF при agreement ≥ 3/5, 4/5, 5/5 vs random. **Убивает:** PF monotonic-improvement с agreement level не наблюдается → ensemble просто average-ный.

**Риск переупаковки:** `ФАКТ`: conformal prediction (секция 2.1) пробовали для фильтрации сделок; ensemble disagreement — другая метрика. Но если все модели учат already-moved, agreement усиливает уже произошедшее. Поэтому gate — risk-control, а не alpha-source. Не закрывать, но и не top-priority.

---

## ФАЗА 2: СХОЖДЕНИЕ

### Фильтры отбора

- **F1 — Не переупаковка закрытого:** секция 8 ретроспективы (direction-only, breach-based trading, Triple Barrier, Fixed11, take/skip).
- **F2 — Live-safe:** не future-derived (секция 7.1).
- **F3 — Обходит хотя бы один накопленный constraint** (секция 7).
- **F4 — Дешёвый эксперимент в один-два runner-запуска.**
- **F5 — Не дублирует уже сверен-ные** uplift-гипотезы (NY exclusion, vol_q4 exclusion, early timeout, pred_adv12 filter — проверены и дали uplift на leakage-обусловленных системах, для live-safe картина неизвестна).

### Таблица отбора

| # | Идея | F1 | F2 | F3 | F4 | F5 | Итог |
|---|------|----|----|----|----|----|------|
| 1 | Quantile-Tail Amplitude Selection | PASS | PASS | PASS | PASS | PASS | **A** |
| 2 | Volatility Regime Gating | PASS | PASS | PASS | PASS | PARTIAL | **A** |
| 3 | Time-Effect Decomposition | PASS | PASS | PASS | PASS | PASS | **A** |
| 4 | Limit-Order BUY с трёх-барьерным выходом | PASS | PASS | PASS | PASS | PASS | **A** |
| 5 | Conditional Direction при Amplitude-Gate | PASS | PASS | PASS | PASS | PASS | **B** (требует oracle-gate первой) |
| 6 | Position-Ordinal как Live-Safe фильтр | PASS | PASS | PASS | PASS | PASS | **B** |
| 7 | MI Upper Bound / Power Analysis | PASS | PASS | PASS | PASS | PASS | **A** (диагностика, first) |
| 8 | Multi-Position Risk-Adjusted Sizing | PASS | PASS | PARTIAL | PASS | PASS | **C** |
| 9 | Calendar News Cycle Overlay | PASS | PASS | PASS | PARTIAL | PASS | **B** |
| 10 | Cross-Instrument Lead-Lag | PASS | PASS | PASS | PASS | PASS | **B** |
| 11 | Adversarial Distribution Gate | PASS | PASS | PASS | PASS | PASS | **B** |
| 12 | Entropy/Ranking вместо регрессии | PASS | PASS | PASS | PARTIAL | PASS | **B** |
| 13 | Process-Based Synthetic Envelope | PASS | PASS | PARTIAL | PARTIAL | PASS | **C** |
| 14 | Calendar-of-Themes recurrent patterns | PASS | PASS | PASS | PASS | PASS | **B** (data-heavy) |
| 15 | Ensemble Disagreement как Risk-Gate | PASS | PASS | PASS | PASS | PASS | **C** (вторичен) |

F5 частично у идеи 2: vol_q4 exclusion уже проверен в `pf_uplift_discovery` (passed proбы, но на leakage-обусловленных entry_path). Здесь ML-классификация режима — другой механизм, но критерий смерти должен учитывать, что часть baseline-mechanical уже экспериментирована.

---

## ФИНАЛЬНЫЙ РЕЙТИНГ — Recommendations

### Tier 0 — Делать раньше других (диагностика)

#### 7. MI Upper Bound / Power Analysis

**Почему:** после 150 экспериментов и схлопывания in-sample → OOS необходим честный top-down вопрос: «есть ли вообще сигнал в данных?». Если MI ~ 0 — все идеи 1–6 в конечном итоге упрутся в тот же кросс-OOS-collapse. Если MI > 0 — это даёт信心 продолжать.

**Первый шаг:** KSG MI estimator по всем live-safe признакам vs target (direction и amplitude). Суммарный MI = upper bound конкретной информации. Параллельно: power curve N vs minimum detectable PF.

**Критерий смерти:** суммарный MI ~ 0 для всех live-safe признаков по направлению, и MI ~ 0 для amplitude → предсказуемость принципиально ограничена данными; проект должен перейти к другой методологии (например, не alpha-trading, а risk-management с event-overlay).

**Оценка:** `ФАКТ` по ретроспективе — не пробовали, диагностическая идея. Сложность: средняя (нужна корректная KSG-реализация).

---

### Tier 1 — Делать немедленно после Tier 0

#### 1. Quantile-Tail Amplitude Selection

**Почему:** amplitude — единственный residual-устойчивый сигнал (Spearman 0.29–0.54 vs 0.0248 у direction). Tail-фильтр сокращает выборку до «крупных» движений, где PF может быть достаточным.

**Первый шаг:** XGBoost quantile regression (quantiles 0.10/0.50/0.90), таргет `entry_movement = max(entry_up_H, entry_dn_H)`, live-safe features. Подвыборка `pred_q90 > Q3(actual)`. Метрика: PF + bootstrap CI на frozen OOS, ≥ 2 horizons (H6, H12).

**Критерий смерти:** PF < 1.0 на top-25% подвыборке, либо N < 30 сделок за 5+ лет.

#### 4. Limit-Order BUY с трёх-барьерным выходом

**Почему:** limit-order BUY PF=1.53 — единственная fully-live-safe конфигурация, прошедшая gate. Расширение exit-слоя — самый дешёвый путь к работе в production. MT5 infrastructure уже parity 99.05%.

**Первый шаг:** Grid search (TP × SL × time-exit) для limit-order entries, на canonical (0.20) и stress (0.40) spread. Метрика: PF, N, bootstrap CI, N neg years.

**Критерий смерти:** PF < 1.0 при spread ≥ 0.30, либо best-config N < 30 OOS.

---

### Tier 2 — Делать после Tier 1 (если Tier 1 дал сигнал)

#### 5. Conditional Direction при Amplitude-Gate

**Почему:** direction непредсказуем на full-sample, но возможно предсказуем на хвостах амплитуды. Зависит от идей 1 (amplitude model) и 7 (обоснование).

**Первый шаг:** Oracle-gate (на actual future amplitude top-25%):direction model residual Spearman. Дешёвей, чем full pipeline.

**Критерий смерти:** residual Spearman на oracle-top-25% ≤ 0.10 → edge не в conditional direction.

#### 2. Volatility Regime Gating

**Почему:** regime drift — вторая по важности проблема. Path: explicit detector → простые правила внутри режима.

**Первый шаг:** CUSUM change-point detection на rolling ATR, 2–3 режима. Stability check детектора на OOS.

**Критерий смерти:** детектор нестабилен (regime F1 < 0.6) → нет live-safe regime definition; либо PF < 1.0 внутри всех режимов.

---

### Tier 3 — Исследовать если Tier 1/2 не дали результата

#### 3. Time-Effect Decomposition

**Почему:** time-only dominance 85.9% — либо крупнейший alpha-source, либо крупнейшая иллюзия. Need explicit mechanism, не просто ML-time-feature.

**Первый шаг:** Partial dependence: hour, weekday, month, session; rolling stability 2017–2022 vs 2023–2026. Параллельно: cross-check `pf_uplift_discovery` results (NY exclusion, vol_q4 exclusion) на live-safe subset.

**Критерий смерти:** паттерны 2023–2026 полностью противоположны 2017–2022 → close, переупаковка Fixed11.

#### 10. Cross-Instrument Lead-Lag

**Почему:** если own-price already-moved, кросс-инструмент может не быть already-moved для XAUUSD.

**Первый шаг:** Cross-correlation XAGUSD → XAUUSD и DXY → XAUUSD на лагах 1–5 баров. Stability rolling 1-year windows.

**Критерий смерти:** корреляция < 0.30 или нестабильна после 2022.

#### 11. Adversarial Distribution Gate

**Почему:** если regime drift необратим, нужно знать, когда модель «видит» unfamiliar data и не торгует. Это meta-gate.

**Первый шаг:** Classifier train(2017–2022) vs test(2023–2026) on live-safe features. AUC + PF post-gate.

**Критерий смерти:** classifier AUC < 0.55.

---

### Tier 4 — Длинный список, не модульно от Tier 0–3

Идеи 6 (position-ordinal proxy), 8 (multi-position sizing), 9 (calendar news), 12 (ranking loss), 13 (process-based envelope), 14 (calendar-of-themes), 15 (ensemble disagreement). Каждую не отбрасываем, но они либо зависимы от Tier 1/2 (6 — от detection), либо требуют внешних данных (9, 14), либо спекулятивны (13), либо risk-control (8, 15). Достоин проработки, если Tier 0–3 исчерпаны.

---

## Ключевые наблюдения

**Наблюдение 1 (ФАКТ из ретроспективы):** Все in-sample PF 4.29–39.74 схлопываются на OOS до PF 0.84–1.28. Это систематический паттерн, не статистический шум. Возможные объяснения: (a) предсказуемость XAUUSD H1 фундаментально низка (MI ~ 0); (b) leakage во всех live-unsafe системах; (c) regime drift.

**Наблюдение 2 (ФАКТ):** Лучшие live-safe результаты: limit-order BUY PF=1.53 на spread=0.20, entry_path_v1_live_safe PF=2.34 на 25 сделках. PF=1.53 — единственная конфигурация с приемлемым N (55.3 сделок/год, 0 neg years). Это отправная точка для идеи 4.

**Наблюдение 3 (ГИПОТЕЗА):** Амплитуда residual-movement после already-moved остаётся 0.29–0.54 Spearman — больше, чем у direction (0.02). Это указывает, что alpha может существовать в conditional-amplitude, а не conditional-direction. Идеи 1 и 5 directly test это.

**Наблюдение 4 (СПЕКУЛЯЦИЯ):** Если идеи 7 (MI) и 1 (amplitude tail) оба дадут negative result, проект подошёл к фундаментальному пределу предсказуемости на XAUUSD H1 с данным признаковым пространством. В этом случае честный вывод: данные не несут trade-able alpha; следующий шаг — иной рынок (иные features, иное timeframe), иной target (volatility-selling /calendar), или закрытие alpha-поиска.

---

## Приоритеты на квартал

**Q3 2026:** Tier 0 (7) первым как gate → Tier 1 (1, 4) параллельно → Tier 2 (5, 2) после первых результатов. Каждая идея имеет явный criterion-of-death; если идея умирает, решение фиксируется как closed-направление и не возрождается без принципиально нового элемента.

**Q4 2026:** Проверка идей из Tier 3 (3, 10, 11) и из Tier 4 (выборочно, по результатам Q3). Синхронизация результатов с `report` / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` после каждого frozen-test.

## Мониторинг ошибок

- `DOC` — при ссылке на отчёты проектa из `docs/reports/` следует проверять наличие файла; в тексте ссылок на конкретные отчёты вне `retrospective.md` нет.
- `STRUCT` — упоминаемая `pf_uplift_discovery` находится в `ML/reports/pf_uplift_discovery/` (не в `docs/reports/`), что нестандартное расположение — при работе с кодом обратить внимание.
