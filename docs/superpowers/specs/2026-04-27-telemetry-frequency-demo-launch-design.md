# Telemetry Frequency Demo Launch — Design Spec

> **Date**: 2026-04-27
> **Status**: Draft
> **Track**: Подготовка проекта к онлайн demo-launch
> **Goal**: Получить частый диагностический режим для проверки контура `MT -> Nero.csv -> ML -> ml_signals.csv -> MT`, не смешивая его с production-кандидатами по прибыльности
> **Related materials**: `docs/MT/ml_signal_integration.md`, `MT/MQL4/Include/ORDERS.mqh`, `MT/MQL4/Include/SERVICE.mqh`, `docs/reports/2026-04-18-take-skip-frequency-followup.md`, `docs/reports/2026-04-19-execution-policy-v2.md`, `docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`

---

## 1. Context

Проект дошёл до операционной точки:

- есть frozen ML rules и export-contract `time;signal`;
- MT4 уже исполняет прямые ML-сигналы через `iSignal=3`;
- есть MT4-подтверждённые режимы `quality`, `frequency`, `original_plus_path`, `entry_path_v1_quantile`;
- есть инструменты parity/reconciliation для сверки export и MT4 tester log.

Следующий практический этап — не поиск ещё одного красивого backtest, а проверка живого контура на demo-счёте:

- поступает ли свежий `Nero.csv`;
- совпадает ли онлайн export с повторным Python export;
- открывает ли MT4 именно ожидаемые сделки;
- насколько онлайн-исполнение расходится с tester на том же периоде;
- как spread/slippage влияют на результат в единицах ATR.

Главная проблема текущих сильных режимов — малая частота сделок. Для проверки инфраструктуры ждать годы нельзя. Поэтому нужен отдельный диагностический частый режим.

---

## 2. Main Decision

Выбран подход 1:

- не переобучать ML как первый шаг;
- не создавать случайный probe-режим;
- взять существующий ML score/rule contour и ослабить отбор до максимально высокой частоты.

Режим называется:

- `telemetry_frequency_v1`

Его задача:

- набрать статистику исполнения и сверки;
- выявить технические расхождения online/tester;
- оценить влияние spread/slippage;
- проверить устойчивость pipeline.

Его задача **не**:

- доказать прибыльность;
- заменить production-кандидаты;
- участвовать в portfolio verdict;
- использоваться для новых PF-выводов без отдельного research-gate.

---

## 3. Frequency Policy

Практический принцип:

- чем выше частота, тем быстрее выявляются ошибки pipeline;
- но частота не должна превращать режим в шум, где невозможно сопоставлять signal/export/trade.

Первый bounded target:

- подобрать threshold/top-k на историческом test/forward-like периоде так, чтобы получить частоту выше production frequency;
- предпочтительно начать с диапазона `1-5` сделок в день;
- если spread impact и нагрузка MT4 приемлемы, можно расширять дальше.

Подбор частоты должен быть оформлен как diagnostic calibration, а не как search for profit:

- критерий выбора — количество сделок и техническая наблюдаемость;
- PF не является критерием выбора;
- итоговый режим должен быть явно помечен как diagnostic.

---

## 4. Signal Source Design

Основной кандидат для первого прохода:

- существующий `take_skip_trailing_stop_v2` frequency/score contour.

Причины:

- он уже имеет rule consumer: `API/export_take_skip_trailing_stop_v2_signals.py`;
- уже проверялся как более частый режим;
- MT4 already supports direct `ml_signals.csv` execution;
- не требуется менять модельный input contract на первом шаге.

Допустимые варианты отбора:

- `top_k_probability` поверх существующей score column;
- ослабленный probability threshold;
- несколько заранее заданных diagnostic presets, например:
  - `telemetry_low`
  - `telemetry_mid`
  - `telemetry_high`

Недопустимо в первой версии:

- новый широкий ML training sweep;
- новые сложные фильтры;
- оптимизация порога по PF;
- смешивание нескольких систем в один diagnostic signal без отдельного объяснения.

---

## 5. MT4 Execution Design

Нужно максимально использовать текущий MQL-код.

Ключевое решение:

- не писать новый торговый контур;
- менять существующий direct ML path в `lib_ML_Signal.mqh`;
- точка входа остаётся `EXPERT::ML_TRADE()`;
- внешний переключатель остаётся `iSignal=3`.

Дополнительное reuse-правило:

