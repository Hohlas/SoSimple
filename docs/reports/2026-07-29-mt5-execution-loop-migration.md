# MT5 Execution Loop Migration

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Подготовить минимальный MT5-контур, где MT5 формирует `Nero.csv`-совместимый поток и проверяет исполнение ордеров в Strategy Tester.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md`

## Context

Предыдущий fixed11 Python H1 chronology fix показал, что самописная Python-механика исполнения может materially менять выводы. Этот этап переносит проверку fill, SL/TP и ML-close в MT5 Strategy Tester, но не решает сам по себе честность ML-признаков.

MT5 tester can replace Python execution simulation for orders/fills/SL/TP/close mechanics, but it does not by itself prove that Python ML features are live-safe.

## Stage Level

Уровень этапа: диагностический инженерный прототип. Это не production readiness и не кандидатная проверка прибыльности.

## Methodology

Применены ограничения `docs/methodology/03-feature-contract-leakage.md`, `12-backtest-costs.md`, `13-export-mt4-parity.md`, `13b-mt5-execution-parity.md` и `16-reporting-audit.md`.

## What Was Done

- Проверен существующий MT5 target `MT/MQL5/Experts/$o$imple.mq5`; MetaEditor compile прошёл с `0 errors, 0 warnings`.
- Добавлен default-off MT5 `Nero.csv` producer: `InpMT5_ExportNero=false`, имя файла через `InpMT5_NeroFile`, фрактальные поля расширены до 23-го nested поля `Shift`.
- Созданы Python-схемы entry signal и event log, включая запрет future/result колонок в entry CSV.
- Добавлен экспортёр entry-only CSV `ML/baseline/export_mt5_entry_signals.py`.
- Встроен диагностический MT5 executor в существующий `$o$imple.mq5` через `lib_ML_Signal.mqh`, без fallback expert.
- Добавлен post-fill диагностический scorer, `ML_EVAL`/`ML_CLOSE` логирование и запрет ML-close при `bars_since_fill=0`.
- Добавлен Python parser event log и расчёт диагностических MT5-метрик.
- Созданы manual tester runbook и batch-selection design для следующего этапа.

## Multiple Testing Context

Нового выбора модели, правила, порога, winner или locked_test-решения не было.

current_search_budget: один инженерный MT5-прототип, один символ `XAUUSD`, timeframe `H1`, диагностический scorer.

cumulative_search_budget: не изменён относительно fixed11-ветки; этот этап не добавляет новый ML-search.

allowed_max_verdict: `DIAGNOSTIC_ONLY`.

forbidden_interpretations: нельзя говорить, что MT5-прототип прибыльный, live-ready, production-ready или что MT5 `Nero.csv` parity уже доказана.

## Changed Files

- `MT/MQL5/Experts/$o$imple.mq5`
- `MT/MQL5/Include/INPUT.mqh`
- `MT/MQL5/Include/lib_ML_Signal.mqh`
- `MT/MQL5/Include/lib_PIC.mqh`
- `ML/baseline/export_mt5_entry_signals.py`
- `ML/baseline/mt5_signal_schema.py`
- `ML/baseline/parse_mt5_execution_report.py`
- `tests/test_mt5_signal_executor_schema.py`
- `tests/test_parse_mt5_execution_report.py`
- `docs/methodology/13b-mt5-execution-parity.md`
- `docs/schemas/mt5_nero_csv_contract.md`
- `docs/schemas/mt5_open_position_feature_contract.md`
- `ML/reports/mt5_execution_loop/*`

## Verification

Выполнены focused Python tests:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
```

Выполнены статические проверки из задач 1A, 4, 5, 7, 8 и финального плана через `rg`.

Выполнена компиляция:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
```

Compile verdict: `Result: 0 errors, 0 warnings`.

MT5 Strategy Tester runtime-прогон не выполнялся.

## Results

Создан вертикальный диагностический контур:

```text
MT5 Nero.csv export -> Python entry export -> MT5 tester diagnostic execution -> Python metrics parser
```

MT5 `Nero.csv` producer status: `UNKNOWN`. Статическая форма исправлена до 23 nested полей, но row-by-row parity с MT4/current dataset не доказана.

Manual tester status: `manual_user_run_required`.

## Conclusions

Что MT5 должен решать после полного tester-сопровождения: исполнение pending/limit orders, фактический fill, SL/TP и close mechanics должны проверяться в tester, а не финально выбираться Python-симулятором. Текущий прототип компилируется, но не доказывает intrabar fill-and-close logging: диагностический lifecycle вызывается на H1-баре, поэтому сделка, открытая и закрытая внутри одного H1-бара, может не попасть в event log как полноценные `OPEN`/`CLOSE`.

Что MT5 не решает: tester не доказывает, что признаки Python доступны без утечки в момент решения. Feature leakage gate, split/freeze и reconciliation остаются обязательными.

## Limitations / Open Questions

- Автоматический запуск MT5 Strategy Tester агентом не доказан.
- Фактическая parity MT5 `Nero.csv` против MT4/current source не выполнена.
- `OPEN/CLOSE` history logging в текущем `MQL4Compat` остаётся диагностически ограниченным; close reason требует сверки по MT5 history/deals.
- Cost/execution поля `take_profit`, `swap`, `commission`, `order_close_price` и связанные PnL-поля пока нельзя читать как полноценный источник reconciliation без MT5 history/deal сверки.
- Диагностический scorer не является trained ML-exit model.
- Terminal file directory для tester input/output должен быть подтверждён пользователем.
- `mt5_entry_signals.csv` не является готовым артефактом этого этапа; его нужно сгенерировать отдельной командой `ML/baseline/export_mt5_entry_signals.py` из выбранного frozen source и затем скопировать в MT5 tester `Files`.

## Split Disclosure

Train/validation/locked_test split на этом этапе не открывался и не использовался для выбора. Locked test не применялся. Sample CSV синтетический и служит только тесту схемы/парсера.

## Next Step

Сначала вручную или автоматизированно выполнить single-rule MT5 compile/run:

1. Сгенерировать или подтвердить MT5 `Nero.csv` parity.
2. Сгенерировать `mt5_entry_signals_<run_id>.csv` через `ML/baseline/export_mt5_entry_signals.py`, положить его в MT5 tester `Files` как `mt5_entry_signals.csv` и запустить с `InpMT5_DiagnosticExecutor=true`.
3. Вернуть `mt5_trade_events.csv`.
4. Запустить `ML/baseline/parse_mt5_execution_report.py` и сверить events/deals.

Batch selection 20-50 кандидатов разрешён только после успешного single-rule прототипа и понятного producer parity статуса.

## Related Materials

- `docs/reports/2026-07-29-mt5-feasibility.md`
- `docs/reports/2026-07-29-mt5-manual-tester-runbook.md`
- `docs/reports/2026-07-29-mt5-batch-selection-design.md`
- `ML/reports/mt5_execution_loop/mt5_environment_manifest.json`
- `ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json`
- `ML/reports/mt5_execution_loop/manual_run_manifest_template.json`
- `ML/reports/mt5_execution_loop/batch_selection_contract.json`
