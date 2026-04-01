---
name: jupyter-processing
description: Use when working with Jupyter notebooks - creating, editing, cleaning outputs, exporting, or executing notebooks
---

# Работа с Jupyter Notebooks (Codex-friendly)

## Когда использовать
- Любые задачи по `*.ipynb`: запуск, очистка output, экспорт в `.py`/`.md`.
- Когда notebook нужно проверить без чтения полного JSON в контекст.

## Project guardrails (SoSimple)
- Не читать notebook целиком как JSON в чат.
- Перед коммитом очищать outputs в исходном `.ipynb`.
- Для анализа кода предпочитать экспорт в `.py`.
- Если notebook читает CSV, применять ограничения из `csv-processing` (сначала 10 строк, затем sampling/chunks).

## Базовый workflow

### 1) Проверить структуру без полного вывода
```bash
jupyter nbconvert --to script statistics/EDA.ipynb --stdout | head -n 80
```

### 2) Выполнить notebook
```bash
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb
```

### 3) Очистить outputs в исходнике
```bash
jupyter nbconvert --clear-output --inplace EDA.ipynb
```

### 4) Экспортировать отчет
```bash
jupyter nbconvert --to markdown --no-input --no-prompt --output EDA_report reports/EDA_executed.ipynb
```

## Создание нового notebook
- Первая ячейка: краткий header (цель, вход, выход, дата).
- В первой код-ячейке: импорты и константы путей через `pathlib.Path`.
- Последняя ячейка: короткое резюме и список артефактов.

Пример минимального header (markdown-ячейка):
```markdown
# EDA: Nero dataset

Файл: statistics/EDA.ipynb
Назначение: Быстрый EDA train-выборки
Вход: DATA/Nero_train_labeled.csv
Выход: statistics/reports/EDA_report.md, statistics/plots/*
Обновлён: 2026-04-01
```

## Частые ошибки
| Ошибка | Как исправить |
|---|---|
| Коммит notebook с output | Очистить `--clear-output --inplace` |
| Пытаться ревьюить большой `.ipynb` как JSON | Сначала `nbconvert --to script` |
| Жестко прошитые абсолютные пути | Использовать `Path` и переменные окружения |
| Загрузка больших CSV целиком в notebook | Использовать `nrows`, `usecols`, `chunksize` |

## Короткий checklist перед завершением
- Notebook выполняется без ошибок (`nbconvert --execute`).
- Outputs очищены в исходном файле.
- Если менялась логика, обновлен связанный `.md` в `docs/` или `statistics/reports/`.
- Нет временных артефактов в git (`.ipynb_checkpoints`, промежуточные dump-файлы).