- старые функции открытия, закрытия и изменения позиций находятся в `MT/MQL4/Include/ORDERS.mqh`;
- при доработке multi-position исполнения сначала проверить, можно ли использовать или аккуратно расширить существующие функции из `ORDERS.mqh`;
- прямые вызовы `OrderSend`, `OrderClose`, `OrderModify` в `lib_ML_Signal.mqh` допустимы только если существующие функции `ORDERS.mqh` не подходят по контракту для diagnostic ML flow;
- если потребуется менять торговую операцию, предпочтение отдаётся модификации уже имеющейся функции, а не созданию параллельной реализации.

В текущем коде уже есть параметры и функции, связанные с multi-position режимом:

- `ML_MaxPositions`;
- `MLP_ManageMultiPositions(...)`;
- `MLP_OpenMarketOrder(...)`;
- `MLP_CountOwnMarketOrders(...)`.

Перед реализацией нужно проверить фактическое поведение:

- действительно ли `ML_MaxPositions > 1` разрешает несколько открытых ML-позиций;
- не остаётся ли скрытого ограничения "одна позиция в одном направлении";
- не блокируют ли старые `BUY.Typ` / `SEL.Typ` состояния новые позиции в multi-position режиме;
- корректно ли закрываются несколько позиций одного направления.

Если ограничение "одна позиция в одном направлении" всё ещё существует, его нужно менять в существующей функции/ветке, а не обходить новым MQL-контуром.

---

## 6. Position Policy

Для `telemetry_frequency_v1` разрешаются несколько одновременных позиций.

Обязательные предохранители:

- отдельный magic number или явно отделимый magic/comment для diagnostic режима;
- `ML_MaxPositions` как общий лимит открытых ML-позиций;
- ограничение не больше одного открытия на один bar time;
- фиксированный минимальный лот на demo;
- отключение money management для diagnostic режима;
- явный режим `Real=false`/demo-only в запусковом чеклисте.

Первичная настройка:

- `ML_MaxPositions > 1`;
- точное значение выбрать в implementation plan после проверки исторической плотности сигналов;
- не считать `ML_MaxPositions` торговой оптимизацией, это safety limit.

---

## 7. Exit Policy

Чтобы spread impact был сравним с оригинальной стратегией, сделка должна быть достаточно крупной в ATR.

Базовый diagnostic exit:

- `SL = 3 ATR`;
- `TP = 5 ATR`;
- `max_hold_bars` обязателен.

Причина:

- мелкие SL/TP сделают spread слишком большой частью результата;
- `3/5 ATR` сохраняет масштаб сделки ближе к исходной стратегии;
- `max_hold_bars` предотвращает зависание позиций и падение фактической частоты.

Практическое замечание:

- текущий `ML_BackStopATR` используется как дальний страховочный stop;
- `ML_TakeProfitATR` уже есть;
- для настоящего `SL=3 ATR` может понадобиться отдельное уточнение текущей stop-логики в existing `MLP_OpenMarketOrder(...)`, а не новый open path.

---

## 8. Logging Design

Логирование должно покрывать весь путь от сигнала до сделки.

### Python/export log

Фиксировать:

- source CSV path;
- source CSV modified time;
- source CSV row count;
- source CSV last bar time;
- model/checkpoint/rule path;
- rule hash or file hash;
- threshold/top-k preset;
- exported row count;
- nonzero signals;
- BUY/SELL count;
- duplicate time count;
- output hash.

### MT4 open log

Фиксировать:

- `ticket`;
- `magic`;
- `mode=telemetry_frequency_v1`;
- `signal_time`;
- `entry_time`;
- `direction`;
- `score`;
- `threshold/top-k preset`;
- `ATR`;
- spread at entry;
- entry price;
- SL price;
- TP price;
- lot;
- current open position count.

### MT4 close log

Фиксировать:

- `ticket`;
- close reason;
- `entry_time`;
- `exit_time`;
- holding bars;
- entry price;
- exit price;
- ATR;
- spread at close;
- gross PnL in ATR;
- net PnL in account currency;
- slippage if available.

Спред нужно считать и хранить в относительной форме:

- `spread_at_entry / ATR`;
- `spread_at_close / ATR`.

---

## 9. Daily Reconciliation Design

Ежедневная сверка должна быть автоматизирована.

Минимальный daily job:

