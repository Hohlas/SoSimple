# MT5 Batch Selection: 32 Candidates

**Goal:** Прогнать 32 предобранных кандидата через MT5 Strategy Tester
на validation-периоде, собрать метрики, применить multiple-testing correction,
определить победителя по заранее заданным гейтам.

**Status:** DRAFT

```text
depends_on: docs/reports/2026-07-31-mt5-nero-parity.md (PARITY_PASS)
blocks: locked_test freeze
supersedes: none
exit_decisions: BATCH_WINNER | BATCH_NO_WINNER | BATCH_BLOCKED
locked_test_policy: не используется для отбора; freeze после выбора победителя
```

## Контекст

Шортлист: `ML/reports/entry_based_movement_filter_candidates.csv` (32 кандидата).
Каждый кандидат — конфигурация movement-фильтра (profile, model, horizon,
threshold). Все `selection_eligible=True`, `yearly_check_pass=True`.

Инфраструктура готова:
- Export: `ML/baseline/export_mt5_entry_signals.py`
- Parse: `ML/baseline/parse_mt5_execution_report.py`
- Schema: `ML/baseline/mt5_signal_schema.py`
- Tester: headless Wine/xvfb, ~8 мин/прогон
- Single-rule diagnostic: пройден (2026-07-30)

## Global Constraints

- Status: DIAGNOSTIC_ONLY до полного цикла (leakage/split/locked_test).
- Selection только на validation, не на locked_test.
- Multiple-testing correction обязательна (32 > 10): Holm-Bonferroni.
- Запрещено: PnL/PF/trading-выводы без reconciliation + locked_test.
- Кандидаты заморожены — не добавлять/удалять по результату прогона.
- `git push` не делать.

## Архитектура

```
Для каждого кандидата (32 шт):
  1. Python: сгенерировать entry signals CSV
     (source → prepare_mt5_entry_source → export_mt5_entry_signals)
  2. MT5 tester: прогнать с DiagnosticExecutor=true
     (читает entry CSV → ставит limit orders → пишет events CSV)
  3. Python: распарсить events, собрать метрики

После всех:
  4. Агрегировать метрики, применить Holm-Bonferroni
  5. Определить победителя по гейтам
  6. Отчёт
```

## Design Decisions

1. **Validation период:** 2021.01.04–2022.12.02 (пересечение movement
   scores val_select 2021–2023 и order mechanics 2019.06–2022.12).
   ~4947 баров. Split roles: combined (один период для select+eval) →
   потолок RESEARCH_ONLY. Фиксируем как ограничение первого прогона.

2. **Source data pipeline:**
   - Order mechanics: `ML/reports/fractal0_entry_quality_filter_scores.csv`
     (9463 строки, side/limit_price/protective_stop_price/atr, sep=`;`).
   - Movement scores: пересчёт через `benchmark_entry_based_movement_filter.py`
     для каждого из 8 уникальных (profile, model, horizon). Кэш: 4 threshold
     используют один score frame → 8 обучений, не 32.
   - Join: по normalized time (EQ формат `2019-06-20 16:00:00`, freeze формат
     `2021.01.04 01:00` → привести к datetime).
   - Filter: score >= candidate.score_cutoff → подмножество сигналов.
   - Ожидание: top-5% ≈ 250 сигналов, top-30% ≈ 1500 на кандидата.

3. **Метрика отбора:** primary = profit_factor из MT5 tester events
   (reconciled: CLOSED_TX / UNEXPLAINED=0). Secondary: trades_count,
   win_rate, max_drawdown, PF_buy/PF_sell, PF по годам.
   PF считается gross (без swap/commission — в TX-строках обе колонки = 0).

4. **Гейты победителя:**
   - trades_count >= 100 (общий) И >= 30 на сторону (BUY/SELL).
     Кандидаты с 30 <= trades < 100: статус diagnostic_only, в выборе
     winner не участвуют, метрики включаются в таблицу.
   - UNEXPLAINED == 0 (reconciliation PASS)
   - BS_p05 > 1.0 (нижняя граница block bootstrap CI для PF,
     блоки 10–20 сделок, >= 1000 итераций)
   - Holm-Bonferroni: p-value для H0: PF <= 1.0 через block bootstrap
     (блоки 10–20 последовательных сделок, >= 1000 итераций).
     Коррекция на N кандидатов, прошедших gate trades >= 100.
   - Profit concentration: effective_profit_years >= max(1.5, 0.6 * 2) = 1.5
     (n_years = 2 для периода 2021–2022). Провал понижает статус до
     research_only, не автоматический reject (согласно 09-validation-freeze).
   - Tie-breaker: BS_p05 desc, затем trades_count desc.

