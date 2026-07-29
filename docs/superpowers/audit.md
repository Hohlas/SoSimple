# Аудит отчета `2026-07-29-fixed11-current-history-rerun`

Проверялся отчет `docs/reports/2026-07-29-fixed11-current-history-rerun.md` и только связанные с ним первоисточники: план, методология, JSON/CSV-артефакты, roadmap/changelog/handoff/wiki и скрипт сверки истории.

## 1. В отчете не раскрыты обязательные raw rows / signals / sample-size детали

- **Важность**: важно
- **Место**: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`, секции `Results` и `Split Disclosure`, строки 370-474
- **Суть проблемы**: отчет показывает количество сделок, но не показывает количество строк исходного locked-test input, число сигналов до/после фильтров и явный `sample_size_gate` по split. Для fixed11 это особенно важно, потому что текущий прогон оставляет `DATA/Nero_XAUUSD_test_labeled.csv` неизмененным, а меняет только OHLC-источник исполнения.
- **Доказательство**:
  - В отчете есть сделки: aggregate `trades 14507 -> 13039`, slot 1 `1196 -> 1091` на строках 382-406.
  - В `Split Disclosure` указаны путь и роль split, но нет raw rows / signals / sample-size gate: строки 466-474.
  - Методология требует это явно: `docs/methodology/16-reporting-audit.md:94` — отчет должен содержать количество raw rows, событий, сигналов и сделок после фильтров по каждому split; `docs/methodology/10-frozen-test-oos.md:30` требует `sample_size_gate` после фильтров.
- **Почему это важно**: без этих чисел следующий агент видит итоговые сделки, но не может быстро понять, сколько исходных locked-test строк было доступно, сколько сигналов отсеялось каждым правилом и не маскируется ли малый N.
- **Рекомендуемое исправление**: добавить в `Results` или `Split Disclosure` короткую таблицу:
  - `locked_test_raw_rows` для `DATA/Nero_XAUUSD_test_labeled.csv`;
  - число базовых сигналов BUY/SELL до фильтров, если runner это считает;
  - `n_trades` по каждому из 11 rules после фильтров;
  - явный вывод `sample_size_gate=PASS/DIAGNOSTIC_ONLY/UNKNOWN` и критерий.

## 2. Raw-data inventory для M5/H1 раскрыт неполно

- **Важность**: важно
- **Место**: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`, `Verification`/`Results`, строки 83-149 и 372-380
- **Суть проблемы**: отчет проверяет наличие, хэши и совпадение с HST, но не фиксирует в самом отчете полный минимум raw-data inventory для текущих H1/M5: `symbol`, broker/source, timezone, price convention и статус использования M5 как `execution_ordering_only`.
- **Доказательство**:
  - Отчет приводит пути и хэши на строках 93-117, а HST-сверку на строках 119-149 и 372-380.
  - Методология `docs/methodology/01-raw-data-inventory.md:35-43` требует для младшего таймфрейма путь, CSV contract, symbol, broker/source, timezone, price convention, frequency/gaps, соответствие H1 source и статус использования.
  - Методология `docs/methodology/12-backtest-costs.md:96-98` понижает execution-выводы до `DIAGNOSTIC_ONLY`, если source/timezone/price convention не доказаны. Отчет верно держит `DIAGNOSTIC_ONLY`, но сам набор сведений не раскрывает.
- **Почему это важно**: текущий этап как раз отделяет эффект смены OHLC. Без явного source/timezone/price convention нельзя отличить реальную смену истории от смены соглашения о цене.
- **Рекомендуемое исправление**: добавить в `Context` или `Results` блок `OHLC inventory`:
  - `symbol=XAUUSD`, `timeframe=H1/M5`;
  - producer: `MT/MQL4/Scripts/ExportOHLC.mq4`, если это подтвержденный producer;
  - broker/source: `MetaQuotes-Demo` или `UNKNOWN`, если не доказано;
  - timezone: `UNKNOWN` или фактически подтвержденное значение;
  - price convention: `UNKNOWN` или подтвержденное значение;
  - `M5 usage=execution_ordering_only, not feature_source`;
  - неполные края: H1 CSV до `2026-07-29 13:00`, HST до `2026-07-28 18:00`; M5 CSV до `2026-07-29 14:25`, HST до `2026-07-28 07:55`.

