# Triple Barrier Classification — Design Spec

> **Дата**: 2026-03-22
> **Статус**: Draft
> **Трек**: Параллельный (не заменяет regression_updn)

---

## 1. Цель

Создать ML-модель, которая предсказывает вероятность касания TP-барьера раньше SL-барьера для 6 комбинаций SL/TP × 2 направления = 12 бинарных таргетов.

**Проблема**: Текущая regression_updn модель показывает PF=4.50 на OOS, но PF≈1.03 в MT4, потому что Python PF считает сумму MFE (идеальных пиковых экскурсий), а MT4 торгует с фиксированными SL/TP. Triple Barrier устраняет этот разрыв — метрика PF напрямую соответствует торговой механике.

**Параллельность**: regression_updn сохраняется без изменений. Оба трека работают независимо, каждый со своим чекпоинтом, сигналами и MT4-функцией.

---

## 2. Параметры барьеров

### SL/TP сетка (в единицах ATR)

| # | Направление | SL | TP | R:R | Имя таргета |
|---|-------------|----|----|-----|-------------|
| 1 | BUY | 2 | 3 | 1:1.5 | buy_sl2_tp3 |
| 2 | BUY | 2 | 6 | 1:3.0 | buy_sl2_tp6 |
| 3 | BUY | 2 | 9 | 1:4.5 | buy_sl2_tp9 |
| 4 | BUY | 3 | 3 | 1:1.0 | buy_sl3_tp3 |
| 5 | BUY | 3 | 6 | 1:2.0 | buy_sl3_tp6 |
| 6 | BUY | 3 | 9 | 1:3.0 | buy_sl3_tp9 |
| 7 | SELL | 2 | 3 | 1:1.5 | sell_sl2_tp3 |
| 8 | SELL | 2 | 6 | 1:3.0 | sell_sl2_tp6 |
| 9 | SELL | 2 | 9 | 1:4.5 | sell_sl2_tp9 |
| 10 | SELL | 3 | 3 | 1:1.0 | sell_sl3_tp3 |
| 11 | SELL | 3 | 6 | 1:2.0 | sell_sl3_tp6 |
| 12 | SELL | 3 | 9 | 1:3.0 | sell_sl3_tp9 |

### Временной барьер
- **Timeout**: 24 бара (H1 → 24 часа)
- Используются существующие `up_24` / `dn_24` из dataset

---

## 3. Маркировка (Labeling)

### Источник данных
- `up_24`, `dn_24` — максимальные экскурсии вверх/вниз за 24 бара (из fractal[0])
- `ATR` — ATR строки (сырой, до нормализации)

### Логика маркировки

Функция `label_triple_barrier()` в `processing/label_main.py`. Вызывается ПОСЛЕ `label_updn()`, ДО `normalize_rowwise()` — на сырых (ненормализованных) данных.

**Единицы**: up_24/dn_24 хранятся в raw price (max(High-P) / max(P-Low) в валюте инструмента). Деление на ATR обязательно для перевода в ATR-единицы.

```python
def label_triple_barrier(df):
    """Вычисляет 12 бинарных Triple Barrier меток из raw MFE."""
    up = df['up_24']  # max excursion up за 24 бара (raw price)
    dn = df['dn_24']  # max excursion down за 24 бара (raw price)
    atr = df['ATR']

    # Конвертация в ATR-единицы (обязательно — raw price → ATR units)
    up_atr = up / atr
    dn_atr = dn / atr

    SL_LEVELS = [2, 3]
    TP_LEVELS = [3, 6, 9]

    for sl in SL_LEVELS:
        for tp in TP_LEVELS:
            # BUY: цена вверх на TP*ATR, не упав на SL*ATR
            df[f'buy_sl{sl}_tp{tp}'] = ((up_atr >= tp) & (dn_atr < sl)).astype(int)
            # SELL: зеркально
            df[f'sell_sl{sl}_tp{tp}'] = ((dn_atr >= tp) & (up_atr < sl)).astype(int)

    return df
```

### Обработка неоднозначных случаев
- Если `up_24 >= TP*ATR` И `dn_24 >= SL*ATR` → метка = **0** (консервативно)
- Это автоматически следует из условия `dn_atr < sl` — если dn достиг SL, условие false → 0