5. **Автоматизация:** один Python-скрипт (`ML/baseline/run_mt5_batch.py`)
   управляет циклом: score → filter → export → tester → parse → next.
   Tester запускается subprocess (xvfb-run wine terminal64.exe /config:...).

6. **Именование:** run_id = `{profile}_{model}_{horizon}h_thr{threshold_value}`.
   Пример: `simple_combined_extra_trees_small_3h_thr0.05`.
   Events: `batch/{run_id}/events.csv`. Metrics: `batch/{run_id}/metrics.json`.

7. **Время:** 32 × ~8 мин = ~4.5 часа. Resume-by-skip: если metrics.json
   существует и valid — skip.

8. **Cumulative search budget:** benchmark оценил 64 конфигурации
   (2 профиля × 2 модели × 4 горизонта × 4 порога); 32 прошли фильтры
   selection_eligible + yearly_check. Holm-Bonferroni применяется к N <= 32
   (фактическое число кандидатов, прошедших sample_size_gate).
   Полный бюджет раскрыт в отчёте.

9. **Tester model:** Model 1 (1-minute OHLC), идентично single-rule
   diagnostic и parity. Смена модели делает результаты несравнимыми.

## Known Risks

- **ERROR-4756:** send failures. Mitigation: UNEXPLAINED=0 gate.
- **Gross PF:** PF считается без swap и commission (в TX-строках оба = 0).
  Статус результата не выше DIAGNOSTIC_ONLY до применения cost model
  по docs/methodology/12-backtest-costs.md.
- **Timing contract тривиален:** bridge копирует signal_time во все
  временные поля (time_policy=copy). Не является доказательством
  leakage-free. Не используется как гейт победителя.
- **ORDER_EXPIRED семантика:** событие означает «отложник исчез И срок
  истёк», а не «снят по сроку». Для сравнимости fill-rate между
  кандидатами: установить ORDER_TIME_SPECIFIED на отложники или явно
  снимать просроченный pending (см. lifecycle отчёт, Limitations).
- **LiveUpdate:** payload удалён из liveupdate-каталога, но при следующем
  скачивании петля может вернуться. Перед batch: проверить отсутствие
  liveupdate-файлов или заблокировать каталог.
- **~4947 баров на пересечении:** меньше чем полный период. Достаточно
  для первого понимания (user confirmed).
- **Combined split roles:** потолок RESEARCH_ONLY. Для полноценного
  verdict нужен отдельный val-eval период (будущий шаг).

---

## Task 1: Скрипт генерации entry signals для 32 кандидатов

**Files:**
- Input: `ML/reports/entry_based_movement_filter_candidates.csv` (32 кандидата)
- Input: `ML/reports/fractal0_entry_quality_filter_scores.csv` (order mechanics)
- Input: `ML/reports/entry_based_amplitude_movement.json` (source для benchmark)
- Reuse: `ML/baseline/benchmark_entry_based_movement_filter.py` (materialize_candidate_score_frames)
- Reuse: `ML/baseline/prepare_mt5_entry_source.py`, `export_mt5_entry_signals.py`
- New: `ML/baseline/run_mt5_batch.py`
- Output: `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.csv`

**Steps:**
- [ ] Написать `run_mt5_batch.py`:
  - Загрузить candidates CSV и EQ scores CSV.
  - Инициализировать runtime_context для benchmark (splits, targets, caches).
  - Для каждого кандидата:
    - `materialize_candidate_score_frames(candidate, ctx)` → score frame с time.
    - Normalize time, join с EQ scores (inner join on time).
    - Filter: score >= score_cutoff.
    - Подмножество EQ rows → prepare_mt5_entry_source → export_mt5_entry_signals.
    - Записать entry_signals.csv в `batch/{run_id}/`.
  - Валидировать: schema PASS, row count > 0.
- [ ] Запустить. Проверить: 32 CSV существуют, signal counts разумны.

**Критерий:** 32 entry CSV существуют, schema valid, signal count > 0.

---

## Task 2: Скрипт автоматизации MT5 tester (batch loop)

**Files:**
- New: `ML/baseline/run_mt5_batch.py` (tester loop section)
- Input: entry signals из Task 1
- Output: `ML/reports/mt5_execution_loop/batch/{run_id}/events.csv`
- Output: `ML/reports/mt5_execution_loop/batch/{run_id}/metrics.json`

