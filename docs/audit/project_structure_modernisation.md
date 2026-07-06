## компактный AGENT_BOOTSTRAP.md.
      - стартовый маршрут;
      - 6-8 обязательных правил;
      - карта “вопрос -> источник”;
      - текущий research focus;
      - запрет на чтение тяжёлых файлов без причины.
уже полностью реализован в agents.md
- маршрут поиска через knowledge-rag и проверку первоисточника: AGENTS.md:26               
  - правила экономного чтения: AGENTS.md:56                                                  
  - запрет читать MODULE_INDEX.md целиком без причины: AGENTS.md:59                          
  - указание, что audit и archive не читать без явной просьбы: AGENTS.md:118                 
  - карта основных артефактов проекта: AGENTS.md:79

## knowledge-rag:
 тестовая проверка дала слабый результат на 4 запросах:  MRR@5 = 0.1458, Recall@5 = 0.5.
Это значит, что текущий поиск полезен как кандидатный  список, но его нельзя считать достаточным маршрутизатором.
Цель: Recall@5 >= 0.9, MRR@5 >= 0.8
Измерить качество текущего knowledge-rag. Не на 6 запросах, а хотя бы на 30-50 типовых запросах проекта:
      - модуль
      - отчёт
      - гипотеза
      - термин
      - текущий статус
      - прошлый отказ

## Правило чтения файлов
файлы более 100КБ только через  поиск или точечное чтение
CONTEXT_HANDOFF.md - держать коротким


## машинно-читаемые регистры (json)
вынести тяжёлые индексы в короткие реестры = заменить changelog.md  и MODULE_INDEX.md на json.
Выделить из тяжёлых файлов короткие реестры - навигационные факты в компактную структуру.
    - module_registry.json - реестр модулей;
    - report_registry.json - реестр отчётов;
    - term_glossary.json - глоссарий терминов;
При замене changelog.md на report_registry.json нужно строго соблюдать заполнение всех полей. От отчета к отчету может требоваться разный состав/название полей, поэтому добавим свободные объекты details, metrics, artifacts, notes. Верхний уровень строгий, свободный блок только для данных, не влияющих на маршрутизацию.
Пример:
 {
    "date": "2026-07-02",
    "report_path": "docs/reports/2026-07-02-regression-updn-already-moved-audit.md",
    "title": "Regression Up/Dn Already Moved Audit",
    "verdict": "DIAGNOSTIC_ONLY",
    "topics": ["regression_updn", "entry_open"],
    "summary": "Сигнал от fractal0_price подтверждён, но не переносится на вход next open.",
    "artifacts": [
      "ML/reports/regression_updn_already_moved_audit.json"
    ],
    "details": {
      "spearman_from_fractal_h3": 0.8786,
      "spearman_after_entry_open_h3": -0.0149,
      "already_moved_share_h3": 0.5729
    },
    "notes": [
      "Не использовать pred_log_ratio как market-entry сигнал на следующем open."
    ]
  }





## Граф связей/навигации 
- базовый слой: через report_registry.json + module_registry.json + wiki;
- расширенный слой: через Graphify при необходимости.

Добавить граф связей поверх уже существующих индексов:
файл → модуль → отчёт → тест → wiki-синтез → артефакт.
Это даст быстрый “глубокий охват” без чтения всего текста.

Graphify  (Skill, CLI, MCP) - граф знаний, ссылки между Markdown, AST-связи кода
создаёт graph.html, GRAPH_REPORT.md, graph.json;
MCP даёт query_graph, get_node, get_neighbors, shortest_path и др.
включать только для вопросов такого типа:
      - “что связано с этим отчётом?”
      - “какие модули используют эту идею?”
      - “какие стадии уже закрывали похожую гипотезу?”
      - “что связывает MQL4 producer, Python preprocessing и отчёт?”



## Источник истины

  - Правила работы агента: AGENTS.md.
  - Текущее состояние: CONTEXT_HANDOFF.md.
  - Первичные выводы этапов: docs/reports/*.md.
  - Краткий индекс этапов: CHANGELOG.md или report_registry.json, но не оба как независимые
  источники.
  - Реестр модулей: MODULE_INDEX.md или module_registry.json, но не оба как независимые
  источники.
  - Wiki: синтез и навигация, не первоисточник.


