# Triple Barrier: найдена причина старого расхождения и заново проверен MT4

> **Date**: 2026-04-08 17:22 MSK
> **Status**: Completed
> **Goal**: Понять, почему старая TB-разметка плохо сходилась с MT4, исправить причину и заново проверить TB на свежем прогоне тестера
> **Related plan/spec**: `docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md`, `docs/reports/2026-04-08-triple-barrier-hardening.md`
> **Related commit**: `2dcbf90`

## Context

Первая проверка в MT4 дала слишком плохой результат и выглядела как окончательный провал TB. Но во время разборки сделок выяснилось, что это сравнение было нечестным: Python и MT4 часто считали не одну и ту же сделку.

Главная причина оказалась в разметке. TB-исход в Python считался не от времени строки сигнала, а от времени `fractal0` внутри этой строки. Обычно это на 1 бар раньше. После этого MT4 открывает сделку ещё на следующем баре. В результате Python нередко начинал считать исход на 2 бара раньше реального входа MT4.

Из-за этого старый отрицательный вывод по MT4 нельзя было принимать как окончательный. Пришлось полностью пересобрать цепочку: исправить разметку, заново обучить TB, заново выпустить сигналы и ещё раз прогнать MT4.

## What Was Done

- В `processing/label_signals.py` исправлена привязка времени: TB-разметка теперь считает исход от времени строки сигнала, а не от `fractal0.time`.
- В `statistics/signal_tracer.py` исправлены две вещи, которые мешали честной сверке:
  - разбор нового 22-польного `fractal0`;
  - расчёт времени в UTC, без ложного сдвига.
- В `MT/MQL4/Include/OUTPUT.mqh` добавлены понятные строки в лог при рыночном закрытии сделки, чтобы было видно причину закрытия.
- Заново пересчитаны TB-колонки в `DATA/Nero_{train,validation,test}_labeled.csv`.
- После пересчёта заново пройден весь TB-цикл:
  - обучение;
  - калибровка вероятностей;
  - выбор зафиксированного правила только на validation;
  - финальная оценка на test;
  - выпуск нового `ml_signals_tb.csv`.
- Новый `ml_signals_tb.csv` синхронизирован и для MT4, и для tester.
- Выполнен новый MT4-прогон по свежему файлу сигналов.
- По свежему логу построена новая сверка Python ↔ MT4.

## Changed Files

- `processing/label_signals.py` (обновлён)
- `statistics/signal_tracer.py` (обновлён)
- `MT/MQL4/Include/OUTPUT.mqh` (обновлён)
- `tests/test_triple_barrier_first_touch.py` (создан)
- `tests/test_signal_tracer_tb.py` (создан)
- `ML/checkpoints/transformer_tb_best.pt` (пересохранён)
- `ML/checkpoints/transformer_tb_result.json` (обновлён)
- `ML/reports/threshold_analysis_tb.md` (обновлён)
- `ML/reports/evaluate_test_tb.md` (обновлён)
- `ML/reports/tb_selected_rule.json` (создан)
- `MT/MQL4/Files/ml_signals_tb.csv` (перегенерирован)
- `MT/tester/files/ml_signals_tb.csv` (синхронизирован)
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md` (обновлён)

## Verification

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_first_touch.py tests/test_signal_tracer_tb.py tests/test_triple_barrier_calibration.py tests/test_generate_signals_research.py tests/test_triple_barrier_training.py -q
./.venv/bin/python -m ML.train --model transformer --task triple_barrier --epochs 50 --seed 42 --clear_cache --encoder_ckpt ML/checkpoints/transformer_updn_best.pt
./.venv/bin/python -m ML.threshold_analysis --task triple_barrier --model transformer
./.venv/bin/python -m ML.evaluate_test --task triple_barrier --model transformer
./.venv/bin/python -m API.generate_signals --task triple_barrier --model transformer --theta 0.475 --min-ev 0.10
cmp MT/MQL4/Files/ml_signals_tb.csv MT/tester/files/ml_signals_tb.csv
./.venv/bin/python statistics/signal_tracer.py --from-log MT/tester/logs/20260408.log --signals MT/MQL4/Files/ml_signals_tb.csv --csv-out ML/reports/tb_mt4_reconciliation_after_relabel.csv
rg -o "CLOSE_REQ (BUY|SELL) reason=[A-Za-z_]+" -N MT/tester/logs/20260408.log
rg -o "TB SKIP reason=[A-Za-z_]+" -N MT/tester/logs/20260408.log
```

Observed:

