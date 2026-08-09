# Аудит: docs/reports/2026-08-01-mt5-saved-batch-fill-rate-probe.md

> Дата аудита: 2026-08-08
> Аудитор: Qoder
> Метод: фактическая верификация по артефактам, коду, тестам, методологии и перекрёстным ссылкам

---

## Резюме

Числовые утверждения отчёта полностью подтверждены артефактами — все 12 JSON-значений, все 8 CSV-метрик и все 5 Spearman-корреляций совпадают. Все тесты проходят (24 passed). Все перекрёстные ссылки валидны. Однако отчёт имеет структурные пробелы относительно методологии (отсутствуют Verification section, artifact hashes, side-specific breakdown, yearly decomposition) и содержит некорректный текст (опечатки, смешение языков, мусорные символы).

---

## Замечания

### 1. Spearman-корреляции и residual вычислены вне кода

- **Важность**: важно
- **Место**: строки 85-96 отчёта; `ML/baseline/mt5_execution_diagnostics.py`
- **Суть**: Отчёт заявляет Spearman rank correlations (5 пар) и residual (`active_signal_rows - ORDER_PLACED - OPEN_FAILED` = 1874, 12.53%) как результаты анализа. Однако в `ML/baseline/mt5_execution_diagnostics.py` нет ни `scipy`, ни `spearmanr`, ни кода для вычисления residual. Функция `build_fill_rate_diagnostics` агрегирует суммы (`total_active_signal_rows`, `total_open_failed`), но не выполняет вычитание и не считает корреляции. Эти вычисления были сделаны внешним способом (вручную или отдельным скриптом), но не задокументированы и не воспроизводимы из кода.
- **Доказательство**: `grep -n "spearman\|scipy\|residual" ML/baseline/mt5_execution_diagnostics.py` — нет результатов. Функция `build_fill_rate_diagnostics` (строка ~785) возвращает агрегаты, но не корреляции.
- **Почему важно**: Методология `16-reporting-audit.md` требует воспроизводимость. Читатель не может повторить вычисление Spearman или residual, выполнив только команды из отчёта. Команда `--phase fill-rate` генерирует JSON без корреляций и CSV без residual-колонки.
- **Рекомендация**: Либо добавить вычисление Spearman и residual в `build_fill_rate_diagnostics` (с тестами), либо явно указать в отчёте, что корреляции вычислены ad-hoc (например, pandas `.corr(method='spearman')` в интерактивной сессии), и привести команду/скрипт.

---

### 2. Отсутствует раздел Verification

- **Важность**: важно
- **Место**: отчёт целиком; методология `16-reporting-audit.md` строка 24
- **Суть**: Методология 16 требует выделенный раздел `Verification` с командой и результатом тестов. Отчёт содержит команду `pytest` (строка 57), но не имеет отдельного раздела с выводом. Сравнение с предыдущим отчётом (`2026-08-01-mt5-execution-hygiene-postbatch.md`): тот имеет раздел `Verification` с командой и результатом `53 passed in 0.47s`.
- **Доказательство**: `docs/methodology/16-reporting-audit.md` строка 24: "Verification: команды и ожидаемые результаты". В отчёте нет заголовка `## Verification`.
- **Почему важно**: Нарушение структуры отчёта, затрудняет верификацию следующим агентом.
- **Рекомендация**: Добавить раздел `## Verification` с командой и результатом: `24 passed in 0.37s`.

---

### 3. Отсутствуют хеши артефактов

- **Важность**: важно
- **Место**: отчёт, раздел `Structured Artifact Cross-Check`; методология `16-reporting-audit.md` строка 31
- **Суть**: Методология 16 требует "hashes" для артефактов. Отчёт не содержит SHA256-хеши для `fill_rate_diagnostics.json` и `fill_rate_candidates.csv`. Предыдущий отчёт (`2026-08-01-mt5-execution-hygiene-postbatch.md`) содержит раздел `Artifact Hashes` с 10 хешами.
- **Доказательство**: `docs/methodology/16-reporting-audit.md` строка 31: "Указать команды, версии, paths, hashes". В отчёте нет раздела с хешами.
- **Почему важно**: Без хешей невозможна верификация неизменности артефактов.
- **Рекомендация**: Добавить раздел `## Artifact Hashes` с хешами обоих файлов. Фактические хеши:
  - `fill_rate_diagnostics.json`: `f97ba0d5662f1ab01fffea38cc3b460bf7b9fcba5d7121b1945a8492a24cd40e`
  - `fill_rate_candidates.csv`: `7583bd611dc613647ff5ce26f6eb50e9086cdd3e6ebaf795b737417553a5c59f`