**Steps:**
- [ ] Шаг 0 (перед циклом):
  - Перекомпилировать `$o$imple.mq5`, верифицировать 0 errors.
  - Проверить отсутствие liveupdate-файлов в каталоге терминала.
  - Убедиться что `#property tester_file "mt5_entry_signals.csv"` присутствует
    в исходнике (без него tester agent очищает каталог Files).
- [ ] Шаг 1 — Smoke test (1 кандидат, Model 2 Open Prices, 2021.01–2021.03):
  - Взять первый кандидат из списка.
  - Прогнать pipeline: entry CSV → tester → events → parse → metrics.
  - Цель: убедиться что entry CSV читается, ордера ставятся/закрываются,
    events CSV пишется, reconciliation UNEXPLAINED=0, metrics.json собирается.
  - Время: ~30 секунд. Если не работает — чиним до полного batch.
  - Smoke-артефакты: `batch/_smoke/` (не входят в итоговую таблицу).
- [ ] Шаг 2 — Полный batch (Model 1, 2021.01–2022.12):
- [ ] Для каждого run_id:
  - Скопировать entry CSV в tester Files как `mt5_entry_signals.csv`
    (имя захардкожено в #property tester_file — не переименовывать).
  - Создать .set (DiagnosticExecutor=true, EntrySignalFile, EventFile)
  - Создать INI в /tmp/mt5_batch_{run_id}.ini (путь без пробелов —
    Wine парсит /config: с пробелами с лишней кавычкой).
  - Запустить tester, дождаться завершения
  - Извлечь events CSV из tester Files
  - Распарсить → metrics.json
  - Проверить: UNEXPLAINED, event count > 0
- [ ] Resume logic: если metrics.json существует и valid — skip.
- [ ] Логировать прогресс: `{i}/32 done, last={run_id}, events={N}`.

**Критерий:** 32 metrics.json существуют, все с UNEXPLAINED=0.

---

## Task 3: Агрегация, multiple-testing correction, verdict

**Files:**
- Input: 32 metrics.json
- New: `ML/baseline/run_mt5_batch.py` (фаза `--phase aggregate`)
- Output: `ML/reports/mt5_execution_loop/batch/batch_summary.json`

**Steps:**
- [ ] Собрать таблицу: run_id, PF, trades, win_rate, drawdown, UNEXPLAINED,
  PF_buy, PF_sell, trades_buy, trades_sell, PF_2021, PF_2022.
- [ ] Исключить кандидатов с UNEXPLAINED > 0.
- [ ] Разделить: trades >= 100 → eligible для winner; 30 <= trades < 100 →
  diagnostic_only (метрики в таблице, в выборе не участвуют).
- [ ] Для каждого eligible-кандидата: block bootstrap (блоки 10–20 сделок,
  >= 1000 итераций) → p-value для H0: PF <= 1.0, BS_p05 (нижняя граница CI).
- [ ] Holm-Bonferroni на p-value по eligible-кандидатам (alpha=0.05).
- [ ] Profit concentration для eligible: effective_profit_years,
  best_year_share, PF_without_best_year.
- [ ] Применить гейты победителя (Design Decisions п. 4).
- [ ] Ранжировать по BS_p05 desc. Tie-breaker: trades_count desc.
- [ ] Verdict: BATCH_WINNER (если top-1 прошёл все гейты) | BATCH_NO_WINNER.
- [ ] Записать batch_summary.json.

**Критерий:** verdict определён, таблица метрик полная.

---

## Task 4: Отчёт + handoff

**Files:**
- New: `docs/reports/2026-07-31-mt5-batch-selection.md` (или фактическая дата)
- Update: `CONTEXT_HANDOFF.md`, `CHANGELOG.md`

**Steps:**
- [ ] Отчёт: context, methodology, таблица 32 метрик, verdict, ограничения.
- [ ] Обновить handoff: active state, decision, next step.
- [ ] Обновить changelog.
- [ ] Обновить batch_selection_contract.json: status → EXECUTED.

**Критерий:** отчёт + handoff + changelog записаны.

---

## Вопросы (закрыты)

1. **Source data:** ~~какой путь к score CSV?~~ Scores генерируются на лету
   через `materialize_candidate_score_frames` из `entry_based_amplitude_movement.json`.
   Готовых score-файлов не требуется (Design Decisions п. 2).
2. **Validation period:** ~~val-select или val-eval?~~ Combined roles →
   потолок RESEARCH_ONLY (Design Decisions п. 1).
3. **Порог trades_count:** ~~30 достаточно?~~ Методология требует >= 100
   для winner, >= 30 на сторону. Применяем (Design Decisions п. 4).

---

## Appendix: Implementation Notes

### A1. Изменение в MQL5 (COUNT.mqh)

При `MT5_DiagnosticExecutor=true` функция `EXPERT::COUNT()` пропускает
`PIC()` и `POC_SIMPLE()` (COUNT.mqh:5). Nero.csv не создаётся.
Это ожидаемо: diagnostic executor не использует фракталы.

### A2. Task 1 — API контракты

#### runtime_context

```python
from ML.baseline.benchmark_entry_based_movement_filter import (
    _build_runtime_context,
    materialize_candidate_score_frames,
)
import json

source_artifact = json.loads(Path("ML/reports/entry_based_amplitude_movement.json").read_text())
ctx = _build_runtime_context(source_artifact)
# ctx keys: splits, targets_by_split, profile_cache, score_family_cache,
#           requested_threads, effective_threads
```

`_build_runtime_context` (строка 291) вызывает `amplitude.load_entry_based_splits()`
и `amplitude.build_movement_targets()`. Данные берутся из DATA/ (обработанные CSV).

#### candidate dict

Каждая строка `entry_based_movement_filter_candidates.csv` → dict.
Ключи, используемые `materialize_candidate_score_frames`:
`profile`, `model_key`, `horizon`, `target_family` (cache key);
`score_cutoff` (для фильтрации).

#### materialize_candidate_score_frames → возвращает

```python
{
    "frames": {
        "val_select": DataFrame(columns=["score", target_col, "time"], index=splits index),
        "val_eval": ...,
        "low_n_disclosure": ...,
    },
    "seed_count": int,
    "score_aggregation": "median_across_rerun_seeds",
    ...
}
```

Для batch нужен `frames["val_select"]` (период 2021–2023, пересечение с EQ).

#### prepare_entry_quality_source (prepare_mt5_entry_source.py:55)

Вход: DataFrame с колонками `SOURCE_COLUMNS`:
```
time, signal_time, side, limit_price, protective_stop_price, atr
```
Выход: DataFrame с `OUTPUT_COLUMNS`:
```
time, feature_time, feature_available_time, decision_time, rule_id,
side, limit_price, protective_stop_price, atr
```
Все временные поля копируются из signal_time (diagnostic bridge).
sep=`;` при чтении и записи.

#### export_mt5_entry_signals (export_mt5_entry_signals.py:190)

CLI:
```bash
./.venv/bin/python -m ML.baseline.export_mt5_entry_signals \
  --source-csv prepared.csv \
  --output-csv batch/{run_id}/entry_signals.csv \
  --output-json batch/{run_id}/entry_signals.json \
  --run-id {run_id} \
  --max-fill-lag-bars 6
```

Выходной CSV (sep=`;`) содержит `MT5_SIGNAL_COLUMNS`:
```
time, feature_time, feature_available_time, decision_time, rule_id,
side, entry_type, limit_price, stop_price, atr, max_fill_lag_bars
```
`entry_type` = BUY_LIMIT / SELL_LIMIT (автоматически из side).
`stop_price` маппится из `protective_stop_price`.

#### Join logic (для run_mt5_batch.py)

```python
# EQ scores: time формат "2019-06-20 16:00:00"
# score frame: time формат "2021.01.04 01:00" (из splits index)
# → pd.to_datetime оба, inner join on time
# → filter: score >= candidate["score_cutoff"]
# → подмножество EQ rows (side, limit_price, protective_stop_price, atr)
# → prepare_entry_quality_source → export_mt5_entry_signals
```

Период: оставить только строки с time в [2021.01.04, 2022.12.02].

### A3. Task 2 — MT5 Tester: шаблоны и пути

#### Ключевые пути

```
Wine prefix:        ~/.mt5
Terminal:           ~/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe
MetaEditor:         ~/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe
Tester Files:       ~/.mt5/drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files/
.set каталог:       ~/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Profiles/Tester/
Experts (runtime):  ~/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/
```

Experts в runtime — hardlink на `MT/MQL5/Experts/` (один файл).

#### Компиляция (docs/methodology/13b-mt5-execution-parity.md:126)

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'

# Проверка:
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -5
# Ожидание: "Result: 0 errors, 0 warnings"
```

Код возврата wine НЕ является verdict (может быть 1 при успехе).

#### .set файл формат

Кодировка: UTF-16LE. Расширение: `.set`.
Расположение: `~/.mt5/.../MQL5/Profiles/Tester/{name}.set`

**Критично:** строковые параметры — `Name=value` без `||`.
Булевы/числовые — `Name=value||default||min||max||N`.

Diagnostic-параметры (из lifecycle .set):
```ini
InpMT5_DiagnosticExecutor=true||false||0||true||N
InpMT5_EntrySignalFile=mt5_entry_signals.csv
InpMT5_EventFile=mt5_trade_events_{run_id}.csv
InpMT5_BlockBarsSinceFill0Exit=true||false||0||true||N
InpMT5_ExportNero=false||false||0||true||N
```

Остальные параметры эксперта (PIC, ATR, signals) — не влияют на diagnostic,
но должны присутствовать. Скопировать полный .set из lifecycle:
`~/.mt5/.../Profiles/Tester/mt5_tx_lifecycle_20260731.set`
и заменить только EventFile + ExportNero=false.

#### INI файл (образец: mt5_tx_lifecycle_tester_20260731_full.ini)

```ini
[Tester]
Expert=$o$imple.ex5
ExpertParameters={set_filename}.set
Symbol=XAUUSD
Period=H1
Optimization=0
Model=1
FromDate=2021.01.04
ToDate=2022.12.02
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

Для smoke: Model=2, FromDate=2021.01.04, ToDate=2021.03.31.
INI класть в /tmp/ (путь без пробелов).

#### Запуск тестера

```bash
WINEPREFIX=~/.mt5 xvfb-run -a wine \
  '~/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe' \
  /config:/tmp/mt5_batch_{run_id}.ini
```

Завершение: процесс wine завершается сам (ShutdownTerminal=1).
Ждать: poll PID или `wait`. Таймаут: 20 минут (8 мин норма + запас).

#### Порядок файлов для каждого прогона

1. Скопировать entry CSV → Tester Files как `mt5_entry_signals.csv`
2. Записать .set → Profiles/Tester/
3. Записать INI → /tmp/
4. Запустить terminal64.exe
5. После завершения: забрать events CSV из Tester Files
6. Распарсить:
```bash
./.venv/bin/python -m ML.baseline.parse_mt5_execution_report \
  --events batch/{run_id}/events.csv \
  --output-json batch/{run_id}/metrics.json
```

#### LiveUpdate pre-check

```bash
ls ~/.mt5/drive_c/users/*/AppData/Roaming/MetaQuotes/Terminal/*/liveupdate/
# Если есть файлы — переместить в /tmp/ перед batch
```

### A4. Task 3 — Block bootstrap

Реализация: numpy вручную (без внешних зависимостей типа arch).

```python
def block_bootstrap_pf(pnl_series: np.ndarray, n_iter=2000, block_size=15, seed=42):
    """
    pnl_series: массив PnL по сделкам (последовательно во времени).
    block_size: 10-20 сделок (фиксированный, не случайный).
    Возвращает: (p_value, bs_p05)
      p_value: доля итераций где PF <= 1.0
      bs_p05: 5-й перцентиль распределения PF
    """
    rng = np.random.default_rng(seed)
    n = len(pnl_series)
    n_blocks = ceil(n / block_size)
    pf_samples = np.empty(n_iter)
    for i in range(n_iter):
        starts = rng.integers(0, n - block_size + 1, size=n_blocks)
        sample = np.concatenate([pnl_series[s:s+block_size] for s in starts])[:n]
        gross_profit = sample[sample > 0].sum()
        gross_loss = abs(sample[sample < 0].sum())
        pf_samples[i] = gross_profit / gross_loss if gross_loss > 0 else np.inf
    p_value = float((pf_samples <= 1.0).mean())
    bs_p05 = float(np.percentile(pf_samples, 5))
    return p_value, bs_p05
```

Holm-Bonferroni: отсортировать p-value по возрастанию, для ранга k из N:
adjusted_alpha_k = alpha / (N - k + 1). Отклонять H0 пока p_k <= adjusted_alpha_k.

Profit concentration:
```python
yearly_gross_profit = {year: pnl[pnl > 0 & year_mask].sum() for year in [2021, 2022]}
shares = [gp / total_gp for gp in yearly_gross_profit.values()]
effective_profit_years = 1.0 / sum(s**2 for s in shares)
```

### A5. Candidates CSV → run_id маппинг

```python
run_id = f"{row['profile']}_{row['model_key']}_{int(row['horizon'])}h_thr{row['threshold_value']}"
# Пример: simple_combined_extra_trees_small_3h_thr0.05
```

8 уникальных (profile, model_key, horizon) → 4 threshold каждый = 32 кандидата.
Не все комбинации profile×model присутствуют (только 8 из 16 возможных).

### A6. Окружение

- Python: `./.venv/bin/python` (виртуальное окружение в корне repo)
- Тесты: `./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q`
- Wine: 9.0, xvfb-run для headless
- Рабочая директория: `/home/hohla/git/SoSimple`
