# Stage 4.4 Diagnostic Micro-Check — Report

> **Status:** `DIAGNOSTIC_ONLY` — no test opened, no winner selected, Stage 4 verdict unchanged.
> **Date:** 2026-06-15
> **Source:** `docs/audit/next.md` (Vector B)

## Context

Stage 4.3 post-mortem показал, что breach-ранжирование и fav/TP слой совместно ограничивают PF около 1.015 на val_eval (≥2019). Хотя oracle ceiling = 104.9 PF подтверждает, что проблема не в механике правил, а в извлечении сигнала, остаются вопросы, можно ли улучшить PF без замены модели:

1. Даёт ли ослабление breach-фильтра (`p=0.5`) рост PF?
2. Уступает ли fav-based TP фиксированному TP? Если нет — Transformer Stage 5 может не учить fav как цену TP.
3. Работает ли breach без fav-фильтра?

Все проверки — на val_eval (≥2019), где исторически выбран Stage 4 winner. Нового model selection нет. Результаты не являются торговым правилом.

## Methodology and Split

| Параметр | Значение |
|----------|----------|
| Target | `sell_H6_off05` |
| Split | train ≤2016, val_stop 2017-2018, val_eval ≥2019 |
| Breach model | XGBoost `base_raw_plus_time`, early stopping on val_stop |
| Fav model | RF `base_raw` |
| Spread | canonical 0.20 (OHLC=Bid) |
| Entry | Open следующего H1-бара |
| Exit | first-touch SL/TP/TIMEOUT, ambiguous bar = SL |
| Block bootstrap | 500 iter, block_size=15 |
| Breach AUC val_eval | 0.6674 |

## Search Budget Disclosure

| Experiment | Variants | diagnostic_cells |
|------------|:--------:|:----------------:|
| Relax breach (p=0.5) | 1 | 1 |
| Fixed TP (R ∈ {0.5, 0.7, 1.0}) | 3 | 3 |
| Breach-only entry + Fixed TP (R ∈ {0.5, 0.7, 1.0}) | 3 | 3 |
| Baseline (Stage 4.2) | 1 | 1 |
| **Total** | | **8** |

- 8 diagnostic cells
- 5 permutation tests (baseline, relax, 3×breach-only) × 500 iter
- 8 block bootstrap × 500 iter

## Baseline Sanity Check

| Metric | Expected (Stage 4.2) | Actual |
|--------|:--------------------:|:------:|
| PF | 1.015 | **1.015** |
| n_trades | 503 | **503** |
| BS median | 0.996 | **0.996** |
| BS p05 | 0.837 | **0.837** |

Baseline полностью воспроизводится.

## Experiment 1: Relax Breach Filter (p=0.5)

**Hypothesis:** Ослабление breach-фильтра с p=0.4 до p=0.5 увеличит PF за счёт пропуска блокированных oracle-безопасных сделок.

| Metric | Baseline (p=0.4) | Relax (p=0.5) | Δ |
|--------|:----------------:|:-------------:|:--:|
| PF | **1.015** | 0.862 | **−0.153** |
| n_trades | 503 | 1441 | +938 |
| BS p05 | 0.837 | 0.791 | −0.046 |
| Perm median PF | 0.817 | 0.816 | — |
| Perm n_ge | 0/500 | 20/500 | — |
| Perm p-value | ≈0.002 | ≈0.042 | — |

**Oracle diagnostics of added rows:**

| Category | Count |
|----------|:-----:|
| Oracle-safe (breach_flag_true=0) | 536 |
| Oracle-bad (breach_flag_true=1) | 402 |
| Safe ratio | 57.1% |

**Conclusion:** Ослабление breach-фильтра ухудшает PF (1.015 → 0.862), несмотря на добавление 938 сделок (из которых 57% oracle-безопасны). 43% oracle-плохих добавленных сделок разрушают PnL. Breach-фильтр на p=0.4 необходим.

## Experiment 2: Fixed TP (breach+fav-фильтр)

**Hypothesis:** Фиксированный TP (`tp = stop_val × R`) не хуже fav-based TP (`tp = pred_fav × 0.4`). Входной фильтр идентичен baseline.

| R | PF | BS p05 | n | ΔPF vs baseline | avg_win_r | avg_loss_r |
|:--:|:---:|:------:|:--:|:---------------:|:---------:|:----------:|
| 0.5 | **1.036** | 0.867 | 503 | **+0.021** | 0.469 | 0.791 |
| 0.7 | **1.038** | 0.886 | 503 | **+0.023** | 0.602 | 0.769 |
| 1.0 | 0.937 | 0.805 | 503 | −0.078 | 0.699 | 0.758 |
| Baseline (fav) | 1.015 | 0.837 | 503 | — | 0.472 | 0.700 |

**Conclusion:** Fixed TP при R=0.5 и R=0.7 даёт скромный прирост PF (+0.02) и более высокий BS_p05 (0.867–0.886 vs 0.837). Fav-based TP не имеет преимущества над простым фиксированным TP. При R=1.0 PF падает ниже baseline (0.937): TP ставится слишком далеко, сделки чаще закрываются по SL/TIMEOUT, не дойдя до цели.

## Experiment 3: Breach-Only Entry + Fixed TP

**Hypothesis:** Breach-фильтр (p=0.4) без fav-порогов (`skip_min_fav=True, skip_min_rr=True`) + fixed TP даёт PF не хуже baseline.

