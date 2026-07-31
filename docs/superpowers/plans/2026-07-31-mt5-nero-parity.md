# MT5 Nero.csv Producer Parity Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Доказать или явно ограничить, что MT5-советник `$o$imple.mq5` генерирует
`Nero_MT5.csv`, совместимый с эталонным MT4 `Nero_XAUUSD.csv` по формату,
структуре и числовому содержанию. Результат — verdict `PARITY_PASS`,
`PARITY_PARTIAL` (с перечнем расхождений) или `PARITY_FAIL`.

**Architecture:** MT5 tester запускается в режиме `InpMT5_ExportNero=true` на
XAUUSD H1 за период, перекрывающий эталонный MT4 файл. Полученный `Nero_MT5.csv`
сравнивается с `MT/MQL4/Files/Nero_XAUUSD.csv` Python-скриптом по чек-листу
`docs/schemas/mt5_nero_csv_contract.md`. Сравнение структурное (формат, колонки,
вложенные поля) и числовое (agreement rate по direction/price/ATR).

**Tech Stack:** MQL5 (`lib_PIC.mqh` NERO_CSV_CREATE), MT5 Strategy Tester под
Wine/xvfb, Python 3 via `./.venv/bin/python`, pandas, pytest.

```text
depends_on: docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md
blocks: MT5 batch selection for 20-50 candidates
supersedes: none
exit_decisions: PARITY_PASS | PARITY_PARTIAL | PARITY_FAIL
locked_test_policy: not used; no winner/threshold/rule/cost/entry/exit/stop selection
```

## Global Constraints

- Не модифицировать `lib_PIC.mqh`, `$o$imple.mq5` или любой MQL-код в рамках
  этого плана. Parity проверяет существующий код как есть. Если обнаружен
  дефект формата — фиксируем в отчёте, не чиним.
- Эталон: `MT/MQL4/Files/Nero_XAUUSD.csv` (62764 строки данных,
  2004.07.07 20:00 — 2026.04.22 12:00, 104 колонки).
- MT5 tester сценарий: XAUUSD, H1, 2019.06.20–2022.12.03, Model 1
  (1-minute OHLC) — тот же период, что и lifecycle-прогон 31.07.
- `USE_NORMALIZED_OUTPUT=false` в обоих кодах (MT4 и MT5) — сравнение по
  сырым значениям.
- Все результаты `DIAGNOSTIC_ONLY`. Никаких PnL/PF/trading-выводов.
- Запускать только целевые тесты: новый `tests/test_mt5_nero_parity.py`.
- `git push` не делать.

## Methodology Map

| Этап плана | Методика | Обязательные проверки | Критерий завершения |
|---|---|---|---|
| Task 1: генерация Nero_MT5.csv | `13b-mt5-execution-parity.md` — **только** разделы «Компиляция» (строки 124-143) и «Порядок» шаги 1-3, 10 (tester metadata). Trade-execution проверки 13b (opened/closed, close reasons, PnL) не применяются. | compile log `0 errors`; tester metadata записан; файл извлечён из правильного каталога | `Nero_MT5.csv` существует, >0 строк данных |
| Task 2: Python-скрипт сравнения | Нет выделенного раздела методологии. Применяются общие принципы `13-export-mt4-parity.md` (counts, reconciliation, classification расхождений) + чек-лист `docs/schemas/mt5_nero_csv_contract.md`. | все пункты чек-листа контракта покрыты; тесты green | `pytest tests/test_mt5_nero_parity.py` PASS |
| Task 3: запуск сравнения | Нет выделенного раздела методологии. Применяются общие принципы `13-export-mt4-parity.md` (critical_mismatch_count, объяснение расхождений) + чек-лист контракта. | каждый пункт чек-листа имеет числовой результат; расхождения классифицированы | verdict определён |
| Task 4: отчёт | `16-reporting-audit.md` (команды, хеши, limitations, verdict, structured artifact) | отчёт содержит все секции; manifest JSON с ключевыми числами; sha256 артефактов | отчёт + manifest записаны |

**Раздел методологии, которого нет:** не существует отдельного раздела для
сравнения feature-producer CSV между платформами. `13b` регламентирует
trade-execution parity (entry CSV → сделки, event log, PnL), а не feature
stream. Для Task 2/3 порядок действий основан на общих принципах `13`
(frozen input, counts, reconciliation, classification) и конкретном чек-листе
`docs/schemas/mt5_nero_csv_contract.md`.

