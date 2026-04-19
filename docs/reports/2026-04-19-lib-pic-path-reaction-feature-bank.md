# lib_PIC Path-Reaction Feature Bank

Дата: 2026-04-19  
Ветка: `lib-pic-path-reaction-feature-bank`

## Цель

Добавить отдельный слой признаков по `Up/Dn`, не смешивая его с geometry-bank.

Смысл: `Up/Dn` описывают историческую реакцию цены после уже существующего уровня. Это не форма уровня, а поведение цены после него.

## Что сделано

Добавлен модуль:

```text
ML/lib_pic_path_reaction_feature_bank.py
```

Он строит признаки из:

- `Dir`;
- `Up3/Dn3`;
- `Up6/Dn6`;
- `Up12/Dn12`;
- `Up24/Dn24`;
- `Up48/Dn48`.

## Логика

Для каждого фрактала признаки переводятся в сторону уровня:

- если `Dir > 0`, то `fav = Up`, `adv = Dn`;
- если `Dir < 0`, то `fav = Dn`, `adv = Up`.

Так модель получает не просто “ход вверх/вниз”, а “благоприятный/неблагоприятный ход относительно направления уровня”.

## Новые признаки

По окнам `5/10/20/50/100` и горизонтам `3/6/12/24/48` строятся:

- `fav*_mean/max/recent`;
- `adv*_mean/max/recent`;
- `edge*_mean/recent`, где `edge = fav - adv`;
- `rr*_mean/recent`, где `rr = fav / adv`;
- `win_proxy*_share`, где `fav > adv`;
- наклоны `fav/adv/edge` между 3 и 48 барами;
- наклоны `fav/adv/edge` между 12 и 48 барами.

Всего по умолчанию: `305` новых признаков.

## Временная корректность

`Up/Dn` формируются в `lib_PIC.mqh` инкрементально по уже прошедшим барам и экспортируются в `Nero.csv` как состояние, известное на момент строки. Поэтому сам факт использования `Up/Dn` не является заглядыванием вперёд.

Эта семантика зафиксирована в `docs/DATA_FLOW.md`.

## Проверки

```bash
python -m pytest tests/test_lib_pic_path_reaction_feature_bank.py -q
```

Результат:

```text
5 passed
```

Проверка на реальном validation-сэмпле:

- `61` признак на одно окно;
- `0` NaN;
- корректная обработка `fractal0` как самого свежего фрактала.

## Следующий шаг

Сравнить три набора входов в bounded benchmark:

- baseline без новых feature-bank;
- baseline + geometry-bank;
- baseline + geometry-bank + path-reaction-bank.

Отбор только на validation, test как frozen check.
