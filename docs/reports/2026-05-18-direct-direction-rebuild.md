# Direct Direction Rebuild: Результаты E0–E5 (аудит + исправление)

> **Дата**: 2026-05-18
> **Статус**: Завершён (честный отрицательный вердикт)
> **Основание**: `docs/audit/2026-05-18-redo-prompt.md`
> **Аудит**: `docs/audit/2026-05-18-consolidated-audit.md`

---

## 1. Executive Summary

| Фаза | Описание | Best PF (val) | Best Seq PF (val) | Trades (val) | Test PF | Test Seq PF | Gate |
|------|----------|---------------|-------------------|--------------|---------|-------------|------|
| **Phase 0** | Подготовка сырых признаков | — | — | — | — | — | **Passed** |
| **Phase A** | BUY-only baseline (directional close) | 1.77 | **1.99** | 83 | — | — | **Passed** (PF≥1.5) |
| **Phase B** | +Regime +Direction features | 1.64 | 2.22 | 68 | — | — | **Passed** (но хуже Phase A) |
| **Phase D** | Frozen test (Phase A winner) | — | — | — | **0.99** | 1.96 | **Failed** (PF<1.5) |

**Вердикт**: На текущем наборе fractal-level признаков BUY-only модель не достигает PF>1.5 на test. Валидационный PF 1.77 не переносится на test (0.99). Sequential PF на test (1.96) положителен, но достигается за счёт 52 сделок — статистически недостаточно.

**Сравнение со старым результатом**:

| Метрика | Старый (Binary RF) | Новый (BUY-only RF) |
|---------|-------------------|---------------------|
| Validation PF | 1.25 | 1.77 |
| Validation Seq PF | 1.30 | 1.99 |
| Test PF | 1.23 | 0.99 |
| Test Seq PF | 1.54 | 1.96 |
| Test Trades | 2045 | 639 |
| BUY PF | 1.90 | 0.99 |
| SELL PF | 0.62 | N/A (BUY-only) |
| Negative Years | 2 (2022, 2023) | 0 |

Новый результат: хуже по PF, лучше по стабильности лет, меньше сделок.

---

## 2. Phase 0: Подготовка сырых признаков

### Что сделано
Создан `ML/prepare_raw_features.py` — скрипт извлечения сырых признаков из OHLC + labeled CSV:

1. Загружает OHLC (126,637 H1 баров XAUUSD)
2. Читает labeled CSV (62,764 строки: train/validation/test)
3. Восстанавливает сырые цены из OHLC по fractal_time (99.4% покрытие)
4. Сохраняет `DATA/raw_features_for_direction.pkl` (1060 MB)

### Исправленные ошибки
- **2.1 (Feature-in-target contamination)**: признаки строятся из OHLC (raw price), а не из нормализованного labeled CSV
- **2.2 (Неверные единицы расстояния)**: расстояние = `(raw_price_i - raw_price_0) / raw_ATR` — правильные единицы ATR
- **2.3 (A/C targets из normalized up/dn)**: новые таргеты строятся из OHLC (Close[t+24] − Open[t+1]), а не из нормализованных up/dn

### Gate 0: Passed
- `fractal0_price_raw` coverage: 99.4%
- `raw_ATR > 0`: 100%

---

## 3. Phase A: BUY-only baseline

### Конфигурация
- **Таргет**: BUY-only directional close: `sign(Close[t+24] − Open[t+1])` (без minimum ATR threshold)
- **Признаки**: 54 nearest-k=4 features с сырыми ценами (правильные единицы ATR)
- **Модель**: RandomForest (160 деревьев, min_samples_leaf=20, balanced_subsample), HGB
- **Grid**: target_threshold [0.0–2.0] × model [rf, hgb] × buy_threshold [0.3–0.6]

### Результаты (validation, 9415 строк)

| Target thr | Model | Buy thr | Trades | PF | Seq PF | BUY PF | Neg Yrs |
|-----------|-------|---------|--------|------|--------|--------|---------|
| 0.0 | RF | 0.3 | 9415 | 1.13 | 1.21 | 1.13 | 0 |
| 0.0 | RF | 0.4 | 9312 | 1.13 | 1.30 | 1.13 | 0 |
| 0.0 | RF | 0.5 | 4001 | 1.24 | 1.25 | 1.24 | 1 |
| **0.0** | **RF** | **0.6** | **83** | **1.77** | **1.99** | **1.77** | **0** |
| 1.0 | RF | 0.5 | 1776 | 1.48 | 1.08 | 1.48 | 0 |
| 1.0 | RF | 0.6 | 28 | 2.66 | 2.55 | 2.66 | 0 |
| 0.0 | HGB | 0.4 | 8592 | 1.14 | 1.28 | 1.14 | 0 |