## Design Decisions (fixed before implementation)

1. **Период сравнения:** tester запускается на 2019.06.20–2022.12.03, но
   фактический выход MT5 начинается с 2019.07.02 15:00 (первые ~12 дней —
   прогрев: producer не пишет строки, пока не заполнен массив из
   LevelsAmount=101 фракталов). Фактический объём MT5: ~9378 строк данных.
   Из MT4 файла берётся только пересечение по `time`. Строки вне пересечения
   игнорируются. Более поздний старт MT5 — ожидаемое поведение producer,
   не дефект.
2. **Ключ join:** колонка `time` (формат `YYYY.MM.DD HH:MM`).
   Дубликаты времени присутствуют в обоих файлах (MT4: 3764, MT5: 473 —
   известны как артефакт gap-fill истории XAUUSD, методология 13 строка 68:
   «Известен effect duplicate timestamps»). Дубликаты не являются blocker
   для PASS. Политика дедупликации: при join берётся последняя строка для
   каждого `time` (tail-wins). Количество дубликатов фиксируется в manifest
   как диагностическая метрика.
3. **Структурное сравнение:**
   - количество колонок и имена заголовков;
   - количество вложенных полей на фрактал (ожидание: 22 в текущем MT4 файле,
     23 в текущем коде MT4/MT5 — расхождение фиксируется);
   - parse success rate для `fractal0..fractal99`.
4. **Числовое сравнение (на пересечении строк):**
   - `fractal0.direction` (поле 3, индекс 2): agreement rate;
   - `fractal0.price` (поле 2, индекс 1): abs diff summary (mean, p50, p95,
     max);
   - `ATR` (колонка 4): abs diff summary;
   - `fractal0.T` (поле 1, индекс 0): agreement rate (timestamp уровня).
5. **Пороги verdict:**
   - `PARITY_PASS`: column/format match 100%, direction agreement >= 95%,
     price p95 diff <= 5.0 (в цене, USD за унцию XAUUSD), ATR p95 diff <= 1.0
     (в цене);
   - `PARITY_PARTIAL`: format match, но числовые пороги не пройдены;
     расхождения объяснимы (разница котировок, сессий, округления);
   - `PARITY_FAIL`: структурное несовпадение (колонки, формат, parse errors).
   Единицы: все diff в абсолютной цене (USD за унцию), не в пунктах.
   Обоснование порогов: эмпирическая оценка на первом совпадающем баре
   (2019.07.02 15:00) даёт |diff|=1.7 при XAUUSD ~1400; за 3.5 года
   разница историй между MT4/MT5 может достигать 3-5 USD на H1 ATR ~5-15.
   Порог 5.0 — диагностический, установлен до прогона.
   **Anti-tuning disclosure:** пороги зафиксированы до запуска сравнения
   и не пересматриваются по результату. Если p95 > 5.0, verdict PARTIAL
   или FAIL без ретюннинга.
   Дополнительно: вместо единственного порога скрипт строит распределение
   diff и классифицирует: small drift (<0.1), broker-history shift (0.1-5),
   systematic (>5). Классификация попадает в отчёт.
6. **22 vs 23 поля:** если MT5 пишет 23 поля (с Shift), а MT4 файл содержит
   22 — это не FAIL, а known format evolution. Сравнение первых 22 полей
   выполняется; 23-е поле (Shift) проверяется на внутреннюю консистентность
   MT5 (integer, >= 1 для непустых фракталов — Shift = bar-смещение уровня
   назад, всегда положителен для прошлых баров; эмпирически min=1, max~148).
7. **Причина расхождений:** если agreement < 100%, обязательна классификация:
   (a) разница котировок MT4/MT5; (b) разница bar indexing (MT4 vs MQL4Compat);
   (c) rounding; (d) баг. Пункт (d) — blocker.

## Known Unknowns / Risks

- **MT4 файл сгенерирован другим билдом:** текущий `Nero_XAUUSD.csv` содержит
  22 поля, тогда как текущий код MT4 пишет 23. Файл мог быть создан старой
  версией `lib_PIC.mqh`. Если формат критичен, потребуется перегенерация MT4
  файла (вне scope этого плана — фиксируем как ограничение).
