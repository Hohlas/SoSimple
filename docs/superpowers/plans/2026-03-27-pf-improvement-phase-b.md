# PF Improvement — Phase B: Новые таргеты + Лимитный вход

> **Spec:** `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`
> **Цель:** PF ≥ 2.0 (агрегат), PF ≥ 1.5 по каждому году
> **Старт:** Phase A baseline = PF 1.23 (367 сделок)

---

## Блок 1: Исследования (до реализации)

### Task 1: Path-ordering анализ BOTH_HIT (B.3 prep)

**Цель:** Проверить, что в BOTH_HIT барах SL действительно бьёт первым, и подобрать правило для label_signals.py.

**Данные:**
- `statistics/all_trades.csv` — все сделки с gt_category=BOTH_HIT
- `DATA/XAUUSD_H1_OHLC.csv` — 126,637 H1 баров с Open/High/Low/Close

**Что сделать:**
1. Из all_trades.csv взять все BOTH_HIT сделки (BUY и SELL)
2. Для каждой сделки: по bar_time + dir определить SL_level и TP_level (из mt4_stp, mt4_prf полей)
3. Прокрутить H1 OHLC bar-by-bar (от bar+1 до bar+12): первый бар, где High≥TP или Low≤SL — фиксируем результат
4. Случай "оба в одном баре": сравниваем (Open - Low) vs (High - Open)
5. Посчитать: в BOTH_HIT какой % SL first vs TP first

**Артефакт:** Markdown отчёт `docs/archive/signal_tracer/path_ordering_analysis.md` + число `%SL_first`

**Script:** `statistics/analyze_path_ordering.py` (новый)

---

### Task 2: Слипаж лимитного ордера (B.2 prep)

**Цель:** Оценить, сколько сделок вернулось бы к цене фрактала для исполнения Buy Limit.

**Данные:**
- `statistics/all_trades.csv` — поле `val` (цена входа MT4), нужно поле `fractal_price` (close фрактального бара)
- `DATA/XAUUSD_H1_OHLC.csv` — для проверки баров

**Что сделать:**
1. `fractal_price` ≈ Close[bar] на момент сигнала — это цена, по которой был бы выставлен лимит
2. `val` = цена реального входа в MT4
3. `slippage = val - fractal_price` для BUY (положительный = хуже цены фрактала)
4. Посчитать: mean/median slippage в ATR
5. Симуляция: для всех SIGNAL-сделок проверить — если бы лимит стоял на fractal_price, достигла ли Low цену в течение следующих N=3,6 баров? (% исполненных лимиток)
6. Оценить изменение PF при исполнении через лимит

**Артефакт:** Отчёт `docs/archive/signal_tracer/limit_order_analysis.md`

---

### Task 3: Анализ 2025H2 слабости

**Цель:** Понять, почему PF=0.63 в 2025H2 (6 месяцев), чтобы не оверфитить.

**Что сделать:**
1. Из all_trades.csv отфильтровать 2025-07-01 .. 2025-12-31
2. Сравнить распределение: ratio, gt_category, dir (BUY/SELL), ATR
3. Проверить: изменился ли рынок (ATR, волатильность)? Или модель деградировала?
4. Проверить: есть ли кластер "убийц" — конкретные диапазоны ratio/gt_category с плохим PF?

**Артефакт:** Раздел в `docs/archive/signal_tracer/phase_b_research.md`

---

## Блок 2: Лимитный вход в EA (быстрый выигрыш)

### Task 4: Buy/Sell Limit в lib_ML_Signal.mqh

**Зависимость:** Task 2 (данные о % исполнения лимиток)

**Если Task 2 покажет:** слипаж > 0.2 ATR и > 60% лимиток исполняются → реализуем.

**Что изменить в EA:**

В `lib_ML_Signal.mqh`, функция `ML_TRADE()`:

1. Добавить новый extern-параметр `ML_EntryMode` (0=MARKET, 1=LIMIT)
2. При ML_EntryMode=1:
   - BUY: `set.BUY.Val = fractal_close_price` (цена Close фрактального бара сигнала)
   - Тип ордера: Buy Limit (pending order)
   - SL/TP от `set.BUY.Val`, не от текущего Ask
   - Экспирация: `ML_PendingExpiry` баров
3. При ML_EntryMode=0: без изменений (текущее поведение)

**Новые extern в $o$imple.mq4:**
```c
extern char   ML_EntryMode     = 0;  // 0=MARKET, 1=LIMIT (fractal price)
extern char   ML_PendingExpiry = 3;  // баров до отмены лимитки
```

**Сложности:**
- Цена фрактала нужна в ML_TRADE() — получать из ML-CSV или из Close[bar+N]
- Лимитки требуют особой обработки в ORDERS.mqh (проверка исполнения)

**Артефакт:** обновлённые `lib_ML_Signal.mqh`, `$o$imple.mq4`, `$o$imple.ini`

