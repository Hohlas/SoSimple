# Quick Reference

*For AI agents: быстрый справочник команд и форматов*

***

## Commands

### Preprocessing
```bash
# Label and split dataset
python processing/label_main.py --input MT/MQL4/Files/Nero.csv

# Normalize
python processing/normalize.py --input data/Nero_train_labeled.csv \
  --scaler data/scaler.pkl
```

### Statistics
```bash
# Generate statistic file
python statistics/statistics.py --input data/Nero_train_labeled.csv
# Выполнить ноутбук и сохранить результат в отдельный файл
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb
# Исключает изображения и исходный код, оставляя только текстовые отчеты
jupyter nbconvert --to markdown --no-input --no-prompt --output reports/EDA_report EDA_executed.ipynb
# Очистить выходы в исходном файле
jupyter nbconvert --clear-output --inplace EDA.ipynb
```

***

## File Formats

### Nero.csv (raw)
- **Location:** `MT/MQL4/Files/Nero.csv`
- **Separator:** `;`
- **Encoding:** UTF-8
- **Columns:** time, open, high, low, close, volume, ATR, ...

### Nero_train_labeled.csv (processed)
- **Location:** `data/Nero_train_labeled.csv`
- **Columns:** + target_label (0/1)

***

## File Paths

### Data
- Raw: `MT/MQL4/Files/Nero.csv`
- Processed: `data/Nero_*_labeled.csv`
- Normalized: `data/Nero_*_norm.csv`

### Code
- Preprocessing: `processing/`
- Statistics: `statistics/`
- ML (planned): `ML/`

### Documentation
- Module docs: `docs/data_preprocessing/`, `docs/data_analysis/`
- MQL4 docs: `docs/mql4/`

***

## Critical Rules (Top 3)

### 1. No CSV in context (rule 007)
```python
# ✅ Do this
df = pd.read_csv('file.csv', nrows=100)

# ❌ Don't do this
df = pd.read_csv('file.csv')  # Loads 100MB!
```

### 2. MQL4 encoding (rule 100)
```python
# ✅ Correct
open('lib_PIC.mqh', encoding='utf-16-le')

# ❌ Incorrect
open('lib_PIC.mqh')  # UnicodeDecodeError
```

### 3. File headers first (rule 002)
Always read file header before analyzing code.

***

## Need More?

- All rules: `.ai/RULES_INDEX.md`
- All skills: `.ai/SKILLS_INDEX.md`