- **Разница котировок:** MT4 и MT5 tester могут использовать разную историю
  (брокер, сервер, модель генерации тиков). Числовое совпадение не будет 100%.
  Эмпирически: первый совпадающий бар даёт |diff|=1.7 при цене ~1395.
- **MQL4Compat layer:** `SHIFT()`, `BTIME()`, `iTime()` в MT5 идут через слой
  совместимости. Возможна разница в bar indexing (MT4: bar 0 = текущий;
  MT5: то же через compat). Влияние: поле Shift и T.
- **LevelsAmount:** MT5 `#define LevelsAmount 101` → 100 фракталов
  (fractal0..fractal99). MT4 заголовок тоже 104 колонки = 4 + 100. Совпадение
  ожидается, но проверяется.
- **Tester Files каталог:** Nero_MT5.csv пишется в runtime Files каталог
  tester agent, не в repo. Путь:
  `~/.mt5/drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files/`.
- **Существующий файл:** Nero_MT5.csv уже существует (191 MB, 9378 строк,
  2019.07.02 15:00 — 2022.12.02 22:00), создан lifecycle-прогоном 31.07.
  Решение о переиспользовании/перегенерации принимается в Task 1.
- **Прогрев producer:** первые ~12 дней tester (2019.06.20–2019.07.02) не
  дают строк Nero — массив фракталов заполняется постепенно. Это ожидаемое
  поведение (`cnt == LevelsAmount` gate в `lib_PIC.mqh:923`).
- **Объём:** ~9378 строк × 100 фракталов × 23 поля — парсинг может занять
  время; pandas справится.

---

## Task 1: Генерация Nero_MT5.csv в MT5 Tester

**Методика:** `13b-mt5-execution-parity.md` — только разделы «Компиляция» и
«Порядок» шаги 1-3, 10 (tester metadata). Trade-execution проверки не применяются.

**Files:**
- Read-only: `MT/MQL5/Experts/$o$imple.mq5`, `MT/MQL5/Include/lib_PIC.mqh`
- Output: `ML/reports/mt5_nero_parity/Nero_MT5.csv` (копия из tester Files)
- Output: `ML/reports/mt5_nero_parity/mt5_nero_parity_compile.log`

**Steps:**
- [x] **Проверить существующий файл.** `Nero_MT5.csv` уже существует в tester
      Files (191 MB, 9378 строк, 2019.07.02 15:00 — 2022.12.02 22:00),
      сгенерирован lifecycle-прогоном 31.07 с `InpMT5_ExportNero=true`.
      Зафиксировать решение: переиспользовать или перегенерировать.
      В любом случае скопировать текущий файл в
      `ML/reports/mt5_nero_parity/Nero_MT5_from_lifecycle_20260731.csv`
      до любого нового прогона.
- [x] Проверить симлинк `MQL5 -> MT/MQL5` в терминале.
- [x] Скомпилировать `$o$imple.mq5` headless (команда из 13b). Сохранить лог.
      Проверить `0 errors, 0 warnings`.
- [x] Проверить `liveupdate/` payload отсутствует; нет запущенного
      `terminal64.exe`.
- [x] Создать `.set` файл `MT/MQL5/Profiles/Tester/mt5_nero_parity.set`
      (UTF-16LE, формат `Name=value||...||N`):
      ```
      InpMT5_ExportNero=true||false||0||true||N
      InpMT5_NeroFile=Nero_MT5.csv||Nero_MT5.csv||Nero_MT5.csv||Nero_MT5.csv||N
      InpMT5_DiagnosticExecutor=false||false||0||false||N
      ```
      (DiagnosticExecutor выключен — нужен только Nero producer, не исполнение.
      Producer `NERO_CSV_CREATE` не зависит от флага diagnostic executor:
      `lib_PIC.mqh:782` проверяет только `MT5_ExportNero`.)