- `pytest`: `10 passed`
- TB переобучение завершилось, лучший checkpoint: `epoch=3`, `best val mean_auc=0.5982`
- Новое зафиксированное правило выбрано только на validation: `theta=0.475`, `min_ev=0.10`
- Новый отчёт по test вне MT4 записан в `ML/reports/evaluate_test_tb.md`
- `ml_signals_tb.csv` для MT4 и tester совпадают
- `signal_tracer.py` разобрал свежий лог MT4 и построил сверку на `92` сделках

## Results

### Исправленный результат вне MT4

| Metric | Value |
|---|---:|
| Зафиксированное правило | `theta=0.475`, `min_ev=0.10` |
| Validation PF | `1.53` |
| Validation trades | `121` |
| Validation wins / losses / timeouts | `70 / 51 / 14` |
| Test PF вне MT4 | `1.11` |
| Test trades | `253` |
| Test wins / losses / timeouts | `128 / 125 / 24` |

### Новый MT4-прогон

| Metric | Value |
|---|---:|
| Net profit | `2932.44` |
| PF | `1.27` |
| Trades | `92` |
| Profitable / losing | `46 / 46` |
| Max drawdown | `18.67%` |

### Сверка сделка за сделкой

| Metric | Value |
|---|---:|
| Сделок в сверке | `92` |
| Python labels: `TP_FIRST / SL_FIRST / TIMEOUT` | `44 / 40 / 8` |
| MT4: `WIN(TP) / LOSS(SL) / WIN(MKT) / LOSS(MKT) / OPEN` | `34 / 31 / 12 / 14 / 1` |
| Среднее `SL Δ` | `0.000578` |
| Среднее `TP Δ` | `0.000698` |
| Совпадение жёстких исходов `TP/SL` | `61 из 65` (`93.8%`) |
| Win rate у `TP_FIRST` сделок в MT4 | `88.4%` |
| Loss rate у `SL_FIRST` сделок в MT4 | `85.0%` |

### Причины оставшейся разницы

Из лога MT4:

- `TB SKIP reason=PosBlock`: `113` раз
- `CLOSE_REQ reason=HoldOverTime`: `22` раза
- `CLOSE_REQ reason=TB_Reversal`: `4` раза
- `1` сделка осталась открытой в конце теста

## Conclusions

Старый вывод “TB не переносится в MT4” оказался неверным. Главная причина старого провала была не в spread, не в ATR и не в самих уровнях SL/TP, а в сдвиге времени в TB-разметке. Python и MT4 часто считали уже не одну и ту же сделку.

После исправления картина изменилась:

- уровни SL/TP между Python и MT4 теперь совпадают почти идеально;
- по жёстким исходам `TP/SL` совпадение уже высокое;
- MT4 больше не хуже результата вне MT4, а даже немного лучше по PF: `1.27` против `1.11`.

Оставшаяся разница теперь в основном объясняется уже не ошибкой разметки, а правилами торговли в MT4:

- в MT4 нельзя открыть новую сделку, если старая ещё жива (`PosBlock`);
- часть сделок закрывается по лимиту времени (`HoldOverTime`);
- часть сделок закрывается по новому обратному сигналу (`TB_Reversal`);
- вход в MT4 происходит на следующем баре.

То есть сейчас TB уже не выглядит “бумажной” схемой, которая ломается при переносе в MT4. Основная старая ошибка найдена и исправлена. Но для совсем честного сравнения теперь нужен следующий шаг: считать результат вне MT4 не “каждый сигнал отдельно”, а по тем же торговым правилам, что и MT4.

## Limitations / Open Questions

- Текущий test вне MT4 всё ещё не повторяет механику MT4 один в один.
- Сравнение `253` offline trades и `92` MT4 trades пока не является сравнением “один к одному”, потому что MT4 пропускает часть сигналов из-за уже открытой позиции.
- SELL-часть TB по-прежнему слабее BUY-части.
- Новый вывод опирается на один свежий MT4 log `20260408.log`; для полной уверенности полезно будет повторить проверку ещё на одном прогоне после появления режима оценки, который повторяет правила MT4.

## Next Step

Следующий шаг: добавить в Python режим оценки, который повторяет MT4 один в один.

Он должен учитывать:

1. вход на следующем баре;
2. только одну открытую позицию;
3. закрытие по времени `HoldOverTime`;
4. закрытие по новому обратному сигналу `TB_Reversal`.

После этого нужно ещё раз сравнить offline и MT4 уже в одинаковых правилах торговли и только потом решать, продвигать ли TB дальше как отдельный торговый режим.

## Related Materials

- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `docs/superpowers/plans/2026-04-08-triple-barrier-runtime-verdict.md`
- `ML/reports/threshold_analysis_tb.md`
- `ML/reports/evaluate_test_tb.md`
- `ML/reports/tb_selected_rule.json`
- `MT/MQL4/Files/ml_signals_tb.csv`
- `MT/tester/logs/20260408.log`
