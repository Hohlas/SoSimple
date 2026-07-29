# Fixed11 Python/MT4 Fill Chronology Analysis

> **Дата**: 2026-07-29
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: зафиксировать проблему расхождения fill между Python и MT4 и проверить, соблюдает ли Python-runner хронологию событий внутри H1-бара при наличии M5 execution OHLC.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`

## Context

Анализ продолжает parity-разбор retained fixed11 rule slot 1:

- MT4 event artifact: `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv`;
- Python trades artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`;
- Python run metadata: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`;
- H1 OHLC: `DATA/XAUUSD_H1_OHLC.csv`;
- M5 execution OHLC: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`;
- MT4 tester history checked manually from `XAUUSD60.hst`, `XAUUSD5.hst`, `XAUUSD1.hst`;
- inspected runner: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`.

Перед этим MT4 был изменён так, чтобы ставить лимитные ордера по Python-правилу
`E3_open_pullback_1_0atr` и читать экспортированные Python-времена
`MLClose`. После этого MT4 PnL стал слишком оптимистичным, поэтому отдельная
проверка была посвящена честности хронологии исполнения между Python и MT4.

## Уровень этапа

Проверочный parity/debug этап. Новый ML-search, новый отбор rules, cutoffs,
profiles, models, targets, filters, stops, entry/exit policies или spreads не
выполнялись.

Максимально допустимый вердикт: `DIAGNOSTIC_ONLY`.

## What Was Done

1. Проверено, как Python использует `execution_ohlc_path`.
2. Проверено, используется ли M5 для времени исполнения лимитки и порядка
   `MLClose`.
3. Сравнены сделки Python rule slot 1 с MT4 event log по
   `signal_time + direction`.
4. Классифицированы `StalePendingAfterMLClose` и
   `StaleFillAfterMLClose`.
5. Сравнён Python H1 OHLC с текущей H1-историей MT4 tester.
6. Проверено распределение Python PnL по `hold_bars`.
7. Собраны наглядные примеры, где Python записывает fill и `MLClose` на один
   H1 timestamp, а M5 показывает, что лимитка впервые была задета позже внутри
   этого H1-часа.

## Multiple Testing Context

Новый выбор модели или правила не выполнялся.

Текущий search budget:

- rules tested: только существующий retained rule slot 1;
- new models: 0;
- new feature profiles: 0;
- new thresholds: 0;
- new entry/exit policies: 0;
- new spreads: 0.

Накопленный контекст: этот анализ проверяет уже выбранный locked-test candidate
path. Он не подтверждает прибыльность и не должен использоваться как новое
правило выбора winner.

Запрещённая интерпретация: не считать свежий MT4 PnL после stale handling
доказательством, что система готова к live или прибыльна.

## Changed Files

- `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`

Код и CSV-артефакты этим анализом не менялись.

## Verification

Использованные команды:

```bash
rg -n "execution_ohlc|_resolve_same_bar_with_execution_ohlc|simulate_trade\\(|build_entry_rows|fill_time|exit_time|first_exit_execution_time|M5" \
  ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  ML/reports/fractal0_fixed11_rich_entry_locked_test.json \
  docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md
