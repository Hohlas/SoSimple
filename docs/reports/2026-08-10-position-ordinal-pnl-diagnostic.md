# Position-Ordinal PnL Diagnostic — 2026-08-10

> **Stage level:** `research_hypothesis` · **Allowed verdict:** `DIAGNOSTIC_ONLY` · **Result:** `PASS` (14 tests, JSON artifact)

## Research-first disclosure

- lifecycle_status: research_hypothesis
- origin_bias: follow-up to MT5 multi-position closeout (2026-08-07)
- research_priority: medium — определить, деградирует ли PF с ростом порядкового номера одновременно открытой позиции (ordinal) в MT5 max=64 пилоте
- current_search_budget: 0 model/search configurations; анализ сохранённых артефактов `multipos_pilot/max64/`
- cumulative_search_budget: inherited from 2026-08-07 batch (32 кандидата × max=64)
- next_probe_freeze: no ML winner selection; interpret ordinal PF patterns only
- allowed_max_verdict: DIAGNOSTIC_ONLY
- forbidden_interpretations: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

После закрытия multi-position refactor (2026-08-03) и full batch 32×2 (2026-08-07) возник вопрос: деградирует ли качество сделок (PF) с ростом порядкового номера одновременно открытой позиции?

MT5 max=64 пилот позволяет открывать до 64 позиций одновременно. Каждая позиция имеет ordinal — порядковый номер на момент открытия (1, 2, 3, ..., 64). Гипотеза: если PF деградирует с ростом ordinal, это указывает на механику исполнения (broker latency, slippage, liquidity), а не на качество сигнала.

Scope: только diagnostic analysis сохранённых events.csv из 32 кандидатов max=64 пилота. Без MT5 tester rerun, без выбора winner, без интерпретации PF как прибыльности.

## Methodology

### Data source

- Каталог: `ML/reports/mt5_execution_loop/multipos_pilot/max64/`
- 32 кандидата, каждый содержит `events.csv` (event log MT5 tester)
- Формат событий: `event;time;ticket;side;profit;open_positions`
- События: `OPEN` (открытие позиции), `CLOSE` (закрытие позиции), другие (INIT, ORDER_PLACED, ML_EVAL — игнорируются)

### Trade parsing

- Парсинг сделок по парам OPEN/CLOSE, связанных по `ticket`
- Ordinal извлекается из `open_positions` OPEN-события (snapshot на H1-баре)
- Year извлекается из `time` OPEN-события (формат `YYYY.MM.DD HH:MM`)
- Сделки без OPEN-события пропускаются

### PF computation

- Profit Factor = gross_profit / gross_loss
- Если gross_loss == 0 и gross_profit > 0: PF = inf
- Если gross_profit == 0: PF = 0.0
- Если gross_loss == 0 и gross_profit == 0: PF = 0.0

### Ordinal grouping

- Порог группировки предзадан до анализа: 1, 2, 3, 4, 5+
- Ordinal >= 5 агрегируется в группу "5+" (7.6% сделок, 682 из 8934)

### Bootstrap CI

- Candidate-level resampling (не block bootstrap)
- `n_bootstrap=2000`, `seed=42`
- 95% CI (2.5th и 97.5th percentiles)
- Bootstrap исключает PF=inf из ci_values
- Минимум 20 значений для расчёта CI

### Yearly decomposition

- Декомпозиция по годам для каждого ordinal (A5 шаг 1)
- Проверка монотонности PF по ordinal (A5 шаг 4)

### Implementation

- `ML/baseline/position_ordinal_analysis.py` — загрузка events, парсинг сделок, вычисление PF, bootstrap, вывод JSON
- `tests/test_position_ordinal_analysis.py` — 14 unit-тестов (TDD)
- `ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json` — выходной артефакт

## Results

### Summary statistics

- Кандидатов: 32
- Всего сделок: 8934
- Сделок с известным ordinal: 8934 (100%)

### PF by ordinal (aggregated)

| Ordinal | PF | n | CI lower | CI upper |
|---------|------|------|----------|----------|
| 1 | 1.013 | 3657 | 0.959 | 1.064 |
| 2 | 0.953 | 2458 | 0.868 | 1.030 |
| 3 | 0.854 | 1430 | 0.779 | 0.960 |
| 4 | 0.961 | 707 | 0.829 | 1.154 |
| 5+ | 3.205 | 682 | 2.909 | 3.650 |

### Observations

1. **Non-monotonic pattern.** PF не монотонно убывает с ростом ordinal:
   - Ordinal 1: PF=1.013 (близко к 1.0)
   - Ordinal 2: PF=0.953 (снижение)
   - Ordinal 3: PF=0.854 (минимум)
   - Ordinal 4: PF=0.961 (восстановление)
   - Ordinal 5+: PF=3.205 (резкий рост)