## 3. Утверждение про pre/post hash equality для десяти путей недостаточно воспроизводимо

- **Важность**: улучшение
- **Место**: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`, строки 152-168
- **Суть проблемы**: отчет утверждает `Pre/post hashes matched exactly for all ten paths`, но в отчете рядом сохранены только пять observed hashes для OHLC/labeled input. Хэши старого JSON/trades есть в `comparison.json`, а хэши source rules/source artifact есть в current JSON, но хэши трех runner-файлов в структурных артефактах не сохранены.
- **Доказательство**:
  - Строки 152-165 перечисляют 10 путей, строка 167 утверждает, что pre/post совпали.
  - `ML/reports/fractal0_fixed11_current_history_comparison.json` содержит хэши old/current JSON/trades; проверка командой показала совпадение текущих файлов:
    `old_json_sha256=True`, `old_trades_sha256=True`, `current_json_sha256=True`, `current_trades_sha256=True`.
  - `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json` содержит `source_rules_csv_sha256` и `source_artifact_sha256`, но не содержит хэши:
    `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`,
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py`,
    `ML/baseline/benchmark_fractal0_entry_quality_filter.py`.
  - Методология требует paths/hashes/rules/checkpoints: `docs/methodology/16-reporting-audit.md:31`; ключевые числа и источники должны быть сверяемы: `docs/methodology/16-reporting-audit.md:96-97`.
- **Почему это важно**: если runner-файл позже изменится, отчет уже не докажет, каким именно кодом был сделан rerun. `git diff` после факта не заменяет сохраненный хэш кода на момент прогона.
- **Рекомендуемое исправление**: добавить в отчет таблицу `pre/post hash check` с 10 путями и хэшами либо добавить эти хэши в current-history JSON. Если pre-hashes не были сохранены, смягчить утверждение до фактически проверяемого: какие хэши сохранены, а для runner-кода указать `git diff -- ...` на момент выполнения без заявления о сохраненном pre/post equality.

## 4. В `Changed Files` не указан обновленный manifest, хотя отчет говорит, что он пересобран

- **Важность**: улучшение
- **Место**: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`, строки 31-34 и 63-81
- **Суть проблемы**: в `What Was Done` написано, что пересобран `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`, но в `Changed Files` этот файл отсутствует.
- **Доказательство**:
  - Пересборка manifest заявлена на строках 31-34.
  - В списке измененных файлов строки 65-73 и generated artifacts строки 77-81 manifest не указан.
  - Команда чтения manifest подтвердила, что он содержит новые секции `current_data_h1_vs_hst`, `current_m5_vs_hst_m5`, `previous_python_h1_vs_current_data_h1` и статус `DIAGNOSTIC_ONLY`.
- **Почему это важно**: следующий агент может не понять, что `fill_chronology_manifest.json` является частью результата этого этапа, а не только сторонним входом.
- **Рекомендуемое исправление**: добавить `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json` в `Changed Files` или отдельный список `Updated supporting artifacts`.

## 5. `Multiple Testing Context` не раскрывает cumulative search budget

- **Важность**: улучшение
- **Место**: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`, строки 43-61
- **Суть проблемы**: отчет хорошо фиксирует текущий диагностический бюджет (`new_rules=0`, `new_models=0`, `new_thresholds=0`), но не раскрывает накопленный контекст поиска, из которого появились fixed11 rules. Есть ссылки на связанные материалы, но нет краткого `cumulative_search_budget` или ссылки на конкретный budget-id/отчет, где он зафиксирован.
- **Доказательство**:
  - Строки 45-58 содержат только текущий бюджет rerun.
  - Методология `docs/methodology/16-reporting-audit.md:22` требует `current` и `cumulative search budget` для Multiple Testing Context.
  - Отчет ссылается на старые материалы на строках 494-502, но не связывает их с накопленным бюджетом.
