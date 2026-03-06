# SoSimple

Торговый бот на базе ML для прогнозирования разворотов тренда (Forex H1).

## Документация
- 🤖 **[AGENTS.md](AGENTS.md)** — руководство для работы с проектом (для ИИ-агентов и разработчиков)
- 📋 **[CHANGELOG.md](CHANGELOG.md)** — история изменений
- 📊 **[DATA_FLOW.md](docs/DATA_FLOW.md)** — поток данных через пайплайн

## Быстрый старт
```bash
# Установка зависимостей
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Обработка данных
python processing/label_main.py --input MT/MQL4/Files/Nero.csv
```

## Статус
🔄 В активной разработке. Готовы: сбор данных, препроцессинг, EDA, ML модели.

> 🤖 AI agents: see [AGENTS.md](AGENTS.md)