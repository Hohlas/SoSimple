# lib_pic_geometry_feature_bank.py

## Назначение

Строит производные признаки геометрии уровня из уже экспортируемых фракталов `lib_PIC`.

Модуль нужен как следующий шаг после диагностики важности признаков: группа `geometry` дала самый сильный сигнал, поэтому её нужно расширить аккуратно и без изменения `lib_PIC.mqh`.

## Входные данные

DataFrame с колонками:

```text
fractal0 ... fractal99
```

Ожидаемый текущий формат фрактала — 22 поля:

```text
T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr
```

Для обратной совместимости модуль может обработать укороченную строку, если в ней есть хотя бы `front/back/reverse`.

## Выходные данные

Копия исходного DataFrame с добавленными колонками вида:

```text
pic_geom_front_mean_w5
pic_geom_ratio_recent_w20
pic_geom_balance_std_w50
pic_geom_size_recent_minus_mean_w100
```

Окна по умолчанию:

```python
(5, 10, 20, 50, 100)
```

`fractal0` считается самым свежим фракталом.

## Признаки

Используются только безопасные поля:

- `front`;
- `back`;
- `reverse`;
- `fractal_atr`.

Не используются:

- `Up12/Dn12/.../Up6/Dn6`, потому что это будущий ход цены относительно фрактала;
- новые поля из `lib_PIC`, которых пока нет в `Nero.csv`.

Основные производные признаки:

- `front / back`;
- `(front - back) / (front + back)`;
- `front / (front + back)`;
- `front + back`;
- доля уровней, где `front > back`;
- доля сбалансированных уровней;
- отличие свежего значения от среднего по окну.

## Использование

```python
from ML.lib_pic_geometry_feature_bank import build_lib_pic_geometry_feature_bank

frame = build_lib_pic_geometry_feature_bank(frame)
```

## Ограничения

- Это только генератор признаков, не торговый benchmark.
- Он не доказывает прибыльность сам по себе.
- Если входной CSV уже нормализован, признаки строятся по нормализованным `front/back/reverse`.
- Перед включением в новый training track нужна отдельная проверка на validation/test.
