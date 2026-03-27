# PF Improvement — Phase A: Исследования + EA оптимизация

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Провести 5 исследований (блок 1) для понимания полной картины, затем реализовать фильтрацию/оптимизацию EA для достижения PF ≥ 1.2 (baseline).

**Architecture:** Исследования выполняются Python-скриптами в `statistics/`. Изменения EA — в `lib_ML_Signal.mqh` и `$o$imple.mq4`. Валидация — через MT4 Strategy Tester + signal_tracer --from-log.

**Tech Stack:** Python 3.11+, numpy, csv, matplotlib (для scatter plots). MQL4 для EA.

**Spec:** `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`

---

## Task 1: A.1.1 — MARKET P&L: добавить close_price в CSV-экспорт

**Проблема:** `close_price` уже парсится из лога (signal_tracer.py:596) и хранится в dossier (строка 278), но **не включён в fieldnames CSV** (строка 720-725). 51% сделок (MARKET) не имеют точного P&L в текущем CSV.

**Files:**
- Modify: `statistics/signal_tracer.py:720-725` (fieldnames list)

- [ ] **Step 1: Добавить `close_price` и `mt4_pnl_atr` в CSV fieldnames**

В `statistics/signal_tracer.py`, строка ~720, добавить поля в список `fieldnames`:
```python
fieldnames = ['time', 'direction', 'ratio', 'close_type', 'mt4_result',
              'val', 'stp', 'prf', 'close_price', 'atr_mt4',
              'mt4_sl_dist', 'mt4_tp_dist', 'mt4_sl_atr', 'mt4_tp_atr',
              'mt4_pnl_pips', 'mt4_pnl_atr',
              'sl_dist', 'tp_dist', 'sl_atr', 'tp_atr',
              'sl_delta', 'tp_delta', 'atr_delta',
              'up_12', 'dn_12', 'category', 'lag_bars']
```

- [ ] **Step 2: Вычислять mt4_pnl_pips и mt4_pnl_atr в build_dossier**

В `statistics/signal_tracer.py`, после строки ~291, добавить расчёт P&L:
```python
# P&L для всех типов закрытия
cp = mt4_trade.get('close_price')
if cp is not None:
    if mt4_trade['dir'] == 'BUY':
        d['mt4_pnl_pips'] = cp - mt4_trade['val']
    else:
        d['mt4_pnl_pips'] = mt4_trade['val'] - cp
    d['mt4_pnl_atr'] = d['mt4_pnl_pips'] / mt4_trade['atr_mt4'] if mt4_trade['atr_mt4'] > 0 else 0
```

