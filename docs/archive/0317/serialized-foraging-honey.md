# SoSimple ML Recovery Plan

## Context

Все протестированные архитектуры (BiLSTM, CNN1D, Transformer, Hybrid) не дают Profit Factor > 1.0 (лучший результат: PF = 0.728 при Pearson r = 0.56). Оптимизация гиперпараметров (50 trials Optuna) и кастомные loss-функции не помогли.

**Диагностика провала (по убыванию вероятности):**

1. **Целевая переменная `predict` определена неверно** (90%) — переменный горизонт + тривиальная утечка `direction` в знак таргета → 97.5% directional accuracy это артефакт, не результат
2. **Классификация с 2100 примерами при 147K параметрах** (85%) — фундаментальное переобучение, потолок F1_minority ≈ 0.35
3. **Отсутствует контекст режима рынка** (75%) — один и тот же фрактал в тренде и флете имеет разный смысл, модель не может разделить
4. **Слабый базовый сигнал** (60%) — форекс близок к random walk, но Transformer r=0.56 уже показывает что-то есть
5. **Архитектура** (30%) — НЕ главная причина, менять не надо

---

## Стратегия: 3 независимые сессии

Каждая сессия — самодостаточный промпт с полным контекстом.

---

## Сессия 1: MQL4 — новые таргеты MFE/MAE в экспорте данных

### Контекст для промпта сессии 1

```
Проект: SoSimple — автоторговая система XAUUSD H1 на фракталах (Price in Channel).
Стек: MQL4, MetaTrader 4.
Ключевой файл: /home/hohla/git/SoSimple/MQL4/lib_PIC.mqh (библиотека фракталов).
Данные: Nero.csv — каждая строка это снэпшот 100 фракталов на момент появления нового фрактала.

ЗАДАЧА: Добавить в экспорт Nero.csv новые целевые переменные MFE и MAE
для фиксированных горизонтов N = 12, 24, 48, 96 H1-баров.

ТЕКУЩАЯ ПРОБЛЕМА: Столбец predict = -back * direction имеет переменный горизонт
(back обновляется до момента пробития фрактала — через разное число баров).
Это делает таргет шумным и неоднородным.

РЕШЕНИЕ:
Для каждого фрактала (направление dir ∈ {-1, +1}) вычислить:
  MFE_N = движение цены В СТОРОНУ сигнала на горизонте N баров / ATR
  MAE_N = движение цены ПРОТИВ сигнала на горизонте N баров / ATR

Для Buy (dir=+1):
  MFE_N = (iHigh(sym, PERIOD_H1, iHighest(sym, PERIOD_H1, MODE_HIGH, N, 1)) - close[0]) / ATR
  MAE_N = (close[0] - iLow(sym, PERIOD_H1, iLowest(sym, PERIOD_H1, MODE_LOW, N, 1))) / ATR

Для Sell (dir=-1): MFE и MAE симметрично.

Добавить 8 новых столбцов:
  mfe_12, mae_12, mfe_24, mae_24, mfe_48, mae_48, mfe_96, mae_96

ВАЖНО: значения записываются в строку фрактала РЕТРОСПЕКТИВНО, после того как
прошло N баров. Строки для последних N баров будут иметь NaN/0 и отфильтруются в Python.

Изучи lib_PIC.mqh и текущий EA. Предложи минимальные изменения.
```

### Критические файлы
- `/home/hohla/git/SoSimple/MQL4/lib_PIC.mqh`
- `/home/hohla/git/SoSimple/MQL4/` (EA-файлы экспорта)
- `/home/hohla/git/SoSimple/DATA/Nero.csv` (структура для понимания)

### Ожидаемый результат
Новый Nero.csv с 8 дополнительными колонками. Последние 96 строк будут неполными.

---

## Сессия 2: Python — обновление ML-пайплайна

### Контекст для промпта сессии 2