### Ожидаемое распределение меток
- Узкие барьеры (SL=2, TP=3): больше единиц (чаще достигается)
- Широкие (SL=2, TP=9): мало единиц (редко цена идёт 9 ATR без отката 2 ATR)
- Дисбаланс классов ожидаем — учесть при обучении (pos_weight в BCEWithLogitsLoss)

---

## 4. Pipeline изменений

### Файлы, требующие изменений

| Файл | Изменение |
|------|-----------|
| `processing/label_main.py` | Добавить `label_triple_barrier()`, вызвать после `label_updn()` |
| `ML/data_loader.py` | Новый target='triple_barrier', загрузка 12 колонок |
| `ML/train.py` | Новый `--task triple_barrier`, BCEWithLogitsLoss, binary metrics |
| `ML/utils.py` | Метрики: AUC, Precision, Recall per-target |
| `ML/compare_architectures.py` | Поддержка `--task triple_barrier` |
| `ML/optimize.py` | Поддержка `--task triple_barrier` |
| `ML/evaluate_test.py` | OOS оценка для triple_barrier |
| `ML/threshold_analysis.py` | Реалистичный PF из SL/TP (новая функция) |
| `API/generate_signals.py` | Генерация `ml_signals_tb.csv` |
| `ML/experiment_logger.py` | Логирование AUC и per-target binary метрик для triple_barrier |

### Новые файлы

| Файл | Назначение |
|------|-----------|
| `MT/MQL4/Include/lib_ML_Signal_TB.mqh` | MT4 интеграция Triple Barrier сигналов |

### Файлы БЕЗ изменений
- `processing/normalize.py` — TB метки бинарные, не нормализуются
- `lib_ML_Signal.mqh` — regression_updn трек не трогаем
- `ML/models/*` — архитектуры переиспользуются, только выходной слой меняется

---

## 5. Data Loader

Новый режим в `data_loader.py`:

```python
if task == 'triple_barrier':
    target_cols = [
        'buy_sl2_tp3', 'buy_sl2_tp6', 'buy_sl2_tp9',
        'buy_sl3_tp3', 'buy_sl3_tp6', 'buy_sl3_tp9',
        'sell_sl2_tp3', 'sell_sl2_tp6', 'sell_sl2_tp9',
        'sell_sl3_tp3', 'sell_sl3_tp6', 'sell_sl3_tp9',
    ]
    y = df[target_cols].values  # shape: (N, 12), dtype: float32
```

Фичи (X) — те же 20 features на 100 фракталов, что и в regression_updn.

**Кэш**: При первом запуске с triple_barrier необходимо удалить `.npy` кэш-файлы в `DATA/` (или использовать `clear_cache=True`), иначе data_loader загрузит старые данные без TB-колонок.

---

## 6. Обучение

| Параметр | Значение |
|----------|----------|
| Task | `triple_barrier` |
| Loss | `BCEWithLogitsLoss` с `pos_weight` (рассчитывается из train set) |
| Выходной слой | Тот же classifier head, что и в regression_updn, с `num_classes=12` |
| Early stopping | Mean AUC на validation (patience=10) |
| Scheduler | ReduceLROnPlateau (monitor=val_mean_auc) |
| Чекпоинт | `ML/checkpoints/transformer_tb_best.pt` |

### Метрики (per-target + mean)
- **AUC ROC** — основная, порог-независимая
- **Precision / Recall** @ threshold — для анализа
- **Calibration** — совпадение P(TP hit) с реальной частотой (reliability diagram)

---

## 7. Threshold Analysis (реалистичный PF)

Ключевое отличие от regression_updn: PF считается из **фиксированных SL/TP**, а не из MFE.

```python
def analyze_triple_barrier(y_pred_proba, y_true, sl, tp, thresholds):
    for theta in thresholds:
        buy_mask = y_pred_proba[:, col_buy] > theta
        sell_mask = y_pred_proba[:, col_sell] > theta

        # BUY trades
        buy_wins = y_true[buy_mask, col_buy].sum()       # count of TP hits
        buy_losses = buy_mask.sum() - buy_wins            # SL hits + timeouts

        # SELL trades (аналогично)
        sell_wins = y_true[sell_mask, col_sell].sum()
        sell_losses = sell_mask.sum() - sell_wins

        profit = (buy_wins + sell_wins) * tp
        loss = (buy_losses + sell_losses) * sl

        pf = profit / loss
```