1. взять online `Nero.csv`;
2. пересобрать актуальные ML signals тем же Python export command;
3. сравнить полученный export с тем, что фактически лежал в MT4;
4. распарсить MT4 log/trade report;
5. сравнить expected signals vs opened trades;
6. при наличии tester run на том же периоде сравнить online trades vs tester trades.

Итог daily job:

- `summary.json`;
- `summary.md`;
- `signals_diff.csv`;
- `trades_reconciliation.csv`;
- exit code:
  - `0` если критичных расхождений нет;
  - non-zero если есть missed signals, wrong direction, unexpected open, broken CSV, stale data.

Первый implementation вариант может расширять существующие инструменты:

- `ML/benchmark_signal_export_parity.py`;
- `statistics/signal_tracer.py`;
- existing MT4 log lines from `lib_ML_Signal.mqh`.

Для MQL-side мониторинга и сравнения online/test нужно отдельно проверить и использовать существующие функции из:

- `MT/MQL4/Include/SERVICE.mqh`.

Ожидаемый reuse scope для `SERVICE.mqh`:

- tester/report file creation;
- `OnTester()` metrics/reporting;
- `REPORT(...)` pipeline;
- текущие механизмы online monitoring, включая контроль missed bars;
- сохранение параметров и magic-linked service metadata.

Если текущий формат `SERVICE.mqh` не покрывает нужные поля telemetry, его нужно расширять совместимо, а не строить отдельный MQL-сервисный слой.

Не нужно сразу строить тяжёлую систему мониторинга. Нужен воспроизводимый CLI, который можно запускать каждый день.

---

## 10. Tester vs Online Comparison

Сравнение tester/online должно быть отдельным слоем.

Сравнивать:

- число сигналов;
- число открытых сделок;
- пропущенные сигналы;
- направление;
- entry time;
- exit time;
- close reason;
- PnL in ATR;
- spread/ATR;
- slippage/ATR.

Ожидаемые причины расхождения:

- разный spread;
- исполнение по текущим котировкам;
- задержка обновления CSV;
- broker stop-level;
- intra-bar order of high/low in Python simulation;
- timezone/server-time mismatch.

Критичные причины:

- MT4 не видит свежий `ml_signals.csv`;
- signal time смещён;
- направление перепутано;
- opened trade отсутствует без documented skip reason;
- online использовал другой rule/checkpoint/hash.

---

## 11. Safety Boundaries

Diagnostic режим должен быть изолирован от production-кандидатов.

Обязательные границы:

- отдельный режим/label в логах;
- отдельная директория отчётов;
- отдельные daily reconciliation artifacts;
- минимальный фиксированный лот;
- запрет на вывод "режим прибыльный" по diagnostic calibration;
- запрет смешивать diagnostic trades с production portfolio stats.

Если режим случайно показывает прибыль, это только повод открыть отдельный research stage, а не production verdict.

---

## 12. Testing Strategy

Проверки до demo:

- unit tests для Python calibration/export logic;
- unit tests для daily reconciliation parser;
- fixture-based test на MT4 log lines;
- export parity check без MT4 log;
- export parity check с сохранённым tester log;
- ручной tester run с `ML_MaxPositions > 1`;
- проверка, что несколько позиций одного направления могут быть открыты и закрыты.

MQL-specific acceptance:

- при `ML_MaxPositions=1` старое поведение не ломается;
- при `ML_MaxPositions>1` нет блокировки одной позиции в одном направлении;
- `MaxPositions` ограничивает общее число открытых ML-позиций;
- все close reasons попадают в лог с ticket;
- daily parser может связать open/close по ticket.

---

## 13. Deliverables

Первый этап должен дать:

- spec and implementation plan;
- diagnostic calibration report по частоте;
- frozen diagnostic preset for `telemetry_frequency_v1`;
- updated/export CLI if needed;
- updated existing MQL direct ML path if current multi-position behavior incomplete;
- documented reuse or modification points for `ORDERS.mqh` and `SERVICE.mqh`;
- automated daily reconciliation CLI;
- docs for demo launch checklist;
- tester proof before demo account run.

---

## 14. Decision Rule

Этап считается готовым к demo, если:

- diagnostic signals генерируются воспроизводимо;
- MT4 открывает ожидаемые сделки;
- несколько одновременных позиций реально работают;
- daily reconciliation автоматически ловит критичные расхождения;
- spread/ATR и slippage/ATR попадают в отчёты;
- production-кандидаты не затронуты и остаются отдельно.

Если любой пункт не выполнен, demo запуск откладывается до исправления технической причины.
