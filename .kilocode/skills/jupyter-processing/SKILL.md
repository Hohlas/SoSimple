---
name: jupyter-processing
description: Use when working with Jupyter notebooks - creating, editing, cleaning outputs, exporting, or executing notebooks
---

# Работа с Jupyter Notebooks

## Overview

Jupyter Notebooks (.ipynb) требуют особого подхода для поддержания чистоты и воспроизводимости:

**Ключевые принципы работы с notebooks:**
- **File Header** — первая ячейка с документацией о файле
- **Clean Outputs** — очистка output'ов перед коммитом (nbstripout)
- **No Full Load** — никогда не загружай весь notebook в контекст целиком
- **Export for Analysis** — конвертация в .py для анализа кода

**Проблемы при неправильной работе:**
- Засорение git истории большими output'ами
- Невоспроизводимые результаты
- Переполнение контекста (token limit)
- Сложности при code review

## When to Use

- Создание новых Jupyter notebooks
- Очистка outputs перед коммитом
- Конвертация notebook в скрипт для анализа
- Команды: "jupyter notebook", "ipynb file", "clean outputs", "export notebook"

Applies to: `**/*.ipynb` файлы

## The Workflow

### Phase 1: Create (Создание нового notebook)

**Шаг 1.1: Создать структуру директорий**
```bash
# Создаём директорию для ноутбуков проекта
mkdir -p statistics/notebooks
mkdir -p analysis/notebooks
```

