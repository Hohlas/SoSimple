---
last_updated: 2026-06-06
sources: 5
status: active
---

# Limit-Order + Feature Foundation (05-29 — 06-05)

> После limit-order entry experiment фокус сместился с "исполним ли Close-entry" на "какие фрактальные признаки реально несут сигнал".

## Хронология

### Limit-order entry (05-29)

Close-entry был переведён в исполнимую форму через pending BUY/SELL LIMIT на уровне `Close[row]`: 6 баров на fill, 24 бара на барьер, canonical spread `0.20`.

Результат baseline: BUY `buy_sl3_tp3` прошёл gate на canonical spread с PF `1.531`, fill rate `96.4%`, `55.3` сделок в год и `0` отрицательных лет. SELL не прошёл из-за асимметрии XAUUSD. Transformer на filled BUY targets дал около случайного качества по главной цели.

Источник: [2026-05-29-limit-order-entry.md](../../docs/reports/2026-05-29-limit-order-entry.md)

### Feature ablation (06-01)

После исправления бага парсинга признаков `parse_fractal_to_features()` старый flat baseline перестал проходить gate: PF `1.069`, `2` отрицательных года. Старый PF `1.53` был связан с тем, что direction `+/-1` попадал в price-поля.

Из engineered-групп полезной оказалась только `path_long`: PF `1.538`, около `52` сделок в год, `0` отрицательных лет. Вариант без `fractal0` почти сохранил результат, значит сигнал не держится только на частично известном текущем фрактале.

Источник: [2026-06-01-feature-ablation.md](../../docs/reports/2026-06-01-feature-ablation.md)

### Direction-only + TB (06-03)

100 направлений фракталов сами по себе дают сильный диагностический сигнал для `edge_h = up_h - dn_h`: на test `edge_6` PF `6.427`, `edge_12` PF `3.921`, отрицательных лет `0`.

Но этот сигнал не стал торговым TB-правилом. Лучший TB-вариант `buy_sl2_tp3` дал PF `1.113` и `3` отрицательных test-года. Вывод: направления несут информацию о будущем движении, но порядок касаний SL/TP текущая RF-постановка не извлекает устойчиво.

Источник: [2026-06-03-direction-only-signal.md](../../docs/reports/2026-06-03-direction-only-signal.md)

### Fractal channel ablation (06-04)

Новая абляция использовала 29-канальный тензор из `parse_fractals_to_3d()` без старого pooled-normalization артефакта. Для `edge_6` полный набор дал test PF `11.30`, `0` отрицательных лет; `only_base` сохранил PF `8.75`, `only_dir` — `6.41`, `only_path` — `3.97`.

Для `buy_sl3_tp3` устойчивый TB-сигнал не подтвердился: meaningful sample был только у `only_dir` и `only_path`, но годовая устойчивость отсутствовала. `edge_6` остаётся диагностической, а не торговой целью.

Источник: [2026-06-04-fractal-ablation.md](../../docs/reports/2026-06-04-fractal-ablation.md)

### RF GridSearch (06-05)

GridSearch по RF для `edge_6` показал, что основной прирост даёт глубина дерева. Лучший validation-кандидат на 10 фракталах: `n_estimators=200`, `max_depth=20`, `min_samples_leaf=1`, PF `12.96` против baseline `11.38`.

Статус диагностический: проверка была на 10K train rows и 10 фракталах, без frozen test. Нельзя закреплять это как production-дефолт до полного прогона на 100 фракталах и test.

Источник: [2026-06-05-rf-gridsearch.md](../../docs/reports/2026-06-05-rf-gridsearch.md)

## Сводный вывод

Фрактальные признаки действительно несут сильный сигнал о будущей амплитуде движения (`edge_6`), и этот сигнал не сводится к одному `fractal0.dir`. Но перевод диагностического edge-сигнала в устойчивое торговое правило с порядком касаний SL/TP пока не подтверждён.

Практический следующий шаг: проверять лучший RF-кандидат и feature subset на полном тензоре с frozen test, отдельно пересматривая TB-постановку и выход по timeout.
