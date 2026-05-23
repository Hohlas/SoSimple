# Prompt: переделка исследований Direct Direction (E0–E5)

> **Дата**: 2026-05-18
> **Основание**: `docs/audit/2026-05-18-consolidated-audit.md`
> **Цель**: переделать все эксперименты E0–E5 с исправлением найденных критических ошибок

---

## 0. Контекст для агента

Проект SoSimple — ML-бот для прогнозирования разворотов Forex (XAUUSD, H1). Предыдущий этап `improving-direct-direction-results` (E0–E5) дал неудовлетворительный результат: лучший кандидат Binary RF показал Test PF=1.23, но SELL PF=0.62 (убыточно), 2 отрицательных года, PF>2.0 не достигнут.

Два независимых аудита (Codex, Kimi) выявили критические ошибки в методологии и данных. Этот prompt ставит задачу **переделать все исследования с нуля, исправив ошибки**.

---

## 1. Обязательные источники для изучения

Прочитай **все** перечисленные файлы перед началом работы:

### Контекст проекта
- `AGENTS.md` — главный индекс, правила работы
- `CONTEXT_HANDOFF.md` — текущее состояние проекта
- `docs/DATA_FLOW.md` — схема потока данных MT4→ML→MT4
- `docs/dataset_description.md` — описание формата данных
- `CHANGELOG.md` (первые 300 строк) — история изменений
- `docs/superpowers/plans/2026-05-15-improving-direct-direction-results.md` — предыдущий план
- `docs/reports/2026-05-15-direct-direction-improvement.md` — предыдущий отчёт
- `docs/archive/answer.md` — скорректированный промпт для аудита

### Аудиты (обязательно)
- `docs/audit/2026-05-18-consolidated-audit.md` — консолидированный аудит (**главный документ**)
- `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md`
- `docs/audit/2026-05-18-kimi-independent-audit.md`

### Код, который нужно изменить
- `processing/normalize.py` — нормализация (источник ошибки 2.1)
- `ML/fractal_level_feature_builder.py` — построение признаков (источник ошибки 2.2)
- `ML/entry_path_direct_direction_targets.py` — построение таргетов (источник ошибки 2.3)
- `ML/benchmark_entry_path_binary_direction.py` — benchmark (источник ошибки 1.1)
- `ML/benchmark_entry_path_score_direction.py` — score direction benchmark
- `ML/benchmark_entry_path_fractal_level_direct_direction.py` — запуск E0 экспериментов

### Артефакты предыдущих экспериментов (для проверок)
- `ML/reports/entry_path_v1_direct_direction_improvement/aggregate_summary.md`
- `ML/reports/entry_path_v1_binary_direction/summary.json`
- `ML/reports/entry_path_v1_binary_direction/frozen_test.json`
- `ML/reports/entry_path_v1_binary_direction/validation_grid.csv`
- `ML/reports/entry_path_v1_binary_direction/frozen_test_grid.csv`

---

## 2. Критические ошибки (что именно сломано)

### 2.1. Feature-in-target contamination (нормализация)
`processing/normalize.py` нормализует фрактальные `Up/Dn` в общем пуле с top-level target columns `up_3..dn_48`. Изменение только top-level таргетов меняет нормализованные значения фрактальных признаков (`fractal1.up_12/dn_12/up_24/dn_24/up_48/dn_48`).

**Что делать**: перестроить fractal-level признаки из raw/current-row source (`Nero.csv`), а не из уже нормализованного `DATA/Nero_*_labeled.csv`.

### 2.2. Неверные единицы расстояния
`ML/fractal_level_feature_builder.py` вычисляет `(fractal.price - fractal0.price) / ATR`, но `price` уже min-max normalized, а `ATR` — сырой. Физический смысл сломан.

**Что делать**: исправить — либо брать raw price из исходной строки, либо найти правильный знаменатель (raw ATR из оригинальной строки Nero.csv).

### 2.3. A/C targets из нормализованных значений
`ML/entry_path_direct_direction_targets.py` строит target families A/C из top-level `up/dn`, которые уже нормализованы, а не выражены в ATR.