- **Почему это важно**: fixed11 не возник из одного запуска; без накопленного контекста легко забыть, что текущий сильный PF/PnL является частью длинной исследовательской цепочки, а не независимым новым доказательством.
- **Рекомендуемое исправление**: добавить одну строку в `Multiple Testing Context`, например:
  `cumulative_search_budget=inherited from fixed11 locked-test / candidate audit / mutual-correlation pruning reports; no new search in this rerun`.
  Лучше указать конкретные связанные отчеты и, если есть, идентификатор budget-а.

## Проверенные утверждения без замечаний

- Числа в таблицах `Aggregate fixed11`, `Retained slot 1` и same-H1 блоке совпадают с `ML/reports/fractal0_fixed11_current_history_comparison.json` и `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`.
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json` содержит `verdict=DIAGNOSTIC_ONLY`, `decision=FIXED11_CURRENT_HISTORY_DIAGNOSTIC_ONLY`, `stage_status=DIAGNOSTIC_ONLY`, `allowed_max_verdict=DIAGNOSTIC_ONLY`.
- `comparison.json` содержит 11 rules и хэши old/current JSON/trades; текущие хэши файлов совпадают с записанными в `comparison.json`.
- H1/M5 расхождения с HST действительно находятся на последней строке соответствующего HST:
  - H1: `2026-07-28 18:00:00`, HST last `2026-07-28 18:00:00`;
  - M5: `2026-07-28 07:55:00`, HST last `2026-07-28 07:55:00`.
- Roadmap, changelog, handoff и wiki не повышают статус выше `DIAGNOSTIC_ONLY` и не называют current-history rerun MT4 parity proof.

## Команды аудита

```bash
graphify query "fixed11 current history rerun report plan methodology artifacts" --budget 1500
rg -n "fixed11-current-history|current-history|current_history|DIAGNOSTIC_ONLY|candidate_check_required|fractal0_fixed11_current_history" docs wiki CHANGELOG.md CONTEXT_HANDOFF.md ML/reports -g '*.md' -g '*.json'
sed -n '1,260p' docs/reports/2026-07-29-fixed11-current-history-rerun.md
sed -n '261,560p' docs/reports/2026-07-29-fixed11-current-history-rerun.md
sed -n '1,220p' docs/methodology/README.md
sed -n '1,220p' docs/methodology/01-raw-data-inventory.md
sed -n '1,180p' docs/methodology/10-frozen-test-oos.md
sed -n '1,180p' docs/methodology/12-backtest-costs.md
sed -n '1,220p' docs/methodology/16-reporting-audit.md
sha256sum ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json ML/reports/fractal0_fixed11_current_history_comparison.json ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv ML/reports/fractal0_fixed11_rich_entry_locked_test.json ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv
./.venv/bin/python - <<'PY'
import json, hashlib
from pathlib import Path
comp=json.loads(Path('ML/reports/fractal0_fixed11_current_history_comparison.json').read_text())
for key,pathkey in [('old_json_sha256','old_json_path'),('old_trades_sha256','old_trades_path'),('current_json_sha256','current_json_path'),('current_trades_sha256','current_trades_path')]:
    p=Path(comp[pathkey])
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    print(key, comp[key], h, comp[key]==h)
PY
./.venv/bin/python - <<'PY'
import pandas as pd
p='ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv'
df=pd.read_csv(p, sep=';')
rule='rank05_time_only_linear_target_entry_avoid_sl_top30'
sub=df[df.rule_id==rule].copy()
print('rows', len(df))
print('rules', df['rule_id'].nunique())
print('slot1_trades', len(sub))
print('slot1_pnl', round(float(sub.pnl_r.sum()),6))
print('slot1_hold0', int((sub.hold_bars==0).sum()))
print('slot1_same_fill_exit', int((pd.to_datetime(sub.fill_time)==pd.to_datetime(sub.exit_time)).sum()))
print('slot1_hold0_reasons', sub[sub.hold_bars==0].close_reason.value_counts().to_dict())
print('slot1_hold0_pnl', round(float(sub[sub.hold_bars==0].pnl_r.sum()),6))
PY
```
