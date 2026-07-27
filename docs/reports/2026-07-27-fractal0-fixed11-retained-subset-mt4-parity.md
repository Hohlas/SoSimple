# Fractal0 Fixed11 Retained Subset MT4 Parity

> **Дата**: 2026-07-27
> **Статус**: Completed
> **Вердикт**: UNKNOWN
> **Stage decision**: parity_blocked
> **Цель**: Проверить, что MT4/tester исполняет retained subset так же, как Python fixed11 contract, или честно зафиксировать blocker.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`

## Context

Этап проверял только 5 retained fixed11 rules из `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`.

Это не новый отбор правил. Не менялись rules, cutoffs, profiles, models, targets, filters, entries, exits, stops, spread, fill policy и PnL convention.

Python contract заморожен в `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`:

- `stop_policy_id = S2_fractal0_buffer_0_5_entry_floor_2`
- `entry_id = E3_open_pullback_1_0atr`
- `mask_id = M0_no_mask`
- `exit_id = X2_ml_opposite_any_p0_50`
- `spread = 0.20`
- execution OHLC: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`

## Уровень этапа

Проверочный parity-gate после locked-test, candidate audit и mutual-correlation pruning.

`locked_test` использовался только для воспроизведения уже принятых 5 правил и проверки возможности экспорта/исполнения. Новый winner или новый cutoff не выбирался.

## Methodology

Применены:

- `docs/methodology/13-export-mt4-parity.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/DATA_FLOW.md`

По методике статус `UNKNOWN` считается блокирующим до доказательства обратного. Поэтому при недоказанном MT4 contract export/tester/reconciliation не запускались.

## What Was Done

1. Проверен retained subset: ровно 5 правил из pruning artifact.
2. Проверена форма trade stream по `signal_time`, `fill_time`, `side`, `rule_id`.
3. Проверен Python fixed11 execution contract.
4. Проверены MT4 runtime sources: `MT/MQL4/Experts/$o$imple.mq4`, `MT/tester/$o$imple.ini`, `MT/MQL4/Files/#.csv`, `MT/tester/opt.set`, `docs/MT/trading_strategy.md`, `docs/MT/ml_signal_integration.md`.
5. Созданы freeze/feasibility artifacts.
6. Экспорт остановлен, потому что текущий MT4 runtime не доказал честное исполнение пяти правил без потери `rule_id` и без схлопывания дублей времени.

## Multiple Testing Context

Новый search не выполнялся.

Scope фиксирован:

- input rules: 5 retained rules;
- source selection: previous pruning only;
- new choices: none;
- maximum verdict for this stage without proven MT4 match: `UNKNOWN`.

## Changed Files

- `ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json`
- `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Verification

Команды:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

retained_path = Path("ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json")
trades_path = Path("ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv")
retained = [r["rule_id"] for r in json.loads(retained_path.read_text(encoding="utf-8"))["rules"] if r["decision"] == "RETAIN"]
df = pd.read_csv(trades_path, sep=";")
sub = df[df["rule_id"].isin(retained)].copy()
sub["direction"] = sub["side"].map({"BUY": 1, "SELL": -1})
by_time = sub.groupby("signal_time").agg(rows=("rule_id", "size"), directions=("direction", lambda s: len(set(s))))
print(len(sub), sub["signal_time"].nunique(), sub[["signal_time", "direction"]].drop_duplicates().shape[0], int((by_time["rows"] > 1).sum()), int((by_time["directions"] > 1).sum()))
PY
```

Result: `6177 2806 2827 1670 21`.

```bash
./.venv/bin/python -m json.tool ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json
./.venv/bin/python -m json.tool ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json
```

Result: both JSON files are valid.

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json").read_text(encoding="utf-8"))
print(data["feasibility_decision"])
assert data["feasibility_decision"] in {"parity_feasible", "parity_blocked"}
if data["feasibility_decision"] == "parity_blocked":
    raise SystemExit(2)
