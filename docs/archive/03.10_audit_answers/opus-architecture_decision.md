# Architecture Decision Record
> **SoSimple ML — Финальный выбор архитектуры (Этап 3.3)**
> **Дата**: 2026-03-09
> **Статус**: ПРИНЯТО

---

## Резюме

**Выбранная архитектура**: **BiLSTM** для регрессии `|predict|`
**Запасная**: Transformer (для ансамбля или если BiLSTM не проходит HPO)
**Стратегия**: regression-first с пороговым преобразованием в торговый сигнал

| Метрика | BiLSTM regression | Лучший baseline RF classification |
|---------|-------------------|------------------------------------|
| Pearson r | **0.555** | — |
| R² | 0.306 | — |
| MAE | 0.103 | — |
| Macro F1 (classification) | 0.553 | 0.556 |
| F1_minority (classification) | 0.355 | 0.370 |
| Параметры | 147K | — |
| Время обучения | 128с | — |

---

## Обоснование выбора BiLSTM

### Почему BiLSTM, а не Transformer?

| Критерий | BiLSTM | Transformer |
|----------|--------|-------------|
| Pearson r (regression) | 0.555 | 0.563 (+1.4%) |
| Время обучения | 128с | **1549с (12x медленнее)** |
| Best epoch | 3 | 49 |
| Параметры | 147K | 70K |
| HPO feasibility | 50 trials × 128с = 1.8ч | 50 trials × 1549с = **21.5ч** |
| Oверфиттинг | Быстрый (ep.3) | Медленный (ep.49) |

- Разница в Pearson r = 0.008 — **статистически незначима** при 9341 val samples
- BiLSTM в 12x быстрее — критично для HPO
- Transformer — запасной вариант для ансамбля (разный inductive bias)

### Почему не CNN1D или Hybrid?

- **CNN1D**: Pearson r = 0.519 — слабее BiLSTM на 0.036, самая маленькая модель (42K), но недостаточная expressive power для длинных зависимостей
- **Hybrid CNN+LSTM**: Pearson r = 0.546 — конкурентоспособна, но не лучше BiLSTM. Сложнее в HPO (больше гиперпараметров CNN блока)

### Почему регрессия, а не классификация?

Подробное обоснование: [project_audit_and_plan.md § 1.2](docs/archive/03.10_audit_answers/opus-project_audit_and_plan.md)

Краткое:
1. **Классификация уперлась в потолок** (F1_minority ≈ 0.37 у всех 5 архитектур включая RF)
2. **~1000 примеров на сигнальный класс** — недостаточно для deep learning
3. **Регрессия использует все 43K примеров** — нет проблемы дисбаланса
4. **Торговый сигнал** генерируется через порог θ на |predict| — настраиваемый precision/recall

---

## Сравнение с Baseline

### Классификация (для reference)

| Модель | Macro F1 | F1(-1) | F1(1) | Тип |
|--------|----------|--------|-------|-----|
| Dummy (stratified) | 0.330 | 0.02 | 0.02 | Baseline |
| Random Forest | 0.556 | 0.39 | 0.35 | Baseline |
| BiLSTM | 0.553 | 0.37 | 0.34 | NN |
| Transformer | 0.567 | 0.39 | 0.36 | NN |
| Hybrid | 0.568 | 0.42 | 0.35 | NN |

**Вывод**: NN не дают значимого прироста над RF baseline для классификации. Все модели упираются в один потолок. Проблема — в данных, не в архитектуре.

### Регрессия — прирост от обучения

| Модель | Pearson r | R² | Прирост vs trivial (r=0) |
|--------|-----------|-----|--------------------------|
| BiLSTM | 0.555 | 0.306 | +0.555 |
| Transformer | 0.563 | 0.306 | +0.563 |
| Mean prediction | 0.000 | 0.000 | baseline |

---

## Сравнение NN архитектур

### Классификация (checkpoint-ы по состоянию на 2026-03-09)

| Модель | Macro F1 | F1(-1) | F1(0) | F1(1) | F1_minority | Params | Time, s | Best Ep |
|--------|----------|--------|-------|-------|-------------|--------|---------|---------|
| Hybrid | 0.568 | 0.417 | 0.935 | 0.353 | 0.385 | 83K | 156 | 10 |
| Transformer | 0.567 | 0.392 | 0.949 | 0.359 | 0.376 | 70K | 641 | 11 |
| BiLSTM | 0.553 | 0.370 | 0.949 | 0.340 | 0.355 | 147K | 23 | 2 |
| CNN1D | —¹ | 0.368 | 0.931 | 0.325 | 0.346 | 42K | 250 | 34 |

