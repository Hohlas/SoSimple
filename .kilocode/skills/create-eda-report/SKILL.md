---
name: create-eda-report
description: Use when running automated exploratory data analysis with statistics.py and EDA.ipynb
---

# Создание EDA отчёта

## Overview

Запуск автоматизированного статистического анализа и генерация EDA-отчётов с использованием statistics.py и EDA.ipynb.

## When to Use

- Необходимость проанализировать новый датасет
- Проверка качества маркировки данных
- Команды: "analyze", "analyze [file]", "run eda"

Applies to: `Nero.csv`

## The Workflow

**Команда**: `run eda` или `analyze`
**Назначение**: Запустить полный цикл статистического анализа и EDA для датасета Nero.

Шаги:
0. Спросить о нобходимости проведения EDA и подтвердить, что пользователь хочет запустить анализ.
1. Запустить сбор статистики:
   `cd statistics && python statistics.py`
   * Генерирует: `statistics_summary.json`, `class_balance_report.csv`, `feature_distributions.csv`, `nero_sample_stratified.csv`, `class_statistics.json`

2. Сгенерировать EDA отчёт из ноутбука:
   `cd statistics && jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb`
   * Генерирует: `reports/EDA_executed.ipynb` и графики в `plots/`

Выходные данные:
- JSON/CSV отчеты в `statistics/`
- Выполненный ноутбук в `statistics/reports/`
- Графики в `statistics/plots/`

## Quick Reference

| Category | Values |
|----------|--------|
| Tags | analysis, eda, data |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Running EDA on full large dataset | Use sampling for initial exploration |
| Forgetting to check class balance | Review class_balance_report.csv |
| Not saving plots to plots/ directory | Configure output paths correctly |
