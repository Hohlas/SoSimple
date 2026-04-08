# Triple Barrier: актуальная база вне MT4 после полной пересборки

> **Date**: 2026-04-08 17:22 MSK
> **Status**: Completed
> **Goal**: Довести TB до честной схемы вне MT4: реальное первое касание, калибровка вероятностей, выбор порогов только на validation, режим “не торговать” и выпуск нового набора сигналов для MT4
> **Related plan/spec**: `docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md`, `docs/superpowers/plans/2026-03-22-triple-barrier.md`, `docs/superpowers/specs/2026-03-22-triple-barrier-design.md`
> **Related commit**: `2dcbf90`

## Context

Этот этап собрал для TB рабочую основу вне MT4. Нужны были четыре вещи:

- считать исход по реальному первому касанию;
- калибровать вероятности;
- выбирать правило только на validation;
- дать модели право не торговать, если преимущество слабое.

По ходу этапа была уточнена и привязка времени старта сделки: разметка должна стартовать от времени строки сигнала. После этого вся TB-цепочка была собрана заново от разметки до нового `ml_signals_tb.csv`, чтобы дальнейшие сравнения с MT4 опирались уже на одну и ту же схему.

## What Was Done

- В `processing/label_signals.py` TB-разметка переведена на реальное первое касание барьеров по окну в `24` бара.
- Timeout больше не смешивается с loss: теперь это отдельное значение `0.5`.
- Разметка теперь стартует от времени строки сигнала, а не от `fractal0.time`.
- Общая логика TB-сигнала вынесена в `ML/tb_signal_logic.py`:
  - выбор лучшего сигнала;
  - расчёт expected value;
  - режим “не торговать” через `min_ev`.
- Добавлен слой калибровки вероятностей `ML/tb_probability_calibration.py`.
- В `ML.train.py`, `ML.threshold_analysis.py`, `ML.evaluate_test.py` и `API/generate_signals.py` включены:
  - калибровка вероятностей;
  - зафиксированное правило только по validation;
  - загрузка правила из `tb_selected_rule.json`.
- `statistics/signal_tracer.py` расширен для TB-сделок, чтобы потом можно было честно сверить Python и MT4.
- После уточнения времени заново пересобраны:
  - TB-колонки в `DATA/Nero_{train,validation,test}_labeled.csv`;
  - checkpoint TB-модели;
  - зафиксированное правило;
  - test-оценка;
  - `ml_signals_tb.csv`.

## Changed Files

- `processing/label_signals.py` (обновлён)
- `ML/train.py` (обновлён)
- `ML/threshold_analysis.py` (обновлён)
- `ML/evaluate_test.py` (обновлён)
- `API/generate_signals.py` (обновлён)
- `statistics/signal_tracer.py` (обновлён)
- `ML/tb_signal_logic.py` (создан)
- `ML/tb_probability_calibration.py` (создан)
- `tests/test_triple_barrier_first_touch.py` (создан)
- `tests/test_triple_barrier_calibration.py` (создан)
- `tests/test_generate_signals_research.py` (создан)
- `tests/test_signal_tracer_tb.py` (создан)
- `tests/test_triple_barrier_training.py` (создан)
- `ML/checkpoints/transformer_tb_best.pt` (пересохранён)
- `ML/checkpoints/transformer_tb_result.json` (обновлён)
- `ML/reports/tb_probability_calibrator.joblib` (создан)
- `ML/reports/tb_selected_rule.json` (создан)
- `ML/reports/tb_validation_logits.npy` (создан)
- `ML/reports/tb_validation_targets.npy` (создан)
- `ML/reports/threshold_analysis_tb.md` (обновлён)
- `ML/reports/evaluate_test_tb.md` (обновлён)
- `MT/MQL4/Files/ml_signals_tb.csv` (перегенерирован)

## Verification

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_first_touch.py tests/test_triple_barrier_calibration.py tests/test_generate_signals_research.py tests/test_signal_tracer_tb.py tests/test_triple_barrier_training.py -q
./.venv/bin/python -m ML.train --model transformer --task triple_barrier --epochs 50 --seed 42 --clear_cache --encoder_ckpt ML/checkpoints/transformer_updn_best.pt
./.venv/bin/python -m ML.threshold_analysis --task triple_barrier --model transformer
./.venv/bin/python -m ML.evaluate_test --task triple_barrier --model transformer
./.venv/bin/python -m API.generate_signals --task triple_barrier --model transformer --theta 0.475 --min-ev 0.10
```

Observed:

- `pytest`: `10 passed`
- Лучший checkpoint TB: `epoch=3`, `best val mean_auc=0.5982`
- Новое зафиксированное правило записано в `ML/reports/tb_selected_rule.json`
- Новый отчёт по test вне MT4 записан в `ML/reports/evaluate_test_tb.md`
- Новый `ml_signals_tb.csv` выпущен для MT4

## Results

### TB после полной пересборки

| Metric | Value |
|---|---:|
| Best validation Mean AUC | `0.5982` |
| Test Mean AUC | `0.5895` |
| Зафиксированное правило | `theta=0.475`, `min_ev=0.10` |

### Validation

| Metric | Value |
|---|---:|
| Trades | `121` |
| Wins / Losses / Timeouts | `70 / 51 / 14` |
| Win Rate | `57.9%` |
| PF | `1.53` |
| Dominant target | `buy_sl3_tp3` (`105` trades) |

### Final test

| Metric | Value |
|---|---:|
| Trades | `253` |
| Wins / Losses / Timeouts | `128 / 125 / 24` |
| Win Rate | `50.6%` |
| PF | `1.11` |
| Dominant target | `buy_sl3_tp3` (`220` trades) |

### Новый файл сигналов

| Split | BUY | SELL | FLAT |
|---|---:|---:|---:|
| Train | `359` | `23` | `43382` |
| Validation | `114` | `7` | `9257` |
| Test | `237` | `16` | `9125` |
| Total | `670` | `46` | `58050` |

## Conclusions

Этап дал для TB актуальную базу вне MT4:

- первое касание считается по реальному пути цены;
- вероятности калибруются;
- правило фиксируется только на validation;
- при слабом преимуществе модель может не торговать.

По итогам полной пересборки рабочая база вне MT4 получилась такой: `PF=1.11` на test при `253` сделках. Это не “идеальный” результат, но уже нормальная и понятная отправная точка для сравнения с MT4 и для дальнейших решений по TB.

## Limitations / Open Questions

- Test вне MT4 пока считает сделки проще, чем MT4.
- BUY-часть выглядит сильнее SELL-части.
- `min_ev` помог сделать правило строже, но сам запас преимущества всё ещё небольшой.
- Финальный смысл этого этапа можно оценивать только вместе со следующим MT4-прогоном на новом `ml_signals_tb.csv`.

## Next Step

Взять новый `ml_signals_tb.csv`, прогнать его в MT4 и проверить:

1. совпадают ли уровни SL/TP;
2. совпадают ли исходы сделок;
3. не ломается ли TB после правил реальной торговли в MT4.

Этот шаг выполнен в следующем отчёте: `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`.

## Related Materials

- `docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md`
- `docs/superpowers/plans/2026-03-22-triple-barrier.md`
- `docs/superpowers/specs/2026-03-22-triple-barrier-design.md`
- `ML/reports/threshold_analysis_tb.md`
- `ML/reports/evaluate_test_tb.md`
- `ML/reports/tb_selected_rule.json`
- `MT/MQL4/Files/ml_signals_tb.csv`
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
