# Context Handoff

Дата: 2026-06-11.

## Текущий этап

Stage 4 «XGBoost Trading Layer» и Stage 4.1 controls завершены. XGBoost breach-классификатор (AUC 0.68) не конвертируется в статистически значимый PF; быстрые контрольные улучшения также не сработали.

### Полный путь Stage 3.x → Stage 4

| Этап | Модель | Лучший профиль | AUC mean | ΔAUC vs RF base_raw | Торговый PF | Вердикт |
|------|--------|----------------|----------|----------------------|-------------|---------|
| Stage 3 | RF | `relative_geometry` | 0.6580 | +119 bp | — | Profile comparison only |
| Stage 3.1 | RF | `relative_geometry_clean` | 0.6581 | +127 bp | — | Uplift = time, not density |
| Stage 3.2 | XGBoost | `base_raw_plus_time` | 0.6799 | +345 bp | — | Best table-model classifier |
| Stage 4 | XGBoost breach + RF fav | `base_raw_plus_time` | 0.6741 | — | **1.106** (BS_p05=0.923) | ❌ FAIL |
| Stage 4.1 | XGBoost-fav / combined breach | `base_raw_plus_time` | — | — | **1.065** combined (BS_p05=0.883, perm_p=0.050) | ❌ FAIL |

### Результаты Stage 4

| Метрика | base_raw_plus_time | relative_geometry_clean |
|---------|-------------------|-------------------------|
| Winner target | sell_H6_off05 | sell_H6_off05 |
| Winner PF | 1.106 | 1.142 |
| Winner BS_p05 | 0.923 | 0.906 |
| Winner trades/year | 86.0 | 54.5 |
| Таргетов PF ≥ 1.0 | 1/8 | 2/8 |
| Buy mean PF | 0.87 | 0.89 |
| Sell mean PF | 0.99 | 1.01 |
| Gate PF > 1.15 | 0/8 | 0/8 |

### Результаты Stage 4.1

| Проверка | Лучший/ключевой результат | Вердикт |
|----------|---------------------------|---------|
| XGBoost-fav вместо RF-fav | sell_H6_off05 PF 1.106 → 0.904; все 4 SELL-таргета хуже Stage 4 | ❌ FAIL |
| Combined breach H6 AND H12 | sell_comb_off05 PF=1.065, BS_p05=0.883, perm_p=0.050 | ❌ FAIL |
| Permutation test | perm median PF=0.837, perm p95=1.061, observed PF=1.065 | Слабое отделение от случайной перестановки |

### Ключевые находки Stage 4

1. Улучшение breach-классификатора с RF (AUC 0.645) до XGBoost (AUC 0.680) дало лишь маргинальный прирост PF (Stage 2: 0.975 → Stage 4: 1.106). 7/8 таргетов остались убыточными.
2. AUC не предсказывает PF: sell_H12_off02 имеет лучший AUC (0.696) но PF=0.976; sell_H6_off05 имеет AUC=0.674 но PF=1.106.
3. Buy-сторона структурно невыгодна: все 4 buy-таргета PF < 0.94. Причина: XAUUSD в аптренде, buy-фракталы (поддержки) реже дают прибыльный пробой.
4. `base_raw_plus_time` и `relative_geometry_clean` практически идентичны для торговли. Простой профиль предпочтительнее.
5. Статистическая значимость отсутствует: все BS_p05 < 1.0. Winner не отличается от PF=1.0 с доверительной вероятностью.
6. Stage 4.1 подтвердил, что проблема не решается локально: XGBoost-fav ухудшил PF, combined breach не превзошёл Stage 4 winner и не прошёл permutation test с запасом.
7. Проблема глубже классификатора: табличные модели выжали почти всё из плоского фрактального представления. Нужно sequence-представление (Transformer) или пересмотр торговой логики.

### Файлы Stage 4

- `docs/reports/2026-06-11-stage4-trade-xgboost.md` — канонический отчёт Stage 4 (NEW)
- `ML/baseline/benchmark_fractal_stop_stage4.py` — скрипт Stage 4 (NEW)
- `ML/reports/stage4_trade.json` — base_raw_plus_time результаты (NEW)
- `ML/reports/stage4_trade_geom.json` — relative_geometry_clean результаты (NEW)
- `ML/baseline/benchmark_fractal_stop_stage4_1.py` — скрипт Stage 4.1 controls (NEW)
- `ML/reports/stage4_1.json` — Stage 4.1 результаты (NEW)

### Все файлы Stage 3.x (существующие)

- `docs/reports/2026-06-10-feature-profiles-stage3.md` — канонический отчёт Stage 3.x
- `ML/baseline/benchmark_fractal_stop_stage3.py` — Stage 3 RF profile comparison
- `ML/baseline/benchmark_fractal_stop_stage3_1.py` — Stage 3.1 RF ablation
- `ML/baseline/benchmark_fractal_stop_stage3_2.py` — Stage 3.2 XGBoost comparison
- `ML/reports/stage3_profiles.json`, `stage3_1_profiles.json`, `stage3_2_xgboost.json`

### Git

Ветка: `feature/fractal-stop-fav-spec`.

### Не staged / untracked

В рабочем дереве есть untracked артефакты Stage 3.1/3.2/4. Не удалять и не откатывать без явной просьбы.

## Следующий шаг

После Stage 4/4.1 FAIL: не открывать test для текущего кандидата. Быстрые контрольные эксперименты уже проверены и не прошли gate.

Приоритет: Transformer encoder на фрактальной sequence либо пересмотр торговой постановки/таргета. Причина: Stage 3.2/4/4.1 показали, что плоское табличное представление фракталов достигло потолка для RF и XGBoost в текущей схеме `breach -> fav -> trade`.
