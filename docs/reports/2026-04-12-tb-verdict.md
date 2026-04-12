# Triple Barrier — Production Verdict

> **Date**: 2026-04-12 17:22
> **Status**: Completed — **not production (gate_fail)**
> **Goal**: Починить симулятор TB под float-конвенцию лейблов и вынести честный verdict по TB-слою как кандидату в MT4 execution
> **Related plan/spec**: `docs/superpowers/plans/2026-04-11-quantile-status-decision.md` (secondary TB stage)
> **Related commit**: pending
> **Rule**: [ML/reports/tb_selected_rule.json](../../ML/reports/tb_selected_rule.json) (`theta=0.475`, `min_ev=0.1`, support-gated)

---

## Короткий итог

TB-слой оценён по тем же n-boost критериям, что применялись к `entry_path_v1_quantile`. На validation (2019–2022) слой выглядит здоровым (PF=4.33), но на test (2023–2026) разваливается до PF=1.28 с 42% win_rate и двумя явно отрицательными годовыми срезами. **Gate не пройден.**

---

## 1. Предпосылки

До этого benchmark TB `simulate_mt4_tb` показывал `losses=0, pf=inf` на обоих сплитах — эти числа были артефактом бага, а не реальным результатом. Любое решение по TB блокировалось, пока симулятор не соответствует label-конвенции.

## 2. Найденный и устранённый баг симулятора

**Файл**: [ML/triple_barrier_mt4_execution.py](../../ML/triple_barrier_mt4_execution.py)

