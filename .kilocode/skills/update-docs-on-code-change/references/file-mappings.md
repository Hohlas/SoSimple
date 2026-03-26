# File Mappings: Код → Документация

Справочник соответствий между файлами кода и их документацией для проекта SoSimple.

## Маппинги по директориям

### processing/

| Файл кода | Документация | Раздел DATA_FLOW.md |
|-----------|--------------|---------------------|
| processing/label_main.py | docs/processing/label_main.py.md | Pipeline → Label |
| processing/label_signals.py | docs/processing/label_signals.py.md | Pipeline → Label |
| processing/normalize.py | docs/processing/normalize.py.md | Pipeline → Norm |

### statistics/

| Файл кода | Документация | Раздел DATA_FLOW.md |
|-----------|--------------|---------------------|
| statistics/statistics.py | docs/statistics/statistics.py.md | — |
| statistics/EDA.ipynb | docs/statistics/EDA.ipynb.md | — |
| statistics/signal_tracer.py | docs/statistics/signal_tracer.py.md | — |

### ML/

| Файл кода | Документация | Раздел DATA_FLOW.md |
|-----------|--------------|---------------------|
| ML/train.py | docs/ML/train.py.md | — |
| ML/optimize.py | docs/ML/optimize.py.md | — |
| ML/data_loader.py | docs/ML/data_loader.py.md | — |
| ML/compare_architectures.py | docs/ML/compare_architectures.py.md | — |
| ML/baseline/baseline_experiments.py | docs/ML/baseline_experiments.py.md | — |
| ML/models/*.py | docs/ML/neural_networks.md | — |

### MT/MQL4/Include/

| Файл кода | Документация | Раздел DATA_FLOW.md |
|-----------|--------------|---------------------|
| MT/MQL4/Include/lib_PIC.mqh | docs/MT/lib_PIC.mqh.md | Pipeline → MT4 Export |
| MT/MQL4/Include/*.mqh | docs/MT/[имя].mqh.md | — |

## Шаблоны путей

### Python скрипты
```
processing/[script].py → docs/processing/[script].md
statistics/[script].py → docs/statistics/[script].md
ML/[script].py → docs/ML/[script].md
```

### MQL4 заголовки
```
MT/MQL4/Include/[lib].mqh → docs/MT/[lib].mqh.md
```

### Jupyter notebooks
```
statistics/[name].ipynb → docs/statistics/[name].ipynb.md
```

## Правила обработки

1. Если документация не существует → предложить создать
2. Если скрипт участвует в pipeline → обновить DATA_FLOW.md
3. Если изменения значительные → обновить CHANGELOG.md
