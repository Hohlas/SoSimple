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
`parity_blocked`: текущий файл `time;signal` всё ещё не сохраняет `rule_id`,
а одновременные противоположные сигналы внутри одного правила не
представимы одной строкой. Политика экспорта консервативная:
одинаковые направления на одном времени схлопываются в одну строку,
противоположные направления на одном времени не экспортируются.

Экспортированные строки:

| Slot | BackTest | Rule | Source rows | Exported rows | Opposite-time groups omitted |
|---:|---:|---|---:|---:|---:|
| 1 | 2 | `rank05_time_only_linear_target_entry_avoid_sl_top30` | 1196 | 1137 | 10 |
| 2 | 3 | `rank02_time_only_linear_target_entry_ev_regression_top40` | 1782 | 1708 | 11 |
| 3 | 4 | `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50` | 693 | 662 | 4 |
| 4 | 5 | `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50` | 2265 | 2166 | 17 |
| 5 | 6 | `rank10_movement_plus_time_linear_target_entry_ev_regression_top50` | 241 | 231 | 0 |

## Split Disclosure

Inherited locked-test interval:

- `locked_test_min_time = 2022-12-02 11:00:00`
- `locked_test_max_time = 2026-06-04 12:00:00`

Source: `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`.

## Limitations / Open Questions

- MT4 can still be used, but not through one plain `time;signal` file for all 5 retained rules.
- It is still unknown whether current MT4 can exactly reproduce `E3_open_pullback_1_0atr`, `S2_fractal0_buffer_0_5_entry_floor_2`, `X2_ml_opposite_any_p0_50` and spread `0.20`.
- `parity_blocked` is not a failure of the 5 retained rules; it is a runtime/export mismatch that blocks honest parity.

## Conclusions

MT4/tester parity for the retained subset is not proven.

The correct project status is `UNKNOWN / parity_blocked`, because the current runtime/export route cannot honestly preserve the five-rule trade stream and cannot be assumed to execute the same Python contract.

Parity is not proof of profitability even after it is implemented.

## Next Step

Choose one honest next mode:

- run separate per-rule MT4 exports and tester runs, if each per-rule stream has no duplicate/opposite time problem and the runtime contract is acceptable;
- implement a new MT4 runtime/export that preserves `rule_id` and fixed11 execution contract;
- run only a weaker aggregate signal-reading diagnostic and mark it `DIAGNOSTIC_ONLY`, not fixed11 trade parity.

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