Label convention в `DATA/Nero_*_labeled.csv` — **float** (см. [processing/label_signals.py:919](../../processing/label_signals.py#L919)):

| значение | смысл |
|---:|---|
| `1.0` | TP первым коснулся |
| `0.0` | SL первым коснулся |
| `0.5` | Ни одного касания в окне (timeout) |

Симулятор же приводил outcome к `int`:
```python
outcome = int(source_row.get(open_position['source_target'], 0))
if outcome > 0: ...   # TP
elif outcome < 0: ... # SL — НИКОГДА не срабатывал
else: ...             # всё остальное → HoldOverTime, pnl=+0.5
```

`int(1.0)=1` срабатывал на TP, но `int(0.0)=0` и `int(0.5)=0` оба падали в `else`, так что **все SL перекодировались в "HoldOverTime" с положительным pnl_atr=+0.5**. `losses=0, pf=inf` — прямое следствие.

### Фикс

Добавлена константа-классификатор:
```python
def _classify_tb_outcome(raw) -> str:
    value = float(raw) if raw is not None else 0.5
    if value >= 0.75: return 'tp'
    if value <= 0.25: return 'sl'
    return 'timeout'
```
и обе точки закрытия позиции (регулярная и финальная) переведены на float-сравнение.

### Тесты

[tests/test_triple_barrier_mt4_execution.py](../../tests/test_triple_barrier_mt4_execution.py) использовал старую `{1, -1, 0}` int-схему и проходил ложно (`int()` возвращал исходные целые). Все 6 тестов переведены на float `{1.0, 0.0, 0.5}`. После правки: **6/6 зелёные**.

---

## 3. Gate-критерии (унифицированно с quantile)

| Критерий | Порог | Обоснование |
|---|---:|---|
| `N_trades` (test) | ≥ 30 | статистическая база |
| `PF` (test) | > 2.0 | запас над baseline |
| `negative_year_slices` | = 0 | нет убыточных лет (срезы с N<3 игнорируются) |

---

## 4. Результаты

### Validation (2019–2022)

```
trades=28 wins=16 losses=4 timeouts=2 reversals=8
PF=4.33 win_rate=57.1%
```

| year | N | PF | net_pnl_atr | win_rate |
|---:|---:|---:|---:|---:|
| 2019 | 6 | 2.17 | 3.5 | 0.50 |
| 2020 | 16 | 2.67 | 15.0 | 0.44 |
| 2021 | 2 | ∞ | 12.0 | 1.00 |
| 2022 | 4 | ∞ | 9.5 | 1.00 |

### Test (2023–2026)

```
trades=69 wins=29 losses=23 timeouts=5 reversals=17
PF=1.28 win_rate=42.0%
```

| year | N | PF | net_pnl_atr | win_rate |
|---:|---:|---:|---:|---:|
| 2023 | 6 | 0.55 | -5.0 | 0.33 |
| 2024 | 21 | 1.19 | 3.5 | 0.38 |
| 2025 | 34 | 2.12 | 28.0 | 0.56 |
| 2026 | 8 | 0.00 | -9.0 | 0.00 |

### Разбор по reason (test)

| reason | count | mean pnl_atr | sum |
|---|---:|---:|---:|
| TP | 24 | +3.25 | +78.0 |
| SL | 23 | -2.74 | -63.0 |
| TB_Reversal | 17 | 0.00 | 0.0 |
| HoldOverTime | 5 | +0.50 | +2.5 |

Чистый pnl_atr на test: **+17.5** на 69 сделок (средняя ≈ +0.25/trade). Dominant target — `buy_sl3_tp3` (46 из 69).

---

## 5. Gate-проверка

| Критерий | Значение | Результат |
|---|---:|---|
| N_trades (test) | 69 | ✅ |
| PF (test) | 1.28 | ❌ (порог 2.0) |
| negative_year_slices (test, N>3) | 2 (2023, 2026) | ❌ |

**Вердикт: gate_fail.**

---

## 6. Интерпретация

- **Validation vs test regime shift.** PF падает с 4.33 до 1.28, win_rate с 57% до 42%. Это не шумовая флуктуация — 2023 слабый (N=6, 33% win), 2026 полностью отрицательный (N=8, 0% win). Слой поймал конкретный режим 2019–2022 и не обобщается.
- **Baseline (простой score-filter A @ 7.5%)** на тех же тест-данных даёт ~15 трейдов и сопоставимый PF, quantile-слой — 48 трейдов при PF=8.18. TB при почти 5x большем N даёт PF в ~6 раз ниже quantile. Слой **не превосходит** ни baseline, ни quantile.
- **TP-ветка работает** (24 сделки, средняя +3.25 ATR, dominant target `buy_sl3_tp3`), но обнуляется стеной SL (23 сделки, средняя −2.74 ATR) и reversal-ами (17 сделок, +0.00).

---

## 7. Решение

TB-слой **не** подключается к MT4 как production или parallel execution mode. Production-опора остаётся `regression_updn` (baseline) + `entry_path_v1_quantile` (parallel, производит 22 сделки на test с PF=3.64 sequential).

### Что с TB делать дальше

- Rule `tb_selected_rule.json` зафиксирован как исторический артефакт — **не удалять**, но помечать frozen.
- Дальнейшие попытки монетизировать TB имеет смысл делать только с другим rule-селектором (не support-gated 80 trades), и обязательно с yearly-slicing gate на validation, а не только агрегатом.
- На forward-данных после 2026-06 будет полезно заново прогнать TB сделки — если 2026 catastrophic year окажется локальным всплеском, решение можно пересмотреть. До тех пор — закрыто.

---

## 8. Артефакты

- [ML/reports/tb_mt4_verdict/validation_summary.json](../../ML/reports/tb_mt4_verdict/validation_summary.json)
- [ML/reports/tb_mt4_verdict/validation_yearly.csv](../../ML/reports/tb_mt4_verdict/validation_yearly.csv)
- [ML/reports/tb_mt4_verdict/validation_trades.csv](../../ML/reports/tb_mt4_verdict/validation_trades.csv)
- [ML/reports/tb_mt4_verdict/test_summary.json](../../ML/reports/tb_mt4_verdict/test_summary.json)
- [ML/reports/tb_mt4_verdict/test_yearly.csv](../../ML/reports/tb_mt4_verdict/test_yearly.csv)
- [ML/reports/tb_mt4_verdict/test_trades.csv](../../ML/reports/tb_mt4_verdict/test_trades.csv)
