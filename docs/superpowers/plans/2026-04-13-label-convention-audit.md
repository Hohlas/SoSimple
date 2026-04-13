# Label Convention Audit — Triple Barrier float labels

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Найти и устранить все места в коде, где TB-лейблы (float-конвенция `1.0=TP, 0.0=SL, 0.5=Timeout` из [processing/label_signals.py:919](processing/label_signals.py#L919)) обрабатываются неверно — через `int(...)`, через `~win_mask`, через сравнение `== 1` без явного тождества типов, через бинарную интерпретацию SL vs non-SL и т.п. Корневой инцидент — баг в `ML/triple_barrier_mt4_execution.py`, где `int(outcome)` сливал SL (`0.0`) и Timeout (`0.5`) в одну ветку и давал `losses=0, pf=inf`. Этот аудит проверяет, что аналогичный паттерн больше нигде не маскирует результаты.

**Architecture:** Аудит **read-mostly**. Изменения кода допустимы только при подтверждённом баге с воспроизводимым numerical impact. Каждое изменение сопровождается тестом. Никакого рефакторинга «заодно», никакой переформулировки label convention. Единая канон-схема — float `{1.0, 0.0, 0.5}` из `processing/label_signals.py`.

**Tech Stack:** Python 3.11, pytest, pandas/numpy, ripgrep, существующие тесты `tests/test_triple_barrier_*`.

**Non-goals:**
- Не пересматривать саму label convention (float остаётся каноном).
- Не ретюнить `tb_selected_rule.json`, `theta`, `min_ev`.
- Не реанимировать TB как production — он остаётся frozen historical artifact (см. `docs/reports/2026-04-12-tb-verdict.md`).
- Не править MQL-стороны (`MT/MQL4/Include/lib_ML_Signal_TB.mqh`) — у них своя int-конвенция в рантайме.
- Не трогать `entry_path_v1` int-классы (0..5) — это другая семантика.

---

## File Structure

### Read First
- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-12-tb-verdict.md`
- `processing/label_signals.py` (только секция `first_barrier_hit` / `TB_TARGET_NAMES`)
- `ML/triple_barrier_mt4_execution.py`
- `tests/test_triple_barrier_mt4_execution.py`

### Suspect Files (initial inventory — расширить на Task 2)
- `ML/tb_signal_logic.py` — найденный кандидат на баг (см. Task 3, Step 3)
- `ML/threshold_analysis.py`
- `ML/evaluate_test.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/tb_probability_calibration.py`
- `API/generate_signals.py`
- `statistics/signal_tracer.py`

### Artefacts To Create During Execution
- `ML/reports/label_convention_audit.md` — финальный аудит-отчёт (inventory, findings, fixes, residual risk)
- `ML/reports/label_convention_audit_inventory.csv` — машиночитаемый inventory с колонками `file;line;snippet;risk;verdict`
- `docs/reports/2026-04-13-label-convention-audit.md` — stage report

### Files Possibly Modified (only if a bug is confirmed)
- `ML/tb_signal_logic.py`
- любой файл из inventory, по которому Task 4 даст **confirmed bug**
- сопутствующие тесты в `tests/`

### Files To Update At Stage Close
- `CHANGELOG.md` (только если был реальный фикс или подтверждённое отсутствие багов)
- `CONTEXT_HANDOFF.md`
- `wiki/log.md` (запись об аудите)

---

### Task 1: Bootstrap And Freeze The Convention

**Files:**
- Read: `AGENTS.md`
- Read: `CONTEXT_HANDOFF.md`
- Read: `docs/reports/2026-04-12-tb-verdict.md`
- Read: `processing/label_signals.py`
- Read: `ML/triple_barrier_mt4_execution.py`
- Read: `tests/test_triple_barrier_mt4_execution.py`

- [ ] **Step 1: Read the current stage context**

Run:

```bash
sed -n '1,160p' AGENTS.md
sed -n '1,80p' CONTEXT_HANDOFF.md
sed -n '1,200p' docs/reports/2026-04-12-tb-verdict.md
```

Expected:
- TB понятен как «не production, frozen artifact»
- Корень бага — `int(outcome)` в `ML/triple_barrier_mt4_execution.py`, исправлено через `_classify_tb_outcome`

- [ ] **Step 2: Pin the canonical label convention from source**

Run:

```bash
sed -n '880,940p' processing/label_signals.py
sed -n '1,60p' ML/triple_barrier_mt4_execution.py
```

Expected:
- В `processing/label_signals.py` строки `df.at[i, f'buy_sl{sl}_tp{tp}'] = 0.5 if buy_result == -1 else float(buy_result)` (и аналог для sell) подтверждают: значения колонок `buy_sl*_tp*` / `sell_sl*_tp*` — float `{1.0, 0.0, 0.5}`
- В `ML/triple_barrier_mt4_execution.py` функция `_classify_tb_outcome` использует пороги `>=0.75 → TP`, `<=0.25 → SL`, иначе `Timeout`
- Запиши в scratchpad «канон»:
  ```text
  TB_LABEL_TP = 1.0
  TB_LABEL_SL = 0.0
  TB_LABEL_TIMEOUT = 0.5
  TB_LABEL_TP_THRESHOLD = 0.75
  TB_LABEL_SL_THRESHOLD = 0.25
  ```

- [ ] **Step 3: Re-run TB regression suite as the safety baseline**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_triple_barrier_mt4_execution.py \
  tests/test_triple_barrier_first_touch.py \
  tests/test_triple_barrier_calibration.py \
  tests/test_triple_barrier_training.py \
  tests/test_signal_tracer_tb.py \
  tests/test_generate_signals_research.py -q
```

Expected:
- Все тесты зелёные. Если что-то падает — **остановиться** и зафиксировать как pre-existing failure до начала аудита; ни одного fix в этом плане не делаем поверх красного baseline.

- [ ] **Step 4: Define the audit rubric**

Запиши в scratchpad **ровно** эти risk-категории — они потом попадут в inventory CSV:

```text
R1 int_cast            — outcome/label кастуется в int (теряет 0.5)
R2 not_win_is_loss     — loss_mask = ~win_mask или loss = total - wins (сливает SL+Timeout)
R3 binary_eq           — сравнение `== 1` / `== 0` без обработки 0.5
R4 truthiness          — `if outcome:` / `bool(outcome)` (0.0 и 0 эквивалентны)
R5 sign_assumption     — `np.sign(outcome)` или `outcome > 0` без учёта 0.5
R6 dtype_drift         — приведение колонки `buy_sl*_tp*` к int dtype при чтении
R7 missing_timeout     — обработка только TP/SL без явного timeout-branch
R8 ok                  — паттерн встречается, но семантически корректен
```

Expected:
- Все findings в Task 3–4 классифицируются по этим кодам, без свободной формы.

---

### Task 2: Build The File Inventory

**Files:**
- Read: весь репо через `rg` (без открытия больших файлов целиком)

- [ ] **Step 1: Список всех файлов, читающих TB-колонки**

Run:

```bash
rg -n "buy_sl[0-9]+_tp[0-9]+|sell_sl[0-9]+_tp[0-9]+|TB_TARGET_NAMES" \
  --type py \
  -g '!tests/**' \
  -g '!**/archive/**'
```

Expected:
- Список файлов содержит как минимум: `processing/label_signals.py`, `processing/label_main.py`, `ML/data_loader.py`, `ML/train.py`, `ML/evaluate_test.py`, `ML/threshold_analysis.py`, `ML/tb_signal_logic.py`, `ML/triple_barrier_mt4_execution.py`, `ML/tb_probability_calibration.py`, `API/generate_signals.py`, `statistics/signal_tracer.py`
- Зафиксируй полный список в scratchpad как **TB_LABEL_CONSUMERS**

- [ ] **Step 2: Расширь inventory тестами**

Run:

```bash
rg -n "buy_sl[0-9]+_tp[0-9]+|sell_sl[0-9]+_tp[0-9]+|TB_TARGET_NAMES|tb_outcome|_classify_tb_outcome" tests/ --type py
```

Expected:
- Получен список тестов, которые тоже должны соблюдать float-конвенцию. Добавь в **TB_LABEL_CONSUMERS_TESTS**.

- [ ] **Step 3: Создай скелет inventory CSV**

Создай файл `ML/reports/label_convention_audit_inventory.csv` с заголовком:

```csv
file;line;snippet;risk;verdict;notes
```

Expected:
- Файл существует и пуст (только заголовок). Будет дополняться в Task 3.

- [ ] **Step 4: Skip-list — что НЕ аудитим**

Запиши в scratchpad явный skip-list и причину:

```text
- MT/**/*.mq4, MT/**/*.mqh        — MQL runtime, своя int-схема
- docs/**, wiki/**                — документация, не код
- docs/archive/**                 — архив
- ML/baseline/**                  — не использует TB-лейблы
- entry_path_*                    — int-классы 0..5, другая семантика
- tests/test_entry_path_*         — то же
```

Expected:
- Skip-list зафиксирован, в Task 3 эти пути не trigger-ят findings.

---

### Task 3: Static Audit — Grep Patterns Per Risk Category

Для каждого Step ниже: запусти команду, для **каждой** строки результата открой файл по строке ±10, классифицируй по rubric из Task 1 Step 4, и впиши строку в `ML/reports/label_convention_audit_inventory.csv`. Если паттерн ложно-положительный — risk=`R8 ok` с короткой нотой почему.

**Files:**
- Read: все из `TB_LABEL_CONSUMERS`
- Modify: `ML/reports/label_convention_audit_inventory.csv` (append-only)

- [ ] **Step 1: R1 — int(...) над outcome/label/result/target**

Run:

```bash
rg -n "int\(\s*[a-zA-Z_]*outcome|int\(\s*[a-zA-Z_]*label|int\(\s*[a-zA-Z_]*result|int\(\s*[a-zA-Z_]*target|int\(\s*[a-zA-Z_]*tb_|int\(\s*[a-zA-Z_]*barrier|int\(\s*y\b|int\(\s*y_true|int\(\s*y_tb" \
  --type py \
  -g '!tests/test_entry_path_*' \
  -g '!ML/baseline/**' \
  -g '!docs/**'
```

Expected:
- Для каждой строки определи: имя переменной — это TB-лейбл (`buy_sl*_tp*` или производное от `y_tb` / `outcomes` / `outcome` из TB-симулятора)? Если да — это **R1 int_cast** и требует Task 4 dynamic check. Если переменная — это `entry_path` class label или индекс — `R8 ok`.

- [ ] **Step 2: R2 — loss_mask = ~win_mask (или эквивалент)**

Run:

```bash
rg -n "loss_mask\s*=\s*~|losses?\s*=\s*[a-zA-Z_]+\s*-\s*wins?|loss\s*=\s*total\s*-\s*win|loss\s*=\s*[a-zA-Z_]+\s*-\s*wins?" \
  --type py
```

Также проверь руками:

```bash
rg -n "win_mask|loss_mask|timeout_mask" --type py
```

Expected:
- **Известный кандидат:** `ML/tb_signal_logic.py:120-122` — `loss_mask = ~win_mask`, при том что `timeout_mask = outcomes == 0.5` определён, но в `loss_mask` не вычитается. Это **R2 not_win_is_loss**, требует dynamic check в Task 4 Step 2.
- Для каждой остальной находки: проверь, что losses не включают timeouts. Если включает — R2.

- [ ] **Step 3: R3 — binary equality on TB columns**

Run:

```bash
rg -n "==\s*1(\.0)?\b|==\s*0(\.0)?\b|==\s*-1\b" --type py \
  -g '!tests/test_entry_path_*' \
  -g '!ML/baseline/**'
```

Expected:
- Для каждой строки: проверь, что левая часть — это TB-лейбл. Сравнение `== 1.0` корректно для TP-маски **только если** Timeout обрабатывается отдельной маской. `== 0` без отдельной обработки 0.5 — **R3 binary_eq**.
- Особо проверь `ML/tb_signal_logic.py:120-121` — там `outcomes == 1.0` и `outcomes == 0.5` явные, это часть R2-баги, не отдельный R3.

- [ ] **Step 4: R4 — truthiness over outcome**

Run:

```bash
rg -n "if\s+outcome\b|if\s+not\s+outcome\b|bool\(\s*outcome|if\s+result\s*:\s*$|if\s+label\s*:\s*$" \
  --type py
```

Expected:
- `if outcome:` поверх float `{0.0, 0.5, 1.0}` — `0.0` falsy, `0.5` и `1.0` truthy → SL уходит в else вместе с «нет данных». Это **R4 truthiness**.

- [ ] **Step 5: R5 — sign / `> 0` over outcome**

Run:

```bash
rg -n "np\.sign\(\s*[a-zA-Z_]*outcome|np\.sign\(\s*[a-zA-Z_]*label|outcome\s*>\s*0|outcome\s*<\s*0|label\s*>\s*0\.5|label\s*<\s*0\.5" \
  --type py
```

Expected:
- `np.sign(0.5) == 1.0` — Timeout сольётся с TP. Любая такая находка по TB-лейблу — **R5 sign_assumption**.

- [ ] **Step 6: R6 — dtype drift при чтении CSV**

Run:

```bash
rg -n "astype\(\s*int|astype\(\s*np\.int|astype\(\s*['\"]int" --type py \
  -g '!tests/test_entry_path_*' \
  -g '!ML/baseline/**'
```

Expected:
- Любой `astype(int)` поверх колонки `buy_sl*_tp*` / `sell_sl*_tp*` или над `y_tb` тензором — **R6 dtype_drift**, конверсия 0.5 → 0 теряется молча.
- В `ML/data_loader.py` обрати особое внимание на блок `TB targets: shape={y.shape}` (~line 684) и проверь dtype при загрузке.

- [ ] **Step 7: R7 — missing timeout branch**

Для каждого файла из `TB_LABEL_CONSUMERS` найди функции, которые принимают одно значение `outcome`/`label` и возвращают TP/SL/PnL. Проверь, что есть **явная** ветка для timeout (`0.5`).

Run:

```bash
rg -n "def .*(outcome|barrier|tb_|label)" --type py \
  -g '!tests/test_entry_path_*' \
  -g '!ML/baseline/**'
```

Expected:
- Каждая функция-классификатор имеет три ветки (TP, SL, Timeout) или явный assert на бинарный вход. Иначе — **R7 missing_timeout**.

- [ ] **Step 8: Зафиксируй inventory**

Run:

```bash
wc -l ML/reports/label_convention_audit_inventory.csv
sort -t';' -k4,4 ML/reports/label_convention_audit_inventory.csv | head -n 50
```

Expected:
- Inventory содержит **все** найденные паттерны, отсортированы по risk-категории
- Каждый non-`R8` finding имеет файл:строку и одну строку snippet

Stop condition:
- Если ни одна команда из Step 1–7 не вернула вообще ничего (и при этом TB-консьюмеров много) — это подозрительно. Перепроверь, что `rg` запускался из корня репо и `--type py` активен. Не закрывай Task 3 без хотя бы одного non-`R8` или явного письменного объяснения «всё чисто».

---

### Task 4: Dynamic Audit — Reproduce Each Suspected Bug

Для каждого finding с risk ∈ {R1, R2, R3, R4, R5, R6, R7} построй **минимальный numerical reproducer**: маленький synthetic dataset, прогон через подозрительную функцию, сравнение результата с ожидаемым по float-канону.

**Files:**
- Read: каждый файл с non-`R8` finding
- Create: временный pytest файл `tests/test_label_convention_audit.py` (удалить в Task 6, если не понадобится постоянно)

- [ ] **Step 1: Каркас reproducer-тестов**

Создай `tests/test_label_convention_audit.py`:

```python
"""Temporary audit harness — verifies TB float-label handling.

Removed at stage close if no permanent reproducers needed.
"""
import numpy as np
import pandas as pd

TP = 1.0
SL = 0.0
TIMEOUT = 0.5
```

Expected:
- Файл существует, импортируется без ошибок: `./.venv/bin/python -m pytest tests/test_label_convention_audit.py -q` → 0 collected (пока).

- [ ] **Step 2: Reproducer для known suspect — `ML/tb_signal_logic.py` evaluate_rule**

Добавь тест, который вызывает `ML.tb_signal_logic.evaluate_rule` (или ближайшую публичную функцию, которая использует `loss_mask = ~win_mask`) на synthetic `df_signals` + `y_true_raw`, где явно стоят 1 TP, 1 SL и 1 Timeout с разными `tp_atr` / `sl_atr`. Проверь:

```python
assert result["wins"] == 1
assert result["losses"] == 1            # NOT 2 — timeout не должен считаться loss
assert result["timeouts"] == 1
assert result["loss"] == sl_atr_of_sl_row   # NOT sl_atr_of_sl_row + sl_atr_of_timeout_row
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_label_convention_audit.py::test_tb_signal_logic_loss_excludes_timeout -q
```

Expected:
- Тест **падает** на текущем коде → подтверждает R2-баг
- Если тест зелёный — внимательно перечитай `evaluate_rule`: возможно, `loss_mask` где-то в цепочке скорректирован. Перепиши тест ещё жёстче. Если всё-таки baseline корректен — переведи finding в `R8 ok` с пояснением в notes.

- [ ] **Step 3: Reproducer для каждого R1/R3/R4/R5/R6/R7 finding**

Для каждой строки из inventory с такими risk-категориями добавь отдельный test:
- input — synthetic frame с одной TP, одной SL, одной Timeout строкой
- expected — посчитай руками что должна вернуть функция при float-каноне
- assert — точное равенство

Run после каждого нового теста:

```bash
./.venv/bin/python -m pytest tests/test_label_convention_audit.py -q
```

Expected:
- Каждый тест либо **падает** (подтверждает баг — переходим к Task 5) либо **зелёный** (false positive — обновляем inventory на `R8 ok` с notes=«reproducer green»)

- [ ] **Step 4: Зафиксируй верстку findings**

Обнови `ML/reports/label_convention_audit_inventory.csv`: для каждой строки колонка `verdict` принимает одно из:

```text
confirmed_bug      — reproducer падает, нужен fix
false_positive     — reproducer зелёный, статический паттерн безопасен
needs_review       — нет reproducer (например, callsite отсутствует), оставить как наблюдение
```

Expected:
- Каждая non-`R8` строка имеет verdict
- Количество `confirmed_bug` записано в scratchpad — это объём работы Task 5

Stop condition:
- Если `confirmed_bug == 0` — пропусти Task 5, переходи сразу к Task 6 и в отчёте явно укажи «no fixes required, reproducer-tests confirm safety».

---

### Task 5: Apply Minimal Fixes (only for confirmed bugs)

**Files:**
- Modify: только файлы из inventory с `verdict=confirmed_bug`
- Modify: соответствующие тесты в `tests/`

- [ ] **Step 1: Fix `ML/tb_signal_logic.py` (если confirmed)**

Если Task 4 Step 2 подтвердил баг — изменения **минимальные**:

```python
# было:
loss_mask = ~win_mask

# стало:
loss_mask = outcomes == 0.0
# (timeout_mask уже определён выше)
```

Также проверь, что `losses = int(loss_mask.sum())`, `wins`, `timeouts` в сумме дают `trades`. Добавь assert в саму функцию:

```python
assert wins + losses + timeouts == trades, "TB outcome partition must cover all rows"
```

Expected:
- После фикса reproducer-тест из Task 4 Step 2 становится зелёным
- Существующие TB-тесты остаются зелёными:
  ```bash
  ./.venv/bin/python -m pytest tests/test_triple_barrier_*.py -q
  ```
- **Не трогай** TB selected rule, JSON-артефакты, `theta`, `min_ev` — это другой scope

- [ ] **Step 2: Numerical impact estimate для `ML/tb_signal_logic.py`**

Если фикс был — пересчитай benchmark на frozen `tb_selected_rule.json`:

```bash
./.venv/bin/python -m ML.benchmark_triple_barrier_mt4_execution --rule ML/reports/tb_selected_rule.json --split validation
./.venv/bin/python -m ML.benchmark_triple_barrier_mt4_execution --rule ML/reports/tb_selected_rule.json --split test
```

(Если такая команда не существует ровно так — найди реальную точку входа `rg -n "tb_signal_logic" --type py` и используй её.)

Expected:
- Сравни PF / win_rate с числами из `docs/reports/2026-04-12-tb-verdict.md` (validation PF=4.33, test PF=1.28)
- Если расхождение незначительное (< 1% по PF) — фикс косметический, отметь это в отчёте
- Если расхождение **меняет verdict** (например, validation PF падает с 4.33 до 1.5) — это критическое открытие, **остановись**, эскалируй пользователю до закрытия Task 6, потому что меняется выводная часть `tb-verdict.md`

- [ ] **Step 3: Применить остальные confirmed fixes по тому же шаблону**

Для каждого оставшегося `confirmed_bug` finding:
1. минимальный код-фикс (только то, что чинит репродуктор)
2. reproducer-test становится зелёным
3. полный TB suite остаётся зелёным
4. numerical impact зафиксирован

Expected:
- После всех фиксов:
  ```bash
  ./.venv/bin/python -m pytest tests/test_triple_barrier_*.py tests/test_label_convention_audit.py -q
  ```
  даёт all green
- Никакой не-TB файл не модифицирован

Stop condition:
- Если фикс затрагивает `processing/label_signals.py` сам по себе (т.е. меняет канон) — **немедленно остановись**. Аудит не имеет права менять source-of-truth для лейблов.

---

### Task 6: Promote Reproducer Tests Or Discard

**Files:**
- Modify or Delete: `tests/test_label_convention_audit.py`

- [ ] **Step 1: Reшение по каждому reproducer-тесту**

Для каждого теста в `tests/test_label_convention_audit.py`:
- Если он соответствует **постоянному инварианту** (например, «losses не включают timeouts») — **оставить навсегда**, переименовать осмысленно, перенести в более подходящий файл (например, в `tests/test_triple_barrier_mt4_execution.py` или новый `tests/test_tb_signal_logic.py`)
- Если он был только подтверждением частного бага и инвариант уже покрыт другим тестом — удалить
- Если ни одно из двух — оставить в `tests/test_label_convention_audit.py` как permanent guard, переименовать файл в `tests/test_tb_label_invariants.py`

Expected:
- Не остаётся файла с временным именем `test_label_convention_audit.py`
- Все permanent reproducer-тесты находятся в осмысленно названных файлах и зелёные

- [ ] **Step 2: Финальный full TB pytest pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_triple_barrier_mt4_execution.py \
  tests/test_triple_barrier_first_touch.py \
  tests/test_triple_barrier_calibration.py \
  tests/test_triple_barrier_training.py \
  tests/test_signal_tracer_tb.py \
  tests/test_generate_signals_research.py \
  tests/test_tb_label_invariants.py 2>/dev/null \
  -q
```

Expected:
- All green. Если test_tb_label_invariants.py не существует (Task 6 Step 1 решил перенести тесты в существующие файлы) — убери его из команды.

---

### Task 7: Audit Report And Stage Close

**Files:**
- Create: `ML/reports/label_convention_audit.md`
- Create: `docs/reports/2026-04-13-label-convention-audit.md`
- Modify: `CHANGELOG.md` (только при confirmed fixes)
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/log.md`

- [ ] **Step 1: Аудит-отчёт**

Создай `ML/reports/label_convention_audit.md` со строгой структурой:

```md
# Label Convention Audit — TB float labels

> Date: 2026-04-13
> Trigger: bug в `ML/triple_barrier_mt4_execution.py` (исправлено 2026-04-12), систематическая проверка остальных consumer-ов.
> Canonical convention: `1.0=TP, 0.0=SL, 0.5=Timeout`, source `processing/label_signals.py:919`.

## Inventory

Полный inventory: `ML/reports/label_convention_audit_inventory.csv`.

| risk | total | confirmed_bug | false_positive | needs_review |
|------|------:|--------------:|---------------:|-------------:|
| R1 int_cast | … | … | … | … |
| R2 not_win_is_loss | … | … | … | … |
| ... | | | | |

## Confirmed Bugs

Для каждого:
- file:line
- природа
- numerical impact (с точными до/после)
- fix (1-3 строки diff)
- покрытый тест

## False Positives Of Note

Паттерны, которые статически выглядели подозрительно, но семантически безопасны. Краткое объяснение почему — чтобы будущий аудит не тратил на них время.

## Residual Risk

Что **не** покрыто этим аудитом:
- MQL-сторона (отдельная int-конвенция в рантайме)
- (что-то ещё, если применимо)

## Verdict

Один из:
- `clean` — багов не найдено
- `fixed` — баги найдены и исправлены, тесты добавлены, выводы предыдущих стадий не меняются
- `fixed_with_revision` — баги исправлены, выводы как минимум одной предыдущей стадии нужно пересмотреть (перечислить какие)
```

Expected:
- Отчёт содержит все 5 секций
- Verdict — одна из трёх строк, без soft-формулировок

- [ ] **Step 2: Stage report**

Создай `docs/reports/2026-04-13-label-convention-audit.md` по шаблону `docs/reports/2026-04-12-tb-verdict.md` с секциями: Context, What Was Done, Changed Files, Verification, Results, Conclusions, Limitations, Next Step, Related Materials.

Expected:
- Stage report ссылается на `ML/reports/label_convention_audit.md` и `ML/reports/label_convention_audit_inventory.csv`
- Содержит точные команды, которые реально выполнялись
- Conclusions цитирует verdict из аудит-отчёта дословно

- [ ] **Step 3: CHANGELOG entry (только при `verdict ∈ {fixed, fixed_with_revision}`)**

Если verdict == `clean` — **не** добавляй запись в CHANGELOG (правило `CLAUDE.md`: doc-only / no behavior change ⇒ нет changelog).

Если есть фиксы — добавь одну запись формата:

```md
## [2026-04-13] — Label Convention Audit: TB float-labels

### Исправлено
- `<file>`: <короткое описание> (см. `docs/reports/2026-04-13-label-convention-audit.md`)

### Результаты
- `<file>` numerical impact: <до → после>

### Вывод
<verdict + одна фраза почему>
```

Expected:
- CHANGELOG обновлён ровно тогда, когда были реальные изменения в behavior

- [ ] **Step 4: Update CONTEXT_HANDOFF.md**

Замени блок `Open Risks` строки про `Label convention risk` на актуальное состояние:
- если `clean` или `fixed` — пометить риск как `closed: 2026-04-13 — audit verdict <X>`
- если `fixed_with_revision` — оставить как **open** с указанием стадии, чьи выводы пересматриваются

Также обнови `Last Completed Stage` и `Next Step` если нужно.

Expected:
- Handoff отражает реальное состояние после аудита

- [ ] **Step 5: wiki/log.md entry**

Добавь одну строку в `wiki/log.md`:

```md
- 2026-04-13 — label_convention_audit: <verdict>, inventory=<N>, confirmed_bugs=<K>. report=docs/reports/2026-04-13-label-convention-audit.md
```

Expected:
- wiki/log.md содержит запись об аудите. **Не** создавай новую wiki research-страницу — это операционный аудит, не линия исследования.

- [ ] **Step 6: Final clean pass**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q -k "triple_barrier or tb_label or label_convention"
git status --short
```

Expected:
- Все TB-связанные тесты зелёные
- В working tree только то, что было осознанно изменено: inventory CSV, аудит-отчёт, stage report, possibly fix-файлы и tests, CHANGELOG/HANDOFF/wiki log. Никаких случайных правок в `ML/baseline/`, `entry_path_*`, MT4-сторону, archive.

---

## Self-Review Checklist

- Аудит **не меняет** label convention в `processing/label_signals.py`.
- Аудит **не ретюнит** `tb_selected_rule.json`, не пересматривает frozen verdict.
- Каждое изменение кода обосновано **падающим репродуктором до фикса** и **зелёным после**.
- Inventory покрывает все 7 risk-категорий (R1..R7), даже если в категории 0 находок.
- Каждый non-`R8` finding имеет verdict ∈ {confirmed_bug, false_positive, needs_review}.
- Verdict аудита — одна из трёх строк: `clean` / `fixed` / `fixed_with_revision`.
- CHANGELOG обновлён тогда и только тогда, когда был реальный fix.
- CONTEXT_HANDOFF.md отражает финальный статус риска `Label convention risk`.
- Если фикс в `tb_signal_logic.py` материально меняет числа из `2026-04-12-tb-verdict.md` — это эскалировано пользователю до закрытия стадии, а не молча зафиксировано.
- MQL-сторона (`MT/MQL4/Include/lib_ML_Signal_TB.mqh`) **не** трогается этим планом.
- Нет рефакторинга «заодно» в файлах с findings.