2. **Ordinal 5+ anomaly.** PF=3.205 значительно выше остальных ordinal. Возможные объяснения:
   - Малое число сделок (682, 7.6% от общего)
   - Селективное поведение: кандидаты открывают 5+ позицию только при сильном сигнале
   - Bootstrap CI узкий ([2.909, 3.650]), но это descriptive, не inferential

3. **Wide CI for ordinal 4.** CI=[0.829, 1.154] — широкий из-за малого числа сделок (707) и вариативности между кандидатами.

4. **Yearly decomposition.** Доступна в JSON-артефакте (`by_ordinal_by_year`). Не все кандидаты имеют сделки во все годы.

### Ordinal N+ Filter Analysis

Обнаружен систематический паттерн: позиции с высоким ordinal (open_positions на момент открытия) имеют значительно лучший PF.

**Терминология:**
- **Сигнал** — событие от ML модели ("открой позицию")
- **Позиция** — реально открытая сделка в MT5
- **open_positions** — количество УЖЕ открытых позиций на момент появления сигнала
- **Ordinal** — значение open_positions на момент открытия позиции (равномерсилено количеству открытых позиций перед этой)

**Постфактум анализ:**

Анализ считает прибыль ТОЛЬКО от позиций с ordinal >= threshold. Это НЕ фильтр сигналов, а постфактум группировка уже открытых позиций.

| Threshold (ordinal >=) | n_positions | total_profit | avg_profit | PF | WR |
|------------------------|-------------|--------------|------------|------|------|
| 1 (baseline) | 8934 | 22533 | 2.5 | 1.06 | 45% |
| 2 | 5277 | 20499 | 3.9 | 1.10 | 47% |
| 3 | 2819 | 25305 | 9.0 | 1.25 | 50% |
| 4 | 1389 | 33903 | 24.4 | 1.78 | 57% |
| 5 | 682 | **34966** | 51.3 | 3.20 | 64% |
| 6 | 378 | 23096 | 61.1 | 3.83 | 67% |

**Детальное сравнение ordinal >= 4 vs ordinal >= 5:**

| Метрика | ordinal >= 4 | ordinal >= 5 |
|---------|--------------|--------------|
| n_positions | 1389 | 682 |
| total_profit | 33903 | **34966** |
| avg_profit | 24.4 | **51.3** |
| PF | 1.78 | **3.20** |
| WR | 57% | **64%** |
| PF 2021 | 2.48 | **3.58** |
| PF 2022 | 1.46 | **2.96** |
| Candidates profit>0 | **32/32** | 30/30 |
| Median profit/cand | 941 | **1035** |

**Устойчивость ordinal >= 5 по годам:**
- 2021: n=273, profit=16288, PF=3.58, WR=65%
- 2022: n=409, profit=18678, PF=2.96, WR=64%

**Устойчивость ordinal >= 5 по кандидатам:**
- 30/32 кандидатов с profit > 0 (94%)
- 28/32 кандидатов с PF > 1.5 (88%)

**Природа паттерна:**

Позиции с ordinal >= 5 открываются, когда кандидат уже открыл 4+ позиции. Это указывает на:
1. **Селективное поведение:** кандидаты открывают 5+ позицию только при очень сильном сигнале
2. **Высокую волатильность:** несколько входов подряд на сильном тренде
3. **Уверенность модели:** много одновременных входов = высокая вероятность направления

**Фундаментальная проблема реализации в live-торговле:**

Фильтр `open_positions >= threshold` **нереализуем** в live-торговле:

1. Чтобы открыть позицию с ordinal=5, нужно сначала открыть позиции с ordinal 1, 2, 3, 4
2. Если мы пропускаем сигналы с open_positions < 5, мы не открываем позиции
3. Если мы не открываем позиции, open_positions не увеличивается
4. open_positions никогда не достигнет 5 → мы не откроем НИ ОДНОЙ позиции

**Пример:**
- Сигнал 1: open_positions=0 → пропускаем сигнал → позиция не открыта
- Сигнал 2: open_positions=0 → пропускаем сигнал → позиция не открыта
- Сигнал 3: open_positions=0 → пропускаем сигнал → позиция не открыта
- ... open_positions остаётся 0, мы никогда не достигнем threshold=5

**Вывод:** Результаты — это постфактум анализ уже открытых позиций, не готовая торговая стратегия. Фильтр по open_positions не может быть реализован в live-торговле без модификации логики открытия позиций.

**Возможные альтернативы:**
1. **Фильтр по признакам сигнала:** найти признаки, которые коррелируют с высоким ordinal (вероятность модели, ATR, волатильность)
2. **Фильтр по количеству сигналов на баре:** если на одном H1-баре появляется много сигналов, это может быть аналогом высокого ordinal
3. **Двухэтапная логика:** открывать первые N позиций без фильтра, затем применять фильтр для последующих

