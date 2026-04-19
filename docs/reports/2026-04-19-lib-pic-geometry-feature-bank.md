# lib_PIC Geometry Feature Bank

Дата: 2026-04-19  
Ветка: `lib-pic-geometry-feature-bank`

## Цель

Реализовать первый безопасный набор новых входных признаков вокруг геометрии уровня `lib_PIC`.

Причина: диагностика [2026-04-19-current-feature-importance-diagnostics.md](2026-04-19-current-feature-importance-diagnostics.md) показала, что группа `geometry` (`front/back/reverse`) заметно сильнее остальных групп при объяснении цели `trail_24_pnl_atr_x8`.

## Что сделано

Добавлен модуль:

```text
ML/lib_pic_geometry_feature_bank.py
```

Он строит признаки из уже существующих полей:

- `front`;
- `back`;
- `reverse`;
- `fractal_atr`.

Модуль не использует `Up/Dn`, чтобы не тащить во входные признаки будущий ход цены.

## Новые признаки

По окнам `5/10/20/50/100` строятся:

- среднее, стандартное отклонение, максимум и свежее значение `front`;
- среднее, стандартное отклонение, максимум и свежее значение `back`;
- среднее, максимум и свежее значение `reverse`;
- `front / back`;
- `(front - back) / (front + back)`;
- `front / (front + back)`;
- `front + back`;
- доля уровней, где `front > back`;
- доля сбалансированных уровней;
- отличие свежего `front/back/size` от среднего по окну;
- сводки по `fractal_atr`.

Всего по умолчанию: `145` новых признаков.

## Почему это безопасный следующий шаг

Этот этап не меняет:

- `lib_PIC.mqh`;
- формат `Nero.csv`;
- разметку;
- модель обучения;
- торговую логику MT4.

Он только добавляет воспроизводимый Python-слой признаков, который можно включить или выключить в будущих training/benchmark экспериментах.

## Риски

- Если входной CSV уже содержит нормализованные `front/back/reverse`, признаки строятся по нормализованным значениям. Это допустимо для ML, но не равно сырой рыночной величине.
- Высокая важность `geometry` в диагностике не доказывает прибыльность новой модели.
- Следующий этап обязан проверять этот слой через validation-first benchmark.

## Проверки

```bash
python -m pytest tests/test_lib_pic_geometry_feature_bank.py -q
```

Результат:

```text
5 passed
```

## Следующий шаг

Подключить `lib_pic_geometry_feature_bank` к одному bounded training track или read-only feature diagnostic:

- сравнить baseline без geometry bank и с geometry bank;
- не менять другие параметры одновременно;
- отбирать только на validation;
- test использовать один раз как frozen check.
