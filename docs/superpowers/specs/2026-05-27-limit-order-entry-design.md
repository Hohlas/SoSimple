# Limit Order Entry Convention — Design Spec

**Status:** draft
**Date:** 2026-05-27
**Branch:** (new feature branch, TBD)

## Problem

Текущий лейблинг использует `entry_price = Close[row]`, что давало высокие validation/test diagnostics под старым протоколом, но неисполнимо в live (fractal0 подтверждается только на Close 3-го бара → MQL пишет строку → watcher обрабатывает → bar уже закрыт). Попытка перейти на `entry_price = Open[row+1]` разрушила модель (PF=0.76, 528 label flips в high-confidence строках). Close[row] объявлен `DIAGNOSTIC_ONLY`, цикл methodology остановлен на Stage 09.

## Hypothesis

Лимитный ордер на уровне Close[row] делает Close-entry исполнимым: ордер висит до возврата цены, либо исполняется мгновенно по лучшей цене (если гэп в нашу пользу). Гэп перестаёт быть adversarial — он либо даёт лучший вход, либо задерживает вход, либо отменяет сигнал без убытка.

## Design

### 1. Entry Convention

| Параметр | Значение |
|----------|----------|
| Тип ордера | BUY LIMIT / SELL LIMIT |
| Цена ордера | `Close[row_time]` (из H1 OHLC, предполагаем Bid-priced) |
| Entry price для PnL | `Close[row_time]` (Ask для BUY, Bid для SELL — соответствует цене лимитного ордера в MT) |
| Fill window | 6 баров H1 (от t+1 до t+6 включительно) |
| Barrier window | 24 бара от fill (F+1 .. F+24) |
| Макс. длительность сделки | 30 баров от сигнала |
| No fill | Ордер отменяется, PnL = 0 |

#### Spread-adjusted fill and exit conditions

OHLC H1 — Bid-цены. В MT4:
- BUY: открывается по Ask, закрывается по Bid
- SELL: открывается по Bid, закрывается по Ask

Лимитная цена в MT:
- BUY LIMIT: `Ask_entry = Close[row]`
- SELL LIMIT: `Bid_entry = Close[row]`

**Fill conditions:**

| Направление | Fill-условие | Причина |
|-------------|-------------|--------|
| BUY LIMIT | `Low[Bid] <= Close[row] - spread` | Ask = Bid + spread; limit Ask = Close[row]; Low[Ask] ≤ limit → Low[Bid] + spread ≤ Close[row] |
| SELL LIMIT | `High[Bid] >= Close[row]` | Bid-Bid, без поправки |

**Exit (TP/SL) conditions:**

| Направление | TP условие | SL условие | Причина |
|-------------|-----------|-----------|--------|
| BUY | `High[Bid] >= Close[row] + tp*ATR` | `Low[Bid] <= Close[row] - sl*ATR` | Закрытие по Bid |
| SELL | `Low[Bid] <= Close[row] - tp*ATR - spread` | `High[Bid] >= Close[row] + sl*ATR - spread` | Закрытие по Ask ≈ Bid + spread |

Эффект spread на SELL: TP труднее достичь, SL легче достичь → PF SELL-сделок ниже, чем без spread. Это консервативно и правильно.

`spread` — НЕ хардкод. Берётся из MT symbol metadata / tester logs. Для XAUUSD на пятизнаке типичный спред 20–35 пунктов (0.20–0.35 USD), но единицы зависят от `Digits` символа.

Phase 1 запускается с **spread grid**: `[0, baseline, 2×baseline, 4×baseline]`. Это покажет чувствительность fill rate и PF к спреду.

Если spread превышает значимую долю ATR — fill rate и PF схлопнутся, гипотеза нежизнеспособна.

#### Внутрибаровые неоднозначности (same-bar ambiguity)

OHLC не даёт порядка тиков внутри бара. Возможны 4 типа неоднозначностей:

| Тип | Условие | Где возникает |
|-----|---------|---------------|
| Fill+SL same bar | `Low[F] <= limit AND Low[F] <= SL` (BUY) | На баре fill |
| Fill+TP same bar | `High[F] >= TP` после fill на том же баре | На баре fill |
| Fill+TP+SL same bar | Все три уровня задеты в одном баре | На баре fill |
| TP+SL same bar (post-fill) | `High >= TP AND Low <= SL` на любом баре после fill | В barrier scan |