PY
```

Result: `parity_blocked`, exit code `2`; export/tester stopped as planned.

## Results

Stage decision: `parity_blocked`.

Причины:

- retained stream has `6177` trades but only `2806` unique `signal_time`;
- `1670` signal-time groups have duplicate rows;
- `21` signal-time groups have opposite directions;
- plain `time;signal` would lose `rule_id` and collapse rows by time;
- current MT4 `iSignal=3` direct mode is documented as next-bar CSV execution with `ML_HoldBars`/TP/back-stop/reversal settings, not as proven Python fixed11 `E3/S2/X2/spread=0.20` execution.

No `ml_signals.csv` export was produced. No MT4 tester run was started. No reconciliation report was produced.

## MT4 Manual Tester Patch

После ручной компиляции MT4 был найден runtime blocker: при `BackTest=1`
эксперт падал на чтении параметров, потому что `INPUT_FILE_READ()` считает
первую рабочую строку как `BackTest=2`, а строки `INFO` должны содержать
пробел и дефис. Исправлено:

- `BackTest=2..6` теперь выбирает пять retained rules;
- `INFO` в `#.csv` содержит диапазон дат `2025.11.14-2026.05.11`;
- созданы `ml_signals_fixed11_rule01.csv` ... `ml_signals_fixed11_rule05.csv`
  в `MT/MQL4/Files/` и `MT/tester/files/`;
- `MLP NO_SIGNAL` выключен по умолчанию через `ML_LogNoSignal=false`, потому
  что это отладочная запись для баров без сигнала, а не ошибка;
- summary экспорта сохранён в
  `ML/reports/fractal0_fixed11_retained_mt4_parity/fixed11_rule_signal_exports.json`.

Этот patch нужен для ручного запуска MT4 tester. Он не меняет вердикт
`parity_blocked`: текущий per-rule файл `time;signal;atr;stop` всё ещё не сохраняет
`rule_id` внутри одной общей retained-корзины, а одновременные противоположные
сигналы внутри одного правила не представимы одной строкой. Политика экспорта
консервативная: одинаковые направления на одном времени схлопываются в одну
строку, противоположные направления на одном времени не экспортируются.

Экспортированные строки:

| Slot | BackTest | Rule | Source rows | Exported rows | Opposite-time groups omitted |
|---:|---:|---|---:|---:|---:|
| 1 | 2 | `rank05_time_only_linear_target_entry_avoid_sl_top30` | 1196 | 1137 | 10 |
| 2 | 3 | `rank02_time_only_linear_target_entry_ev_regression_top40` | 1782 | 1708 | 11 |
| 3 | 4 | `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50` | 693 | 662 | 4 |
| 4 | 5 | `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50` | 2265 | 2166 | 17 |
| 5 | 6 | `rank10_movement_plus_time_linear_target_entry_ev_regression_top50` | 241 | 231 | 0 |

## MT4 Tester Diagnostic Finding

После ручного запуска tester для rule slot 1 сигналы начали читаться, но сделки
не совпали с Python trade stream. Подтверждённые причины:

- `ML_MaxPositions=1` открывал только одну позицию и блокировал большую часть
  сигналов: в логе было `Position blocked: 687 (60.5%)`;
- `ML_AllowReversal=0` отключал закрытие по обратному сигналу, хотя Python
  contract использует `exit_id = X2_ml_opposite_any_p0_50`;
- `ML_Trade_Events` для закрытий писал `signal_time=1970.01.01 00:00`, поэтому
  закрытия нельзя было надежно связать с исходной строкой сигнала.

Исправления для повторного ручного tester-прогона:

- в `#.csv` и `MT/tester/$o$imple.ini` для retained slots выставлено
  `ML_MaxPositions=20` и `ML_AllowReversal=1`;
- multi-position режим теперь закрывает BUY на новом `signal=-1` и SELL на
  новом `signal=1` с причиной `ReverseSignal`;
- при открытии ордера эксперт пишет `signal_time` в comment, а при закрытии
  переносит его в `ML_Trade_Events`.

Второй runtime patch исправил грубое несоответствие входа: fixed11 retained
multi-position ветка больше не открывает market-order сразу. Она ставит
`OP_BUYLIMIT` / `OP_SELLLIMIT` по правилу `E3_open_pullback_1_0atr`:

