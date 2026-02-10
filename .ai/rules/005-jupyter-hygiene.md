При работе с .ipynb:
- Первая ячейка: Markdown file header
- Последняя ячейка: резюме результатов
- Очисти outputs перед коммитом (nbstripout)
- Не помещай в контекст целиком, используй sampling

Экспорт в .py для анализа кода:
jupyter nbconvert --to script notebook.ipynb