---

### 4. Нет BUY/SELL side-specific breakdown

- **Важность**: важно
- **Место**: раздел `Results`; методология `11-robustness.md` строка 51
- **Суть**: Методология 11 требует: "Side-specific failure не скрывается balance metric." Отчёт заявляет применение `11-robustness.md` (строка 37), но не содержит никакого разделения по сторонам (BUY vs SELL). CSV `fill_rate_candidates.csv` содержит колонки `buy_signal_rows` и `sell_signal_rows`, но в отчёте они не использованы.
- **Доказательство**: `docs/methodology/11-robustness.md` строка 51. `fill_rate_candidates.csv` содержит колонки `buy_signal_rows`, `sell_signal_rows` (подтверждено чтением файла). Отчёт не содержит таблиц или чисел с разделением по BUY/SELL.
- **Почему важно**: Без side-specific анализа невозможно исключить, что низкий fill rate — артефакт одной стороны (например, SELL в bull market). Это может исказить вывод о position-policy dominance.
- **Рекомендация**: Добавить таблицу side-specific fill rate: для BUY и SELL отдельно — active_signal_rows, trades, fill_rate, position_or_pending_order_exists %. Если данные недоступны из events.csv по сторонам, зафиксировать это в Limitations.

---

### 5. Отсутствует continuation_budget

- **Важность**: улучшение
- **Место**: раздел `research-first disclosure`, строки 13-22; методология `00-research-management.md` строки 59-60
- **Суть**: Методология 00 требует поле `continuation_budget` — сколько новых probe-партий разрешено до пересмотра ветки. Research-first disclosure содержит 7 из 8 обязательных полей, но не включает `continuation_budget`.
- **Доказательство**: `docs/methodology/00-research-management.md` строки 59-60: "continuation_budget: сколько новых probe-партий разрешено до пересмотра ветки". Поле отсутствует в строках 13-22 отчёта.
- **Почему важно**: Следующий агент не знает лимит диагностических итераций.
- **Рекомендация**: Добавить строку: `continuation_budget: 0 новых probe-партий; текущая диагностика — последняя перед пересмотром ветки` (или иное значение).

---

### 6. Отсутствует yearly decomposition

- **Важность**: улучшение
- **Место**: раздел `Results`; методология `A5-post-mortem-diagnostics.md` строка 78
- **Суть**: A5 строка 78: "Обязательно повторить декомпозицию по годам." Отчёт не содержит разложения ни по годам, ни по периодам. Per-candidate данные в `fill_rate_candidates.csv` не включают `pf_by_year` или `effective_profit_years`.
- **Доказательство**: `docs/methodology/A5-post-mortem-diagnostics.md` строка 78. Отчёт не содержит yearly breakdown.
- **Почему важно**: Без yearly decomposition невозможно оценить, устойчив ли вывод о position-policy dominance на всех периодах или только на отдельных годах.
- **Рекомендация**: Если данные доступны в per-run `metrics.json` — добавить yearly fill-rate таблицу. Если нет — зафиксировать в Limitations как gap для следующего probe.

---

### 7. Отсутствует explicit Multiple Testing Context section

- **Важность**: улучшение
- **Место**: структура отчёта; методология `16-reporting-audit.md` строка 22
- **Суть**: Методология 16 требует отдельный раздел `Multiple Testing Context`. Данные есть в research-first disclosure (строки 18-19: `current_search_budget`, `cumulative_search_budget`), но нет выделенного раздела.
- **Доказательство**: `docs/methodology/16-reporting-audit.md` строка 22 перечисляет "Multiple Testing Context" как обязательный отдельный раздел.
- **Почему важно**: Усложняет быструю проверку бюджета тестирования следующим агентом.
- **Рекомендация**: Вынести `current_search_budget` и `cumulative_search_budget` в отдельный раздел `## Multiple Testing Context`.