- BUY: `limit = calculation_open - atr`;
- SELL: `limit = calculation_open + atr`;
- `calculation_open = Open[0]` на баре постановки заявки;
- срок жизни pending order покрывает `6` проверяемых баров после бара расчёта;
- `atr` берётся из третьей колонки fixed11 signal CSV;
- `stop` берётся из четвёртой колонки fixed11 signal CSV как Python
  `protective_stop_price`.

В MT4 log и `ML_Trade_Events` добавлена строка `ORDER_PLACED` с
`signal_time`, `order_time`, `expires`, `calculation_open`, `requested_price`,
`atr`, `stop_source`, `Val`, `Stp` и `Prf`. Реальный `OPEN` пишется отдельно
после того, как tester исполнит pending order, и повторяет исходные
`calculation_open`, `requested_price`, `atr` и `signal_time` поставленной заявки.

Это всё ещё diagnostic run, а не доказанный full parity, пока новый tester run
после recompilation не подтвердит совпадение `signal_time + direction +
fill_time`.

Ручной tester-прогон rule slot 1 после limit-order patch:

- `MLP_INIT`: loaded `1137` rows from `ml_signals_fixed11_rule01.csv`;
- `Total signals: 1136`;
- `ORDER_PLACED`: `1136`;
- `Opened: 890 (BUY=378 SELL=512)`;
- `deleted due expiration`: `246`;
- `Position blocked: 0`;
- `Timeout closes: 412`;
- `Reverse closes: 478`;
- `OPEN_FAILED`, `Cannot open`, `array out of range`: `0`;
- `ORDER_PLACED` formula check passed: no violations of
  `BUY=calculation_open-atr`, `SELL=calculation_open+atr`.

Remaining confirmed mismatches after that run:

- Python rule01 source has `1196` trades, export has `1137` rows, MT4 opened
  `890` trades;
- `20` Python `signal_time + direction` keys are absent from export because
  they are opposite-direction duplicate-time groups that cannot be represented
  by one `time;signal` row;
- same-direction duplicate-time rows are collapsed into one MT4 row;
- `246` pending orders expired because expiration ended before the last Python
  eligible fill bar;
- MT4 stop used fallback `ML_BackStopATR=50`, while Python uses `S2`
  `protective_stop_price`;
- some `OPEN` rows had polluted `entry_time` because order-counting inside log
  output changed the selected MT4 order before all fields were read.

Follow-up patch after this run:

- fixed11 CSV files were regenerated as `time;signal;atr;stop`;
- `lib_ML_Signal.mqh` reads `stop` and passes it to `OrderSend`;
- pending expiration covers the six Python fill-check bars after the
  calculation bar;
- `OPEN` logging caches `entry_time`, lot and open-position count before any
  helper that can change the selected MT4 order.

Ручной tester-прогон rule slot 1 after `time;signal;atr;stop` patch:

- `TestGenerator: spread set to 100`;
- event CSV spread: `1.00` on `ORDER_PLACED` / `OPEN` / `CLOSE`;
- Python fixed11 contract spread: `0.20`;
- `ORDER_PLACED`: `1136`;
- closed tickets: `937`;
- explicit `OPEN` rows: `914`;
- `23` tickets closed inside one H1 bar before the runtime could log a live
  market order;
- close reasons: `StopLoss=448`, `ReverseSignal=312`, `Timeout=177`;
- `OPEN_FAILED`, `Cannot open`, `array out of range`: `0`;
- `ORDER_PLACED` formula check passed: no violations of
  `BUY=calculation_open-atr`, `SELL=calculation_open+atr`.

This run is not a valid fixed11 parity run because tester spread was `1.00`, not
the frozen Python `0.20`. It is useful only as a runtime smoke test showing that
limit orders and CSV stops are now active.

Follow-up patch after this run:

- broker-history closes now write a missing `OPEN` row first when a pending order
  opened and closed between two H1 runtime calls;
- fixed11 runtime now prints `MLP SPREAD_MISMATCH` once when `Ask-Bid` differs
  from expected `0.20`.

Ручной tester-прогон rule slot 1 after spread/history-open patch:

- `TestGenerator: spread set to 20`, event CSV spread is `0.20` on
  `ORDER_PLACED` / `OPEN` / `CLOSE`;