- [x] Создать INI-файл `mt5_nero_parity.ini` (UTF-8, в корне без пробелов):
      ```ini
      [Tester]
      Expert=$o$imple.ex5
      ExpertParameters=mt5_nero_parity.set
      Symbol=XAUUSD
      Period=H1
      Optimization=0
      Model=1
      FromDate=2019.06.20
      ToDate=2022.12.03
      ForwardMode=0
      Deposit=10000
      Currency=USD
      Leverage=1:500
      ExecutionMode=0
      Visual=0
      ReplaceReport=1
      ShutdownTerminal=1
      UseLocal=1
      UseRemote=0
      UseCloud=0
      ```
- [x] Запустить tester:
      ```bash
      WINEPREFIX=~/.mt5 xvfb-run -a wine \
        "$HOME/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe" \
        /config:C:\\mt5_nero_parity.ini
      ```
- [x] Дождаться завершения (`ShutdownTerminal=1` гарантирует возврат;
      дополнительно проверить отсутствие процесса `terminal64.exe`).
- [x] Извлечь `Nero_MT5.csv` из tester Files каталога в
      `ML/reports/mt5_nero_parity/`.
- [x] Записать tester metadata: build, broker/server, symbol spec, model,
      date range, deposit, spread mode, account mode.
- [x] Проверить: файл существует, >0 строк данных, заголовок начинается с
      `time;signal;predict;ATR;fractal0`.
      **Кодировка:** MT5 пишет CSV в UTF-16LE с BOM (`\ufeff`). Проверять
      содержимое через `encoding='utf-16'`.

**Критерий завершения:** `Nero_MT5.csv` извлечён, содержит данные за ожидаемый
период, заголовок совпадает с ожидаемым форматом.

---

## Task 2: Python-скрипт сравнения и тесты

**Методика:** нет выделенного раздела. Общие принципы `13-export-mt4-parity.md`
(counts, reconciliation, classification) + чек-лист
`docs/schemas/mt5_nero_csv_contract.md`.

**Files:**
- New: `ML/baseline/compare_nero_parity.py`
- New: `tests/test_mt5_nero_parity.py`
- Output: `ML/reports/mt5_nero_parity/nero_parity_comparison.json`

**Steps:**
- [x] Написать `compare_nero_parity.py`:
      - CLI args: `--mt4 PATH --mt5 PATH --output-json PATH`
      - Загрузка CSV: MT4 — `encoding='utf-8'`, MT5 — `encoding='utf-16'`
        (MT5 FileWrite создаёт UTF-16LE с BOM; pandas `encoding='utf-16'`
        обрабатывает BOM автоматически). Delimiter `;`, dtype str.
      - Join по `time`, определение пересечения.
      - Структурные проверки:
        - column names/order match;
        - row count (total, intersection);
        - min/max time;
        - duplicate time count (per file);
        - fractal parse: для каждой строки intersection, каждый непустой
          fractalN → split(':') → len;
        - field count distribution (22 vs 23);
        - 23-е поле (Shift, MT5 only): integer check, >= 1 для непустых
          фракталов (Shift = SHIFT(T) - cur_bar, всегда положителен для
          уровней из прошлого; эмпирически min=1).
      - Числовые проверки (на intersection, для fractal0):
        - direction agreement rate;
        - price abs diff: mean, p50, p95, max;
        - T (timestamp) agreement rate;
        - ATR abs diff: mean, p50, p95, max.
      - Расширенные проверки (для fractal1..fractal9, sampled):
        - direction agreement rate per fractal index;
        - price p95 diff per fractal index.
      - Verdict logic по Design Decision 5.
      - JSON output: все метрики, verdict, расхождения, классификация.
- [x] Написать `tests/test_mt5_nero_parity.py`:
      - Синтетические fixture: 2 мини-CSV (MT4-style 22 поля, MT5-style
        23 поля) с известными значениями.
      - Тест: structural checks correctly detect column mismatch.
      - Тест: direction agreement считается правильно.
      - Тест: price diff summary считается правильно.
      - Тест: verdict PASS/PARTIAL/FAIL по порогам.
      - Тест: 22 vs 23 поля — не FAIL, первые 22 сравниваются.
- [x] Запустить `./.venv/bin/python -m pytest tests/test_mt5_nero_parity.py -q`.
      Все тесты green.

**Критерий завершения:** скрипт работает на синтетике, тесты проходят,
все пункты чек-листа контракта покрыты кодом.

---

## Task 3: Запуск сравнения на реальных данных