```

```bash
./.venv/bin/python - <<'PY'
# CSV/HST reconciliation scripts запускались inline, чтобы посчитать stale
# categories, сравнить H1 CSV vs MT4 HST, проверить первое касание по M1/M5
# и разложить Python PnL по hold_bars. Эти скрипты не меняли файлы проекта.
PY
```

Полный project pytest намеренно не запускался: это была документационная и
диагностическая проверка, а не изменение кода. Кроме того, проектное правило
запрещает запускать `./.venv/bin/python -m pytest tests/ -q` для этого
workflow.

## Results

### Использование M5 в Python runner

Python metadata содержит:

```text
execution_ohlc_path = MT/MQL4/Files/XAUUSD_M5_OHLC.csv
```

Но runner записывает режим использования так:

```text
execution_ohlc_usage = resolve_same_h1_bar_tp_sl_order_only
```

Источник: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, JSON writer around
`pnl_convention`.

Это значит, что M5 используется только для разрешения порядка SL/TP, когда оба
уровня задеты внутри одного H1-бара. M5 не используется для точного timestamp
исполнения лимитки и не используется, чтобы доказать, что `MLClose` произошёл
после fill внутри того же H1-бара.

Факты по коду:

- `_resolve_same_bar_with_execution_ohlc(...)` проверяет M5 только для
  `stop_hit` и `tp_hit`;
- `simulate_trade(...)` начинает симуляцию выхода с `fill_index`;
- `build_exit_decision_rows(...)` начинает ML-exit decision rows с
  `idx = fill_index`;
- `decision_time` получает H1 timestamp, а не M5 timestamp.

### Stale-категории против Python

Свежий MT4 slot 1 event log после stale handling:

```text
ORDER_PLACED=1115
OPEN=717
CLOSE=717
OPEN_FAILED=404
```

Основные stale-категории:

| Category | Count | Python PnL по тем же signal keys |
|---|---:|---:|
| `StalePendingAfterMLClose` | 324 | `-63.592028R` |
| `StaleFillAfterMLClose` | 66 | `-19.812954R` |

Это объясняет, почему свежий MT4 PnL выглядел подозрительно хорошим: многие
короткие убыточные Python-сделки в MT4 либо пропущены как pending deletions,
либо закрыты как stale fills. Причина не обязательно в том, что MT4 выбирает
сделки по будущему PnL; подтверждённая причина в том, что Python и MT4 не имеют
хронологически одинакового контракта fill и выхода внутри одного H1-бара.

### Python H1 против текущей истории MT4 tester

Сравнение `DATA/XAUUSD_H1_OHLC.csv` с текущим MT4 `XAUUSD60.hst` показало:

```text
2004-2022: точное совпадение для проверенных H1 rows
2023: 1984 крупных отличия
2024: 4046 крупных отличий
2025: 4008 крупных отличий
2026: 2549+ крупных отличий
```

Проверка offset не показала сдвиг timezone. Лучшее совпадение при offset `0`.

Интерпретация: с 2023 года Python locked-test OHLC и текущая история MT4 tester
существенно отличаются. Это объясняет часть fill mismatch, особенно случаи,
где Python говорит, что fill был, а текущая MT4 H1/M5/M1 история не подтверждает
касание цены.

### Python PnL по hold_bars

Для Python rule `rank05_time_only_linear_target_entry_avoid_sl_top30`:

| hold_bars bucket | n | sum PnL R | mean R | PF |
|---|---:|---:|---:|---:|
| `0` | 406 | `-113.0071` | `-0.2783` | `0.0481` |
| `1` | 85 | `-10.9074` | `-0.1283` | `0.2293` |
| `2` | 60 | `-3.7852` | `-0.0631` | `0.4537` |
| `3..5` | 121 | `+4.1459` | `+0.0343` | `1.4775` |
| `>5` | 524 | `+518.5808` | `+0.9897` | `22.9780` |

Для `hold_bars=0`:

```text
ML_CLOSE=374, sum=-81.0071R
SL=32, sum=-32.0000R
```

Это поддерживает гипотезу, что очень короткие сделки системно плохие в текущей
Python-симуляции. Но это ещё не доказывает рабочее delayed-entry правило,
потому что такое правило нужно тестировать только после исправления execution
contract.

### Наглядные нарушения хронологии

Критичная проблема не в самом факте `fill_time == exit_time`. Открытие и
закрытие в одном H1-баре допустимы, если M5 доказывает правильный порядок
событий.

Проблема в том, что Python хранит H1 timestamps и для fill, и для `MLClose`, а
M5 показывает, что первое касание лимитки происходит позже внутри этого же
часа.

Пример 1:

| Поле | Значение |
|---|---|
| `signal_time` | `2022-12-05 23:00:00` |
| side | `SELL` |
| Python `fill_time` | `2022-12-06 03:00:00` |
| Python `exit_time` | `2022-12-06 03:00:00` |
| limit | `1772.28` |
| первое M5-касание лимитки | `2022-12-06 03:10` |
| Python close reason | `ML_CLOSE` |
| Python PnL | `-0.3085365853658486R` |

Проблема хронологии: Python записывает `MLClose` в `03:00`, но M5 показывает,
что сделка не могла исполниться раньше `03:10`.

Пример 2:

| Поле | Значение |
|---|---|
| `signal_time` | `2022-12-14 22:00:00` |
| side | `BUY` |
| Python `fill_time` | `2022-12-15 03:00:00` |
| Python `exit_time` | `2022-12-15 03:00:00` |
| limit | `1802.05` |
| первое M5-касание лимитки | `2022-12-15 03:15` |
| Python close reason | `ML_CLOSE` |
| Python PnL | `-0.3793478260869556R` |

Проблема хронологии: `MLClose` timestamp равен открытию H1, а M5 показывает,
что вход произошёл только в `03:15`.

Агрегатная проверка Python-сделок `hold_bars=0` + `ML_CLOSE`:

```text
total = 374
first M5 limit touch after H1 open = 172
first M5 limit touch at H1 open = 64
M5 no hit = 138
```

Группа `M5 no hit` частично объясняется найденным рассинхроном истории между
locked Python H1 data и текущими данными MT4/tester.

## Conclusions

Предыдущее предположение "M5 execution OHLC защищает хронологию внутри одного
H1" неверно для `MLClose`. В текущем runner M5 защищает только порядок SL/TP
внутри одного H1-бара.

Python locked-test result для текущего fixed11 path получает статус
`DIAGNOSTIC_ONLY` в части исполнения. Его нельзя считать надёжным
доказательством прибыльности, пока не исправлена хронология fill и same-H1
`MLClose`, а locked-test artifacts не пересчитаны.

Свежий MT4 result также `DIAGNOSTIC_ONLY`. Его высокий PnL объясняется
сочетанием факторов:

- skipped/stale короткие Python-сделки;
- рассинхрон Python/MT4 history с 2023 года;
- Python same-H1 `MLClose` timestamps, которые не сохраняют M5-порядок.

Не доказано, что MT4 "выбирает хорошие сделки" по будущему PnL.
Подтверждённая проблема: сломан или неполон execution contract между Python и
MT4.

## Limitations / Open Questions

- Анализ покрывал только retained rule slot 1.
- Текущие Python artifacts не пересчитывались.
- Код в рамках этого отчёта не исправлялся.
- M1/M5 проверки были диагностическими inline-скриптами; reusable
  reconciliation script ещё не создан.
- Правильный replacement contract ещё не финализирован.
- Нужно решить:
  - запретить `MLClose` на H1-баре fill;
  - сдвинуть первое ML-exit решение на следующий закрытый H1-бар;
  - или реализовать настоящий M5/M1-aware порядок fill и exit внутри H1.

## Split Disclosure

Унаследованный locked-test interval:

- `locked_test_min_time = 2022-12-02 11:00:00`
- `locked_test_max_time = 2026-06-04 12:00:00`

Роль split:

- `locked_test` использовался только для parity/debug анализа уже выбранных
  retained rules;
- новый winner/cutoff/filter по этому анализу не выбирался.

## Next Step

1. Определить исправленный execution contract для Python:
   - минимальный вариант: после fill на H1-баре `T` первое ML-exit решение
     возможно не раньше следующего закрытого H1-бара;
   - более точный вариант: использовать M5/M1 для timestamp лимитного fill и
     разрешать same-H1 exit только если exit decision хронологически позже
     fill.
2. Реализовать contract в Python с точечными тестами:
   - fill на открытии H1;
   - fill после открытия H1;
   - `MLClose` на H1-баре fill;
   - SL/TP same-bar M5 ordering должен остаться прежним.
3. Пересчитать fixed11 locked-test artifacts.
4. Заново экспортировать `ml_signals_fixed11_ruleNN.csv` и
   `ml_exits_fixed11_ruleNN.csv`.
5. Перезапустить MT4 slot 1 и выполнить reconciliation.
6. Только после приемлемого slot 1 проверять slots 2-5.

## Related Materials

- `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- `docs/superpowers/roadmap.md`
- `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
- `DATA/XAUUSD_H1_OHLC.csv`
