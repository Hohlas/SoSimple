# Fractal Channel Ablation — edge_6 + TB

> **Date**: 2026-06-04
> **Status**: Completed (validation + frozen test)
> **Goal**: Измерить вклад групп признаков 29-канального тензора в предсказание edge_6 и buy_sl3_tp3.
> **Related plan/spec**: `docs/audit/to_do.md` — Абляция
> **Related commit**: `fa39797`

## Context

После Фазы 1 (контракт данных, raw price, 23 поля) и Фазы 2 (ATR-distance признаки, N_FRACTAL_FEATURES=29) запущена абляция каналов тензора. Старая абляция (`ML/baseline/feature_ablation.py`) работала на pooled-нормализации и старом парсинге flat-признаков. Результаты могли быть артефактом нормализации.

Новая абляция использует `parse_fractals_to_3d()` напрямую, RF на подмножествах 29 каналов. Пороги — только train. Validation для отбора вариантов, frozen test для финальной оценки.

## What Was Done

**Группы признаков:**

| Группа | Каналы | Индексы |
|--------|--------|---------|
| base | price, direction, front, back, strong, break, reverse, power, count, impulse | 0–9 |
| path | up_12, dn_12, up_24, dn_24, up_48, dn_48, up_3, dn_3, up_6, dn_6 | 10–19 |
| atr_ratio | log(fractal_atr / ATR) | 20 |
| time | hour_sin, hour_cos, time_pos, log_shift, log_delta_shift | 21–25 |
| atr_dist | signed_dist_atr, abs_dist_atr, dir_dist_atr | 26–28 |

**Варианты**: `all`, `no_path`, `no_atr_dist`, `no_time`, `no_base`, `no_horizon6` (убраны up_6/dn_6 — горизонт цели), `only_dir`, `only_base`, `only_time`, `only_path`.

**Модель**: `RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)` для edge_6; `RandomForestClassifier` (те же параметры) для buy_sl3_tp3.

**Цели**: edge_6 (регрессия, пороги LONG=70-й перцентиль / SHORT=30-й перцентиль на train), buy_sl3_tp3 (классификация на известных исходах, порог 70-й перцентиль train-вероятностей).

**Скрипт**: `ML/baseline/fractal_ablation.py`, JSON: `ML/reports/fractal_ablation.json` (validation), `ML/reports/fractal_ablation_test.json` (frozen test).

## Changed Files

- Новый: `ML/baseline/fractal_ablation.py`
- Новый: `ML/reports/fractal_ablation.json` (validation)
- Новый: `ML/reports/fractal_ablation_test.json` (frozen test)
- Новый: `docs/reports/2026-06-04-fractal-ablation.md`

## Verification

Данные: `DATA/Nero_XAUUSD_train_labeled.csv` (44 159 строк, 2004–2019), `DATA/Nero_XAUUSD_validation_labeled.csv` (9 463 строк, 2019–2022).

`statistics/data_contract_smoke_check.py` — все проверки пройдены. Тензор (N, 100, 29), цена не бинарна, direction ∈ {−1, 1}, ATR-distance не в [0, 1].

## Results

### edge_6 (validation, 2019–2022, пороги из train)

| Вариант | Каналов | PF | Δ vs all | Сделок | Win% | NegY |
|---------|---------|-----|----------|--------|------|------|
| **all** | 29 | **12.33** | — | 5 568 | 88.3% | 0 |
| **no_atr_dist** | 26 | 12.06 | −0.28 | 5 554 | 88.0% | 0 |
| **no_horizon6** | 27 | 11.98 | −0.35 | 5 571 | 88.1% | 0 |
| no_path | 19 | 11.68 | −0.65 | 5 598 | 87.8% | 0 |
| no_time | 24 | 10.80 | −1.53 | 5 799 | 87.3% | 0 |
| **only_base** | 10 | 8.81 | −3.52 | 5 962 | 85.7% | 0 |
| no_base | 19 | 7.85 | −4.48 | 5 494 | 83.5% | 0 |
| only_dir | 1 | 7.13 | −5.21 | 5 959 | 81.9% | 0 |
| only_path | 10 | 4.16 | −8.17 | 5 343 | 77.2% | 0 |
| only_time | 5 | 0.98 | −11.35 | 6 376 | 49.2% | 3 |

Годовая разбивка ключевых вариантов:

| Год | all | no_atr_dist | only_base | only_dir |
|-----|-----|-------------|-----------|----------|
| 2019 | 10.0 | 9.3 | 7.4 | 6.2 |
| 2020 | 13.0 | 13.8 | 9.3 | 7.9 |
| 2021 | 13.6 | 12.6 | 9.3 | 6.9 |
| 2022 | 12.3 | 12.0 | 8.6 | 7.2 |

### buy_sl3_tp3 (validation, порог 70-й перцентиль train)

Порог фиксирован: 70-й перцентиль train-вероятностей, без sweep. Test не участвует.

| Вариант | PF | Сделок | Win% | NegY |
|---------|-----|--------|------|------|
| no_horizon6 | 4.00 | 5 | 80.0% | 2 |
| no_atr_dist | 2.00 | 3 | 66.7% | 3 |
| only_dir | 1.49 | 164 | 59.8% | 0 |
| no_path | 1.43 | 17 | 58.8% | 1 |
| only_path | 1.24 | 347 | 55.3% | 1 |
| no_base | 1.10 | 82 | 52.4% | 1 |
| only_time | 0.91 | 111 | 47.7% | 2 |
| no_time | 0.75 | 7 | 42.9% | 3 |

Годовая only_dir: 2019 PF=1.23, 2020 PF=1.27, 2021 PF=2.64, 2022 PF=1.30.

