---
priority: CONTEXT
trigger: Работа с .ipynb файлами
affects: statistics/*.ipynb, docs/data_analysis/
description: Правила чистоты Jupyter notebooks (clear outputs, no hardcoded paths)
tags: jupyter, notebooks, reproducibility
---

При работе с .ipynb:
- Первая ячейка: Markdown file header
- Последняя ячейка: резюме результатов
- Очисти outputs перед коммитом (nbstripout)
- Не помещай в контекст целиком, используй sampling

Экспорт в .py для анализа кода:
jupyter nbconvert --to script notebook.ipynb
