# Fractal0 Fixed11 Retained Subset MT4 Parity

> **Дата**: 2026-07-27
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Stage decision**: parity_in_progress
> **Цель**: приблизить MT4/tester исполнение retained fixed11 rule slot 1 к замороженному Python fixed11 contract и зафиксировать оставшиеся расхождения.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`

## Context

Этап относится к 5 retained fixed11 rules из `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`.

Это не новый отбор правил. Не менялись rules, cutoffs, profiles, models, targets, filters, stop policy, entry rule, exit rule, spread или PnL convention.

Python contract заморожен в `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`:

- `stop_policy_id = S2_fractal0_buffer_0_5_entry_floor_2`
- `entry_id = E3_open_pullback_1_0atr`
- `mask_id = M0_no_mask`
- `exit_id = X2_ml_opposite_any_p0_50`
- `spread = 0.20`
- H1 OHLC: `DATA/XAUUSD_H1_OHLC.csv`
- execution OHLC: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`

Проверка выполнялась вручную через MT4 Strategy Tester. Агент не может сам компилировать MQL4 и запускать tester.

## Уровень этапа

Проверочный parity-gate после locked-test, candidate audit и mutual-correlation pruning.

`locked_test` использовался только для воспроизведения уже выбранных правил и диагностики совпадения Python/MT4. Новый winner или cutoff не выбирался.

## What Was Done

1. Для retained slots добавлены отдельные MT4 signal files `ml_signals_fixed11_rule01..05.csv` в формате `time;signal;atr;stop`.
2. MT4 fixed11 multi-position route переведён с входа по рынку на `E3_open_pullback_1_0atr`:
   - BUY requested price = `calculation_open - ATR`;
   - SELL requested price = `calculation_open + ATR`;
   - `stop` берётся из CSV как Python `protective_stop_price`.
3. Постановка лимитки сдвинута так, чтобы MT4 начинал ловить fill с того же H1-бара, что Python.
4. Если к моменту постановки лимитный уровень уже пройден, MT4 открывает market order по фактической текущей цене и логирует это как `MARKET_AFTER_LIMIT_PASSED`.
5. Если после такого входа CSV-stop становится невалидным для MT4, сделка пропускается с причиной `MarketAfterLimitPassedStopInvalid`.
6. Для retained slots добавлены отдельные exit files `ml_exits_fixed11_rule01..05.csv` в формате `signal_time;exit_time`.
7. MT4 теперь закрывает позицию по `MLClose`, когда для её `signal_time` наступает Python `exit_time`.
8. Сырой выход по обратному entry-сигналу отключён для fixed11 parity settings: `ML_AllowReversal=0`.
9. В `ML_Trade_Events` и runtime logs добавлены поля/события для сверки: `ORDER_PLACED`, `OPEN`, `CLOSE`, `calculation_open`, `requested_price`, фактическая цена ордера, stop, spread и `signal_time`.

## Multiple Testing Context

Новый search не выполнялся.

Scope фиксирован:

- input rules: 5 retained rules;
- tester run: только rule slot 1 / `ML_RuleSlot=1`;
- source selection: previous pruning only;
- new choices: none;
- allowed maximum verdict for this diagnostic stage: `DIAGNOSTIC_ONLY`.

Запрещённая интерпретация: свежий положительный MT4 PnL не является доказательством live-ready торговой системы. Это диагностический результат одного rule slot после ручной MT4-сверки.

## Changed Files

- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `MT/MQL4/Files/#.csv`
- `MT/tester/files/#.csv`
- `MT/tester/$o$imple.ini`
- `MT/MQL4/Files/ml_signals_fixed11_rule01.csv` ... `ml_signals_fixed11_rule05.csv`
- `MT/tester/files/ml_signals_fixed11_rule01.csv` ... `ml_signals_fixed11_rule05.csv`
- `MT/MQL4/Files/ml_exits_fixed11_rule01.csv` ... `ml_exits_fixed11_rule05.csv`
- `MT/tester/files/ml_exits_fixed11_rule01.csv` ... `ml_exits_fixed11_rule05.csv`
- `tests/test_mql_telemetry_params_csv_contract.py`

## Verification

Targeted pytest:

```bash
./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q
```

Result:

```text
28 passed in 0.10s
```

Fresh MT4 tester event artifact:

```text
MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv
```

Примечание от 2026-07-29: этот path является перезаписываемым tester output.
Текущий файл уже относится к более позднему stale-handling прогону и не
воспроизводит числа ниже. Для актуального файла см.
`docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md` и
`ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`.
Старый snapshot этого прогона не был сохранён отдельным immutable path, поэтому
числа ниже являются исторической записью отчёта, а не свежей проверкой текущего
CSV.

Manual summary command used after tester run:

```bash
./.venv/bin/python - <<'PY'
import csv, collections
p = "MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv"
counts = collections.Counter()
reasons = collections.Counter()
placed = collections.Counter()
profit = 0.0
with open(p, newline="") as f:
    for row in csv.DictReader(f, delimiter=";"):
        counts[row["event"]] += 1
        if row["event"] == "ORDER_PLACED":
            rp = float(row["requested_price"] or 0)
            op = float(row["order_open_price"] or 0)
            placed["market_after_limit_passed" if op and abs(op - rp) > 0.011 else "limit"] += 1
        if row["event"] == "CLOSE":
            reasons[row["reason"]] += 1
            profit += float(row["profit"] or 0)
print(counts)
print(placed)
print(reasons)
print(round(profit, 2))
PY
```