---

## Блок 3: Новые таргеты (переобучение модели)

### Task 5: First-barrier-hit лейблинг (B.3)

**Зависимость:** Task 1 (path-ordering анализ)

**Что добавить в `processing/label_signals.py`:**

```python
def label_first_barrier_hit(df_signals, ohlc_h1, sl_atrs=[1.5, 2.0, 2.5], tp_atrs=[2.0, 3.0, 4.0, 6.0]):
    """
    Для каждого сигнала и каждой пары (SL_ATR, TP_ATR) определяет:
    1 = TP hit first, 0 = SL hit first, 0.5 = TIMEOUT (ни один за 12 баров)
    Возвращает DataFrame с 12 бинарными таргетами.
    """
```

Логика bar-by-bar:
- `entry_price = Close[bar_idx]` (цена фрактала)
- `sl_price = entry_price - sl_atr * ATR` (для BUY)
- `tp_price = entry_price + tp_atr * ATR`
- Скан H1 OHLC[bar+1..bar+12]:
  - если `Low[i] <= sl_price` и `High[i] >= tp_price` → oба: compare `Open[i]-sl_price` vs `tp_price-Open[i]`
  - если только `High[i] >= tp_price` → TP=1
  - если только `Low[i] <= sl_price` → SL=0
- Если ничего за 12 баров → 0.5

**Новые колонки:** `win_sl15_tp20`, `win_sl15_tp30`, ..., `win_sl25_tp60` (12 штук)

**Артефакт:** обновлённый `processing/label_signals.py`

---

### Task 6: Расширение горизонтов 3H/6H (B.1)

**Что добавить в `MT/MQL4/Include/lib_PIC.mqh`** (NERO_CSV_CREATE):
- Расчёт `up_3`, `dn_3`, `up_6`, `dn_6` аналогично up_12, dn_12

**Что добавить в `processing/label_signals.py`:**
- Лейблинг up_3/dn_3/up_6/dn_6 (max excursion за 3 и 6 баров)

**Что добавить в `ML/data_loader.py`:**
- Расширить UPDN_TARGETS: `['up_3','dn_3','up_6','dn_6','up_12','dn_12','up_24','dn_24','up_48','dn_48']`

**Зачем сначала анализ (Task 1/2), потом это:**
- Если BOTH_HIT SL_first > 70% → приоритет Task 5 (first-barrier-hit) над Task 6
- Если BOTH_HIT SL_first < 50% → другая проблема, нужен доп. анализ

---

### Task 7: Asymmetric loss (B.4)

**Что изменить в `ML/train.py`** (или loss.py):

```python
# Вместо MSE
alpha = 2.5  # штраф за недооценку adverse

for i, tgt in enumerate(UPDN_TARGETS):
    if 'dn' in tgt:  # adverse для BUY
        loss += alpha * F.mse_loss(pred[:, i], true[:, i])
    else:
        loss += F.mse_loss(pred[:, i], true[:, i])
```

**Тестировать:** alpha = 1.5, 2.0, 2.5, 3.0 на validation set.

---

## Блок 4: Валидация

### Task 8: Переобучение и тест сигналов

После Task 5-7:
1. Запустить полный pipeline: `label_main.py` → `train.py` → `generate_signals.py`
2. Запустить `signal_tracer.py --from-log` на новом ml_signals.csv
3. Сравнить OOS PF Python vs MT4

### Task 9: MT4 Strategy Tester

1. Скопировать новый ml_signals.csv в MT4/Files/
2. Запустить тестер с Phase B параметрами
3. Зафиксировать PF, WR, MaxDD, walk-forward по годам

---

## Приоритет задач

```
Task 1 (path-ordering)  ←── ПЕРВЫЙ: определяет архитектуру таргетов
Task 2 (limit slippage) ←── ПАРАЛЛЕЛЬНО с Task 1
Task 3 (2025H2)         ←── ПАРАЛЛЕЛЬНО

Task 4 (EA limit)       ←── после Task 2 (если slippage > 0.2 ATR)
Task 5 (first-barrier)  ←── после Task 1 (если SL_first > 70%)
Task 6 (3H/6H targets)  ←── после Task 5 (расширение)
Task 7 (asymm loss)     ←── параллельно с Task 5/6

Task 8+9 (train+test)   ←── ФИНАЛ
```

---

## Ожидаемый результат

| Изменение | Ожидаемый прирост PF | Риск |
|---|---|---|
| Лимитный вход (+0.034 ATR) | +0.05–0.10 | Низкий (часть сделок не исполнится) |
| First-barrier-hit таргеты | +0.3–0.6 | Средний (переобучение) |
| 3H/6H таргеты | +0.1–0.2 | Низкий |
| Asymmetric loss | +0.1–0.3 | Низкий |
| **Итого Phase B** | **PF ~1.7–2.3** | — |
