# fractal_level_feature_builder.py

## Назначение
Строит fractal-level признаки для direct-direction и entry-path diagnostics: nearest-k, zones и zones+nearest-k.

## Исправленный price-distance contract
Distance features (`*_raw_distance_atr`, zones, closest distance) должны считаться как:

```text
(raw fractal price - raw fractal0 price) / raw ATR
```

Для этого `build_fractal_level_features(..., raw_price_frame=...)` принимает raw/current-row frame с тем же порядком строк, что и основной frame. Если `raw_price_frame` не передан, используется старый frame, что допустимо только для диагностик, где price уже raw.

## Provenance
- `feature_source`: current-row фракталы; для price distance — raw/current-row source.
- `target_source`: top-level `up_*/dn_*`, OHLC-derived targets или другие supervised labels.
- `diagnostic_source`: `signal`, `predict`, prediction CSV, score diagnostics.

Model inputs не должны зависеть от top-level target columns. Это покрыто тестом perturbation: изменение `up_*/dn_*` на уровне строки не меняет output feature frame.

## Использование
```python
features = build_fractal_level_features(
    labeled_frame,
    raw_price_frame=raw_sorted_frame,
    input_family="nearest_k",
    k=4,
)
```