**Что делать**: пересчитать target families A/C из raw значений (OHLC или raw up/dn из Nero.csv до нормализации).

### 2.4. Нарушение протокола winner selection
Код `pick_validation_winner()` не исключает one-sided кандидатов, не фильтрует по `negative_years == 0`, сортирует по `validation_pf` раньше `validation_sequential_pf`.

**Что делать**: исправить протокол: (1) отсеять one-sided; (2) `negative_years == 0`; (3) сортировать по `validation_sequential_pf` после gates; (4) frozen test строго соответствует validation winner.

### 2.5. SELL анти-сигнал
SELL precision (0.153) < random baseline (0.185). Инверсия калибровки: выше confidence → ниже win rate.

**Что делать**: временный отказ от SELL. BUY-only interim baseline.

### 2.6. Шумный trailing-profit таргет
24-баровый trailing profit пересекается с внутридневным шумом. BUY recall=14.1%, SELL recall=7.4%.

**Что делать**: заменить на более стабильный таргет (directional close: `sign(Close[t+24] - Close[t+1])` при `|return| > threshold × ATR`, или фиксированный hold return).

---

## 3. План работ (строго последовательно)

### Phase 0: Подготовка (1 скрипт)
Создай единый скрипт `ML/prepare_raw_features.py`, который:
- Читает raw `Nero.csv` (не нормализованный)
- Сортирует фракталы (через `processing/fractal_preprocessing.py`)
- Извлекает из каждой строки raw price, raw ATR, raw up/dn для всех фракталов
- Сохраняет датасет `DATA/raw_features_for_direction.pkl` (или .parquet) с колонками:
  - `time`, `raw_price`, `raw_ATR`, `raw_up_12..dn_48` для каждого фрактала
  - `fractal0.direction`, `fractal0.front`, `fractal0.back`, `fractal0.impulse` (raw)
  - Исходные таргеты (`signal`, `predict`) — для справки
  - OHLC данные для расчёта новых таргетов

**Gate 0**: скрипт отработал, файл создан, parity-проверка: `raw_price` из нового файла совпадает с raw price из `Nero.csv` до нормализации.

### Phase A: BUY-only baseline (новый скрипт)

Создай `ML/benchmark_buy_only_direction.py` (не трогая старые файлы, чтобы не сломать существующий код):

#### A1. Новый таргет (directional close)
- Target = `sign(Close[t+24] - Close[t+1])` при `|Close[t+24] - Close[t+1]| > threshold × ATR[t]`
- Threshold grid: [0.0, 0.5, 1.0, 1.5, 2.0] × ATR
- BUY-only: target ∈ {0 (SKIP), 1 (BUY)} — SELL не используется
- Сравни с альтернативой: фиксированный hold return за 24 бара (без trailing stop)

#### A2. Новые признаки (из raw source)
- Все старые геометрические признаки (`front`, `back`, `impulse`, `power`, `count`, `break`, `reverse`) — из raw source, с правильным ATR-знаменателем
- `fractal0_direction` — явно как вход (а не на 20-м месте)
- `fractal0_strong` — бинарный признак
- Price-distance: `(fractal_i.price - fractal0.price) / raw_ATR` — правильные единицы
- Nearest-k признаки: только k=4 (лучший по E0), но из raw source

#### A3. BUY-only модель
- RandomForest (160 деревьев, min_samples_leaf=20) — как в E1, но BUY vs SKIP
- HGB как альтернатива
- Grid: threshold (BUY confidence) ∈ [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], margin ∈ [0.0, 0.05, 0.10, 0.15]

#### A4. Walk-Forward Validation (вместо единого split)
- 5-fold walk-forward: train на 60%, validation на 20%, test на 20% каждого fold
- Fold 1: train[:48%], val[48%:68%], test[68%:88%]
- Fold 2: train[:60%], val[60%:80%], test[80%:100%]
- Fold 3: train[:72%], val[72%:92%], test[92%:100%]
- Итоговая метрика: средняя PF по всем validation folds

