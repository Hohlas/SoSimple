# Feature Ablation Study — limit-order entry convention

**Date:** 2026-06-01
**Branch:** `feature/limit-order-entry-convention`
**Data:** `DATA/spread_0.20/` (canonical spread=0.20)
**Target:** `buy_sl3_tp3`
**Model:** RandomForestRegressor (n_estimators=100, max_depth=10, random_state=42)
**Gate:** PF ≥ 1.3, fill_rate ≥ 20%, trades/year ≥ 6, negative_years == 0

## Context

После исправления бага парсинга признаков (T1: `parse_fractal_to_features` использовал Dir вместо Price), baseline flat features изменился с 102 мусорных признаков на 202 корректных (100 dir + 100 price + f0_front + ATR).

Проверка вклада engineered признаков `build_grouped_features()` (~428 features, excl. `ret_dir_atr_lag1`) через поочерёдное отключение групп.

## Results

### Summary table

| Variant | Features | PF | Fill% | T/yr | NegY | R/trade | TopDay | Gate |
|---------|----------|-----|-------|------|------|---------|--------|------|
| **A: flat** | 202 | 1.069 | 96.8% | 2287 | 2 | 0.078 | 0.6% | FAIL |
| B: flat+eng | 630 | 1.037 | 96.9% | 2662 | 2 | 0.042 | 0.5% | FAIL |
| C_atr | 222 | ∞ | 100% | 0.3 | 0 | — | 100% | FAIL |
| C_break_impulse | 242 | 1.051 | 96.9% | 2559 | 2 | 0.058 | 0.5% | FAIL |
| C_direction | 222 | ∞ | 100% | 0.3 | 0 | — | 100% | FAIL |
| C_geometry | 262 | 1.051 | 96.9% | 2612 | 2 | 0.058 | 0.5% | FAIL |
| **C_path_long** | **322** | **1.538** | **98.4%** | **52.4** | **0** | **0.474** | **11.1%** | **PASS** |
| C_path_short | 282 | 1.277 | 97.8% | 53.0 | 2 | 0.294 | 14.5% | FAIL |
| C_price_position | 222 | ∞ | 50.0% | 0.3 | 0 | — | 100% | FAIL |
| C_strength | 262 | 1.057 | 96.8% | 2015 | 2 | 0.065 | 0.7% | FAIL |
| C_row_context | 210 | ∞ | 100% | 0.3 | 0 | — | 100% | FAIL |
| **C_path_long_nf0** | **298** | **1.488** | **96.8%** | **52.4** | **0** | **0.429** | **11.2%** | **PASS** |

### path_long_yearly PF

**C_path_long** (with fractal0, 322 features):

| Year | PF | Trades |
|------|-----|--------|
| 2019 | 0.00 | 0 |
| 2020 | 1.50 | 96 |
| 2021 | 1.85 | 60 |
| 2022 | 1.08 | 24 |

**C_path_long_nf0** (without fractal0, 298 features):

| Year | PF | Trades |
|------|-----|--------|
| 2019 | 0.00 | 0 |
| 2020 | 1.26 | 104 |
| 2021 | 949.48 | 17 |
| 2022 | 1.10 | 59 |

### Baseline yearly PF (A: flat)

| Year | PF | Trades |
|------|-----|--------|
| 2019 | 1.14 | 1011 |
| 2020 | 1.33 | 2204 |
| 2021 | 0.96 | 2459 |
| 2022 | 0.96 | 2184 |

## Findings

1. **Flat baseline gate fail.** После T1-фикса (правильные price/dir признаки) плоские признаки не проходят gate (PF=1.069, 2 negative years). Старый PF=1.53 был артефактом — модель получала только Dir {-1,1} под видом цены.

2. **Все engineered вместе — вред.** 428 признаков добавляют шум: PF падает с 1.069 до 1.037. 8 из 9 групп бесполезны (не улучшают PF значимо).

3. **path_long — единственная сигнальная группа.** Агрегаты up_12/dn_12/up_24/dn_24/up_48/dn_48 по окнам дают PF=1.538 (Δ+0.469 vs flat), gate PASS. Группа содержит 120 признаков (6 полей × 4 агрегата × 5 окон).

4. **Сигнал НЕ держится только на fractal0.** C_path_long_nf0 (без f0 path-полей) даёт PF=1.488 — всего на -0.05 ниже полной версии. Реальный сигнал идёт от исторических path-значений фракталов 1..99, а не от частичных f0-значений.

5. **Низкая плотность сделок.** Оба path_long-варианта дают ~52 сделки/год — на порядок меньше чем flat (2287). Модель становится очень селективной, что даёт качество, но снижает частоту.

6. **2019 — ноль сделок.** В первый год валидации оба path_long-варианта не выбирают ни одной сделки. Причина: модель обучена на train данных, которые хронологически НОВЕЕ val. Требуется переделать split (старые → train, новые → test).

7. **2021 аномалия (nf0).** PF=949 на 17 сделках — чистый статистический флук. Требуется forward-window проверка.

## Conclusion

Engineered признаки `build_grouped_features` как целое бесполезны (шум). Но **path_long** (агрегаты up/dn за горизонты 12/24/48) — единственная группа, несущая сигнал сверх плоских fractal-признаков. Рекомендация: оставить flat + path_long, удалить остальные engineered-группы.

## Script

`ML/baseline/feature_ablation.py` — запуск: `.venv/bin/python -m ML.baseline.feature_ablation`
