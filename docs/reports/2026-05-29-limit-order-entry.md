# Limit-Order Entry Convention — Stage Report

Дата: 2026-05-29 | Ветка: `feature/limit-order-entry-convention`
Spec: `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md`
Plan: `docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md`

## Цель

Сделать Close-entry исполнимым через pending BUY/SELL LIMIT на уровне Close[row]. Предыдущий протокол (entry = Close[row]) давал высокие diagnostics, но неисполним в live. Переход на Open[row+1] разрушил модель (PF=0.76). Лимитный ордер решает проблему: ордер висит до возврата цены, гэп перестаёт быть adversarial.

## Что сделано

| Фаза | Артефакты | Статус |
|------|-----------|--------|
| Spec | `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md` — spread-adjusted fill/exit, conservative/optimistic/ambiguous, per-side fill_lag, embargo | Done |
| Plan | `docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md` — 10 задач | Done |
| Labeling | `processing/label_signals.py::label_limit_order_barriers()` — 6-bar fill window, 24-bar barrier, spread-adjusted SELL exit, per-side fill_lag, PnL columns, ambiguous flags | Done |
| Tests | `tests/processing/test_limit_order_barriers.py` — 15 тестов: BUY/SELL fill, NO_FILL, spread, ambiguity, skipped rows, PnL, columns | Done |
| Pipeline | `--limit-order --spread` in `label_main.py`, output to `DATA/limit_order/` | Done |
| Purge | `processing/purge_split.py` — 30-bar time-based purge at boundaries | Done |
| Audit | `processing/label_audit.py` — fill_lag distribution, ambiguity per target, old-vs-new comparison | Done |
| Baseline | `ML/baseline/benchmark_limit_order_entry.py` — RF/HGB, fill-only train, threshold sweep on ALL validation, PF from `_pnl_r` | Done |
| Transformer (Phase 3) | `ML/limit_order_train.py` — BUY TB targets на fractal features | Done |
| Agent hub | `.opencode/agents/reviewer.md` — QA agent for docs/code/experiments | Done |

## Spread grid: BUY buy_sl3_tp3 (Baseline, Phase 2)

| Spread | Status | Fill % | PF (best) | Trades/yr | Neg Yrs |
|--------|--------|--------|-----------|-----------|---------|
| 0 | DIAGNOSTIC_ONLY | 98.6% | 1.556 (HGB) | 169.4 | 0 |
| **0.20 (canonical)** | **PASS** | 96.4% | **1.531 (RF)** | 55.3 | 0 |
| 0.40 (2×) | FAIL | 93.9% | 1.232 (RF) | 53.8 | 1 |
| 0.80 (4×) | FAIL | 90.5% | 1.018 (HGB) | 406.0 | 2 |

Gate: PF ≥ 1.3, fill_rate ≥ 20%, trades/year ≥ 6, negative_years = 0.

## SELL (spread=0, diagnostic)

| Model | PF | Neg Yrs | Gate |
|-------|-----|---------|------|
| HGB | 1.36 | 1 | FAIL |
| RF | 0.91 | 3 | FAIL |

XAUUSD bull market асимметрия — SELL исключён из дальнейших инвестиций.

## Fill statistics (spread=0, train set)

| Metric | BUY | SELL |
|--------|-----|------|
| Fill rate | 98.5% | 98.6% |
| Instant (lag=0) | 97.4% | 97.8% |
| Ambiguous | 1.4% | — |

Почти все fill'ы мгновенные (первый бар после сигнала). Fill rate падает на ~2pp за каждые 0.20 спреда.

## Transformer (Phase 3): BUY TB на fractal features

**Данные:** 4,959 train / 1,134 val (BUY + filled only, canonical spread 0.20)
**Модель:** Transformer d=128, 8 heads, 3 layers, 306k params
**Таргеты:** buy_sl{2,3}_tp{3,6,9} — binary WIN/LOSS

| Target | Pos Rate | AUC |
|--------|----------|-----|
| buy_sl2_tp3 | 9.6% | **0.498** |
| buy_sl2_tp6 | 2.2% | 0.570 |
| buy_sl2_tp9 | 0.4% | 0.711 |
| buy_sl3_tp3 | 13.6% | 0.528 |
| buy_sl3_tp6 | 3.3% | 0.413 |
| buy_sl3_tp9 | 0.6% | 0.732 |

**Mean AUC: 0.575** (epoch 2, early stop at 12). Главный target `buy_sl2_tp3` — AUC=0.498 (чистая случайность). Высокие AUC на tp9 (0.71–0.73) — артефакт экстремального дисбаланса (0.4–0.6% positive).

**Вердикт:** Fractal features не несут predictивного сигнала для Transformer на limit-order labels. Консистентно с `docs/reports/2026-05-21-transformer-direction.md`.

## Ключевые решения

- **Limit-order at Close[row]**: делает Close-entry исполнимым. Fill window 6 баров, barrier 24 бара от fill
- **Conservative mode canonical**: same-bar fill+SL → SL; TP on fill bar → not counted
- **Per-side fill_lag**: BUY и SELL заполняются независимо
- **Spread-adjusted SELL exit**: TP/SL/timeout используют Ask=Bid+spread
- **NO_FILL исключён из train, но не из threshold sweep**: модель скоррит все ряды, PF только на filled
- **PF из `_pnl_r`**: реальные R-кратные, а не label-class-based
- **Работоспособность гипотезы**: подтверждена на каноническом спреде 0.20, но ломается при 2× спреде

## Вердикт

Limit-order entry convention — валидный метод сделать Close-entry исполнимым. Канонический BUY лимитник проходит gate (PF=1.53). Воспроизводимость ограничена — робастность теряется при спреде > 0.40.

Transformer на fractal features не извлекает сигнала (AUC=0.5) — повторяет вывод предыдущего Transformer Direction эксперимента. Baseline RF работает лучше (PF=1.53) за счёт деревьев на инженерных признаках, не на сырых фракталах.

SELL направление исключено из дальнейших инвестиций (исторический XAUUSD bull market создаёт неустранимую асимметрию).

## Created files

| File | Purpose |
|------|---------|
| `docs/superpowers/specs/2026-05-27-limit-order-entry-design.md` | Design spec |
| `docs/superpowers/plans/2026-05-27-limit-order-entry-implementation.md` | Implementation plan |
| `processing/label_signals.py` | `label_limit_order_barriers()` function |
| `tests/processing/test_limit_order_barriers.py` | 15 unit tests |
| `processing/purge_split.py` | 30-bar time-based purge |
| `processing/label_audit.py` | Fill/ambiguity audit |
| `ML/baseline/benchmark_limit_order_entry.py` | RF/HGB baseline |
| `ML/baseline/reports/limit_order_spread_grid.md` | Phase 1+2 spread grid report |
| `ML/limit_order_train.py` | Phase 3 Transformer training script |
| `ML/reports/limit_order_transformer.json` | Phase 3 results |
| `.opencode/agents/reviewer.md` | QA review agent |