**Консервативная нижняя граница PF**: Timeouts считаются как полный SL loss. В реальности MT4 закрывает по рыночной цене через 24 бара — убыток может быть меньше SL. Поэтому реальный MT4 PF будет >= Python PF.

---

## 8. Генерация сигналов

### Стратегия выбора лучшей комбинации

Для каждого бара из 12 таргетов:
1. Отфильтровать: `P(TP hit) > θ`
2. Из оставшихся выбрать по максимальному **Expected Value**:
   ```
   EV = P × TP - (1 - P) × SL
   ```
3. Определить направление (BUY/SELL) и SL/TP из имени таргета
4. **Конфликт BUY+SELL**: если оба направления прошли порог — выбирается по максимальному EV. При равном EV — FLAT (не торгуем)

### Формат `ml_signals_tb.csv`

```
time;signal;sl_atr;tp_atr;prob;ev
2023.01.03 04:00;1;2.0;6.0;0.73;3.42
2023.01.03 10:00;-1;3.0;9.0;0.61;3.96
2023.01.03 11:00;0;0;0;0;0
```

| Поле | Описание |
|------|----------|
| `signal` | 1 (BUY), -1 (SELL), 0 (FLAT) |
| `sl_atr` | SL в ATR-единицах (2 или 3) |
| `tp_atr` | TP в ATR-единицах (3, 6 или 9) |
| `prob` | P(TP hit) лучшего таргета |
| `ev` | Expected Value лучшего таргета |

---

## 9. MT4 интеграция

### Новый файл: `lib_ML_Signal_TB.mqh`

```c
// Глобальные массивы (аналог lib_ML_Signal.mqh)
int      TB_SignalCount;
datetime TB_Times[];
char     TB_Signals[];
float    TB_SL[], TB_TP[], TB_Prob[], TB_EV[];

void EXPERT::ML_TRADE_TB() {
    // Lazy init
    static bool loaded = false;
    if (!loaded) { loaded = true; TB_INIT("ml_signals_tb.csv"); }

    int idx = TB_FindSignal(Time[bar]);
    if (idx < 0 || TB_Signals[idx] == 0) return;

    // SL/TP из CSV (в ATR-единицах)
    float sl_dist = TB_SL[idx] * ATR;
    float tp_dist = TB_TP[idx] * ATR;

    if (TB_Signals[idx] == 1 && BUY.Typ == NONE && SEL.Typ == NONE) {
        set.BUY.Sig = GOGO;
        set.BUY.Val = (float)Ask;
        set.BUY.Stp = set.BUY.Val - sl_dist;
        set.BUY.Prf = set.BUY.Val + tp_dist;
    }
    // SELL аналогично
}
```

### Интеграция в MAIN.mqh
- Новый `iSignal` case (например, `case 5: ML_TRADE_TB();`)
- Или параметр для выбора ML-трека

### Timeout
- 24 бара (совпадает с маркировкой)
- `Tper = 24` в параметрах эксперта при тестировании TB

---

## 10. Валидация дизайна

### Критерии успеха
1. **PF в Python ≈ PF в MT4** (gap < 20%) — главный критерий, подтверждающий реалистичность метрики
2. **PF > 1.0** хотя бы для одной SL/TP комбинации на OOS
3. **AUC > 0.55** на test set (лучше random)

### Сравнение с regression_updn
| Метрика | regression_updn | triple_barrier (ожидание) |
|---------|-----------------|---------------------------|
| Python PF | 4.50 (MFE-based) | ~1.2-2.0 (SL/TP-based) |
| MT4 PF | 1.03 | ~1.0-1.8 (ближе к Python) |
| Gap | ~4× | < 20% |

### Риски
1. **Дисбаланс классов**: Широкие TP (9 ATR) могут иметь < 5% позитивов → модель будет предсказывать 0 для всех. Митигация: pos_weight в loss.
2. **Аппроксимация MFE**: Неоднозначные случаи (оба барьера достигнуты) помечены как 0, что может занижать истинный win rate для узких барьеров.
3. **Консервативный PF**: Timeouts считаются как полный SL loss → Python PF будет нижней границей. Реальный MT4 PF может быть выше.

---

**Последнее обновление**: 2026-03-22