#### A5. Winner selection (исправленный протокол)
1. Отсеять конфигурации с `negative_years > 0` на validation
2. Отсеять one-sided (`buy_trades == 0 or sell_trades == 0`)
3. Отсортировать по `validation_sequential_pf` (не `validation_pf`)
4. Выбрать топ-1
5. Документировать выбор в `summary.json`: исходный winner, причина выбора

**Gate A**: validation PF > 1.5, sequential PF > 1.5, negative_years ≤ 1. Если gate не пройден — **честно зафиксировать и перейти к Phase B** (или вынести вердикт о недостижимости).

### Phase B: Улучшение признаков (в том же скрипте)

Если Phase A прошла gate — расширить признаки:

#### B1. Regime-aware признаки
- Скользящая трендовая сила за 50 баров: `(MA50_close[t] - MA50_close[t-50]) / ATR[t]`
- Волатильностный режим: `ATR[t] / ATR_median_200` — low/medium/high
- Классификация режима: bull (`trend_strength > 0.5`), bear (`trend_strength < -0.5`), ranging (иначе)
- Добавить `regime` как категориальный признак (one-hot)

#### B2. Direction-specific признаки
- `fractal0.direction × front` — взаимодействие направления с front
- `fractal0.direction × back` — взаимодействие направления с back
- `fractal0.direction × impulse` — взаимодействие направления с impulse
- Раздельные статистики для UP и DOWN фракталов в nearest-k

#### B3. Transformer score как вход
- Загрузить `ML/checkpoints/transformer_updn_best.pt`
- Прогнать inference на всех строках датасета
- Извлечь `pred_ret_24_dir_atr` — добавить как дополнительный признак
- **Важно**: для live-safe контракта проверить, что `pred_ret_24_dir_atr` доступен на момент инференса (не future-derived)

#### B4. Feature selection
- После добавления признаков — отбор через feature importance (RF) или mutual information
- Удалить признаки с importance < 0.5% (шум)
- Задокументировать топ-20 признаков после отбора

**Gate B**: validation PF > 1.5 на walk-forward (или улучшение > 10% относительно Phase A). Если нет — перейти к Phase C.

### Phase C: Transformer feature extractor (новый скрипт)

Создай `ML/benchmark_transformer_direction.py`:

#### C1. Feature extractor
- Загрузить `transformer_updn_best.pt` (encoder only)
- Для каждой строки: подать 20 фракталов (seq_len=20) → получить hidden states
- Извлечь: (a) CLS-токен, (b) средний пулинг по seq_len, (c) max пулинг
- Объединить с табличными признаками из Phase B (или использовать только энкодер)

#### C2. Классификатор поверх энкодера
- Простой MLP: hidden → ReLU → dropout → binary classification
- Или: заморозить энкодер → обучить только классификатор
- Или: fine-tune энкодер + классификатор (если ресурсы позволяют)
- Сравнить оба подхода

#### C3. BUY-only target
- Тот же таргет, что в Phase A (directional close или hold return)
- BUY vs SKIP

**Gate C**: validation PF > 2.0, sequential PF > 2.0 на walk-forward, negative_years ≤ 1. Если gate не пройден — перейти к Phase D с лучшим кандидатом из Phase B/C.

### Phase D: Frozen test

Только один раз, только для лучшего кандидата:

1. Заморозить конфигурацию (модель, признаки, пороги, таргет)
2. Запустить на test split (последние 15% данных, которые не использовались ни для train, ни для validation)
3. Рассчитать: PF, Sequential PF, BUY/SELL PF, PF по годам, общее число сделок
4. Сохранить в `ML/reports/buy_only_direction_rebuild/frozen_test.json`

**Gate D**: test PF > 1.5, not more than 1 negative year, BUY PF > 1.5. Если gate не пройден — честный вердикт.

---

## 4. Протокол экспериментальной дисциплины