### Frozen Test (2022–2026, пороги из train)

Пороги заморожены на train. Test не участвовал в выборе порогов.

#### edge_6 (70/30 перцентили train-предсказаний)

| Вариант | Test PF | Сделок | Win% | NegY | Годовая PF |
|---------|---------|--------|------|------|------------|
| no_atr_dist | **11.36** | 5 960 | 86.8% | 0 | 13.4/10.6/12.1/11.7/10.1 |
| all | 11.30 | 5 939 | 86.9% | 0 | 12.9/10.1/12.2/12.0/10.0 |
| no_horizon6 | 11.26 | 5 927 | 86.9% | 0 | 13.0/10.2/12.0/11.7/9.8 |
| only_base | 8.75 | 6 104 | 85.2% | 0 | 8.2/7.2/9.2/10.0/7.1 |
| only_dir | 6.41 | 6 874 | 80.5% | 0 | 6.4/5.9/7.0/6.6/6.1 |
| only_path | 3.97 | 5 575 | 76.2% | 0 | 4.5/3.3/4.0/4.0/4.4 |

#### buy_sl3_tp3 (70-й перцентиль train-вероятностей)

| Вариант | Test PF | Сделок | Win% | NegY | Годовая PF |
|---------|---------|--------|------|------|------------|
| only_dir | 1.34 | 225 | 57.3% | 2 | ∞/0.37/2.00/1.20/0.25 |
| only_path | 1.13 | 307 | 53.1% | 2 | 0.20/1.36/1.15/1.18/0.48 |
| only_base | ∞ | 14 | 100% | 3 | — |
| no_atr_dist | 0.00 | 1 | 0% | 5 | — |
| all | 0.00 | 0 | — | 5 | — |
| no_horizon6 | 0.00 | 0 | — | 5 | — |

Большинство вариантов даёт 0 сделок либо 1–14 сделок — статистический шум. `only_dir` (225 сделок) и `only_path` (307 сделок) — единственные варианты с meaningful sample, но годовая устойчивость отсутствует: 2023 PF=0.37 у `only_dir`, 2022 PF=0.20 у `only_path`.

## Conclusions

1. **Base-признаки (цена, геометрия, сила) — главный источник edge_h сигнала.** `only_base` PF=8.75 на test (10 каналов из 29). Это 77% полного тензора PF=11.3.

2. **Признаки той же размерности, что цель, не критичны.** `no_horizon6` (без up_6/dn_6) PF=11.26 — почти равен all PF=11.30. Модель предсказывает edge_6 без прямого доступа к up_6/dn_6.

3. **Path-каналы 3D-тензора (up/dn) несут самостоятельный сигнал** (`only_path` PF=3.97 на test) — не артефакт нормализации. Старые плоские агрегаты path_long этим опытом не проверялись.

4. **ATR-distance не добавляют к edge_h** (Δ от −0.28 до +0.06 в пределах шума). Не удалять, но вклад не подтверждён.

5. **Time-признаки: полезны для edge_h, не подтверждены для TB.** `no_time` PF=10.80 (Δ −1.53 от all) на edge_6 — умеренный вклад. На TB выборка шумная: `no_time` PF=0.75 при 7 сделках на val, test не запускался. Вывод по TB через time-признаки невозможен при текущем размере выборки.

6. **TB-сигнал: при честном пороге (70-й перцентиль train) большинство вариантов даёт 0 сделок.** `only_dir` (225 сделок, PF=1.34) и `only_path` (307 сделок, PF=1.13) — единственные с meaningful sample, но годовая устойчивость отсутствует (2023 PF=0.37 у only_dir). При текущей RF-постановке и честном train-пороге полезный TB-сигнал не подтверждён.

7. **edge_6 — диагностическая цель.** PF=11.3 показывает, что признаки сильно различают строки с большим/малым net excursion. Это НЕ торговый результат (PnL=MFE−MAE). Но масштаб сигнала и устойчивость по годам подтверждают: признаки несут информацию о будущем движении.

## Limitations / Open Questions

1. **Только RF.** Глубокие модели (Transformer, BiLSTM) могут иначе использовать ATR-distance и time-признаки.

2. **Только edge_6 и buy_sl3_tp3.** Другие горизонты (edge_12, другие TB-таргеты) не проверены.

3. **Граница val/test совпадает по времени** (2022-10-28 16:00, разные строки). Для строгого OOS нужен purge.

4. **PnL = MFE−MAE для edge_h** — идеализированная метрика, не торговый результат. PF=11.3 интерпретировать как «модель сильно различает строки с большим и малым net excursion», а не как «торговая стратегия с PF=11.3».

5. **ATR-distance вклад не подтверждён** — разница между all и no_atr_dist в пределах шума (Δ от −0.28 до +0.06). Нельзя утверждать ни «полезен», ни «бесполезен» без дополнительных проверок.

## Next Step

- Повторить абляцию на других горизонтах (edge_12).
- Проверить ATR-distance на глубоких моделях (Transformer).
- Direction + flat up/dn признаки для edge_h (запланировано Фазой 3).
- Для TB — пересмотреть постановку задачи (другие SL/TP комбинации, другой метод отбора сделок).

## Related Materials

- `ML/baseline/fractal_ablation.py` — скрипт абляции
- `ML/baseline/direction_only_signal.py` — direction-only baseline
- `ML/data_loader.py` — parse_fractals_to_3d, каналы 26–28
- `docs/reports/2026-06-03-direction-only-signal.md` — direction-only + TB эксперимент
- `docs/audit/to_do.md` — план абляции
