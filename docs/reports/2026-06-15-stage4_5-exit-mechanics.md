# Stage 4.5 Exit Mechanics Report

> **Status:** DIAGNOSTIC_ONLY — no test opened, no winner selected
> **Date:** 2026-06-15
> **Runner:** `ML/baseline/diagnose_stage4_5_exit_mechanics.py`
> **Source:** `docs/audit/to_do.md` — trailing / partial exit mechanics

## Context

Stage 4.4 показал, что fixed TP R=0.7 не хуже fav-based TP. Вопрос: может ли улучшенная механика выхода (trailing stop, breakeven, partial exit) поднять PF при фиксированных Stage 4.4 моделях?

Методология: берём Stage 4.4 модели (XGBoost breach + RF fav), фиксированные пороги, и применяем разные exit-policy к тому же universe сделок. Синтетические тесты симулятора пройдены (10 из 10).

## Synthetic Simulator Tests

10 тестов: TP-only, SL-only, ambiguous bar (TP+SL → SL first), timeout, breakeven trigger, trailing directional correctness, partial exit. Все passed.

## Baseline Reproduction

| Метрика | Expected | Got | Match |
|---------|----------|-----|-------|
| Fixed R=0.7 PF | 1.038 | 1.038 | OK |
| N trades | 503 | 503 | OK |
| BS_p05 | 0.886 | 0.886 | OK |

Permutation test: 0/500, p≈0.002 — breach-сигнал сохранён при fixed exit.

## Exit Policy Results

| Policy | PF | BS_p05 | n | neg_years | Exits | Spread 0.40 PF |
|--------|-----|--------|---|-----------|-------|----------------|
| `fixed_r_0_7` (baseline) | 1.038 | 0.886 | 503 | 2 | TP:225 SL:150 TMO:128 | 0.928 |
| `breakeven_0_3` | 0.717 | 0.569 | 503 | 4 | TP:103 SL:376 TMO:24 | 0.611 |
| `trail_atr_0_2` | **1.831** | **1.462** | 503 | **1** | TP:91 SL:56 TRAIL:356 | **1.501** |
| `trail_atr_0_3` | 1.296 | 1.048 | 503 | 1 | TP:92 SL:60 TRAIL:351 | 1.061 |
| `partial_50_at_0_5R_then_trail_0_2` | 1.051 | 0.883 | 503 | 1 | TP:155 SL:286 TMO:62 | 0.909 |

### Годовая разбивка (trail_atr_0_2)

| Год | PF | n | PF baseline |
|-----|-----|---|------------|
| 2019 | 0.957 | 120 | 0.918 |
| 2020 | 2.421 | 121 | 1.104 |
| 2021 | 2.828 | 126 | 1.479 |
| 2022 | 1.565 | 136 | 0.839 |

`trail_atr_0_2` улучшает PF каждый год, кроме 2019 (0.957 — ниже 1.0, но выше baseline 0.918).

### Интерпретация механики

- **Breakeven убивает PF.** Преждевременное закрытие при движении 30% к TP приводит к PF=0.717. Входы часто откатываются до срабатывания breakeven.
- **Trailing с 0.2 ATR** (очень tight) даёт лучший PF (1.831), но за счёт массового выхода по трейлингу (71% сделок). Стоп очень плотный: при движении цены на 0.2 ATR в пользу сделки стоп подтягивается немедленно.
- **Trailing с 0.3 ATR** снижает PF до 1.296 — менее агрессивный, но всё ещё значительно лучше baseline.
- **Partial exit 50% на 0.5R + trail** не даёт значимого улучшения (PF=1.051). Первый частичный выход закрывает прибыльную часть, но оставшаяся позиция всё равно часто попадает в SL.

## Spread Stress

| Policy | Spread 0.20 PF | Spread 0.40 PF | Δ |
|--------|:----------:|:----------:|:--:|
| `trail_atr_0_2` | 1.831 | 1.501 | −0.330 |
| `trail_atr_0_3` | 1.296 | 1.061 | −0.235 |
| `fixed_r_0_7` | 1.038 | 0.928 | −0.110 |

`trail_atr_0_2` сохраняет PF > 1.0 при спреде 0.40 (PF=1.501, BS_p05=1.199). Устойчив к cost stress.

## Вердикт для Stage 4.6

`trail_atr_0_2` превышает baseline по всем метрикам (PF +0.793, BS_p05 +0.576, neg_years −1) и проходит spread stress. 

**Это первый diagnostic-результат, заслуживающий чистого candidate-cycle (Stage 4.6).**

Оговорки:
- 71% выходов по трейлингу — стратегия полностью полагается на механику выхода
- 2019 всё ещё убыточен (PF=0.957)
- Breach/fav модели не менялись — это чисто улучшение execution
- Старый trailing PF=1.655 (Stage 4.3 diagnostic) не использовался

## Non-Conclusions

- Нет открытого test.
- Нет выбранного winner.
- Trail_atr_0_2 — diagnostic hypothesis, не production-правило.
- Требуется Stage 4.6 clean candidate-cycle для валидации.

## Search Budget

| Категория | Ячеек |
|-----------|-------|
| Exit policies | 5 (fixed before run) |
| Spred stress levels | 2 |
| Total evaluation cells | 10 |