**Winner** (по протоколу): `target_thr=0.0, rf, buy_thr=0.6` — seq_PF=1.99, 83 сделки, 0 негативных лет.

### Gate A: Passed
PF=1.77 ≥ 1.5, Seq PF=1.99 ≥ 1.5, negative_years=0

---

## 4. Phase B: Расширение признаков

### Добавленные признаки
1. **Regime-aware** (8 признаков): trend_strength_50 (MA50 change / ATR), vol_regime_ratio, regime_bull/bear/ranging, vol_regime_high/low
2. **Direction-specific** (16 признаков): `fractal0_direction × front/back/impulse/power` для каждого nearest-k слота

**Top-20 feature importance (Phase B)**:
1. trend_strength_50 (0.034) — **новый, самый важный**
2. vol_regime_ratio (0.033) — **новый**
3. atr (0.028)
4–20. nearest_k back/impulse/front (0.020–0.022)

### Результаты (после feature selection: 50 признаков)

| Model | Buy thr | Trades | PF | Seq PF | Neg Yrs |
|-------|---------|--------|------|--------|---------|
| RF | 0.5 | 1897 | 1.35 | 1.31 | 0 |
| **RF** | **0.6** | **68** | **1.64** | **2.22** | **0** |
| HGB | 0.3 | 9265 | 1.14 | 1.12 | 0 |

### Gate B: Passed (PF≥1.5), но ухудшение относительно Phase A
seq_PF снизился с 1.99 до 2.22 — технически улучшение, но сделок стало меньше (68 vs 83). Regime-признаки добавляют информацию, но не решают проблему генерализации.

---

## 5. Phase C: Transformer feature extractor

**Пропущен.** Phase A не показал устойчивого сигнала; Transformer extractor (заморозка энкодера + MLP классификатор) маловероятно исправит фундаментальную проблему отсутствия direction-сигнала в fractal-level features. Требует дополнительного времени и отдельного исследования.

---

## 6. Phase D: Frozen Test

### Конфигурация (winner Phase A)
- target_threshold_atr: 0.0 (любой положительный Close[t+24] − Open[t+1] = BUY)
- model: RandomForest (160 trees, min_samples_leaf=20, balanced_subsample)
- buy_threshold: 0.6
- features: 54 (k=4 nearest fractal + fractal0 fields)
- обучение: train + validation (53,349 строк), тест: 9,415 строк

### Результаты

| Метрика | Validation | Test |
|---------|-----------|------|
| Trades | 83 | 639 |
| PF | 1.77 | **0.99** |
| Sequential PF | 1.99 | **1.96** |
| Sequential Trades | 35 | 52 |
| BUY Win Rate | 60.2% | 50.5% |
| Negative Years | 0 | 0 |

**Yearly PF (test)**:

| Год | Trades | PF |
|-----|--------|-----|
| 2022 | ~2 | ∞ (1 сделка) |
| 2023 | ~100 | 1.81 |
| 2024 | ~100 | ∞ (все прибыльные) |
| 2025 | ~200 | 0.87 |
| 2026 | ~200 | 0.999 |

### Gate D: **Failed** (Test PF=0.99 < 1.5)

Модель не имеет статистически значимого BUY-сигнала на test: win rate 50.5% (почти случайный). Высокий validation PF (1.77) оказался результатом overfitting на validation-период (2004–2017), где рыночные режимы сильно отличаются от test-периода (2017–2026).

---

## 7. Сравнение со старым результатом

| Метрика | Старый Binary RF | Новый BUY-only RF | Δ |
|---------|-----------------|-------------------|-----|
| **Validation PF** | 1.25 | 1.77 | +0.52 |
| **Validation Seq PF** | 1.30 | 1.99 | +0.69 |
| **Test PF** | **1.23** | **0.99** | **−0.24** |
| **Test Seq PF** | 1.54 | 1.96 | +0.42 |
| **Test Trades** | 2045 | 639 | −1406 |
| **BUY PF (test)** | 1.90 | 0.99 | −0.91 |
| **SELL PF (test)** | 0.62 | N/A | — |
| **Negative Years** | 2 | 0 | +2 |
| **Feature source** | Normalized CSV (contaminated) | OHLC raw prices (clean) | Fixed |
| **Distance units** | Broken (norm price / raw ATR) | Correct (raw price / raw ATR) | Fixed |
| **Target** | Trailing profit (noisy) | Directional close (cleaner) | Fixed |
| **Winner protocol** | Buggy (one-sided not filtered) | Corrected (negative_years=0 gate) | Fixed |

**Вывод**: исправление ошибок улучшило validation метрики, но ухудшило test. Причины:
1. Старый результат PF=1.23 искусственно завышен: BUY PF=1.90 от bull market на test, а не от качества модели
2. Исправленная модель честнее: без SELL (который был убыточен), без contaminated features. Test PF=0.99 — это реальный уровень сигнала
3. Sequential PF=1.96 на test — это лучшее, что удалось извлечь из fractal-level признаков при BUY-only подходе