Result:

```text
events: ORDER_PLACED=1132, OPEN=1072, CLOSE=1072, OPEN_FAILED=5
placed: limit=1024, market_after_limit_passed=108
close reasons: MLClose=826, Timeout=223, StopLoss=23
profit sum: 62238.59
OPEN_FAILED: 5, all MarketAfterLimitPassedStopInvalid
```

## Results

Fresh rule slot 1 MT4 tester result after implementing Python-like exits:

| Metric | Value |
|---|---:|
| ORDER_PLACED | 1132 |
| OPEN | 1072 |
| CLOSE | 1072 |
| OPEN_FAILED | 5 |
| Limit orders filled normally | 1024 |
| Market-after-limit-passed opens | 108 |
| MLClose closes | 826 |
| Timeout closes | 223 |
| StopLoss closes | 23 |
| Closed profit sum | 62238.59 |

The five failed opens are now explicit and expected:

- `2023.05.03 22:00` SELL
- `2023.10.06 21:00` SELL
- `2025.05.12 08:00` BUY
- `2025.08.26 01:00` SELL
- `2026.03.23 01:00` BUY

All five failed because `MARKET_AFTER_LIMIT_PASSED` would require a stop on the invalid side of the market order.

Rule slot 1 reconciliation against Python `rank05_time_only_linear_target_entry_avoid_sl_top30`:

```text
Python filled rows for rule: 1196
MT4 closes: 1072
matched unique signal_time+direction: 1015
duplicate Python signal_time+direction groups: 57
OPEN_FAILED: 5
```

Close reason cross-check on unique matches:

```text
Python ML_CLOSE -> MT4 MLClose: 761
Python TIME     -> MT4 Timeout: 217
Python TIME     -> MT4 MLClose: 30
Python SL       -> MT4 MLClose: 6
Python ML_CLOSE -> MT4 StopLoss: 1
```

R-sum on unique matches:

```text
limit entries:  Python +316.07 R, MT4 +290.36 R
market-after-limit-passed entries: Python +16.69 R, MT4 +34.91 R
```

## Conclusions

The main confirmed mismatch was exit logic, not stop price calculation.

The previous MT4 diagnostic runs made while fixing the expert are superseded by
the fresh `MLClose` run above. They must not be used as current parity evidence.
Their only retained value is the root-cause finding: without exported Python
exit times, MT4 kept positions open after Python had already exited by
`X2_ml_opposite_any_p0_50`; those positions then often reached StopLoss or
closed on raw reverse entry signals.

Обновление после отчёта, 2026-07-29: оптимистичная интерпретация этого прогона
заменена анализом `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`.
Свежий MT4 PnL и вывод "parity is now much closer" нельзя использовать как
актуальное доказательство parity. Поздний анализ показал, что rule slot 1 всё
ещё имеет существенный fill mismatch, а Python runner может записывать
`ML_CLOSE` на тот же H1 timestamp, что и fill, даже когда M5 показывает первое
касание лимитки позже внутри этого часа.

Этап остаётся `DIAGNOSTIC_ONLY`, не `PASS`. Текущий blocker уже не только
one-bar `MLClose` timing в MQL4; blocker теперь в Python/MT4 execution contract
для хронологии fill и same-H1-bar ML exits.

## Limitations / Open Questions

- `MLClose` timing is still shifted: `798` of `1015` uniquely matched rows have MT4 exit time different from Python exit time, usually one H1 bar later.
- The current tester run covers only `ML_RuleSlot=1`; slots 2-5 have not yet been manually compiled/run/reconciled after the exit-file patch.
- Duplicate `signal_time + direction` groups remain in the Python source; MT4 per-rule `time;signal` export collapses same-direction duplicates.
- `MARKET_AFTER_LIMIT_PASSED` intentionally gives MT4 a different entry price than Python when the limit level was already crossed before order placement.
- Live use of `ml_exits_fixed11_ruleNN.csv` requires a real-time Python process that computes exit decisions after each closed H1 bar. The current exit files were produced from locked-test Python results and are only for tester parity diagnostics.

## Split Disclosure

Inherited locked-test interval:

- `locked_test_min_time = 2022-12-02 11:00:00`
- `locked_test_max_time = 2026-06-04 12:00:00`

Source: `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`.

Split role:

- `locked_test` was not used for new winner/cutoff selection in this stage.
- It was used to reproduce frozen retained rules and diagnose Python-vs-MT4 execution parity.

## Next Step

Обновление после отчёта, 2026-07-29: следующий шаг ниже заменён. Не продолжать
только подстройкой MQL4 `MLClose` timing.

Актуальный следующий шаг:

1. Исправить или перепроектировать Python execution contract так, чтобы fill и
   same-H1-bar `MLClose` decisions сохраняли хронологический порядок.
2. Пересчитать Python locked-test artifacts после исправления execution
   contract.
3. Заново сгенерировать fixed11 MT4 signal/exit exports из исправленного
   Python output.
4. Перезапустить MT4 rule slot 1 и снова сверить fill time, exit time, close
   reasons и R-sum.
5. Только после приемлемого slot 1 повторять tester/reconciliation loop для
   retained slots 2-5.

Stress-spread disclosure and model card remain blocked until retained-subset MT4 parity is either passed or explicitly replaced by a lower-status documented diagnostic.

## Related Materials

- `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/fixed11_rule_signal_exports.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`
