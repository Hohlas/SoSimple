# benchmark_stage4_6_clean_cycle.py

## Purpose
Stage 4.6 clean candidate-cycle runner: проверяет exit-политики из Stage 4.5 в протоколе val_select/val_eval с permutation test, повторяющим выбор.

## Input
- `DATA/Nero_XAUUSD_train_labeled.csv`, `DATA/Nero_XAUUSD_validation_labeled.csv`
- `DATA/XAUUSD_H1_OHLC.csv`

## Output
- `ML/reports/stage4_6_clean_cycle.json`

## Command
```bash
~/git/SoSimple/.venv/bin/python ML/baseline/benchmark_stage4_6_clean_cycle.py
```

## Status
DIAGNOSTIC_ONLY — NO_CANDIDATE (concentration gate failed)

## Candidate Family
1. `fixed_r_0_7` — baseline
2. `trail_atr_0_2` — Stage 4.5 winner
3. `trail_atr_0_3` — Stage 4.5 runner-up

## Split
- train: ≤2016
- val_stop: 2017-2018
- val_select: 2019-2020
- val_eval: 2021-2022

## Limitations
- Концентрационный gate (60%) слишком строг для 2-годичного сплита
- Permutation test (N=100) — только diagnostic, не заменяет test
- Модели фиксированы с Stage 4.4
