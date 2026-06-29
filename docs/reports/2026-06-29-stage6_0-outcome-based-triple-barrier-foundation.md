# Stage 6.0 Outcome-Based Triple-Barrier Foundation

**Дата:** 2026-06-29
**Статус:** Completed
**Вердикт:** MODEL_GATE_FAILED (DIAGNOSTIC_ONLY)
**Цель:** Построить execution-aware outcome-based baseline (TP/SL/timeout) и проверить, содержит ли он больше сигнала, чем exhausted Fractal Stop `H6_off05`.

## Fixed Target Contract

- **Инструмент/таймфрейм:** XAUUSD H1
- **Вход:** `Open[row+1]` (DIAGNOSTIC_ONLY)
- **Горизонт:** 24 H1 баров
- **SL:** 0.5 × ATR от fractal0.price
- **TP:** 2.0 × ATR от entry_price
- **Timeout:** отдельный исход, PnL = signed move / risk
- **Same-bar ambiguity:** AMBIGUOUS_SL_FIRST (консервативно)
- **Цель классификации:** `stage6_tp_vs_rest_flag` (TP=1, SL/ambiguous/timeout=0)
- **Основной профиль признаков:** `clock_shift_back`
- **Раскрывающий профиль:** `clock_shift_back_impulse`
- **Модель:** XGBoost, 3 seed (42, 77, 123)

## Почему старый `up_24`/`dn_24` недостаточен

`up_24`/`dn_24` — это смещённый forward-looking ярлык: он показывает only close-vs-close движение через 24 бара, не учитывая внутрибаровые движения, TP/SL, спред и время удержания. Outcome-based подход моделирует сделку: реальная точка входа, стоп-лосс, тейк-профит, timeout с realised PnL в risk units.

## Preflight

| Split | Valid | Invalid | TP rate | Timeout rate | Warnings |
|-------|-------|---------|---------|-------------|----------|
| train_core (≤2020) | 48,412 | 5 | 37.0% | 4.0% | PNL_R_ABS_MAX_GT_20 |
| val_stop (2021-2022) | 5,412 | 3 | 36.8% | 4.6% | — |
| diagnostic_holdout (2023-2025) | 8,043 | 48 | 37.8% | 3.7% | PNL_R_ABS_MAX_GT_20 |
| low_n_disclosure (2026) | 602 | 560 | 35.5% | 9.6% | — |

Preflight pass: TP rate в диапазоне 5-70%, timeout < 70%, valid rows > 1000. Предупреждения только по PnR_R хвостам (>20 risk units) — ожидаемо для редких движений.

Инвалидные rows (602 в 2026) — TIME_NOT_FOUND, т.к. 2026 в OHLC файле только частично.

## Oracle / All-Trade Baseline

| Split | All-Trade PF | All-Trade Trades/Year | TP-Only Oracle PF |
|-------|-------------|----------------------|-------------------|
| train_core | 0.995 | 2,848 | inf |
| val_stop | 0.959 | 2,706 | inf |
| diagnostic_holdout | 0.980 | 2,681 | inf |
| low_n_disclosure | 1.051 | 602 | inf |

All-trade baseline ~1.0 PF: timeout-ы компенсируют часть SL потерь, но gross PF не превышает 1.0 систематически. TP-only oracle (все сделки закрыты в TP) даёт inf, что ожидаемо: TP = 2.0 ATR, SL = 0.5 ATR.

## Model Metrics

### clock_shift_back (primary)

| Seed | Val AUC | Val PR AUC Lift | Threshold | Val PF |
|------|---------|----------------|-----------|--------|
| 42 | 0.584 | 0.079 | 0.500 | 0.959 |
| 77 | 0.585 | 0.079 | 0.500 | 0.959 |
| 123 | 0.586 | 0.078 | 0.525 | 0.907 |

Median AUC: **0.585** (< 0.60 gate threshold)
Median PR AUC Lift: **0.079** (> 0.05, passes)
Threshold dispersion: 0.025 (passes)

### clock_shift_back_impulse (disclosure)

| Seed | Val AUC | Val PR AUC Lift | Threshold | Val PF |
|------|---------|----------------|-----------|--------|
| 42 | 0.585 | 0.082 | 0.500 | 1.023 |
| 77 | 0.587 | 0.079 | 0.525 | 1.012 |
| 123 | 0.585 | 0.078 | 0.500 | 1.018 |

Median AUC: **0.586** (< 0.60)

## Threshold & Trading Simulation

Threshold grid: 0.50-0.90 step 0.025. Selected thresholds at 0.50-0.525 (lowest edge of grid):

