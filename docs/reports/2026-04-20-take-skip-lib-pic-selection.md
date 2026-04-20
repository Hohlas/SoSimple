# Take/Skip lib_PIC External Selection

Дата: 2026-04-20  
Ветка: `lib-pic-selection-benchmark`  
Статус: completed

## Цель

Проверить, дают ли новые производные признаки `lib_PIC` пользу как внешний слой отбора поверх уже готовых `take_skip_trailing_stop_v2` prediction CSV.

Это не новый training cycle. Модель не переобучалась.

## Метод

Добавлен benchmark:

- `ML/benchmark_take_skip_lib_pic_selection.py`;
- `tests/test_benchmark_take_skip_lib_pic_selection.py`;
- `docs/ML/benchmark_take_skip_lib_pic_selection.py.md`.

Benchmark:

- берёт готовые exports `seq50`;
- добавляет признаки профиля `baseline_clean_geometry_path`;
- перебирает ограниченную сетку score-selector-ов и feature-фильтров;
- выбирает только на validation;
- применяет frozen rule на test без пересчёта порога признака.

Команда:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.benchmark_take_skip_lib_pic_selection \
  --validation-predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/validation.csv \
  --test-predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --validation-source DATA/Nero_validation_labeled.csv \
  --test-source DATA/Nero_test_labeled.csv \
  --output-dir ML/reports/take_skip_lib_pic_selection \
  --seq-len 100 \
  --score-target take_24_x8 \
  --score-target take_24_x4 \
  --eval-x 8 \
  --eval-x 10 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

## Результаты

### Quality-first

Строгий выбор по PF снова выбрал старое правило без feature-фильтра:

| split | selector | feature filter | trades/year | PF | negative years | max DD ATR |
|---|---|---|---:|---:|---:|---:|
| validation | `take_24_x8`, `prob >= 0.70`, exit `x8` | none | 6.75 | inf | 0 | 0.00 |
| test | frozen | none | 8.20 | 39.74 | 0 | 4.38 |

Вывод: `lib_PIC`-фильтр не улучшил уже подтверждённый quality-кандидат.

### Frequency-first

Без feature-фильтра лучший частотный режим остался прежним:

| split | selector | feature filter | trades/year | PF | negative years | max DD ATR |
|---|---|---|---:|---:|---:|---:|
| validation | `take_24_x4`, `top_k 20%`, exit `x10` | none | 23.75 | 3.92 | 0 | 16.65 |
| test | frozen | none | 19.20 | 7.18 | 1 | 8.97 |

### Feature-frequency-first

Лучший частотный режим с обязательным `lib_PIC`-фильтром:

| split | selector | feature filter | trades/year | PF | negative years | max DD ATR |
|---|---|---|---:|---:|---:|---:|
| validation | `take_24_x8`, `top_k 20%`, exit `x10` | `pic_path_win_proxy24_share_w20 >= 0.25` | 16.25 | 3.16 | 0 | 17.85 |
| test | frozen | same threshold | 14.80 | 5.30 | 0 | 9.78 |

## Вывод

Внешний `lib_PIC`-фильтр не стал новым лучшим общим правилом.

Но он дал полезный диагностический сигнал:

- снижает частоту относительно raw frequency (`19.2 -> 14.8` trades/year на test);
- убирает отрицательный годовой срез (`1 -> 0`);
- сохраняет PF сильно выше 1 (`5.30`);
- использует понятный признак: доля свежих фракталов, где благоприятный ход за 24 бара был выше неблагоприятного.

Практический вывод: как внешний слой отбора это не замена текущим `quality` / `frequency` правилам. Но как аргумент для нового обучения на `lib_PIC`-производных признаках результат достаточный: признаки несут некоторую информацию о качестве входа.

## Следующий шаг

Не усложнять внешний слой отбора дальше. Следующий рациональный шаг — новый training track, где `lib_PIC`-производные признаки участвуют уже внутри модели:

- `baseline_clean`;
- `baseline_clean_path`;
- `baseline_clean_geometry_path`;
- контрольный старый профиль.

## Артефакты

- `ML/reports/take_skip_lib_pic_selection/validation_grid.csv`
- `ML/reports/take_skip_lib_pic_selection/final_verdict.json`
