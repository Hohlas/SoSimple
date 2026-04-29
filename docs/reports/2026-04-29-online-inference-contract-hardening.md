# Online Inference Contract Hardening

> **Date**: 2026-04-29
> **Status**: Completed
> **Goal**: Закрыть аудит online preprocessing и заблокировать некорректный запуск legacy ML-контракта, который требует future-derived входные признаки.
> **Related plan/spec**: текущий online diagnostic audit
> **Related commit**: 2b09aec

## Context

Online diagnostic показал два разных класса проблем:

1. Механический preprocessing был неполным: raw `Nero.csv` нужно сортировать и нормализовать так же, как live-safe часть training pipeline.
2. Более серьёзный ML-contract разрыв: legacy `original_baseline` использовал как вход модели row-wise признаки, которые формируются через будущие бары (`predict`, `ret_*`, `fav_*`, `adv_*`). В live `Nero.csv` этих признаков честно нет.

Поэтому задача этапа была не “дочинить старый watcher до production”, а остановить некорректный online ML-запуск и оставить только явно помеченный unsafe режим для проверки механической цепочки MT4 -> Python -> CSV -> MT4.

## What Was Done

- Добавлен общий live-safe preprocessing:
  - сортировка `fractal0..fractalN` по `fractal_time` descending;
  - проверка сортировки после preprocessing;
  - `normalize_rowwise(verbose=False)`;
  - защита от случайной повторной нормализации уже preprocessed snapshot.
- `API.telemetry_signal_watcher` получил `OnlineInferenceContractError`.
- Legacy `original_contour/original_baseline` теперь заблокирован online по умолчанию.
- Добавлен явный override `--allow-unsafe-future-features` только для старой механической диагностики.
- `API.api_server` переведён на общий `preprocess_online_frame()`, чтобы альтернативный inference path не нормализовал неотсортированные фракталы.
- `normalize_rowwise()` получил параметр `verbose`, чтобы runtime watcher не засорял stdout.
- `.kilo/` исключён из git/wiki integrity как локальное runtime/worktree-хранилище.

## Changed Files

- `processing/fractal_preprocessing.py` - общий модуль сортировки фракталов.
- `processing/online_causal_preprocessing.py` - live-safe preprocessing, validation, quiet normalize.
- `processing/normalize.py` - `verbose=False` для runtime.
- `API/telemetry_signal_watcher.py` - contract guard и unsafe override.
- `API/api_server.py` - общий preprocessing вместо прямой нормализации.
- `tests/test_online_causal_preprocessing.py` - CSV I/O, validation, legacy 18-field, quiet runtime, idempotency guard.
- `tests/test_telemetry_signal_watcher.py` - watcher guard и explicit unsafe override.
- `tests/test_api_server_preprocessing.py` - REST inference path использует общий preprocessing.
- Документация: `API/README.md`, `docs/API/`, `docs/MT/trading_strategy.md`, `docs/processing/`, `MODULE_INDEX.md`, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/`.

## Verification

```bash
./.venv/bin/python -m pytest \
  tests/test_online_causal_preprocessing.py \
  tests/test_telemetry_signal_watcher.py \
  tests/test_api_server_preprocessing.py \
  tests/test_inverse_piecewise.py -q
```

Result:

```text
32 passed in 4.14s
```

```bash
./.venv/bin/python -m py_compile \
  processing/fractal_preprocessing.py \
  processing/online_causal_preprocessing.py \
  processing/normalize.py \
  processing/label_main.py \
  API/telemetry_signal_watcher.py \
  API/api_server.py \
  wiki/wiki.py
```

Result: exit code `0`.

```bash
./.venv/bin/python wiki/wiki.py verify
```

Result:

```text
OK — index is up to date.
```

`git diff --check`: exit code `0`.

## Results

- Raw `Nero.csv` больше не должен попадать напрямую в inference path.
- Watcher больше не молча подставляет нули вместо отсутствующих future-derived признаков.
- При текущем legacy `original_baseline` нормальный online result - остановка на `OnlineInferenceContractError`.
- Unsafe override оставлен только для проверки файловой/процессной связки, без права интерпретировать сделки как ML-correct online/test parity.

## Conclusions

Механическая часть online preprocessing hardened, но старый checkpoint не стал production-ready.

Главный вывод этапа: historical test для `original_baseline/original_plus_path` был загрязнён future-derived входными признаками. Поэтому старые test/MT4 результаты по этому контуру нельзя использовать как доказательство честного online качества.

## Limitations / Open Questions

- Производительность сортировки пока построчная (`iterrows()`); для production нужен incremental или vectorized path.
- Live-safe модель ещё не обучена.
- Нужно отдельно определить разрешённый набор row features, доступных на момент бара.
- Старый unsafe watcher можно запускать только для проверки механики цепочки.

## Next Step

Спроектировать и выполнить live-safe retrain:

1. Зафиксировать разрешённый набор признаков.
2. Убрать future-derived входы из training/test.
3. Обучить checkpoint на том же feature builder, который будет использоваться online.
4. Только после этого сравнивать online и test.

## Related Materials

- `docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`
- `docs/API/telemetry_signal_watcher.py.md`
- `docs/processing/online_causal_preprocessing.py.md`
- `docs/MT/trading_strategy.md`
