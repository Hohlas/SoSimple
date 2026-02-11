# SoSimple

Торговый алгоритм на базе машинного обучения для анализа рыночных паттернов и прогнозирования разворотов тренда (Forex, H1).

## Обзор проекта

Проект **SoSimple** направлен на создание автоматической торговой системы на базе нейронных сетей для выявления статистически значимых паттернов в поведении фракталов.

## Основные возможности

- **Фрактальный анализ**: Обработка последовательностей из 100 фракталов для получения глубокого контекста рынка
- **ML Pipeline**: Полный цикл предобработки, включая нормализацию (RobustScaler), маркировку и разделение на выборки с учетом временной причинности
- **Статистический контроль**: Тщательный EDA и статистические тесты (t-test, Mann-Whitney) для валидации признаков
- **Интеграция с MT4**: Сбор данных напрямую из терминала MetaTrader 4

## Быстрый старт

### Документация
- 📖 **[MODULE_INDEX.md](MODULE_INDEX.md)** — индекс всех модулей проекта
- 🔄 **[DATA_FLOW.md](DATA_FLOW.md)** — визуальная карта потока данных
- ⚡ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — шпаргалка команд и путей
- 📋 **[CHANGELOG.md](CHANGELOG.md)** — история major изменений

### Для ИИ-агентов
- 🤖 **[AGENTS.md](AGENTS.md)** — инструкции для работы с проектом
- 📜 **[.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)** — каталог правил
- ⚙️ **[.ai/SKILLS_INDEX.md](.ai/SKILLS_INDEX.md)** — автоматизированные команды

### Детальная документация
- **[docs/dataset_description.md](docs/dataset_description.md)** — структура датасета Nero.csv
- **[docs/data_preprocessing/](docs/data_preprocessing/)** — детали скриптов preprocessing
- **[docs/data_analysis/](docs/data_analysis/)** — статистический анализ и EDA

## Конвейер данных

```mermaid
graph LR
    MT4[MetaTrader 4] -->|lib_PIC.mqh| CSV[Nero.csv]
    CSV -->|normalize.py| Norm[Nero_normalized.csv]
    Norm -->|label_main.py| Samples[Train/Val/Test]
    Samples -->|statistics/| EDA[EDA & Stats]
    Samples -->|ML/| Training[Model Training]
    Training -->|Inference| Signals[Trading Signals]

[Подробная диаграмма:] (DATA_FLOW.md)

## Структура проекта
- [MT/](MT/) — Код на MQL4 для MetaTrader 4
- [processing/](processing/) — Скрипты предобработки (нормализация, маркировка, разделение)
- [statistics/](statistics/) — Статистический анализ и EDA
- [ML/](ML/) — Обучение и архитектуры моделей (в разработке)
- [docs/](docs/) — Детальная документация
- [.ai/](.ai/) — Правила и skills для ИИ-агентов

## Технологический стек
- Языки: Python 3.11+, MQL4
- Библиотеки: Pandas, NumPy, Scikit-learn, Scipy, Matplotlib, Seaborn
- Инфраструктура: PyTorch (планируется), Docker (планируется)

## Статус разработки

Проект находится на стадии активной разработки (🔄). Основные компоненты сбора и предобработки данных готовы, ведется работа над архитектурами моделей машинного обучения.