# AI Agent Configuration

## Project Context
- **Type**: Trading bot system with ML predictions
- **Languages**: Python 3.11+, MQL4, Jupyter Notebooks
- **Tools**: Cursor, Antigravity, Perplexity
- **Documentation**: Русский (код на английском) 

## Pipeline Overview

MT4 (lib_PIC.mqh) → Nero.csv
↓
processing/ → train/val/test + scalers
↓
statistics/ → EDA, reports
↓
ML/ → models (в разработке)


**Детали**: `docs/architecture.md`

## Key Directories

- `MT/MQL4/Include/lib_PIC.mqh` — структурирование рыночных котировок
- `processing/` — нормализация, маркировка, разделение
- `statistics/` — статистический анализ и EDA
- `ML/` — обучение моделей
- `docs/` — документация проекта


## Quick Commands

- **`sync docs`** — Синхронизируй документацию с изменённым кодом
- **`doc this`** — Задокументируй текущий открытый файл
- **`check docs`** — Проверь актуальность всей документации

## Agent Instructions

### При изменении кода:
1. Прочитай file header скрипта
2. Найди соответствующий `.md` в `docs/data_preprocessing/`
3. Обнови **file header** (дата Last Updated) **И** `.md` файл
4. Если изменились входы/выходы → обнови `docs/architecture.md` (секция Pipeline)

### При составлении промптов:
1. Общая картина → `docs/architecture.md`
2. Детали данных → `docs/dataset_description.md`
3. Детали скриптов → `docs/data_preprocessing/[script].md`



### Important Rules

**File headers**: Обязательны для всех `.py`, `.mq4`, `.ipynb`  
**Большие файлы**: НЕ открывай `*.csv` целиком — используй sampling  
**Кодировка MQL4**: UTF-16LE (не UTF-8)

**Детальные правила**: `.ai/rules/`