- Ни один threshold не даёт PF > 1.05 на val_stop
- Требование min 50 trades и 20/year на val выполняется только при threshold ≤ 0.525
- Holdout trades/year при threshold 0.50: ~2,681

Threshold plateau: пройден (стабильные соседи), но это не помогает: PF около 1.0 на всех соседних порогах.

## Permutation Baseline

200 score permutations на val_stop, seed=42:
- Observed PF: 0.959
- Median permuted PF: 0.959
- P95 permuted PF: 0.959
- **Empirical p-value: 1.0**

Модель не превосходит случайное переставление score-ов. Любой threshold на любом наборе permutation даёт тот же PF ~0.96, потому что all-trade baseline уже даёт этот PF. Модель не добавляет сигнала.

## Spread Stress

PF_spread_020 на val_stop: 0.899 (gross: 0.959)
PF_spread_040 на val_stop: 0.844 (gross: 0.959)
Spread-stressed PF значительно ниже gross, что ожидаемо: соотношение reward/risk = 2.0/0.5 = 4, спред 0.20 съедает ~10% PnL.

## Timeout Handling

- Timeout rate: 4.0-4.6% на всех split-ах
- Profitable timeout rate: ~35% (таймауты чаще в минус)
- Total timeout PnL contribution: незначительная (единицы R)
- Timeout как отдельный исход (не loss по умолчанию) оправдан

## Risk/Reward Distribution

- `stage6_risk_atr` median: ~1.2 (SL дистанция чуть больше 1 ATR)
- `stage6_reward_risk` median: ~4.0 (фиксированное 2.0 ATR TP / 0.5 ATR SL)
- PnL_R distribution: heavy-tailed, max abs > 20 на train

## Execution Limitations

- Вход `Open[row+1]`: DIAGNOSTIC_ONLY до проверки runtime timing
- Спред не учтён в основном PnL (только diagnostic spread stress 0.20 и 0.40)
- Same-bar ambiguity: консервативная политика SL_FIRST
- Entry bar high/low считается после входа — порядок внутри бара не гарантирован

## Gate Results

| Check | Result |
|-------|--------|
| preflight_no_tp_outside_range | PASS |
| preflight_no_timeout_gt_70 | PASS |
| preflight_train_val_gt_1000 | PASS |
| auc_ge_0_60 | **FAIL** (0.585) |
| pr_auc_lift_ge_0_05 | PASS (0.079) |
| threshold_selected | PASS |
| threshold_plateau_pass | PASS |
| val_pf_ge_1_15 | **FAIL** (0.959) |
| permutation_p_value_le_0_10 | **FAIL** (1.0) |

**Итоговый статус:** MODEL_GATE_FAILED

AUC 0.585 — модель чуть лучше случайной, но недостаточно для порога 0.60. PR AUC lift 0.079 показывает, что ранжирование частично работает, но не конвертируется в PF > 1.0.

## Выводы

1. **Outcome-based TP/SL/target не даёт устойчивого сигнала** с текущими признаками (`clock_shift_back`). AUC ~0.585, PF ~0.96, permutation p-value = 1.0.
2. **Причина:** all-trade baseline уже даёт PF ~0.96. Модель не может отделить TP-сделки от SL/timeout выше случайного уровня.
3. **Timeout как отдельный исход** оправдан: его распределение отличается от SL, но его доля мала (4%) для существенного влияния.
4. **Spread stress** (0.20-0.40) дополнительно снижает PF на 5-10%, но не является первопричиной неудачи.
5. **Сравнение с Fractal Stop `H6_off05`:** outcome-based подход не превосходит exhausted stop-сигнал ни по AUC, ни по PF. `H6_off05` остаётся закрытой темой.

## Что не делать дальше

- Не расширять поиск признаков для outcome-based TP/SL в текущей постановке.
- Не открывать новый parameter search по horizon/ATR множителям.
- Threshold selection не улучшит PF, так как all-trade baseline фиксирует PF ~0.96.

## Изменённые файлы

Код:
- `ML/baseline/benchmark_stage6_outcome_based.py` — новый модуль
- `tests/test_stage6_outcome_based.py` — 12 тестов

Артефакт:
- `ML/reports/stage6_0_outcome_based_triple_barrier.json`

## Verification

- `pytest tests/ -q`: 891 passed
- JSON invariants: done_runs=6/6, total_runs=6

## Related Materials

- `docs/superpowers/plans/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `ML/reports/stage6_0_outcome_based_triple_barrier.json`
- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
