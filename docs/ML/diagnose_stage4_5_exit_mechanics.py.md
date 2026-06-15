# diagnose_stage4_5_exit_mechanics.py

## Purpose
Stage 4.5 exit mechanics diagnostic runner: проверяет trailing stop, breakeven и partial exit с фиксированными Stage 4.4 breach/fav моделями. Не меняет качество модели — только механику выхода.

## Input
- `DATA/Nero_XAUUSD_train_labeled.csv`, `DATA/Nero_XAUUSD_validation_labeled.csv`
- `DATA/XAUUSD_H1_OHLC.csv` — H1 OHLC=Bid

## Output
- `ML/reports/stage4_5_exit_mechanics.json`

## Command
```bash
~/git/SoSimple/.venv/bin/python ML/baseline/diagnose_stage4_5_exit_mechanics.py
```

## Status
DIAGNOSTIC_ONLY — no test, no winner. Results are diagnostic hypotheses.

## Exit Policies
1. `fixed_r_0_7` — базовый фиксированный TP (baseline Stage 4.4)
2. `breakeven_0_3` — перенос SL на entry после 30% движения к TP
3. `trail_atr_0_2` — trailing stop с отступом 0.2 ATR
4. `trail_atr_0_3` — trailing stop с отступом 0.3 ATR
5. `partial_50_at_0_5R_then_trail_0_2` — закрыть 50% на 0.5R, остальное trail

## Limitations
- Exit simulator использует тот же bar-loop, но усложнён трекингом состояния
- Trailing stop не проверен на MT4/tester parity
- 5 политик + 2 уровня спреда = 10 evaluation cells
