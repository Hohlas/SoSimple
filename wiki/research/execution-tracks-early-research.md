---
last_updated: 2026-05-14
sources: 4
status: active
---

# Execution Tracks: Exit Policy, Outcome-Aligned, Triple Barrier (04-08)

## 1. Exit Policy Research (04-08)

Offline simulator поверх regression_updn для сравнения семейств правил выхода.

**Семейства**: reverse_ratio, weak_edge, profit_guard, их комбинации.

**Результат**: validation winner = `timeout_only` (PF=1.17, 567 trades).
Это тот же `ML_Timeout(12H)`, который уже стоит в MT4. **Новых exit rules не найдено.**

**Вывод**: exit layer не является источником uplift для regression_updn. Если нужен прорыв — другой execution track или другой target.

Источник: [2026-04-08-ml-exit-validation-first.md](../../docs/reports/2026-04-08-ml-exit-validation-first.md)

## 2. Outcome-Aligned Retraining (04-08)

Три семейства outcome-aligned targets: `trade_outcome_cls`, `trade_pnl_reg`, `signal_archetype_cls`.

**Результат**: ни одно семейство не прошло общий trade floor + yearly stability filter на validation. Frozen winner не создан, test не запускался (validation-first discipline).

**Причины провала**:
- Labels по-прежнему close-at-12h, не повторяют реальную MT4 execution.
- trade_outcome и archetype_target схлопываются в одну задачу.
- trade_pnl на signal-only строках — "жёстко плохой" baseline universe.

**Вывод**: outcome-aligned подход требует execution-aware labels (next-bar entry, single open position, exit policy) — простой close-at-12h недостаточен.

Источник: [2026-04-08-outcome-aligned-retraining.md](../../docs/reports/2026-04-08-outcome-aligned-retraining.md)

## 3. Triple Barrier (04-08 — 04-12, три отчёта)

### Hardening: полная пересборка TB вне MT4

- First-touch labeling (24 бара), timeout = 0.5, старт от времени строки сигнала.
- Isotonic calibration вероятностей.
- Правило фиксируется только на validation: `theta=0.475, min_ev=0.10`.
- Test вне MT4: **PF=1.11, 253 trades** (128W / 125L / 24 timeout).
- BUY доминирует (670 BUY vs 46 SELL в train).

### Runtime Verdict: MT4-проверка

| Metric | Python (test) | MT4 (tester) |
|---|---:|---:|
| PF | 1.11 | **1.27** |
| Trades | 253 | 92 |
| SL/TP match | — | 93.8% (61/65) |

Разница объясняется MT4-правилами:
- PosBlock: 113 пропусков (открытая позиция).
- HoldOverTime: 22 закрытия.
- TB_Reversal: 4 закрытия.

**Вывод**: TB-схема согласована с MT4 по уровням. Следующий шаг — Python-режим, повторяющий MT4 execution один в один.

Источники: [2026-04-08-triple-barrier-hardening.md](../../docs/reports/2026-04-08-triple-barrier-hardening.md), [2026-04-08-triple-barrier-runtime-verdict.md](../../docs/reports/2026-04-08-triple-barrier-runtime-verdict.md)

### MT4 Verdict (04-12): gate_fail, не production

Финальный этап по TB-треку. До этого benchmark на `simulate_mt4_tb` давал `losses=0, pf=inf` на обоих сплитах — оказалось артефактом бага: симулятор кастовал outcome через `int(...)`, а лейблы в `DATA/Nero_*_labeled.csv` — float (`1.0=TP, 0.0=SL, 0.5=Timeout`, источник `processing/label_signals.py:919`). `int(0.0)=0` и `int(0.5)=0` оба падали в `else`-ветку `HoldOverTime, pnl=+0.5`, поэтому SL никогда не срабатывал.

Фикс: `_classify_tb_outcome` с порогами `>=0.75` → TP, `<=0.25` → SL, else → Timeout; применён в обеих точках закрытия позиции. Тесты `tests/test_triple_barrier_mt4_execution.py` переведены с устаревшей `{1, -1, 0}` int-схемы на float — 6/6 зелёные.

Честный прогон на `tb_selected_rule.json` (`theta=0.475`, `min_ev=0.1`):

| Split | N | wins | losses | timeouts | reversals | PF | win_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation | 28 | 16 | 4 | 2 | 8 | **4.33** | 57.1% |
| test | 69 | 29 | 23 | 5 | 17 | **1.28** | 42.0% |

Test yearly: 2023 PF=0.55 (N=6), 2024 PF=1.19 (N=21), 2025 PF=2.12 (N=34), 2026 PF=0.00 (N=8, 0% win). Validation yearly: все четыре года положительные (2019–2022).

Gate (унифицированно с quantile: N≥30, PF>2.0, `negative_year_slices=0`):
- N_trades: ✅ (69)
- PF: ❌ (1.28 < 2.0)
- negative_year_slices: ❌ (2023, 2026)

**Verdict**: TB-слой **не** подключается к MT4 как production или parallel execution mode. Явный regime shift между validation и test. `tb_selected_rule.json` зафиксирован как frozen исторический артефакт. Пересмотр возможен только после накопления forward-данных post-2026-06.

Источник: [2026-04-12-tb-verdict.md](../../docs/reports/2026-04-12-tb-verdict.md)
