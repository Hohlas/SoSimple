# Context Handoff

**Дата:** 2026-06-29

## Текущий этап

Stage 6.0 завершён после review-fix rerun. Вердикт: **TRADING_GATE_FAILED** (`DIAGNOSTIC_ONLY`).

Старый промежуточный вывод `MODEL_GATE_FAILED` больше не актуален: после добавления короткого горизонта `H6` model gate проходит, но trading gate не проходит.

## Что исправлено после ревью

В `ML/baseline/benchmark_stage6_outcome_based.py` исправлены критические ошибки Stage 6.0:

- gate теперь читает `auc_median` / `pr_auc_lift_median`, а не отсутствующие поля `auc` / `pr_auc_lift`;
- permutation baseline использует реальные model scores, а не constant score;
- diagnostic threshold применяется к реальным score, если threshold выбран;
- `INVALID` rows исключены из yearly/by-side trading counters;
- JSON хранит predictions/labels для post-mortem;
- добавлен fixed horizon `H6` как primary, `H24` оставлен как disclosure comparison.

## Главный результат

Полный прогон:

- artifact: `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- report: `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `12/12` runs = 2 горизонта × 2 профиля × 3 seed
- gate: `TRADING_GATE_FAILED`

Primary `H6_clock_shift_back`:

- val TP rate: `16.6%`
- val timeout rate: `46.4%`
- median val AUC: `0.6888`
- median PR AUC lift: `0.1141`
- model gate: PASS
- threshold status: `NO_THRESHOLD` на fixed grid `0.50..0.90`
- all-trade val PF: `0.942`
- spread 0.20 all-trade val PF: `0.861`

Disclosure `H6_clock_shift_back_impulse`:

- median val AUC: `0.6937`
- median PR AUC lift: `0.1286`
- threshold status: `NO_THRESHOLD`

Disclosure H24:

- `H24_clock_shift_back` median val AUC: `0.5848`
- selected val PF: `0.933`
- permutation p-value: `0.635`
- вывод: H24 не превосходит случайное ранжирование.

## Методические ограничения

- Stage 6.0 остаётся `DIAGNOSTIC_ONLY`.
- `Open[row+1]` timing не подтверждён runtime parity.
- Основной PnL gross; spread stress считается отдельно.
- `DATA/XAUUSD_H1_OHLC.csv` используется как локальный OHLC source для first-touch; CSV-файлы в проекте игнорируются git.
- `2023-2025` и `2026` не использовались для выбора.
- Threshold grid ниже `0.50` не открывалась, чтобы не превратить review-fix в новый parameter search.

## Правильное направление дальше

Если продолжать Stage 6 ветку, следующий шаг должен быть отдельным bounded follow-up:

- `Stage 6.1` H6 calibration / threshold protocol;
- заранее зафиксировать threshold-схему до обучения: например quantile/top-N или calibrated probability threshold;
- оценивать PF, trades/year, yearly PF, spread stress и permutation baseline;
- не использовать `2023-2025` для выбора;
- не менять одновременно horizon, TP/SL и feature set.

Альтернатива: перейти к Regression Up/Dn target foundation, если решено не тратить бюджет на H6 threshold-калибровку.

## Неправильное направление дальше

- Объявлять Stage 6.0 кандидатом.
- Снижать threshold ниже `0.50` post-hoc без нового плана.
- Подбирать horizon/ATR/TP/SL широким перебором.
- Использовать diagnostic holdout `2023-2025` для выбора порога.
- Продолжать H24 как основное направление.

## Ключевые файлы

Код:

- `ML/baseline/benchmark_stage6_outcome_based.py`
- `tests/test_stage6_outcome_based.py`

Артефакты:

- `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- `ML/reports/stage5_4_fast_price_atr_ablation.json`
- `ML/reports/stage5_3_time_to_breach_target_reformulation.json`

Документация:

- `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