- `MLP SPREAD_MISMATCH`: `0`;
- `MLP_INIT`: loaded `1137` rows from `ml_signals_fixed11_rule01.csv`;
- `ORDER_PLACED`: `1136`;
- `OPEN`: `981`;
- `CLOSE`: `981`;
- `deleted due expiration`: `155`;
- `broker_history_missing_open`: `22`;
- `OPEN_FAILED`, `Cannot open`, `array out of range`: `0`;
- close reasons: `StopLoss=442`, `ReverseSignal=340`, `Timeout=199`;
- `ORDER_PLACED` formula check passed: no violations of
  `BUY=calculation_open-atr`, `SELL=calculation_open+atr`.

Reconciliation against Python export-shape rows for rule slot 1:

- Python source rows for rule01: `1196`;
- export-shape rows after duplicate policy: `1137`;
- MT4 closed trades: `981`;
- matched by `direction + signal_time + entry price`: `981`;
- Python-only rows: `156`;
- MT4-only rows: `0`;
- same H1 fill bucket on matched trades: `695`;
- different H1 fill bucket on matched trades: `286`;
- Python-only rows by Python close reason: `ML_CLOSE=104`, `TIME=48`,
  `SL=4`;
- matched close reason cross-check:
  `ML_CLOSE->StopLoss=415`, `ML_CLOSE->ReverseSignal=184`,
  `ML_CLOSE->Timeout=114`, `TIME->ReverseSignal=154`,
  `TIME->Timeout=85`, `TIME->StopLoss=1`, `SL->StopLoss=26`,
  `SL->ReverseSignal=2`.

Confirmed remaining mismatches after this run:

- expiration boundary: example ticket `24` was placed for signal
  `2023-01-04 22:00`, BUY, `calculation_open=1855.34`, `atr=4.20`,
  `requested_price=1851.14`, `expires=2023-01-05 06:00`; MT4 deleted it at
  `2023-01-05 06:02:30`, while the Python source row has
  `fill_time=2023-01-05 06:00:00`;
- exit logic: Python rule01 uses `X2_ml_opposite_any_p0_50`, a separate
  ML-score exit per open position and `bars_since_fill`; current MT4 diagnostic
  closes on opposite entry signals from the entry CSV, which is not the same
  signal stream.

Follow-up patch after this run:

- pending expiration now keeps one extra H1 guard bar after the Python
  fill-window, because MT4 deletes pending orders at the exact `expiration`
  timestamp.

## Split Disclosure

Inherited locked-test interval:

- `locked_test_min_time = 2022-12-02 11:00:00`
- `locked_test_max_time = 2026-06-04 12:00:00`

Source: `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`.

## Limitations / Open Questions

- MT4 can still be used, but not through one plain `time;signal` file for all 5 retained rules.
- MT4 now implements `E3_open_pullback_1_0atr`, reads the Python `S2` stop from
  CSV and has a valid `spread=0.20` tester run for rule slot 1, but exact parity
  is still not proven because expiration needed a post-run boundary patch and
  `X2_ml_opposite_any_p0_50` is not represented by the current MT4 exit stream.
- `parity_blocked` is not a failure of the 5 retained rules; it is a runtime/export mismatch that blocks honest parity.

## Conclusions

MT4/tester parity for the retained subset is not proven.

The correct project status is `UNKNOWN / parity_blocked`, because the current runtime/export route cannot honestly preserve the five-rule trade stream and cannot be assumed to execute the same Python contract.

Parity is not proof of profitability even after it is implemented.

## Next Step

Next actions:

- recompile MT4 and rerun rule slot 1 with the extra expiration guard;
- compare `deleted due expiration`, `OPEN/CLOSE`, and fill buckets again;
- then implement/export the real `X2_ml_opposite_any_p0_50` close stream if
  exact Python-vs-MT4 parity is still required.

Stress-spread disclosure and model card remain blocked until retained-subset MT4 parity is either passed or explicitly replaced by a documented lower-status diagnostic.

## Related Materials

- `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json`
- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`
- `docs/MT/trading_strategy.md`
- `docs/MT/ml_signal_integration.md`
