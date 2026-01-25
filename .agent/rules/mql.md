---
trigger: always_on
---

# Правила чтения MQL4 (*.mqh)
- Читай оригинальные *.mqh файлы напрямую без конвертации в UTF8.
- Указывай encoding: ANSI или Windows-1251 для Get-Content/PowerShell.
- Пример: Get-Content -Path "file.mqh" -Encoding Default | ...
- Используй clangd для анализа, не создавай utf8 копии.