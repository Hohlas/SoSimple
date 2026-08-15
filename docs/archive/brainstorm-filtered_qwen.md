# Brainstorm Filtered — Арбитраж

Дата: 2026-08-15
Арбитр: автоматический анализ протоколов споров

---

## 1. Короткий список выживших

Все выжившие идеи получили вердикт «условно» — ни одна не получила «выживает».
Список по убыванию потенциала:

### 1. Cross-sectional FX rank selection [кластер 15]
**Суть:** Ранжировать 20-30 FX-пар по относительной силе за N баров; входить в топ-квинтиль long / bottom-квинтиль short. Направление конкретной пары не предсказывается — edge в персистентности рангов.
**Обходимый тупик:** Направленческий сигнал (MI direction FAIL, все постановки 2.7/2.11).
**Убивающий эксперимент:** Собрать H1 OHLC для 20-30 FX-пар (минимум 5 лет). Вычислить momentum-скорость, ранжировать, сформировать long-short портфель (топ/низ 20%). Метрика: PF long-short портфеля на строгом OOS с bootstrap CI (1000 итераций). Убивает: PF lower bound CI < 1.0 или PF < 1.15 после транзакционных издержек.
**Стоимость:** 3-5 дней.
**Потенциал:** 2/5.
**Пометки:** [радикальная]; автор признаёт спекулятивность и отсутствие доказательств edge; crowded factor risk (Menkhoff et al. 2012).

### 2. Cross-asset lead-lag signals [кластер 19]
**Суть:** Использовать движение коррелированных активов (S&P 500 futures, US10Y yield, WTI) как leading indicator для FX-пар. Cross-asset информация потенциально содержит направление раньше, чем сама цена FX.
**Обходимый тупик:** Already-moved (2.11) и информационная граница (2.1).
**Убивающий эксперимент:** Вычислить mutual information между лагированными доходностями cross-asset активов и направлением FX-пары на горизонтах H3/H6/H12. Сравнить с MI-потолком direction (0.003-0.004 bits из 2.1). Метрика: MI в битах, permutation test p<0.05. Убивает: MI <= 0.005 bits (не превышает базовый MI-потолок).
**Стоимость:** 1-2 дня.
**Потенциал:** 2/5.
**Пометки:** [радикальная]; механизм edge (сегментация участников) признан автором слабым и сокращающимся; ретроспектива (раздел 6) явно требует тестов на внешних провайдерах.

### 3. Volatility regime transition prediction [кластер 1]
**Суть:** Предсказывать переходы между режимами волатильности (low->high, high->low), а не направление цены. Торговля при P(transition) > threshold, direction-agnostic straddle-позиции.
**Обходимый тупик:** Already-moved, regime drift.
**Убивающий эксперимент:** Обучить модель предсказания перехода волатильности (realized vol > X ATR за N баров) на train 2019-2022, оценить на frozen test 2023-2026. Метрика: AUC предсказания перехода + PF straddle-симуляции со spread и slippage. Убивает: AUC < 0.55 или PF straddle < 1.0 после spread=0.4+ и slippage на OOS с нижней границей bootstrap CI <= 1.0.
**Стоимость:** 1-2 дня.
**Потенциал:** 1/5.
**Пометки:** [радикальная]; «условно»; автор признал практическую не отличимость от hour-baseline из-за трёх структурных барьеров (spread, already-moved, calendar).

### 4. Regime transition early warning system [кластер 7]
**Суть:** Моделировать вероятность режимного перехода в пределах N баров (change-point detection, structural break tests). Снижать размер позиции или выходить при высоком P(regime change).
**Обходимый тупик:** Regime drift (перелом 2023 обнаружен как резкий, без предвестников).
**Убивающий эксперимент:** Применить BOCPD/CUSUM к OHLC-данным 2004-2022 (train). Определить change-points, разметить периоды warning. Запустить торговую систему с правилом: при warning — reduce size на 50% или exit. Метрика: PF на 2023-2026, lead time (бары между warning и break), false positives. Убивает: lead time < 24 баров ИЛИ PF regime-aware < 1.0 ИЛИ BOCPD обнаруживает < 3 change-points.
**Стоимость:** 2-3 дня.
**Потенциал:** 1/5.
**Пометки:** «условно»; N=1 breakpoint за 2004-2026, статистическая мощность отсутствует; ретроспектива (2.8) показывает резкий перелом без предвестников.