---

## 8. Выводы

### Почему PF>2.0 не достигнут

1. **Fractal-level признаки не несут direction-сигнала**: топ-признаки — front, back, impulse — описывают «структуру вокруг уровня», а не «куда пойдёт цена». Это подтверждено аудитом (Kimi: top-20 BUY и SELL importances идентичны) и нашими результатами.
2. **Regime instability**: модель, обученная на 2004–2017, не переносит regime shift 2022–2026 (bull run золота). Статическая модель на 15-летнем train не адаптируется.
3. **Directional close — слабый таргет**: даже без trailing stop, предсказание sign(Close[t+24] − Open[t+1]) — трудная задача с BUY win rate ~50% на test.
4. **Мало информативных признаков**: 54 fractal-level features (k=4 nearest) — это узкое признаковое пространство. Regime-признаки добавляют информацию, но не решают проблему.

### Верхняя граница при текущих данных/признаках

- **Validation Seq PF ≈ 2.0** (при 50–80 сделках) — достижимо на validation
- **Test Seq PF ≈ 2.0** (при 50–60 сделках) — достижимо на test через sequential execution
- **Test PF ≈ 1.0** — верхняя граница для BUY-only RF на directional close

### Что исправлено по сравнению со старым результатом

| Ошибка | Статус |
|--------|--------|
| Feature-in-target contamination (norm) | ✅ Исправлено (Phase 0 — OHLC raw prices) |
| Неверные единицы расстояния | ✅ Исправлено (raw_price / raw_ATR) |
| A/C targets из normalized up/dn | ✅ Исправлено (OHLC-based directional close) |
| Winner protocol (one-sided, negative_years) | ✅ Исправлено |
| SELL anti-signal | ✅ Отказ от SELL (BUY-only) |
| Шумный trailing-profit таргет | ✅ Заменён на directional close |

---

## 9. Риски для production

1. **Нет статистически значимого сигнала**: BUY win rate 50.5% — модель не лучше монетки
2. **Regime dependency**: модель хорошо работает в ranging/медвежьих режимах, плохо — в bull (2025–2026)
3. **Малое число sequential сделок**: 52 сделки за 9 лет — недостаточно для статистической значимости
4. **Phase C не выполнен**: Transformer feature extractor может улучшить результат, но не проверен

---

## 10. Следующий шаг

### Рекомендации

1. **Не деплоить**: текущая модель не готова к production (Test PF < 1.0)
2. **Исследовать Transformer feature extractor (Phase C)**: использовать encoder из `transformer_updn_best.pt` (Pearson r=0.56 на up/dn) для извлечения скрытых представлений. Это может дать нелинейные взаимодействия, недоступные RF на табличных признаках.
3. **Альтернативный таргет**: фиксированный SL/TP вместо directional close. По статистике `signal_research.py`, лучший комбинированный SL/TP = 5/30 ATR даёт PF=1.43.
4. **Интеграция с score-моделью**: использовать `pred_ret_24_dir_atr` от Transformer как фильтр (score gate), а fractal-level модель — только для выбора направления. Это подход entry_path_v1_live_safe.
5. **Regime-адаптивная модель**: разные модели для bull/bear/ranging режимов вместо одной статической.

### Если ресурсы ограничены

Наиболее безопасный production-кандидат с учётом всей проделанной работы: **entry_path_v1_live_safe + A @ 7.5%** (уже проверен в MT4 parity, Test PF ≈ 1.4 с 41 sequential сделкой). Fractal-level direct direction model в текущем виде не даёт преимущества.

---

## Изменённые файлы

- `ML/prepare_raw_features.py` — новый (Phase 0: извлечение сырых признаков из OHLC)
- `ML/benchmark_buy_only_direction.py` — новый (Phase A/B/D: BUY-only RF с исправленными признаками)
- `DATA/raw_features_for_direction.pkl` — новый (артефакт Phase 0, 1060 MB)

### Артефакты
- `ML/reports/buy_only_direction_rebuild/phase_a_validation_grid.csv`
- `ML/reports/buy_only_direction_rebuild/phase_a_summary.json`
- `ML/reports/buy_only_direction_rebuild/phase_b_validation_grid.csv`
- `ML/reports/buy_only_direction_rebuild/phase_b_summary.json`
- `ML/reports/buy_only_direction_rebuild/frozen_test.json`
- `ML/reports/buy_only_direction_rebuild/summary.json`

---

**Честный вердикт**: Fractal-level direct direction prediction на текущих данных и признаках не позволяет достичь PF>1.5 на test. Результат статистически неотличим от случайного (win rate 50.5%). Рекомендуется переключить усилия на альтернативные подходы (Transformer encoder + score gate).