**Методика:** нет выделенного раздела. Общие принципы `13-export-mt4-parity.md`
(critical_mismatch_count, объяснение расхождений) + чек-лист контракта.

**Files:**
- Input: `MT/MQL4/Files/Nero_XAUUSD.csv`, `ML/reports/mt5_nero_parity/Nero_MT5.csv`
- Output: `ML/reports/mt5_nero_parity/nero_parity_comparison.json`

**Steps:**
- [x] Запустить:
      ```bash
      ./.venv/bin/python ML/baseline/compare_nero_parity.py \
        --mt4 MT/MQL4/Files/Nero_XAUUSD.csv \
        --mt5 ML/reports/mt5_nero_parity/Nero_MT5.csv \
        --output-json ML/reports/mt5_nero_parity/nero_parity_comparison.json
      ```
- [x] Проверить JSON: все секции заполнены, нет NaN/None в ключевых метриках.
- [x] Классифицировать расхождения (если есть):
      - разница котировок (price diff коррелирует с уровнем, не с временем);
      - bar indexing (Shift diff = const offset);
      - rounding (diff < 0.0001);
      - баг (систематический diff в одном поле, не объяснимый выше).
- [x] Определить verdict по Design Decision 5.
- [x] Если `PARITY_FAIL`: зафиксировать blocker, предложить fix (отдельный
      план, не в этом).

**Критерий завершения:** verdict определён, расхождения классифицированы или
отсутствуют.

---

## Task 4: Отчёт и manifest

**Методика:** `16-reporting-audit.md` — отчёт с секциями, команды, хеши,
limitations, verdict.

**Files:**
- New: `docs/reports/2026-07-31-mt5-nero-parity.md` (или фактическая дата)
- New: `ML/reports/mt5_nero_parity/mt5_nero_parity_manifest.json`

**Steps:**
- [x] Написать отчёт с секциями:
      - Context (зависимость от lifecycle closure, цель);
      - What Was Done (генерация, сравнение, чек-лист);
      - Tester Metadata (build, broker, model, dates, spread, account mode);
      - Results (все метрики из JSON, таблицы);
      - Parity Checklist (каждый пункт контракта с результатом);
      - Discrepancy Classification (если есть);
      - Conclusions (verdict + обоснование);
      - Limitations / Open Questions;
      - Split Disclosure: не используется;
      - Next Step;
      - Related Materials.
- [x] Создать manifest JSON:
      - `verdict`;
      - `mt5_rows`, `mt4_rows`, `intersection_rows`;
      - `column_match`, `field_count_mt4`, `field_count_mt5`;
      - `direction_agreement_rate`;
      - `price_p95_diff`;
      - `atr_p95_diff`;
      - `timestamp_agreement_rate`;
      - `duplicate_time_count_mt4`, `duplicate_time_count_mt5`;
      - `sha256` обоих CSV и JSON;
      - `commands` (compile, tester, compare);
      - `tester_metadata`;
      - `limitations`.
- [x] Обновить `CONTEXT_HANDOFF.md`: active state, decision, next step.
- [x] Обновить `CHANGELOG.md`: новая запись в начале.
- [x] Обновить `docs/superpowers/roadmap.md`: ACTIVE section — отметить
      Nero parity как закрытый (или зафиксировать PARTIAL/FAIL).

**Критерий завершения:** отчёт + manifest записаны, handoff обновлён,
verdict доступен следующему агенту без чтения этого плана.

---

## Вопросы для уточнения (если данных недостаточно)

Разрешены аудитом 2026-07-31:
- Эталонный MT4 файл (22 поля): достаточно сравнения первых 22 полей +
  внутренняя консистентность 23-го. Контракт обновлён.
- Пороги: пересмотрены на эмпирической основе (price p95 <= 5.0, ATR p95 <= 1.0).
- DiagnosticExecutor: producer (`NERO_CSV_CREATE`) не зависит от флага
  diagnostic executor (`lib_PIC.mqh:782` проверяет только `MT5_ExportNero`).

Остаётся открытым:
1. **Переиспользование vs перегенерация:** существующий `Nero_MT5.csv` создан
   с `DiagnosticExecutor=true`. Код подтверждает независимость producer, но
   если нужна полная чистота эксперимента — перегенерировать с
   `DiagnosticExecutor=false`. Решение принимается в Task 1.