**Каноническое правило (conservative mode):**

Для каждого TB-комбо независимо:

1. **На баре fill**: если `Low[F] <= SL` → SL (0). Игнорируем fill и TP на этом баре.
2. **В barrier scan (F+1 и далее)**: если в одном баре возможны и TP, и SL → считать SL (0).
3. **TP на баре fill**: не засчитывается (неизвестен порядок fill→TP).

Это максимально консервативно: любой бар, где возможен SL, считается SL.

**Диагностические режимы:**

| Режим | На баре fill | В barrier scan | Использование |
|-------|-------------|----------------|---------------|
| **conservative** | SL если Low≤SL | SL если TP+SL в одном баре | Канонический PF, gate |
| optimistic | Fill first, scan с F+1, order=TP→SL | TP first | Верхняя граница upside |
| ambiguous | Исключить строку из PF если fill bar двусмысленный | Исключить если barrier bar двусмысленный | Чувствительность |

### 2. Labeling Algorithm

Новая функция `label_limit_order_barriers()` в `processing/label_signals.py`.

Использует существующие константы: `TB_SL_LEVELS = [2, 3]`, `TB_TP_LEVELS = [3, 6, 9]` (2 SL × 3 TP = 6 пар × 2 направления = 12 таргетов).

Параметры: `fill_window=6`, `barrier_window=24`, `spread=0.0` (Phase 1: grid [0, baseline, 2×, 4×]), `mode="conservative"`.

```
Для каждой строки с валидным fractal0:
  1. entry_price = Close[row_time] (из H1 OHLC, Bid)
  2. ATR = raw ATR из строки
  3. effective_limit:
        BUY:  entry_price - spread
        SELL: entry_price (Bid-side)
  4. Fill-скан (бары t+1 .. t+fill_window):
        BUY:  ищем первый бар где Low <= effective_limit → fill_idx = абсолютный индекс бара в OHLC
        SELL: ищем первый бар где High >= effective_limit → fill_idx
        Не найден → все 12 TB таргетов = NO_FILL (-999), fill_lag = -1
        Найден → fill_lag = fill_idx - (ohlc_index_of_row + 1), диапазон 0..5
  5. Обработка внутрибаровых неоднозначностей (режим mode, для каждого TB-комбо):
      conservative:
        - На баре fill: если в том же баре возможен SL → SL (0).
          TP на баре fill не засчитывается (неизвестен порядок fill→TP).
        - В barrier scan: если в одном баре возможны и TP, и SL → SL (0).
      optimistic:
        - Fill first, barrier scan с F+1. Порядок в баре: TP, потом SL.
      ambiguous:
        - Если бар двусмысленный (fill+SL, fill+TP, TP+SL) → помечаем -888, исключаем из PF.
  6. Барьерный скан (бары fill_idx+1 .. fill_idx+barrier_window):
      first_touch_barrier_outcome(bars[...], direction, entry_price, sl_price, tp_price)
      Результат: 1=TP_FIRST, 0=SL_FIRST, 0.5=TIMEOUT
  7. PnL (R-multiples):
      _barrier_pnl() от бара fill с учётом spread на выходе для SELL:
        BUY  TP: +tp_r
        BUY  SL: -sl_r
        BUY  TIMEOUT: (CloseBid[last] - entry_price) / ATR
        SELL TP: +tp_r
        SELL SL: -sl_r
        SELL TIMEOUT: (entry_price - (CloseBid[last] + spread)) / ATR
      Примечание: BUY закрывается по Bid, BUY entry=Ask=Close[row], spread уже в entry.
                 SELL закрывается по Ask ≈ Bid + spread, поэтому TIMEOUT корректируется.
  8. Выходные колонки:
      buy_fill_lag: int (0..5 = баров после сигнала до BUY fill, -1 = NO_FILL)
      sell_fill_lag: int (0..5 = баров после сигнала до SELL fill, -1 = NO_FILL)
      ambiguous_flag_{target}: int per target combo (0=чистый, 1=fill+SL, 2=fill+TP,
                                3=fill+TP+SL, 4=post-fill TP+SL)
      {target}_pnl_r: float (R-multiple PnL для каждого TB-комбо)
```

