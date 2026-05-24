---
name: ml-methodology
description: Use when developing, auditing, or evaluating ML models — feature engineering, labeling, data leakage checks, splits, baselines, training, backtesting, MT4 parity, or production preparation
---

# Методика разработки ML-моделей

## Когда использовать

- Старт нового ML-эксперимента или обучения модели.
- Аудит признаков, таргетов, сплита или бэктеста.
- Проверка на утечки данных, feature contract, online/training mismatch.
- Выбор winner на validation и заморозка перед test.
- Подготовка экспорта, MT4 parity или forward-test.
- Настройка мониторинга и retraining policy.

## Как использовать

1. Прочитай [`docs/methodology/README.md`](../../../docs/methodology/README.md) — таблица «задача → файл».
2. Найди файл, соответствующий текущей задаче.
3. Придерживайся файла как инструкции: выполняй действия по шагам, проходи обязательные проверки, не переходи к следующему этапу без `PASS`.