---

### 8. Некорректный текст: опечатки и мусорные символы

- **Важность**: важно
- **Место**: строки 112, 120, 122, 140, 143
- **Суть**: Несколько строк содержат смешение русского и английского, опечатки и мусор:
  - Строка 112: "определён однимёнтий-позитион-полиси" — транслитерация-мусор вместо "single-position policy"
  - Строка 120: "ОРДЕР_ПЛЭЙСД, ОПЕН_ФЭЙЛД. ОПДЭР_ЭКСПАЙРД, ОПНД или КЛОЗЭ" — транслитерация русских букв вместо имён событий
  - Строка 122: "дублирующие сигналы одинакового времени (several active signals per bar)" — смешение языков
  - Строка 140: "Выбрать следующую диагностик:" — обрезанное слово ("диагностику"?)
  - Строка 143: "провзод neighаbie кандидат-сигнал linkage + по-сигнальная exit quality аудит из событияй .csv" — мусор ("провзод", "neighаbie", "событий .csv")
- **Доказательство**: Чтение строк 112, 120, 122, 140, 143 отчёта.
- **Почему важно**: Затрудняет понимание, снижает качество документа. Строки 120 и 143 практически нечитаемы.
- **Рекомендация**: Переписать проблемные строки. Примеры исправлений:
  - Строка 112: "определён single-position policy советника"
  - Строка 120: "ORDER_PLACED, OPEN_FAILED, ORDER_EXPIRED, OPEN или CLOSE"
  - Строка 140: "Выбрать следующую диагностику:"
  - Строка 143: "row-level candidate-signal linkage + по-сигнальный exit quality аудит из events.csv"

---

### 9. "5 FAIL" label не трассируется к артефакту

- **Важность**: вопрос
- **Место**: строка 80
- **Суть**: Отчёт заявляет `fill_rate_by_status.diagnostic_only.count: 21 (16 DIAGNOSTIC_ONLY + 5 FAIL)`. Число 21 подтверждено (`n_diagnostic_only=16`, вычитание `32 - 11 = 21`). Однако label "5 FAIL" не присутствует ни в одном артефакте — это вывод по вычитанию (32 - 11 eligible - 16 diagnostic_only = 5). Ни `batch_summary.json`, ни `fill_rate_diagnostics.json` не содержат поля `status=FAIL` для этих 5 кандидатов.
- **Доказательство**: `batch_summary.json` содержит `table` (32 строки) и `winners_ranked` (11 строк), но не имеет поля `status` с значением `FAIL`. `fill_rate_diagnostics.json` содержит `n_diagnostic_only=16`, но не `n_fail=5`.
- **Почему важно**: Читатель может интерпретировать "FAIL" как статус из артефакта, тогда как это вычисленное значение.
- **Рекомендация**: Уточнить формулировку: "21 = 32 - 11 eligible; из них 16 имеют статус DIAGNOSTIC_ONLY, 5 — не прошли gates (вычислено как 21 - 16)".

---

### 10. Отсутствует explicit holdout non-selection confirmation

- **Важность**: улучшение
- **Место**: раздел `Split Disclosure`, строка 129
- **Суть**: Split Disclosure говорит "`locked_test` was not opened", но не подтверждает явно, что holdout не использовался для selection. Методология 16 строка 93 требует явное подтверждение.
- **Доказательство**: `docs/methodology/16-reporting-audit.md` строка 93: "Явное подтверждение, что holdout/locked_test не использовался для selection, threshold, feature, entry, exit, stop, spread, cost, или PnL convention."
- **Почему важно**: Формальное требование методологии.
- **Рекомендация**: Расширить Split Disclosure: "locked_test was not opened; holdout was not used for any selection, threshold, or convention decision."

---

## Подтверждённые факты (без замечаний)

### Числовые утверждения — все 25 пунктов верифицированы

