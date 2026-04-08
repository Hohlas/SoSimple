# tests/

Unit и smoke-тесты для ключевых модулей SoSimple.

## Запуск

```bash
# Все тесты
./.venv/bin/python -m pytest tests/ -q

# Один файл
./.venv/bin/python -m pytest tests/test_label_updn.py -q
```

## Файлы

| Файл | Тестирует | Охват |
|------|-----------|-------|
| [test_label_updn.py](test_label_updn.py) | `processing/label_signals.py` | `parse_fractal` (11/18 полей), `label_updn` (last-seen логика) |
| [test_inverse_piecewise.py](test_inverse_piecewise.py) | `processing/normalize.py`, `statistics/signal_tracer.py` | round-trip `piecewise_linear_log ↔ inverse` (линейная / log / beyond-cap зоны) |
| [test_signal_research.py](test_signal_research.py) | `API/signal_research.py` | ATR14, excursions, barrier outcomes, ratio_bin, discovery/holdout split |
| [test_signal_path_atlas.py](test_signal_path_atlas.py) | `API/signal_path_atlas.py` | calendar split, path tensor, slices, archetypes, holdout replication, CLI smoke |
| [test_signal_quality_research.py](test_signal_quality_research.py) | `API/signal_quality_research.py` | filter features, variance check, univariate maps, shallow tree, score/holdout |
| [test_exit_policy_research.py](test_exit_policy_research.py) | `API/exit_policy_research.py` | exit triggers, split boundary, same-bar reversal, ranking, frozen-policy guard |

## Зависимости

- `pytest>=8.0`
- `numpy>=1.24`
- `pandas>=2.0`
- `scikit-learn` (для `test_signal_quality_research.py`)

## Примечания

- Тесты используют только синтетические fixtures — реальные данные не требуются.
- Для запуска из корня репозитория: `sys.path.insert` в каждом файле добавляет нужный каталог.
- Реальные CLI-прогоны research-модулей дополнительно верифицируются вручную перед stage close.
