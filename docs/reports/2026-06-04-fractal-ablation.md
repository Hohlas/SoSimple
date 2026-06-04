# Fractal Channel Ablation — edge_6 + TB

> **Date**: 2026-06-04
> **Status**: Completed (validation only, test to follow)
> **Goal**: Измерить вклад групп признаков 29-канального тензора в предсказание edge_6 и buy_sl3_tp3. Ответить: пережил ли path_long исправление нормализации, и какие группы признаков несут сигнал.
> **Related plan/spec**: `docs/audit/to_do.md` — Абляция
> **Related commit**: `fa39797`

## Context

После Фазы 1 (контракт данных, raw price, 23 поля) и Фазы 2 (ATR-distance признаки, N_FRACTAL_FEATURES=29) запущена абляция каналов тензора. Старая абляция (`ML/baseline/feature_ablation.py`) работала на pooled-нормализации и старом парсинге flat-признаков. Результаты могли быть артефактом нормализации.

Новая абляция использует `parse_fractals_to_3d()` напрямую, RF на подмножествах 29 каналов. Оценка только на validation.

## What Was Done

**Группы признаков:**

| Группа | Каналы | Индексы |
|--------|--------|---------|
| base | price, direction, front, back, strong, break, reverse, power, count, impulse | 0–9 |
| path | up_12, dn_12, up_24, dn_24, up_48, dn_48, up_3, dn_3, up_6, dn_6 | 10–19 |
| atr_ratio | log(fractal_atr / ATR) | 20 |
| time | hour_sin, hour_cos, time_pos, log_shift, log_delta_shift | 21–25 |
| atr_dist | signed_dist_atr, abs_dist_atr, dir_dist_atr | 26–28 |

**Варианты**: `all` (29 каналов), `no_path`, `no_atr_dist`, `no_time`, `no_base`, `only_dir`.

**Модель**: `RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)` для edge_6; `RandomForestClassifier` (те же параметры) для buy_sl3_tp3.

**Цели**: edge_6 (регрессия, пороги LONG=70-й перцентиль / SHORT=30-й перцентиль на train), buy_sl3_tp3 (классификация на известных исходах, порог 70-й перцентиль train-вероятностей).

**Скрипт**: `ML/baseline/fractal_ablation.py`, JSON: `ML/reports/fractal_ablation.json`.

## Changed Files

- Новый: `ML/baseline/fractal_ablation.py`
- Новый: `ML/reports/fractal_ablation.json`
- Новый: `docs/reports/2026-06-04-fractal-ablation.md`

## Verification

Данные: `DATA/Nero_XAUUSD_train_labeled.csv` (44 159 строк, 2004–2019), `DATA/Nero_XAUUSD_validation_labeled.csv` (9 463 строк, 2019–2022).

`statistics/data_contract_smoke_check.py` — все проверки пройдены. Тензор (N, 100, 29), цена не бинарна, direction ∈ {−1, 1}, ATR-distance не в [0, 1].

## Results

### edge_6 (validation)

| Вариант | Каналов | PF | Δ vs all | Сделок | Win% | NegY |
|---------|---------|-----|----------|--------|------|------|
| all | 29 | 12.33 | — | 5 568 | 88.3% | 0 |
| no_atr_dist | 26 | 12.06 | −0.28 | 5 554 | 88.0% | 0 |
| no_path | 19 | 11.68 | −0.65 | 5 598 | 87.8% | 0 |
| no_time | 24 | 10.80 | −1.53 | 5 799 | 87.3% | 0 |
| no_base | 19 | 7.85 | −4.48 | 5 494 | 83.5% | 0 |
| only_dir | 1 | 7.13 | −5.21 | 5 959 | 81.9% | 0 |

### buy_sl3_tp3 (validation)

| Вариант | PF | Сделок | NegY |
|---------|-----|--------|------|
| all | ∞ | 1 | 3 |
| no_path | 1.00 | 6 | 3 |
| no_base | 0.86 | 13 | 2 |
| only_dir | 2.33 | 20 | 1 |

Все варианты — 1–20 сделок, статистический шум. Сигнала нет.

## Conclusions

1. **Base-признаки (цена, геометрия, сила) — главный источник сигнала для edge_h.** Их удаление роняет PF с 12.33 до 7.85 (Δ −4.48). Самый большой вклад среди всех групп.

2. **Path-признаки (up/dn) несут умеренный сигнал** (Δ −0.65). Это НЕ артефакт старой pooled-нормализации — сигнал сохраняется на per-pair нормализации и raw-price данных.

3. **ATR-distance признаки почти не добавляют к edge_h** (Δ −0.28). Либо слабая корреляция с edge_6, либо RF не извлекает зависимость.

4. **Time-признаки умеренно полезны** (Δ −1.53). Сезонность и позиция на временной оси вносят вклад.

5. **Полный тензор PF=12.33 — в 1.7× выше direction-only PF=7.13.** Direction-only — нижняя граница, а не потолок. Добавление геометрии/силы/пути/времени даёт существенный прирост.

6. **TB-таргеты (buy_sl3_tp3) — сигнала нет ни на одном варианте.** Подтверждает вывод из direction-only+TB эксперимента: edge_h (форма движения) и порядок касаний (TB) — принципиально разные задачи.

## Limitations / Open Questions

1. **Только validation.** Test не участвовал в оценке. Для финальных цифр нужен frozen test.

2. **Только RF.** Глубокие модели (Transformer, BiLSTM) могут иначе использовать ATR-distance и time-признаки.

3. **Только edge_6 и buy_sl3_tp3.** Другие горизонты (edge_12, другие TB-таргеты) не проверены.

4. **Граница val/test совпадает по времени** (2022-10-28 16:00, разные строки). Для строгого OOS нужен purge.

5. **PnL = MFE−MAE для edge_h** — идеализированная метрика, не торговый результат.

## Next Step

- Frozen test на отложенном test-сплите (2022–2026).
- Повторить абляцию на других горизонтах (edge_12).
- Проверить ATR-distance на глубоких моделях (Transformer).
- Direction + flat up/dn признаки для edge_h (запланировано Фазой 3).

## Related Materials

- `ML/baseline/fractal_ablation.py` — скрипт абляции
- `ML/baseline/direction_only_signal.py` — direction-only baseline
- `ML/data_loader.py` — parse_fractals_to_3d, каналы 26–28
- `docs/reports/2026-06-03-direction-only-signal.md` — direction-only + TB эксперимент
- `docs/audit/to_do.md` — план абляции
