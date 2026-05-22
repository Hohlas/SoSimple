# entry_path_direct_direction_targets.py

## Назначение
Строит target families для direct-direction `SELL / SKIP / BUY`: A, C и D.

## Target provenance
Target D строится из OHLC path и raw ATR, поэтому остаётся допустимым для corrected validation baseline.

A/C target moves с суффиксом `_atr` теперь трактуются строго как ATR units:

```text
buy_fav_h_atr = raw up_h / raw ATR
buy_adv_h_atr = raw dn_h / raw ATR
sell_fav_h_atr = raw dn_h / raw ATR
sell_adv_h_atr = raw up_h / raw ATR
```

Нормализованные split CSV `up_*/dn_*` нельзя использовать как ATR-target source для A/C. Поэтому `summarize_target_frequencies()` по умолчанию включает только Target D; A/C можно включать только при наличии raw up/dn source.

## Ограничения
Если `ATR <= 0`, ATR moves возвращаются как `0.0`, чтобы не создавать бесконечные target values.