#### Implementation notes

- `entry_price = Close[row_time]` — численно Bid-close из OHLC. Семантически: для BUY это **Ask-entry** (лимитник на Ask=CloseBid), для SELL это **Bid-entry**. В коде использовать явные имена:
  - `entry_exec_price = close_bid`
  - `buy_fill_bid_level = entry_exec_price - spread`
  - `sell_fill_bid_level = entry_exec_price`
- Same-bar ambiguity: таблица в секции 1 описана в BUY-терминах (Low, High). В коде использовать side-aware helpers с Bid/Ask/spread, не копировать таблицу буквально.

### 3. Model Training

- Transformer backbone: embedding + encoder-слои — без изменений (entry_path_v1_live_safe)
- Признаки: те же (live-safe, без future-derived)
- Детерминированное обучение: `torch.use_deterministic_algorithms(True)`
- Train/val/test: тот же temporal split (44104 / 9451 / 9451) по абсолютным номерам строк
- **Purge/embargo**: 30 H1 баров (fill 6 + barrier 24). Purge считается по времени (timestamp), а не по числу строк (защита от пропусков в данных). Три границы:

  1. **train→val**: строки train, чей `row_time + 30h` заходит в val-период — исключаются из train loss.
  2. **val→test**: строки val, чей `row_time + 30h` заходит в test-период — исключаются из threshold/rule selection.
  3. **test tail**: последние строки test, для которых нет 30h будущих баров — исключаются из final test metrics (UNKNOWN).
- **NO_FILL в обучении**: fill-only. NO_FILL строки исключаются из train loss (нет осмысленного TB-таргета). Модель видит только строки, где лимитник исполнился.
- **NO_FILL в оценке**: модель выдаёт скор для **всех** строк (включая NO_FILL). Порог выбирается на всех строках валидации без fill-фильтрации. Для каждого порога: сигналы = все строки выше порога → среди них fill-подмножество (считаем PF) и no_fill (информативно). Это гарантирует, что порог не тюнится с foreknowledge о том, какие сигналы исполнятся.
- Целевая переменная: `buy_sl3_tp3`. Значения: 0=SL, 0.5=Timeout, 1=TP.
- Формат таргета: скалярная регрессия (MSE loss), одна регрессионная голова.
- Для `ML/data_loader.py`: NO_FILL sentinel (-999) пропускается при загрузке train/val батчей.

### 4. Evaluation Metrics

PF = gross_profit / gross_loss в R-кратном выражении (Timeout включён по фактическому PnL). Формула соответствует `compute_pf` из `ML/utils.py`.

| Метрика | Определение |
|---------|-------------|
| PF (conservative) | gross_profit / gross_loss, conservative mode, только fill-строки среди selected signals |
| PF (optimistic) | То же, optimistic mode (диагностика upside) |
| mean_R_per_selected_signal | ΣR(filled) / N_selected (включая NO_FILL с R=0) |
| mean_R_per_filled_trade | ΣR / N_filled |
| Fill rate | N_filled / N_selected_signals |
| Selected signals/year | N_selected / years_in_period |
| Filled trades/year | N_filled / years_in_period (≥6 gate) |
| Negative filled-years | 0 (gate) |
| Win rate | TP / (TP + SL) среди fill-строк |
| Ambiguous-bar rate | Доля строк где ambiguous_flag_{primary_target} ≠ 0 среди fill (диагностика) |

#### Stratification по fill_lag

PF, Win rate, и число сигналов — раздельно по сторонам (buy_fill_lag / sell_fill_lag) и группам:

| Группа | fill_lag | Интерпретация |
|--------|----------|---------------|
| Instant | 0 (t+1) | Сигнал немедленно исполним |
| Quick | 1–2 (t+2, t+3) | Сигнал подтверждается в течение 1-2 баров |
| Slow | 3–4 (t+4, t+5) | Значительная задержка |
| Tail | 5 (t+6) | Маргинальный fill, модель decisions по старому snapshot |

