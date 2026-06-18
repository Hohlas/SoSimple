# Context Handoff

Дата: 2026-06-17 (Stage 5.0: обнаружен баг нормализации, исправлен, ожидает повторного прогона).

## Текущий этап

Stage 5.0 Transformer Breach Holdout — **DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG**. Полноразмерный Transformer не был обучен с нормализацией признаков. StandardScaler импортирован, но не применён. Признак `price` (390–2650 долларов) доминировал над остальными (0..1) в attention.

### Что исправлено

1. **Нормализация:** `normalize_profile_features()` — раздельный StandardScaler для token-признаков (fit на валидных позициях train) и row-признаков. Padding остаётся нулём.
2. **relative_price профили:** 3 диагностических профиля с `(fractal_price - f0_price) / ATR` вместо абсолютной цены.
3. **OHLC-проверка меток:** `verify_breach_labels_against_ohlc()` — сверка `sell_stop_broken_H6_off05_flag` с OHLC для 30-40 случайных строк holdout.
4. **JSON-структура:** `previous_run_status: DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG`, scaler stats, OHLC verification.
5. **Тесты:** 43 теста (было 39, +4 для нормализации и relative_price).

### Результат первоначального прогона (без нормализации)

| Метрика | Transformer (primary) | XGBoost base_raw_plus_time |
|---------|----------------------|---------------------------|
| Holdout AUC | 0.6018 | 0.6524 |
| Holdout lift_30 | 0.766 | 0.620 (меньше=лучше) |
| Gate verdict | FAIL (gate1 ❌, gate2 ❌, gate3 ✅) | — |

### Следующий шаг

Запустить повторный прогон с `--single-seed`:
```bash
python -m ML.baseline.benchmark_stage5_transformer_breach --single-seed
```

Прогон включает:
- Phase 1: all100_base10_time + all100_base10_no_time (с нормализацией)
- Phase 2: newest20, nearest40, corridor_10atr (с нормализацией)
- OHLC label verification (автоматически перед обучением)
- relative_price диагностические профили добавлены как Phase 2.5

Ожидаемое время: ~2 часа (6 профилей × ~15-20 мин/профиль с нормализацией).

### Файлы

Код:
- `ML/baseline/benchmark_stage5_transformer_breach.py` — раннер (исправлен: нормализация, relative_price, OHLC-проверка)
- `ML/models/fractal_breach_transformer.py` — модель (без изменений)
- `tests/test_stage5_transformer_breach.py` — 43 теста

Результаты:
- `ML/reports/stage5_transformer_breach.json` — старый результат (без нормализации)
- `docs/reports/2026-06-17-stage5-transformer-breach.md` — отчёт (обновлён)

### Git

Все изменения не закоммичены. Ветка: `feature/fractal-stop-fav-spec`.