| R | PF | BS p05 | n | ΔPF vs baseline | Perm median PF | Perm p-value |
|:--:|:---:|:------:|:-:|:---------------:|:-------------:|:------------:|
| 0.5 | 0.894 | 0.810 | 1724 | −0.121 | 0.839 | ≈0.094 |
| 0.7 | 0.905 | 0.814 | 1724 | −0.110 | 0.845 | ≈0.090 |
| 1.0 | 0.883 | 0.788 | 1724 | −0.132 | 0.828 | ≈0.094 |

**Trade comparison vs baseline:**

| Metric | Value |
|--------|:-----:|
| Trades added | 1221 |
| Added: oracle-safe | 1017 (83.3%) |
| Added: oracle-bad | 204 (16.7%) |

**Conclusion:** Breach без fav-фильтра — убыточен (все PF < 0.91). Хотя 83.3% добавленных сделок oracle-безопасны, 16.7% oracle-плохих сделок в сочетании с низким RR разрушают PnL. Fav-фильтр критичен. Permutation tests: n_ge = 44–46/500, p ≈ 0.09 — breach-only сигнал слабо отделяется от случайного.

## Fav-Filter Isolation (Experiment 2 vs 3)

При одинаковом R сравнение breach+fav фильтр vs breach-only показывает чистый вклад fav-фильтра:

| R | PF (breach+fav) | PF (breach-only) | ΔPF | Δn |
|:--:|:---------------:|:----------------:|:---:|:---:|
| 0.5 | 1.036 | 0.894 | **−0.142** | +1221 |
| 0.7 | 1.038 | 0.905 | **−0.133** | +1221 |
| 1.0 | 0.937 | 0.883 | **−0.054** | +1221 |

Fav-фильтр добавляет +0.054 до +0.142 PF, блокируя 1221 сделку. Это согласуется с результатами Stage 4.3: breach false-safe и fav false-accept — сопоставимые потери.

## Comparison Summary: All 8 Cells

| Cell | p | TP policy | Fav filter | PF | BS p05 | n |
|------|:--:|-----------|:----------:|:---:|:------:|:--:|
| Baseline | 0.4 | fav×0.4 | yes | **1.015** | 0.837 | 503 |
| Relax breach | 0.5 | fav×0.4 | yes | 0.862 | 0.791 | 1441 |
| Fixed TP R=0.5 | 0.4 | stop×0.5 | yes | **1.036** | 0.867 | 503 |
| Fixed TP R=0.7 | 0.4 | stop×0.7 | yes | **1.038** | 0.886 | 503 |
| Fixed TP R=1.0 | 0.4 | stop×1.0 | yes | 0.937 | 0.805 | 503 |
| Breach-only R=0.5 | 0.4 | stop×0.5 | no | 0.894 | 0.810 | 1724 |
| Breach-only R=0.7 | 0.4 | stop×0.7 | no | 0.905 | 0.814 | 1724 |
| Breach-only R=1.0 | 0.4 | stop×1.0 | no | 0.883 | 0.788 | 1724 |

## What Can and Cannot Be Concluded

### Что можно заключить:

1. **Ослабление breach-фильтра ухудшает PF** — p=0.5 добавляет 938 сделок, но 43% из них oracle-плохие, общий PF падает до 0.862.
2. **Fixed TP не хуже fav-based TP** — при R=0.5–0.7 fixed TP даёт PF 1.036–1.038 vs baseline 1.015, с более высоким BS_p05. Fav как прямая цена TP не даёт преимущества над простым fixed TP.
3. **Fav-фильтр критичен** — breach без fav-фильтра даёт PF 0.88–0.91. Fav не нужен как цена TP, но необходим как фильтр входа.
4. **Ни одна ячейка не достигает PF > 1.15** — ни один вариант не проходит gate.

### Что нельзя заключить:

- Fixed TP при R=0.7 **не является winner** — все ячейки проверены на тех же данных, где выбран Stage 4 winner (historical selection bias).
- Breach работает сам по себе **не доказано** — permutation test p ≈ 0.09 недостаточен для утверждения.
- PF 1.038 **не является PASS** — все результаты `DIAGNOSTIC_ONLY`.

## Implications for Stage 5.0 Transformer Design

1. **Fav не нужно учить как цену TP.** Fixed TP при R=0.7 уже работает не хуже (и даже чуть лучше) fav-based TP. Transformer Stage 5.0 должен фокусироваться на **breach-классификации** как основном источнике сигнала, а fav использовать только как **фильтр входа** (min_fav, min_rr).
2. **Breach-фильтр необходим и не должен ослабляться.** p=0.4 остаётся разумным порогом. Улучшение breach-ранжирования (через Transformer) — основной путь к росту PF.
3. **Fav-фильтр нельзя убирать.** Без fav-порогов PF падает на 0.05–0.14. Даже слабая fav-модель RF (Spearman=0.218) полезна как gate.
4. **Улучшение fav-регрессии (Transformer multi-head)** может дать дополнительный прирост через более точный фильтр, но не через прямую цену TP.

## Related Artifacts

- **Script:** `ML/baseline/diagnose_stage4_4.py`
- **JSON output:** `ML/reports/stage4_4_micro_check.json`
- **Source:** `docs/audit/next.md`
- **Previous diagnostics:** `docs/reports/2026-06-15-stage4_3-diagnostics.md`
- **Wiki:** `wiki/research/fractal-stop-research.md`

---

*Verification: baseline PF=1.015, n=503 — Stage 4.2 reproduced.*
*Status: DIAGNOSTIC_ONLY — test NOT opened, winner NOT selected, Stage 4 verdict unchanged.*