| Утверждение | Источник | Статус |
|---|---|---|
| candidate_count: 32 | `fill_rate_diagnostics.json` | PASS |
| verdict: BATCH_NO_WINNER | `fill_rate_diagnostics.json` | PASS |
| n_eligible: 11, n_diagnostic_only: 16 | `fill_rate_diagnostics.json` | PASS |
| total_active_signal_rows: 28808 | `fill_rate_diagnostics.json` | PASS |
| total_trades: 2508 | `fill_rate_diagnostics.json` | PASS |
| total_open_failed: 22767 | `fill_rate_diagnostics.json` | PASS |
| total_order_expired: 67 | `fill_rate_diagnostics.json` | PASS |
| eligible_top.count: 11 | `fill_rate_diagnostics.json` | PASS |
| eligible_top.median: 0.0943 | `fill_rate_diagnostics.json` (0.09430...) | PASS |
| low_fill_rate_count_lt_0_20: 11 | `fill_rate_diagnostics.json` | PASS |
| diagnostic_only.count: 21 | `fill_rate_diagnostics.json` | PASS |
| CSV: 32 строки, `;`-разделитель | `fill_rate_candidates.csv` | PASS |
| 11 eligible, все fill_rate < 0.20 | `fill_rate_candidates.csv` (max=0.1326) | PASS |
| position_or_pending_order_exists = 99.19% | 11522/11616 из CSV | PASS |
| Residual = 1874 (12.53%) | 1874/14954 из CSV | PASS |
| pending_order_not_found = 94 (0.81%) | 94/11616 из CSV | PASS |
| ORDER_EXPIRED = 31 | CSV | PASS |
| Spearman fill_rate <-> trades_count: 0.2275 | Независимое вычисление из CSV | PASS |
| Spearman fill_rate <-> profit_factor: -0.4575 | Независимое вычисление из CSV | PASS |
| Spearman fill_rate <-> open_failed_count: -0.6364 | Независимое вычисление из CSV | PASS |
| Spearman trades_count <-> open_failed_count: 0.5694 | Независимое вычисление из CSV | PASS |
| Spearman trades_count <-> order_expired: 0.6469 | Независимое вычисление из CSV | PASS |

### Код и тесты

- `ML/baseline/mt5_execution_diagnostics.py` содержит все 4 заявленные функции (`count_event_names`, `_numeric_summary`, `summarize_candidate_fill_rate`, `build_fill_rate_diagnostics`) и CLI-фазу `fill-rate`.
- `tests/test_mt5_execution_diagnostics.py` содержит все 3 заявленных теста + 21 других (24 total). Все проходят.
- `pytest` → `24 passed in 0.37s`.

### Перекрёстные ссылки

- Все 4 файла в `Related Materials` существуют.
- План `docs/superpowers/plans/2026-08-01-mt5-saved-batch-fill-rate-probe.md` существует.
- Все 4 файла в `Changed Files` существуют.
- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`: n_valid=32, n_eligible=11 — подтверждено.
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`: PF 1.2323, BS_p05 0.887, fill rate 0.0944 — подтверждено.
- CHANGELOG.md содержит запись `[2026-08-01]` для данного отчёта.
- CONTEXT_HANDOFF.md консистентен с выводами отчёта.
- `fill_rate_candidates.csv` покрыт `.gitignore` (глобальное правило `*.csv`).

### Вердикт

- `DIAGNOSTIC_ONLY` — корректен: нет нового winner, cost model incomplete, linkage UNKNOWN.

---

## Итоговая таблица

| # | Важность | Суть | Статус |
|---|---|---|---|
| 1 | важно | Spearman-корреляции и residual вычислены вне кода, не воспроизводимы | требует исправления |
| 2 | важно | Отсутствует раздел Verification | требует добавления |
| 3 | важно | Отсутствуют хеши артефактов | требует добавления |
| 4 | важно | Нет BUY/SELL side-specific breakdown (методология 11) | требует добавления или явного gap |
| 5 | улучшение | Отсутствует continuation_budget | рекомендуется добавить |
| 6 | улучшение | Отсутствует yearly decomposition (A5) | рекомендуется добавить или зафиксировать gap |
| 7 | улучшение | Отсутствует explicit Multiple Testing Context section | рекомендуется вынести |
| 8 | важно | Опечатки и мусорные символы в строках 112, 120, 122, 140, 143 | требует исправления |
| 9 | вопрос | "5 FAIL" label не трассируется к артефакту | рекомендуется уточнить формулировку |
| 10 | улучшение | Отсутствует explicit holdout non-selection confirmation | рекомендуется добавить |