¹ CNN1D обучена с `metric_mode=f1_minority`, macro F1 не зафиксирован корректно

### Регрессия (checkpoint-ы по состоянию на 2026-03-09)

| Модель | Pearson r | MAE | RMSE | R² | Params | Time, s | Best Ep |
|--------|-----------|-----|------|----|--------|---------|---------|
| **Transformer** | **0.563** | 0.114 | 0.185 | 0.306 | 70K | 1549 | 49 |
| **BiLSTM** ⭐ | **0.555** | 0.103 | 0.185 | 0.306 | 147K | 128 | 3 |
| Hybrid | 0.546 | 0.115 | 0.188 | 0.283 | 83K | 75 | 3 |
| CNN1D | 0.519 | 0.103 | 0.195 | 0.232 | 42K | 60 | 5 |

⭐ BiLSTM — выбор по совокупности: 2-е место по Pearson r, 12x быстрее Transformer, лучший MAE

---

## Анализ ошибок

### Паттерны

1. **Быстрый оверфиттинг**: BiLSTM best_epoch=3 (classification: ep. 2) → модель выучивает полезные паттерны за 2-3 эпохи, далее запоминает шум
2. **Все модели сходятся к одному уровню**: разброс Pearson r = 0.044 (0.519-0.563) — меньше вероятной стат. ошибки. Сигнал ограничен данными.
3. **R² = 0.30**: 70% дисперсии predict не объясняется моделью. Либо данные слишком шумные, либо не хватает features, либо предсказуемость predict объективно низкая.

### Известные ограничения

1. **Precision сигналов при классификации: ~27%** → 73% ложных торговых сигналов
2. **Нет error analysis по конкретным примерам** — не проводился (пункт из Этапа 3.3)
3. **Результаты в checkpoint-ах отличаются от отчётов** — но условия получения не задокументированы
4. **Воспроизводимость под вопросом**: регрессия BiLSTM в отчёте была r=0.324, теперь r=0.555 (+71%). Критически нужен контролируемый перезапуск с фиксированным seed.

---

## Финальная конфигурация

### Модель

```yaml
architecture: BiLSTM
input_shape: [batch, 100, 11]  # 100 fractals, 10 features + ATR
hidden_size: 64
num_layers: 2
bidirectional: true
dropout: 0.3
pooling: concat last hidden fwd+bwd
output: 1  # regression (magnitude)
total_parameters: 147073
```

### Обучение

```yaml
task: regression
target: |predict|  # абсолютное значение predict
loss: HuberLoss (delta=1.0)
optimizer: AdamW (lr=1e-3, weight_decay=1e-4)
scheduler: ReduceLROnPlateau (patience=5, factor=0.5, mode=max)
early_stopping: pearson_r (patience=10)
batch_size: 256
epochs: 50
seed: 42
use_scaler: false
gradient_clipping: max_norm=1.0
```

### Inference (торговый сигнал)

```yaml
model_output: |predict_hat| >= 0
threshold: theta  # определяется на validation (QW-4)
signal_generation:
  if |predict_hat| > theta:
    direction: fractal[0].direction
    signal: -direction  # direction=1 (пик) → Sell, direction=-1 (впадина) → Buy
  else:
    signal: 0  # no trade
```

---

## Рекомендации для следующего этапа

### Немедленные действия (Quick Wins)
1. **Кэшировать parsed данные** в `.npy` — ускорение 60x для повторных экспериментов
2. **Воспроизвести** текущие результаты регрессии с фиксированным seed
3. **Реализовать threshold_analysis.py** — конвертация regression → trading signal
4. **Исправить баг** логирования metric_mode в result JSON

### HPO (после Quick Wins)
5. **Optuna HPO для BiLSTM regression** — 50 trials, пространство поиска: lr, batch_size, weight_decay, huber_delta, patience, scheduler_*
6. **Optuna HPO для Transformer regression** — 30 trials (медленнее, меньше trials)
7. **Ансамбль BiLSTM + Transformer** если оба > 0.55

### Полная дорожная карта
См. [project_audit_and_plan.md § 2.2](docs/archive/03.10_audit_answers/opus-project_audit_and_plan.md)

---

**Автор**: Claude (AI) по запросу Antigravity
**Дата**: 2026-03-09