Если edge существует только в Slow/Tail группах — стратегия сомнительна (stale signal). Если edge только в Instant/Quick — стратегия валидна.

### 5. Methodology Integration & Implementation Order

Новый entry convention → рестарт methodology cycle. Порядок с обязательным baseline-gate перед NN:

**Phase 1 — Labeling + Audit (без модели)**
- Реализовать `label_limit_order_barriers()` с conservative/optimistic/ambiguous режимами
- Регенерировать лейблы на полном датасете
- Аудит: распределение buy_fill_lag / sell_fill_lag, ambiguous_flag по target combo, доля NO_FILL по сторонам
- Аудит: сравнение `label_first_barrier_hit` (старый, entry=Close) vs `label_limit_order_barriers` (новый) на пересекающихся строках
- Purge/embargo: 30 H1 баров (по времени, не по числу строк), обновить split

**Phase 2 — RF/HGB Baseline (gate перед NN)**
- `buy_sl3_tp3` + несколько дополнительных SL/TP комбинаций
- Train на fill-only строках
- Threshold selection на ВСЕХ validation строках (без fill-фильтра)
- PF (conservative) по filled selected trades
- Если RF/HGB не дают PF ≥ 1.3 при fill_rate ≥ 20% → гипотезу закрываем, не идём в NN

**Phase 3 — Transformer (если Phase 2 пройдена)**
- Stages 05-10 methodology: EDA, baselines comparison, sweep, freeze, frozen test
- Все gate с conservative PF и fill_rate метриками

**Phase 4 — MT4 Execution (если Phase 3 пройдена)**
- Pending orders, spread-adjusted entry, expiration

### 6. Files Affected (реализация, не спекуляция)

**Phase 1 (labeling + audit):**

| File | Change |
|------|--------|
| `processing/label_signals.py` | +`label_limit_order_barriers()` с параметрами `fill_window`, `barrier_window`, `spread`, `mode` |
| `processing/label_main.py` | Условный вызов: `--limit-order` флаг, добавляет вызов новой функции в pipeline |
| `processing/label_audit.py` (новый) | Аудит buy_fill_lag / sell_fill_lag распределения, ambiguous_flag по target, сравнение со старыми лейблами |

**Phase 2 (RF/HGB baseline):**

| File | Change |
|------|--------|
| `ML/data_loader.py` | Обработка NO_FILL sentinel (-999), purge/embargo при загрузке |
| `ML/baseline/` | Новый скрипт: RF/HGB на `buy_sl3_tp3` + несколько SL/TP комбинаций с limit-order лейблами |
| `ML/utils.py` | Без изменений (`compute_pf` уже R-multiples) |

**Phase 3 (Transformer, если пройдена):**

| File | Change |
|------|--------|
| `ML/train.py` | Новый датасет, одна регрессионная голова (MSE), fill-only train |
| `ML/evaluate_test.py` | Fill rate, fill_lag stratification, conservative/optimistic PF |
| Methodology-скрипты | Пересоздание `validation_freeze.py`, `stage09_stability_refreeze.py` для нового цикла |

**Документация:**

| File | Change |
|------|--------|
| `docs/methodology/04-labeling.md` | +Limit Order entry convention, spread adjustment |
| `docs/methodology/12-backtest-costs.md` | +Purge/embargo 30 баров, pending order overlap |
| `docs/methodology/03-feature-contract-leakage.md` | +Preflight check для limit-order fill peek |

### 7. Open Questions

1. Порог fill_rate как methodology gate: какое минимальное значение? 20%? 30%?
2. Взвешивание train-семплов по fill_lag: ранний fill (0-1) весомее позднего (4-5)?
3. Нужно ли обучать отдельный fill/no-fill классификатор (2-я голова), или достаточно обучать только на fill-строках?
4. Достаточен ли spread grid [0, baseline, 2×, 4×] для определения жизнеспособности, или нужен более тонкий шаг вокруг baseline?
5. Purge/embargo 30 баров: достаточно ли, учитывая что OHLC может иметь внутрибаровую структуру, недоступную модели на Close[t]?
6. MT4 Tester validation: после Phase 2 (или Phase 3) прогнать сигналы через MT4 Strategy Tester для механической валидации fill-статистики?