**Шаг 1.2: Создать первую ячейку с file header**
```markdown
# EDA Analysis

**Файл**: `statistics/EDA.ipynb`  
**Назначение**: Exploratory Data Analysis для Nero.csv  
**Обновлён**: 2026-03-05

## Входные/Выходные данные
- **Вход**: `DATA/Nero_train_labeled.csv`
- **Выход**: 
  - `statistics/reports/EDA_report.md`
  - `statistics/plots/*.png`

## Зависимости
- pandas>=2.0
- matplotlib>=3.7
- seaborn>=0.12

## Использование
```bash
jupyter nbconvert --execute --to notebook --output EDA_executed EDA.ipynb
```

## Примечания
- Использовать sampling для больших CSV
- Сохранять графики в `plots/`
```

**Шаг 1.3: Настроить kernel и импорты**
```python
# Вторая ячейка — импорты
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Настройки визуализации
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Константы проекта
DATA_DIR = Path('../DATA')
OUTPUT_DIR = Path('./reports')
OUTPUT_DIR.mkdir(exist_ok=True)
```

**Шаг 1.4: Добавить последнюю ячейку с результатами**
```markdown
## Резюме анализа

**Выполнено**:
- [x] Загружено и проанализировано N записей
- [x] Построено X графиков
- [x] Сгенерирован отчёт

**Ключевые находки**:
- Найдено: [краткое описание]
- Рекомендации: [действия]

**Сохранённые артефакты**:
- `reports/EDA_report.md`
- `plots/distribution.png`

**Следующие шаги**:
- [ ] Дополнительный анализ...
```

### Phase 2: Clean (Очистка output'ов)

**Шаг 2.1: Установить nbstripout**
```bash
# Установка nbstripout
pip install nbstripout

# Инициализация для репозитория
nbstripout --install

# Проверка статуса
nbstripout --status
```

**Шаг 2.2: Очистить outputs через nbstripout**
```bash
# Очистка конкретного файла
nbstripout EDA.ipynb

# Очистка всех notebooks
find . -name "*.ipynb" -exec nbstripout {} \;
```

**Шаг 2.3: Очистка через nbconvert (альтернатива)**
```bash
# Очистка outputs в исходном файле (inplace)
jupyter nbconvert --clear-output --inplace EDA.ipynb
```

**Шаг 2.4: Очистка через Jupyter программно**
```python
# В Jupyter: Cell -> All Output -> Clear
# Или программно:
from nbformat import read, write

# Читаем notebook
with open('EDA.ipynb', 'r', encoding='utf-8') as f:
    nb = read(f, as_version=4)

# Очищаем все output'ы
for cell in nb.cells:
    if cell.cell_type == 'code':
        cell.outputs = []
        cell.execution_count = None

# Сохраняем
with open('EDA.ipynb', 'w', encoding='utf-8') as f:
    write(nb, f)
```

**Шаг 2.5: Настроить .gitattributes**
```bash
# Добавить в .gitattributes
echo "*.ipynb filter=nbstripout" >> .gitattributes
echo "*.ipynb diff=ipynb" >> .gitattributes
```

### Phase 3: Export (Конвертация для анализа)

**Шаг 3.1: Конвертация в Python скрипт**
```bash
# Базовая конвертация
jupyter nbconvert --to script statistics/EDA.ipynb

# Результат: statistics/EDA.py
# Теперь можно анализировать код обычными инструментами
```

**Шаг 3.2: Конвертация с шаблоном**
```bash
# Конвертация с определённым шаблоном
jupyter nbconvert --to script \
    --template full \
    statistics/EDA.ipynb
```

**Шаг 3.3: Конвертация в Markdown**
```bash
# Для документации
jupyter nbconvert --to markdown statistics/EDA.ipynb

# С сохранением изображений
jupyter nbconvert --to markdown \
    --extract-output-images \
    statistics/EDA.ipynb
```

**Шаг 3.4: Конвертация в HTML**
```bash
# Для отчётов
jupyter nbconvert --to html statistics/EDA.ipynb

# С шаблоном
jupyter nbconvert --to html \
    --template classic \
    statistics/EDA.ipynb
```

### Phase 4: Execute (Выполнение notebook)

**Шаг 4.0: Подготовка окружения**
```bash
# Переход в директорию проекта
cd ~/git/SoSimple

# Активация виртуального окружения
source /home/hohla/git/SoSimple/.venv/bin/activate

# Установка зависимостей (при необходимости)
# pip install -r requirements.txt

# Переход в директорию со статистикой
cd ~/git/SoSimple/statistics

# Установка переменной окружения для входных данных
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
```

**Шаг 4.1: Выполнение через nbconvert**
```bash
# Выполнить и сохранить результат в ./reports/
jupyter nbconvert --execute \
    --to notebook \
    --output EDA_executed \
    --output-dir ./reports \
    EDA.ipynb

# С таймаутом (для долгих операций)
jupyter nbconvert --execute \
    --to notebook \
    --ExecutePreprocessor.timeout=600 \
    --output EDA_executed \
    --output-dir ./reports \
    EDA.ipynb
```

**Шаг 4.2: Очистка output'ов после работы**
```bash
# Очистка outputs в исходном notebook (inplace)
jupyter nbconvert --clear-output --inplace EDA.ipynb
```

**Шаг 4.3: Конвертация в Markdown для отчёта**
```bash
# Конвертация выполненного notebook в Markdown (без input ячеек)
jupyter nbconvert --to markdown \
    --no-input \
    --no-prompt \
    --output EDA_report \
    reports/EDA_executed.ipynb
```

**Шаг 4.4: Выполнение с параметрами (papermill)**
```bash
# Используем papermill для параметризации
pip install papermill

# Запуск с параметрами
papermill EDA.ipynb \
    reports/EDA_output.ipynb \
    -p input_file '../DATA/Nero_train_labeled.csv' \
    -p sample_size 1000
```

**Шаг 4.5: Выполнение из Python**
```python
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import read, write

# Читаем notebook
with open('EDA.ipynb', 'r', encoding='utf-8') as f:
    nb = read(f, as_version=4)

# Создаём executor
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

# Выполняем
ep.preprocess(nb, {'metadata': {'path': './'}})

# Сохраняем
with open('reports/EDA_executed.ipynb', 'w', encoding='utf-8') as f:
    write(nb, f)
```

**Шаг 4.6: Проверка перед коммитом**
```bash
# Выполнить и проверить на ошибки
jupyter nbconvert --execute \
    --to notebook \
    --stdout \
    EDA.ipynb > /dev/null

# Если ошибок нет — можно коммитить (после nbstripout)
```

## Common Operations

### ✅ Прочитать структуру notebook (не загружая в контекст)
```bash
# Просмотр структуры
jupyter nbconvert --to notebook \
    --stdout EDA.ipynb | \
    python -m json.tool | \
    head -100

# Или используя nbformat
cat << 'EOF' | python3
import json
with open('EDA.ipynb', 'r') as f:
    nb = json.load(f)
print(f"Cells: {len(nb['cells'])}")
print(f"Cell types: {[c['cell_type'] for c in nb['cells']]}")
for i, cell in enumerate(nb['cells'][:5]):
    preview = cell['source'][:100] if cell['source'] else '[empty]'
    print(f"  Cell {i}: {cell['cell_type']} - {preview}...")
EOF
```

### ✅ Извлечь только код
```bash
# Извлечь Python код
jupyter nbconvert --to script EDA.ipynb --stdout | head -50
```

### ✅ Проверить метаданные
```python
import json

with open('EDA.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"nbformat: {nb['nbformat']}.{nb['nbformat_minor']}")
print(f"Kernel: {nb['metadata']['kernelspec']['display_name']}")
print(f"Language: {nb['metadata']['kernelspec']['language']}")
print(f"Total cells: {len(nb['cells'])}")

# Подсчёт по типам
code_cells = sum(1 for c in nb['cells'] if c['cell_type'] == 'code')
md_cells = sum(1 for c in nb['cells'] if c['cell_type'] == 'markdown')
print(f"Code cells: {code_cells}, Markdown cells: {md_cells}")
```

### ✅ Слияние notebooks
```python
from nbformat import read, write, v4

# Читаем несколько notebooks
nb1 = read(open('part1.ipynb'), as_version=4)
nb2 = read(open('part2.ipynb'), as_version=4)

# Создаём новый
merged = v4.new_notebook()
merged.cells = nb1.cells + nb2.cells

# Сохраняем
write(merged, open('merged.ipynb', 'w'))
```

### ✅ Сравнение notebooks
```bash
# Используем nbdiff
pip install nbdime

# Сравнение
nbdiff notebook_v1.ipynb notebook_v2.ipynb

# Веб-интерфейс
nbdiff-web notebook_v1.ipynb notebook_v2.ipynb
```

### ✅ Работа с большими notebooks
```python
# Читаем только структуру, без execution_count и outputs
import json

def read_nb_structure(filepath):
    """Читает только структуру notebook без данных."""
    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    structure = {
        'metadata': nb.get('metadata', {}),
        'cells_count': len(nb.get('cells', [])),
        'cells': []
    }
    
    for i, cell in enumerate(nb.get('cells', [])):
        cell_info = {
            'index': i,
            'type': cell['cell_type'],
            'source_length': len(cell.get('source', '')),
            'output_count': len(cell.get('outputs', [])) if cell['cell_type'] == 'code' else 0
        }
        structure['cells'].append(cell_info)
    
    return structure

# Использование
info = read_nb_structure('EDA.ipynb')
print(f"Cells: {info['cells_count']}")
```

## Quick Start (SoSimple Project)

### Полный рабочий цикл для EDA.ipynb

```bash
# 1. Подготовка окружения
cd ~/git/SoSimple
source /home/hohla/git/SoSimple/.venv/bin/activate
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"

# 2. Выполнение notebook
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb

# 3. Очистка output'ов в исходном файле
jupyter nbconvert --clear-output --inplace EDA.ipynb

# 4. Конвертация в Markdown для отчёта
jupyter nbconvert --to markdown --no-input --no-prompt --output EDA_report reports/EDA_executed.ipynb
```

## Quick Reference

| Category | Values |
|----------|--------|
| Tags | jupyter, notebook, ipynb, data-analysis |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Коммитить notebook с output'ами | Использовать nbstripout перед коммитом |
| Загружать .ipynb целиком в контекст | Конвертировать в .py или извлечь код |
| Жёстко кодировать пути | Использовать `Path` и переменные |
| Использовать абсолютные пути | Использовать относительные пути от notebook |
| Запускать `print(df)` для больших DataFrame | Использовать `df.head()`, `df.info()` |
| Сохранять секреты в notebook | Использовать переменные окружения |
| Игнорировать kernel в метаданных | Указывать конкретный kernel |
| Коммитить checkpoint'ы | Добавить `.ipynb_checkpoints/` в .gitignore |
| Делать notebook слишком большим (>100 ячеек) | Разбивать на логические части |
| Не добавлять file header | Всегда первая ячейка — документация |

## Integration with Other Skills

- **csv-processing** — использовать sampling при загрузке CSV в notebook
- **mql4-processing** — для анализа MQL4 данных в notebook
- **create-eda-report** — генерация отчётов из notebook
- **verification-before-completion** — проверка notebook перед финализацией
- **add-new-module** — документирование notebook как модуля проекта

## Project-Specific Notes

### Расположение notebooks в проекте

```
SoSimple/
├── statistics/
│   ├── EDA.ipynb              # Основной EDA
│   ├── correlation_analysis.ipynb
│   └── notebooks/             # Дополнительные анализы
├── ML/
│   └── experiments/
│       └── model_comparison.ipynb
└── docs/
    └── data_analysis/
        └── EDA.ipynb.md       # Документация к notebook
```

### Стандартные импорты для проекта

```python
# Всегда включать в начало notebook
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Пути проекта
PROJECT_ROOT = Path('.').resolve().parent  # Для notebooks в поддиректориях
DATA_DIR = PROJECT_ROOT / 'DATA'
MT_DIR = PROJECT_ROOT / 'MT' / 'MQL4' / 'Files'
```

### Обработка Nero.csv в notebook

```python
# Правильный способ загрузки (sampling)
df = pd.read_csv(
    DATA_DIR / 'Nero_train_labeled.csv',
    nrows=10000,  # Ограничиваем для EDA
    sep=';'
)

# Для полной обработки — экспортировать в .py
# и запускать как скрипт
```