## Limitations

1. **Не все позиции имеют OPEN-событие.** ~68% позиций не имеют OPEN-события в polling-потоке (polling фиксирует OPEN на H1-баре; если pending order заполняется и/или закрывается до следующего опроса, OPEN не записывается). Измеренные сделки — только ~32% от общего числа позиций.

2. **Нет cost model.** Swap, commission, slippage не вычтены. PF может быть завышен.

3. **Bootstrap по кандидатам, не по сделкам.** При 32 кандидатах и малом числе сделок на высоких ordinal CI широкие. Результаты для ordinal 5+ — descriptive, не inferential. Temporal correlation внутри кандидата не учтена.

4. **max=64 — диагностический режим.** PF в max=64 не является каноническим результатом. Цель — понять механику деградации, не оценить прибыльность.

5. **Группировка 5+ предзадана.** Порог выбран до анализа на основе распределения. Альтернативные пороги (6+, 10+) могут дать другую картину.

6. **Bootstrap CI исключает inf.** Если все сделки в bootstrap-выборке для ordinal bucket выигрышные, PF=inf и исключается из ci_values. Для ordinal 5+ с малым числом сделок это может занизить верхнюю границу CI.

7. **Ordinal — polling snapshot.** `open_positions` на OPEN-событии — snapshot на H1-баре. Для нескольких fills в одном баре OPEN запишет итоговое количество после всех fills бара, а не количество на момент каждого fill. Ordinal может быть неточным для fills в одном баре.

## Conclusion

### Вывод

**PF не деградирует монотонно с ростом ordinal.** Наблюдается non-monotonic pattern с минимумом на ordinal 3 (PF=0.854) и резким ростом на ordinal 5+ (PF=3.205).

**Обнаружен систематический паттерн:** позиции с ordinal >= 5 имеют значительно лучший PF. 28 из 32 кандидатов показывают PF_5+ > PF_1-4 И PF_5+ > 1.5.

**Абсолютная прибыль (постфактум анализ):**
- Позиции ordinal 1-4: total_profit=-12433, avg_profit=-1.5 (убыточны)
- Позиции ordinal 5+: total_profit=+34966, avg_profit=+51.3 (прибыльны)
- Позиции ordinal 5+ дают 7.6% позиций, но 100% прибыли (компенсирует убытки ordinal 1-4)

**Постфактум анализ показывает:**
- ordinal >= 5: profit=34966 (+55% vs baseline), PF=3.20, WR=64%
- ordinal >= 4: profit=33903 (+50% vs baseline), PF=1.78, WR=57%, более устойчив (32/32 кандидата прибыльны)

**Фундаментальная проблема:** Фильтр `open_positions >= threshold` **нереализуем** в live-торговле. Если мы пропускаем сигналы с open_positions < threshold, open_positions не увеличивается, и мы никогда не откроем позиции с высоким ordinal.

**Природа паттерна:** Позиции с ordinal >= 5 открываются, когда кандидат уже открыл 4+ позиции. Это указывает на селективное поведение (сильный сигнал), высокую волатильность или уверенность модели. Но этот паттерн нельзя использовать как фильтр сигналов.

### Next steps

1. **Исследовать альтернативные фильтры.** Найти признаки сигнала, которые коррелируют с высоким ordinal (вероятность модели, ATR, волатильность, количество сигналов на баре).
2. **Фильтр по количеству сигналов на баре.** Если на одном H1-баре появляется много сигналов, это может быть аналогом высокого ordinal.
3. **Двухэтапная логика.** Открывать первые N позиций без фильтра, затем применять фильтр для последующих.
4. **Cost model analysis.** Добавить swap, commission, slippage в PF computation для более реалистичной оценки.
5. **Row-level event linkage.** Разрешить 12.5% residual (сигналы с neither ORDER_PLACED nor OPEN_FAILED) для более полного покрытия сделок.

### Diagnostic verdict

**DIAGNOSTIC_ONLY.** Результаты не являются доказательством прибыльности, готовности к торговле или качества модели. Это diagnostic analysis механики исполнения в max=64 пилоте. Постфактум анализ ordinal — гипотеза для дальнейшего исследования, не готовая торговая стратегия. Фильтр по open_positions нереализуем в live-торговле.

## Related Materials

- Plan: `docs/superpowers/plans/2026-08-10-position-ordinal-pnl-diagnostic.md`
- Artifact: `ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json`
- Code: `ML/baseline/position_ordinal_analysis.py`, `tests/test_position_ordinal_analysis.py`
- Previous report: `docs/reports/2026-08-03-mt5-multi-position-closeout.md`
- Methodology: `docs/methodology/A5-post-mortem-diagnostics.md`, `docs/methodology/11-robustness.md`, `docs/methodology/13b-mt5-execution-parity.md`, `docs/methodology/16-reporting-audit.md`