---

## 2. Таблица-сводка

| Идея | Вердикт | Потенциал | Обходимый тупик | Убивающий результат | Стоимость |
|------|---------|-----------|-----------------|---------------------|-----------|
| Cross-sectional FX rank selection | условно | 2/5 | Направленческий сигнал (MI FAIL) | PF lower CI < 1.0 или PF < 1.15 на OOS | 3-5 дней |
| Cross-asset lead-lag signals | условно | 2/5 | Already-moved, инф. граница | MI <= 0.005 bits | 1-2 дня |
| Volatility regime transition prediction | условно | 1/5 | Already-moved, regime drift | AUC < 0.55 или PF straddle < 1.0 | 1-2 дня |
| Regime transition early warning system | условно | 1/5 | Regime drift | lead time < 24 баров или PF < 1.0 | 2-3 дня |
| Path morphology classification | убита | — | Already-moved | AUC <= 0.55 или PF <= time-only baseline | 2-3 дня |
| Conditional return distribution modeling | убита | — | Low R², already-moved | PF uplift vs ATR-baseline < 0.10 | 2-3 дня |
| Multi-scale amplitude decomposition | убита | — | Already-moved | delta PF < 0.05 vs single-scale | 2-3 дня |
| Cross-asset relative strength signals | убита | — | Regime drift | ADF p > 0.10 или OOS PF < 1.0 | 3-5 часов |
| Liquidity event prediction | убита | — | Already-moved, low R² | AUC < 0.55 или PF < 1.0 после spread×2 | 2-3 дня |
| PCMCI Causal Drivers | убита | — | Low R² | OOS PF lower CI <= 1.0 или в пределах 95-го перцентиля случайного отбора | 1-2 дня |
| Survival Competing Risks Exit | убита | — | — | OOS PF < 1.3 или uplift vs TB-baseline < 0.15 | 2-3 дня |
| Fluctuation Dissipation Entry | убита | — | — | delta-AUC < 0.02 или PF upper quantile lower CI <= 1.0 | 2-3 дня |
| Rank stability confidence | убита | — | — | delta-PF < 0.1 или PF high agreement <= 1.0 | 2-3 дня |
| Nero tick-flow imbalance | убита | — | One-source OHLC, инф. граница | MI < 0.005 bits или delta PF < +0.05 | 1-2 дня |
| Adversarial regime gate | убита | — | Regime drift | PF high-shift >= PF low-shift или AUC < 0.60 | 2-4 часа |
| Volatility risk premium harvesting | убита | — | Инф. граница, хронология fill | Медианный годовой net VRP <= 0 на 2023-2026 | 2-3 дня |
| Execution venue asymmetry | убита | — | Хронология fill, single-source OHLC | Разница <= 0.1 спреда или p > 0.05 | 3-5 дней |

---

## 3. Список убитых