### Запрещено
- **Не использовать test split** для подбора порогов, моделей, признаков
- **Не подбирать пороги** как основное «улучшение» (косметика)
- **Не повторять 3-class формулировку** — доказано нежизнеспособна
- **Не пытаться «подлатать» SELL** фильтрацией — если SELL PF<<1.0, лучше BUY-only
- **Не запускать model sweeps** до исправления feature provenance (Gate 0)
- **Не трогать** `docs/archive/` без явной просьбы пользователя
- **Не загружать** файлы >1MB целиком в контекст

### Требуется
- **Каждый эксперимент — отдельный модуль/файл** (не менять существующие benchmark-файлы)
- **Каждый gate — явная проверка** с результатом pass/fail
- **Все артефакты** — в `ML/reports/buy_only_direction_rebuild/`
- **Воспроизводимость**: `python script.py --seed 42` даёт тот же результат
- **Документация выбора winner**: summary.json с полем `selection_reason`
- **После завершения этапа**: синхронизация `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, wiki ingest

### Окружение
- Python: `~/git/SoSimple/.venv/bin/activate`
- Рабочая директория: `~/git/SoSimple`
- Данные: `DATA/Nero.csv` (raw), `DATA/Nero_XAUUSD_*_labeled.csv` (нормализованные — для справки), `DATA/XAUUSD_H1_OHLC.csv`
- Чекпоинты: `ML/checkpoints/transformer_updn_best.pt`
- Все новые скрипты создавать в `ML/`, тесты — в `tests/`

---

## 5. Критерии успеха

### Минимальный (обязательный)
- **validation PF > 1.5**, sequential PF > 1.5 на walk-forward
- BUY PF > 1.5 (SELL не требуется — BUY-only)
- Не более 1 года с PF < 0.8 на validation
- **Или обоснованно доказано**, что при текущих данных/признаках это недостижимо

### Целевой
- validation PF > 2.0, sequential PF > 2.0
- Стабильность по годам (не более 1 года с PF < 1.0)
- Frozen test PF > 1.5, не более 1 негативного года

### Если целевой недостижим
- Честно задокументировать верхнюю границу с доказательствами
- Предложить наиболее безопасный production-кандидат с оценкой рисков
- Все результаты воспроизводимы скриптами

---

## 6. Формат отчёта

После завершения всех фаз создать отчёт `docs/reports/2026-05-18-direct-direction-rebuild.md`:

1. **Executive Summary** — одна таблица с результатами всех фаз
2. **Phase 0** — описание скрипта `prepare_raw_features.py`, parity-проверка
3. **Phase A** — таргет, признаки, модель, walk-forward результаты, gate verdict
4. **Phase B** — новые признаки, feature importance, gate verdict
5. **Phase C** — Transformer extractor, результаты, gate verdict
6. **Phase D** — frozen test, финальный результат
7. **Сравнение со старым результатом** — таблица old vs new
8. **Выводы** — достигнут ли PF>2.0, если нет — почему
9. **Риски** — что может пойти не так в production
10. **Следующий шаг** — что делать дальше

---

## 7. Анти-паттерны (напоминание)

| Анти-паттерн | Почему |
|-------------|--------|
| Подбор порогов как «решение» | Маскирует проблемы в данных/признаках |
| Использование test для подбора | Data leakage, PF не репрезентативен |
| Frozen test больше одного раза | Multiple testing, ложная уверенность |
| 3-class BUY/SELL/SKIP | Доказано нежизнеспособно (E0–E5) |
| «Починить» SELL порогами | SELL anti-signal фундаментален |
| Один split без walk-forward | Нет оценки стабильности по режимам |
| Повторение неудачных экспериментов без новых данных | Потеря времени |

---

## 8. Первоочередные действия агента

1. Прочитать все обязательные источники (раздел 1)
2. Изучить код `processing/normalize.py`, `ML/fractal_level_feature_builder.py`, `ML/entry_path_direct_direction_targets.py`, `ML/benchmark_entry_path_binary_direction.py`
3. Создать `ML/prepare_raw_features.py` (Phase 0)
4. Убедиться, что raw source даёт корректные признаки (parity check)
5. Сообщить результат Phase 0 пользователю перед переходом к Phase A
6. Далее последовательно: Phase A → B → C → D

**Удачи. Дисциплина важнее скорости.**