Для SL/TP сделок close_price может быть None (лог не содержит close #N для stop loss/take profit).
Для SL: `mt4_pnl_pips = -mt4_sl_dist`, для TP: `mt4_pnl_pips = +mt4_tp_dist`.

```python
if cp is None:
    if ct == 'SL':
        d['mt4_pnl_pips'] = -d.get('mt4_sl_dist', 0)
        d['mt4_pnl_atr'] = -d.get('mt4_sl_atr', 0)
    elif ct == 'TP':
        d['mt4_pnl_pips'] = d.get('mt4_tp_dist', 0)
        d['mt4_pnl_atr'] = d.get('mt4_tp_atr', 0)
```

- [ ] **Step 3: Перегенерировать all_trades.csv**

Run: `python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out all_trades.csv`

Проверить: `head -1 all_trades.csv` должен содержать `close_price;...;mt4_pnl_pips;mt4_pnl_atr`

- [ ] **Step 4: Посчитать полный PF с учётом MARKET**

```bash
python3 -c "
import csv
rows = list(csv.DictReader(open('all_trades.csv'), delimiter=';'))
total_win = sum(float(r['mt4_pnl_atr']) for r in rows if float(r.get('mt4_pnl_atr',0)) > 0)
total_loss = sum(abs(float(r['mt4_pnl_atr'])) for r in rows if float(r.get('mt4_pnl_atr',0)) < 0)
print(f'Full PF (all trades): {total_win/total_loss:.2f}' if total_loss > 0 else 'n/a')
print(f'Win ATR: {total_win:.1f}, Loss ATR: {total_loss:.1f}')
"
```

- [ ] **Step 5: Commit**

```bash
git add statistics/signal_tracer.py
git commit -m "feat(signal_tracer): add close_price and mt4_pnl_atr to CSV export"
```

---

## Task 2: A.1.2 — BOTH_HIT: анализ порядка барьеров

**Проблема:** 32 сделки категории BOTH_HIT — оба барьера (SL и TP) достигнуты за 12H. Нужно определить, что ударило первым. Это валидирует гипотезу path-dependent таргетов (фаза B).

**Files:**
- Create: `statistics/research_both_hit.py`

- [ ] **Step 1: Написать скрипт анализа BOTH_HIT**

Скрипт читает all_trades.csv, фильтрует BOTH_HIT, сравнивает mt4_result (SL или TP первым в MT4) с GT-предсказанием:

```python
"""
Анализ BOTH_HIT сделок: что ударило первым — SL или TP?
Использует mt4_result (реальный результат MT4) как ground truth порядка.
"""
import csv

rows = list(csv.DictReader(open('all_trades.csv'), delimiter=';'))
both = [r for r in rows if r['category'] == 'BOTH_HIT']

print(f"BOTH_HIT: {len(both)} сделок")
print()

sl_first = sum(1 for r in both if 'LOSS' in r['mt4_result'])
tp_first = sum(1 for r in both if 'WIN' in r['mt4_result'])
print(f"  SL first (MT4 LOSS): {sl_first} ({100*sl_first/len(both):.0f}%)")
print(f"  TP first (MT4 WIN):  {tp_first} ({100*tp_first/len(both):.0f}%)")

# Детали: R:R, ratio, direction
print(f"\n{'Time':<20} {'Dir':<5} {'Ratio':>6} {'SL_ATR':>7} {'TP_ATR':>7} {'up_12':>7} {'dn_12':>7} {'MT4':>10}")
for r in both:
    print(f"{r['time']:<20} {r['direction']:<5} {float(r['ratio']):>6.2f} "
          f"{float(r['mt4_sl_atr']):>7.2f} {float(r['mt4_tp_atr']):>7.2f} "
          f"{float(r['up_12']):>7.1f} {float(r['dn_12']):>7.1f} {r['mt4_result']:>10}")
```

- [ ] **Step 2: Run analysis**

Run: `python statistics/research_both_hit.py`

Записать результат: какой % BOTH_HIT → SL first. Если > 70%, path-dependent таргеты критичны.

- [ ] **Step 3: Commit**

```bash
git add statistics/research_both_hit.py
git commit -m "research(A.1.2): BOTH_HIT barrier order analysis"
```

---

## Task 3: A.1.3 — Корреляция pred_dn vs реальный adverse

**Проблема:** Модель предсказывает pred_dn ≈ 0 для BUY, но 40% выбиваются по SL. Нужно понять: pred_dn вообще коррелирует с реальным dn_12?

**Files:**
- Create: `statistics/research_pred_vs_gt.py`

- [ ] **Step 1: Написать скрипт корреляции**

```python
"""
Корреляция pred_dn vs dn_12 (ground truth) для BUY-сигналов.
Также: pred_up vs up_12 для SELL.
"""
import csv
import numpy as np

rows = list(csv.DictReader(open('all_trades.csv'), delimiter=';'))

# Для корреляции нужны pred_up/pred_dn — их нет в текущем all_trades.csv
# Загружаем из ml_signals.csv
sigs = {}
with open('MT/MQL4/Files/ml_signals.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for r in reader:
        sigs[r['time']] = r

buy_pred_dn = []
buy_real_dn = []
buy_ratio = []
for r in rows:
    if r['direction'] != 'BUY':
        continue
    sig = sigs.get(r['time'])
    if not sig:
        continue
    pred_dn = float(sig['pred_dn'])
    real_dn = float(r['dn_12'])
    buy_pred_dn.append(pred_dn)
    buy_real_dn.append(real_dn)
    buy_ratio.append(float(r['ratio']))

buy_pred_dn = np.array(buy_pred_dn)
buy_real_dn = np.array(buy_real_dn)

corr = np.corrcoef(buy_pred_dn, buy_real_dn)[0, 1]
print(f"BUY: pred_dn vs dn_12 correlation: {corr:.4f} (N={len(buy_pred_dn)})")
print(f"  pred_dn: mean={buy_pred_dn.mean():.4f}, median={np.median(buy_pred_dn):.4f}, max={buy_pred_dn.max():.4f}")
print(f"  real_dn: mean={buy_real_dn.mean():.2f}, median={np.median(buy_real_dn):.2f}, max={buy_real_dn.max():.2f}")

# Binned: pred_dn = 0 vs pred_dn > 0
zero_mask = buy_pred_dn < 0.01
print(f"\n  pred_dn ≈ 0 (<0.01): {zero_mask.sum()} trades, mean real_dn={buy_real_dn[zero_mask].mean():.2f}")
nonzero_mask = buy_pred_dn >= 0.01
if nonzero_mask.sum() > 0:
    print(f"  pred_dn > 0 (≥0.01): {nonzero_mask.sum()} trades, mean real_dn={buy_real_dn[nonzero_mask].mean():.2f}")

# Вывод: если corr < 0.2 → pred_dn бесполезен для SL, лучше const SL
print(f"\n{'='*50}")
if abs(corr) < 0.2:
    print("ВЫВОД: pred_dn СЛАБО коррелирует с реальным adverse → формула SL на основе pred_dn ненадёжна, const SL = 2 ATR предпочтительнее.")
else:
    print(f"ВЫВОД: корреляция {corr:.2f} — pred_dn ИНФОРМАТИВЕН для SL.")
```

- [ ] **Step 2: Run**

Run: `python statistics/research_pred_vs_gt.py`

- [ ] **Step 3: Commit**

```bash
git add statistics/research_pred_vs_gt.py
git commit -m "research(A.1.3): pred_dn vs real adverse correlation analysis"
```

---

## Task 4: A.1.4 — Walk-forward PF по полугодиям

**Проблема:** PF по годам: 0.44 / 0.53 / 0.63. Нужно понять стабильность по полугодиям.

**Files:**
- Create: `statistics/research_walkforward.py`

- [ ] **Step 1: Написать скрипт walk-forward**

```python
"""
PF и WR по полугодиям. Проверка стабильности модели во времени.
Использует mt4_pnl_atr из обновлённого all_trades.csv (task 1).
"""
import csv

rows = list(csv.DictReader(open('all_trades.csv'), delimiter=';'))

# Определяем полугодие
def half_year(time_str):
    y = time_str[:4]
    m = int(time_str[5:7])
    return f"{y}H{'1' if m <= 6 else '2'}"

periods = {}
for r in rows:
    hy = half_year(r['time'])
    if hy not in periods:
        periods[hy] = []
    periods[hy].append(r)

print(f"{'Period':<8} {'N':>4} {'W':>4} {'L':>4} {'WR':>6} {'PF(SL/TP)':>10} {'PF(full)':>10}")
print('-' * 60)

for hy in sorted(periods.keys()):
    sub = periods[hy]
    w = sum(1 for r in sub if 'WIN' in r['mt4_result'])
    l = sum(1 for r in sub if 'LOSS' in r['mt4_result'])
    wr = 100*w/len(sub) if sub else 0

    tp_sum = sum(float(r['mt4_tp_atr']) for r in sub if r['mt4_result'] == 'WIN(TP)')
    sl_sum = sum(float(r['mt4_sl_atr']) for r in sub if r['mt4_result'] == 'LOSS(SL)')
    pf_sltp = tp_sum/sl_sum if sl_sum > 0 else 0

    # Full PF (requires mt4_pnl_atr)
    pnl_col = 'mt4_pnl_atr'
    if pnl_col in sub[0]:
        win_atr = sum(float(r[pnl_col]) for r in sub if float(r.get(pnl_col, 0)) > 0)
        loss_atr = sum(abs(float(r[pnl_col])) for r in sub if float(r.get(pnl_col, 0)) < 0)
        pf_full = win_atr/loss_atr if loss_atr > 0 else 0
        pf_full_str = f"{pf_full:.2f}"
    else:
        pf_full_str = "n/a"

    print(f"{hy:<8} {len(sub):>4} {w:>4} {l:>4} {wr:>5.1f}% {pf_sltp:>9.2f} {pf_full_str:>10}")
```

- [ ] **Step 2: Run**

Run: `python statistics/research_walkforward.py`

- [ ] **Step 3: Commit**

```bash
git add statistics/research_walkforward.py
git commit -m "research(A.1.4): walk-forward PF by half-year periods"
```

---

## Task 5: A.1.6 — Entry slippage: market vs fractal price

**Проблема:** EA входит по market на T+1, цена уже ушла от фрактала. Нужно измерить потери от slippage для обоснования limit-ордера.

**Files:**
- Create: `statistics/research_entry_slippage.py`

- [ ] **Step 1: Написать скрипт анализа slippage**

```python
"""
Entry slippage: насколько market entry (val) хуже цены фрактала (price).
Для BUY: slippage = val - fractal_price (положительный = мы купили дороже)
Для SELL: slippage = fractal_price - val (положительный = мы продали дешевле)
"""
import csv
import numpy as np

rows = list(csv.DictReader(open('all_trades.csv'), delimiter=';'))

# Нужен fractal_price — он в signal_tracer dossier как 'price', но не экспортирован в CSV.
# Альтернатива: загрузить из Nero CSV напрямую.
# Пока используем batch.csv (если содержит price) или добавим price в all_trades.csv

# Проверяем наличие price в CSV
if 'price' not in rows[0]:
    print("ОШИБКА: поле 'price' (цена фрактала) отсутствует в all_trades.csv")
    print("Необходимо добавить 'price' в fieldnames signal_tracer.py (аналогично close_price)")
    print("Добавь 'price' в fieldnames и перегенерируй all_trades.csv")
    exit(1)

slippages = []
slippages_atr = []
for r in rows:
    val = float(r['val'])
    price = float(r['price'])
    atr = float(r['atr_mt4'])

    if r['direction'] == 'BUY':
        slip = val - price
    else:
        slip = price - val

    slippages.append(slip)
    slippages_atr.append(slip / atr if atr > 0 else 0)

s = np.array(slippages_atr)
print(f"Entry slippage (val - fractal_price), в ATR:")
print(f"  mean:   {s.mean():.3f}")
print(f"  median: {np.median(s):.3f}")
print(f"  p75:    {np.percentile(s, 75):.3f}")
print(f"  p90:    {np.percentile(s, 90):.3f}")
print(f"  > 0:    {(s > 0).sum()}/{len(s)} ({100*(s > 0).sum()/len(s):.0f}%) — мы купили дороже/продали дешевле")

# Группировка: wins vs losses
win_s = np.array([slippages_atr[i] for i, r in enumerate(rows) if 'WIN' in r['mt4_result']])
loss_s = np.array([slippages_atr[i] for i, r in enumerate(rows) if 'LOSS' in r['mt4_result']])
print(f"\n  Wins:   mean slippage = {win_s.mean():.3f} ATR")
print(f"  Losses: mean slippage = {loss_s.mean():.3f} ATR")
print(f"\n  Если slippage > 0.1 ATR — limit entry значимо улучшит PF")
```

- [ ] **Step 2: Добавить поле `price` в fieldnames signal_tracer.py**

В `statistics/signal_tracer.py:720`, добавить `'price'` в fieldnames (рядом с `'val'`).

- [ ] **Step 3: Перегенерировать all_trades.csv и запустить анализ**

```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out all_trades.csv
python statistics/research_entry_slippage.py
```

- [ ] **Step 4: Commit**

```bash
git add statistics/research_entry_slippage.py statistics/signal_tracer.py
git commit -m "research(A.1.6): entry slippage analysis (market vs fractal price)"
```

---

## Task 6: A.2.1 + A.2.2 — ML_MaxRatio + динамический MaxRR в EA

**Проблема:** ratio > 4.5 убыточен (PF 0.08–0.43). Текущий MaxRR=4.0 создаёт недостижимый TP.

**Files:**
- Modify: `MT/MQL4/Experts/$o$imple.mq4:59-65` (extern params)
- Modify: `MT/MQL4/Include/lib_ML_Signal.mqh:165-193` (SL/TP formula)

- [ ] **Step 1: Добавить extern-параметры в $o$imple.mq4**

После строки `extern double ML_MaxRR = 4.0;` добавить:
```c
extern double ML_MaxRatio     = 0;     // ML: Макс ratio (0=без ограничения). Рекомендация: 4.5
extern int    ML_RR_Mode      = 0;     // ML: 0=текущий (min/cap), 1=log+cap, 2=sqrt
extern double ML_RR_Cap       = 2.5;   // ML: Потолок R:R для режимов 1,2
```

- [ ] **Step 2: Добавить фильтр ML_MaxRatio в lib_ML_Signal.mqh**

В строке 165, изменить условие BUY:
```c
if (sig == 1 && BUY.Typ == NONE && ML_RatioUp[idx] >= ML_MinRatio
    && (ML_MaxRatio <= 0 || ML_RatioUp[idx] <= ML_MaxRatio)) {
```

Аналогично для SELL в строке 186:
```c
else if (sig == -1 && SEL.Typ == NONE && ML_RatioDn[idx] >= ML_MinRatio
         && (ML_MaxRatio <= 0 || ML_RatioDn[idx] <= ML_MaxRatio)) {
```

- [ ] **Step 3: Реализовать динамический MaxRR в lib_ML_Signal.mqh**

Заменить формулу TP (строки 172 и 193). Вместо:
```c
float tp_dist = sl_dist * (float)MathMin(ML_RatioUp[idx] / ML_MinRatio, ML_MaxRR);
```

Использовать:
```c
float rr;
double r = ML_RatioUp[idx] / ML_MinRatio;  // для BUY; для SELL — ML_RatioDn
switch(ML_RR_Mode) {
    case 1:  rr = (float)MathMin(MathLog(r) + 1.0, ML_RR_Cap); break;  // log + cap
    case 2:  rr = (float)MathMin(MathSqrt(r),       ML_RR_Cap); break;  // sqrt + cap
    default: rr = (float)MathMin(r,                  ML_MaxRR);  break;  // текущий
}
float tp_dist = sl_dist * rr;
```

- [ ] **Step 4: Добавить skip reason для MaxRatio**

В блоке else (строка ~208), добавить:
```c
else if (sig== 1 && ML_MaxRatio > 0 && ML_RatioUp[idx] > ML_MaxRatio) { skip_reason = "HighRatio"; }
else if (sig==-1 && ML_MaxRatio > 0 && ML_RatioDn[idx] > ML_MaxRatio) { skip_reason = "HighRatio"; }
```

- [ ] **Step 5: Commit**

```bash
git add MT/MQL4/Experts/\$o\$imple.mq4 MT/MQL4/Include/lib_ML_Signal.mqh
git commit -m "feat(EA): add ML_MaxRatio filter + dynamic MaxRR modes (log/sqrt/cap)"
```

---

## Task 7: A.2.5 — ML-exit: закрытие позиции по ML-сигналу

**Проблема:** 73% TIMEOUT = убыток. Модель может видеть adverse движение на новом фрактале.

**Scope:** Это крупная фича, требующая изменений в generate_signals.py (экспорт pred для всех баров) и lib_ML_Signal.mqh (проверка exit на каждом баре). **Реализация — фаза B**, здесь только исследование: есть ли корреляция между pred_dn на последующих барах и LOSS(MKT).

**Files:**
- Create: `statistics/research_ml_exit.py`

- [ ] **Step 1: Написать скрипт исследования**

Для каждой LOSS(MKT) сделки: найти ml_signals.csv предсказания на барах T+1..T+12 после входа. Если pred_dn растёт — модель "видела" adverse.

```python
"""
Исследование: может ли ML-сигнал на последующих барах предсказать LOSS(MKT)?
Для каждой LOSS(MKT) BUY-сделки смотрим pred_dn на барах T+1..T+12.
"""
import csv
from datetime import datetime, timedelta

# Загрузить ВСЕ строки ml_signals.csv (включая signal=0)
# ВНИМАНИЕ: текущий ml_signals.csv содержит только signal≠0.
# Если signal=0 отсутствует, исследование невозможно → нужен перегенерация.
all_preds = {}
with open('MT/MQL4/Files/ml_signals.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for r in reader:
        all_preds[r['time']] = r

rows = list(csv.DictReader(open('all_trades.csv'), delimiter=';'))
loss_mkt_buy = [r for r in rows if r['mt4_result'] == 'LOSS(MKT)' and r['direction'] == 'BUY']

print(f"LOSS(MKT) BUY: {len(loss_mkt_buy)} сделок")
print(f"ml_signals.csv: {len(all_preds)} строк (signal≠0 only: нужен перегенерация для полного анализа)")

# Проверяем: есть ли SELL-сигнал (sig=-1) в окне T+1..T+12?
has_reverse = 0
for r in loss_mkt_buy:
    t = datetime.strptime(r['time'], '%Y.%m.%d %H:%M')
    for offset in range(1, 13):
        t2 = (t + timedelta(hours=offset)).strftime('%Y.%m.%d %H:%M')
        sig = all_preds.get(t2)
        if sig and int(sig['signal']) == -1:
            has_reverse += 1
            break

print(f"  Есть SELL-сигнал в окне T+1..T+12: {has_reverse}/{len(loss_mkt_buy)} ({100*has_reverse/len(loss_mkt_buy):.0f}%)")
print(f"  Если > 30% — ML-exit имеет потенциал")
```

- [ ] **Step 2: Run**

Run: `python statistics/research_ml_exit.py`

- [ ] **Step 3: Commit**

```bash
git add statistics/research_ml_exit.py
git commit -m "research(A.2.5): ML-exit potential — reverse signal in loss window"
```

---

## Task 8: A.1.5 — Прогон MT4 тестера с фильтрами (ручной)

**Проблема:** Нужен реальный PF на MT4 Strategy Tester с новыми параметрами.

> **Этот task выполняется пользователем вручную в MT4.**

- [ ] **Step 1: Baseline прогон (текущие параметры)**

Записать: PF, WR, N trades, equity curve. Сохранить лог.

- [ ] **Step 2: Прогон с ML_MaxRatio=4.5, ML_RR_Mode=0**

Изменить в тестере: `ML_MaxRatio=4.5`. Записать результат.

- [ ] **Step 3: Прогон с ML_MaxRatio=0, ML_RR_Mode=1 (log+cap), ML_RR_Cap=2.5**

Записать результат.

- [ ] **Step 4: Прогон с ML_MaxRatio=4.5 + ML_RR_Mode=1 (комбо)**

Записать результат.

- [ ] **Step 5: Прогон с ML_BypassTrend=false**

Записать результат.

- [ ] **Step 6: signal_tracer для лучшего прогона**

```bash
python statistics/signal_tracer.py --from-log MT/tester/logs/BEST.log --csv-out best_trades.csv
```

Сравнительная таблица результатов → записать в `docs/archive/signal_tracer/phase_a_results.md`.

---

## Task 9: Отчёт фазы A

**Files:**
- Create: `docs/archive/signal_tracer/phase_a_results.md`

- [ ] **Step 1: Собрать результаты исследований**

Свести все результаты Tasks 1–8 в отчёт:
- Full PF (с MARKET P&L)
- BOTH_HIT: SL first %
- Корреляция pred_dn
- Walk-forward стабильность
- Entry slippage
- ML-exit потенциал
- Прогоны MT4 тестера

- [ ] **Step 2: Выводы и рекомендации для фазы B**

На основе результатов определить:
1. Нужны ли path-dependent таргеты (BOTH_HIT анализ)?
2. Полезен ли pred_dn для SL (корреляция)?
3. Стоит ли limit-entry (slippage)?
4. Стоит ли ML-exit (reverse signal %)?
5. Оптимальные параметры EA (MaxRatio, RR_Mode, RR_Cap)

- [ ] **Step 3: Commit**

```bash
git add docs/archive/signal_tracer/phase_a_results.md
git commit -m "docs: Phase A research results and recommendations"
```

---

## Порядок выполнения

```
Task 1 (close_price в CSV) ─── ПЕРВЫЙ, остальные зависят от него
    ↓
Task 2, 3, 4, 5, 7 ── ПАРАЛЛЕЛЬНО (независимые исследования)
    ↓
Task 6 (EA изменения) ── после понимания результатов
    ↓
Task 8 (MT4 тестер) ── после Task 6 (нужен обновлённый EA)
    ↓
Task 9 (отчёт) ── после всех
```