```
Проект: SoSimple — автоторговая система XAUUSD H1.
Стек: Python 3.11, PyTorch, Pandas, Optuna.

КОНТЕКСТ ПРОВАЛА: Все 4 архитектуры (BiLSTM, CNN1D, Transformer, Hybrid) при лучшей
Pearson r = 0.56 не дают Profit Factor > 1.0. Проблема НЕ в архитектуре, а в данных:
  1. Старый таргет predict имел переменный горизонт → шум
  2. Модель не знает режим рынка (тренд/флет, волатильность)
  3. Все сигналы торгуются, даже слабые

ЗАДАЧА: Обновить ML-пайплайн под новые данные. 3 изменения:

=== ИЗМЕНЕНИЕ 1: Новые таргеты (Multi-task regression) ===
В Nero.csv теперь есть колонки: mfe_12, mae_12, mfe_24, mae_24, mfe_48, mae_48, mfe_96, mae_96
Выбрать горизонт N=24 как основной (можно параметром).
Модель теперь предсказывает ДВА числа: [MFE, MAE]
Файлы для изменения:
  - /home/hohla/git/SoSimple/processing/label_signals.py — убрать старый predict, использовать mfe_N/mae_N
  - /home/hohla/git/SoSimple/ML/data_loader.py — y_tensor shape: (batch, 2) вместо (batch, 1)
  - /home/hohla/git/SoSimple/ML/models/*.py — выходной слой: Linear(64, 2) вместо Linear(64, 1)
  - /home/hohla/git/SoSimple/ML/losses.py — loss = HuberLoss(pred_mfe, true_mfe) + HuberLoss(pred_mae, true_mae)
  - /home/hohla/git/SoSimple/ML/train.py — метрики: Pearson r отдельно для MFE и MAE

=== ИЗМЕНЕНИЕ 2: Добавить признаки режима рынка ===
Текущих фич: 11 (10 фрактал + ATR) × 100 фракталов.
Добавить глобальные фичи (broadcast на все 100 позиций):
  a) ATR_ratio = ATR_current / ATR_month_avg  (волатильный режим: низкий/норма/высокий)
  b) hour_sin = sin(2π * hour / 24)  (азиатская/европейская/американская сессия)
  c) hour_cos = cos(2π * hour / 24)
  d) dow_sin = sin(2π * dayofweek / 5)  (понедельник/пятница эффект)
  e) dow_cos = cos(2π * dayofweek / 5)

ATR_month_avg вычислить по train-сету (последние 30 дней ATR для каждой строки).
Источник времени: существующий столбец time в Nero.csv.
Размерность входа станет: batch × 100 × 16 (вместо 11).

Файлы: /home/hohla/git/SoSimple/processing/normalize.py, data_loader.py

=== ИЗМЕНЕНИЕ 3: Сигнал через MFE/MAE ratio ===
В threshold_analysis.py добавить:
  trade_signal = 1 if (pred_MFE > mfe_threshold) AND (pred_MFE / pred_MAE > ratio_min) else 0
Построить PF-кривую от ratio_min ∈ [0.5, 3.0].

Оставить лучшую архитектуру Transformer (Pearson r = 0.5628 на старых данных).
НЕ менять архитектуру, только input/output размерности.
НЕ запускать Optuna пока — сначала убедиться что новый таргет работает лучше.

ПОРЯДОК РАБОТЫ:
1. Обновить label_signals.py → регенерировать CSV
2. Обновить normalize.py → добавить режимные фичи
3. Обновить data_loader.py → новые размерности и кэш
4. Обновить models/transformer.py → 2 выхода, 16 фич
5. Обновить losses.py → двойной Huber loss
6. Обновить train.py → новые метрики
7. Запустить train.py --model transformer --task regression
8. Сравнить Pearson r(MFE) и Pearson r(MAE) с базовым r=0.56
9. Запустить threshold_analysis.py → проверить PF при MFE/MAE ratio-фильтрации
```

### Критические файлы
- `/home/hohla/git/SoSimple/processing/label_signals.py`
- `/home/hohla/git/SoSimple/processing/normalize.py`
- `/home/hohla/git/SoSimple/ML/data_loader.py`
- `/home/hohla/git/SoSimple/ML/models/transformer.py`
- `/home/hohla/git/SoSimple/ML/losses.py`
- `/home/hohla/git/SoSimple/ML/train.py`
- `/home/hohla/git/SoSimple/ML/reports/threshold_analysis.md` (обновить)

### Критерий успеха
- Pearson r(MFE) > 0.40 на валидации
- PF > 1.0 при ratio_min = 1.5 (даже если процент торгуемых сигналов < 30%)

---

## Сессия 3 (опциональная): Selective Prediction

После получения результатов Сессии 2. Запускается только если PF при ratio-фильтрации близок к 1.0 но не достигает.

```
Реализовать Quantile-based Rejection:
  - Обучить квантильную регрессию (Q10, Q50, Q90) для MFE
  - Торговать только когда Q10 > threshold (нижняя граница уверенности > нуля)
  - Это аналог Conformal Prediction без лишней сложности
```

---

## Что НЕ делать

- НЕ менять архитектуру (Transformer уже хорош, r=0.56)
- НЕ добавлять EMA(200) — MA не работают на форексе по опыту автора
- НЕ добавлять "позицию в диапазоне" — 100 фракталов с нарастающей значимостью уже кодируют это
- НЕ заниматься SVM/L1/SHAP — не актуально на данном этапе
- НЕ запускать Optuna до получения стабильного сигнала на новом таргете
- НЕ трогать классификационную задачу — 2100 примеров это потолок, задача бесперспективна

---

## Зависимости между сессиями

```
Сессия 1 (MQL4) → новый Nero.csv → Сессия 2 (Python) → результаты → Сессия 3 (опц.)
```

Сессии 1 и 2 строго последовательные. Сессия 3 независима и опциональна.
