# AI Agent Configuration

## Project Context
- Type: Multi-language trading bot system
- Languages: Python, MQL4, Jupyter Notebooks
- Primary Tools: Cursor, Antigravity, Perplexity
- Documentation Language: Russian (with English technical terms)  

## Project Structure
.ai/rules/ # Правила документирования и стиля
.ai/prompts/ # Готовые промпты
docs/ # Документация
├── data_analysis/ # Анализ данных
├── data_preprocessing/ # Описания скриптов
├── architecture.md
├── data-flow.md
└── dataset_description.md


## Agent Instructions

### When creating/modifying code:
1. Read script's file header for context
2. Check `docs/data_preprocessing/*.md` for details
3. After changes, update BOTH file header AND .md file
4. Update `docs/data-flow.md` if input/output changed

### When creating prompts:
1. Start with `docs/architecture.md` for context
2. Use `docs/data-flow.md` to understand dependencies
3. Reference specific script docs from `docs/data_preprocessing/*.md`

## Quick Commands

**`sync docs`** — Обнови документацию для изменённых файлов согласно '.ai/rules/update-docs-on-code-change.md' 
**`doc this`** — Документируй текущий файл согласно `.ai/rules/000-documentation.md`  
**`check docs`** — Проверь актуальность документации

## Data Flow
MT/MQL4/Include/lib_PIC.mqh → Nero.csv
↓
processing/label_main.py → Nero_normalization_stats.csv, Nero_test_labeled.csv, Nero_train_labeled.csv, Nero_val_labeled.csv, Nero_atr_scaler.pkl 
↓
statistics/EDA.ipynb → reports/*, plots/*, EDA_files/*

## Documentation Rules

Детальные правила в `.ai/rules/000-documentation.md`

**File header обязателен**:
- Назначение скрипта
- Входные/выходные данные
- Зависимости
- Дата последнего обновления