| Идея | Причина | Ссылка на ретроспективу |
|------|---------|-------------------------|
| Path morphology classification | Переупаковка: фрактальные признаки (Hurst, fractal dimension) уже проверены в 2.10 (AUC 0.53); режимная классификация = 2.11 (amplitude regime); exit по морфологии = 2.3 (TB exit optimization). Направление внутри режима непредсказуемо (2.11: bal_acc 0.5792->0.5287). | Секции 2.10, 2.11, 2.3 |
| Conditional return distribution modeling | Переупаковка: distribution modeling = amplitude regime (2.11: режим объясняется временем+ATR); MFE quantile exit = triple barrier exit (2.3) + take/skip (2.6, PF <= 0.5). MI direction FAIL (2.1). | Секции 2.1, 2.3, 2.6, 2.11 |
| Multi-scale amplitude decomposition | Already-moved масштаб-инвариантна (2.11: 57% строк H3 >=50% движения состоялось); календарная доминантность (2.12: no-ML hour-baseline догоняет ML). | Секции 2.11, 2.12 |
| Cross-asset relative strength signals | Regime drift: корреляции ломаются в risk-off/on (2.8); MI direction FAIL (2.1) применим к spread; малые N и multiple testing (2.2, 2.4). | Секции 2.1, 2.2, 2.4, 2.8 |
| Liquidity event prediction | Исполнение: OHLC не содержит тиковых данных для liquidity events; market order при spread widening = худший fill (2.5: requote ERROR-138); edge origin: retail Forex OTC, брокер извлекает premium, не клиент. | Секции 2.5, 2.11, 2.12 |
| PCMCI Causal Drivers | Информационный потолок direction (2.1: MI 0.003-0.004 bits); нестационарность causal graph (2.8: перелом 2023); данные и выравнивание (2.12: хронология уничтожила edge). | Секции 2.1, 2.8, 2.12 |
| Survival Competing Risks Exit | Переупаковка: competing risks = triple barrier outcomes (2.3: «проблема не решается поиском exit-порогов»); breach signal диагностический, не конвертируется в прибыль (2.7: RF test PF 0.84); Stage 5.2/5.3 уже тестировали Cox survival — DIAGNOSTIC_ONLY. | Секции 2.3, 2.7 |
| Fluctuation Dissipation Entry | MI-потолок direction (2.1: 0.003-0.004 bits); FDT требует равновесия — FX структурно неравновесна; regime-filter не преодолевает MI-потолок (ни один фильтр не восстановил направление). | Секции 2.1, 2.11 |
| Rank stability confidence | Происхождение edge: agreement K моделей измеряет согласованность, не корректность; если все модели разделяют календарный bias, agreement не создаёт направленного edge (2.1 MI FAIL, 2.12: time_only > no_time). | Секции 2.1, 2.12 |
| Nero tick-flow imbalance | Данные не содержат тиков: Nero.csv — H1-бары с фрактальными уровнями, не buy/sell классификация; MI-потолок (2.1); Batch Selection (2.13): 11 кандидатов из Nero, все провалили BS_p05>1.0. | Секции 2.1, 2.13 |
| Adversarial regime gate | Нет базового edge: ни одна модель не достигла PF >= 1.3 (2.8, 2.10, 2.12); gate фильтрует, но не создаёт положительное матожидание; перманентный сдвиг 2023 (2.8) = перманентная остановка торговли. | Секции 2.8, 2.10, 2.12 |
| Volatility risk premium harvesting | Инфраструктурная пропасть: проект на OHLC (2.12, 2.13), опционная инфраструктура отсутствует; транзакционные издержки: спред 0.8 уничтожает кандидатов (2.12); режимная нестабильность (2.8). | Секции 2.8, 2.12, 2.13 |
| Execution venue asymmetry | Инфраструктурный тупик: хронология fill уничтожила edge (2.12: PF 2.82-3.42 -> 0.82-0.94 после фикса); гипотеза зависит от того же механизма. | Секция 2.12 |

---

## 4. Идеи без спора (технический сбой агента)

Следующие идеи не получили вердикта из-за ошибки агента (спор не состоялся):

- **Амплитудно-календарный режимный отпечаток** [кластер 11] — кластеризация по профилю (час x ATR-квантиль), торговля в режимах, соответствующих profitable-кластерам. Обходимый тупик: regime drift.
- **Macro regime portfolio allocation** [кластер 17] — классификация макро-режима (risk-on/risk-off/кризис) по spreads, rates, VIX; аллокация капитала между sub-strategies. Обходимый тупик: режимный перелом 2023 (2.8, 2.9) и календарная доминантность (2.12).

Эти идеи не помечаются [нефальсифицируема] и не включаются в короткий список — требуется отдельный спор.

---

## 5. Понижения вердиктов арбитром

Понижений не произведено. Критики были адекватны или строги; все вердикты «условно» обоснованы структурными барьерами проекта (MI-потолок direction, календарная доминантность, regime drift, already-moved).

---

## Итог

- **Выжило (условно):** 4 идеи
- **Убито:** 13 идей
- **Без спора:** 2 идеи (технический сбой)
- **Понижено арбитром:** 0

**Топ-3 выживших:**
1. Cross-sectional FX rank selection (потенциал 2/5)
2. Cross-asset lead-lag signals (потенциал 2/5)
3. Volatility regime transition prediction (потенциал 1/5)
