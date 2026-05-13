# Context Handoff

Дата: 2026-05-13.

## Текущий этап

Идёт подготовка SoSimple к реальному счёту. Старый unsafe take/skip online
watcher больше не является основным production diagnostic. Основной watcher
переведён на live-safe candidate:

`entry_path_v1_live_safe + A @ 7.5%`

Цель M5 diagnostic остаётся прежней: проверить механику
`MT4 -> Nero.csv -> watcher -> ml_signals.csv -> MT4 -> ml_trade_events.csv`,
а не прибыльность. Частый режим должен быть явно помечен diagnostic-only.

## Git

Локальная ветка: `live-safe-entry-path-watcher`.

Не трогать `AGENTS.md` без явной просьбы пользователя.

## Что уже сделано

- `API.telemetry_signal_watcher` получил `--watcher-mode`.
  - default: `entry_path_v1_live_safe_online`;
  - legacy: `telemetry_frequency_v1_legacy` только с `--allow-unsafe-future-features`.
- Default paths теперь ведут в
  `ML/reports/entry_path_v1_live_safe/runtime/`.
- Entry-path runtime inference использует:
  - checkpoint seed 42 live-safe;
  - rule `ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json`;
  - `feature_profile=entry_path_v1_live_safe`;
  - `include_true_targets=False`.
- `API.export_entry_path_v1_signals` поддерживает metadata, append-to-MT4,
  threshold override и отдельный diagnostic all-rows stress export.
- Основной M5 high-frequency diagnostic:
  - флаг `--entry-path-score-threshold-override`;
  - использует тот же checkpoint, rule, feature profile;
  - сохраняет production gate `signal != 0`;
  - сохраняет направление из prediction/export frame;
  - пишет `diagnostic_only=true` в metadata;
  - production baseline остаётся `A @ 7.5%`.
- `--entry-path-diagnostic-all-rows` оставлен только как mechanical stress mode,
  не parity с production candidate.

## Итоги online/tester сверки 2026-05-12

Создан краткий отчёт:

- `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`.

Ключевой вывод: `ml_signals.csv` online/tester совпали, но старое online-исполнение
пропустило 6 входов на общей исполнимой части. Первые три подтверждены в
online MT4-логе как `requote ERROR-138`.

Стабильный закрытый срез `2026.05.12 00:10` -> `2026.05.12 13:05`:

- online: 67 закрытых сделок, PnL `-680.2`, матожидание `-10.1522`;
- tester: 68 закрытых сделок, PnL `-522.6`, матожидание `-7.6853`;
- парные 65 закрытых сделок: online `-745.0`, tester `-696.7`,
  разница матожидания `-0.7431`.

Главный вред дали пропущенные online-входы, а не расхождения PnL по парным
сделкам.

`ML/online_tester_reconciliation.py` обновлён:

- сравнение online/tester по `signal_time + direction`;
- `OPEN_FAILED` учитывается отдельным статусом;
- добавлены `--start-time` / `--end-time`;
- summary считает `closed_trades`, `signal_basis` и paired-метрики.

`OPEN_FAILED` уже реализован в `MT/MQL4/Include/lib_ML_Signal.mqh`; для старых
логов таких строк ещё нет, поэтому они видны как `missing_open`.

## Открытые вопросы

1. Проверить новый live-safe watcher на online M5 в tmux без
   `--allow-unsafe-future-features`.

2. Найден один вход с задержкой `65` минут:
   - ticket `1581716381`;
   - `BUY`;
   - signal_time `2026.05.11 22:55`;
   - entry_time `2026.05.12 00:00`;
   - spread `0.92`;
   - ATR `1.81`.

   Нужно понять, это стартовый/ночной эффект, задержка файла, ожидание цены, перезапуск, широкий спред или логическая ошибка.

3. Были `requote ERROR-138` при открытии/закрытии. Старый online/tester анализ
   показал, что часть входов из-за этого не открылась. В новом тесте нужно
   проверить, что такие случаи попадают в `OPEN_FAILED`, а не теряются.

4. `MAIL_SEND-706 ERROR-4060` встречается в логах, но относится к почте и не блокирует торговый тракт.

5. Прибыльность diagnostic режима не является критерием успеха текущего этапа.

## Runtime benchmark 2026-05-13

Тяжёлые intermediate CSV benchmark не оставлены в рабочем дереве; итоговые
числа зафиксированы ниже и в `docs/API/telemetry_signal_watcher.py.md`.

Production baseline `A @ 7.5%` на текущем M5-хвосте дал `0` ненулевых
сигналов: raw `Nero.csv` не даёт production `signal != 0` в проверенном окне.

Предыдущий all-rows stress benchmark (`top-N=5000/year`), не production parity:

| Window | Rebuild | Non-zero | Last time | Last signal |
|---:|---:|---:|---|---:|
| 1000 | 17.217s | 953 | 2026.05.11 22:35 | -1 |
| 100 | 3.541s | 98 | 2026.05.11 22:35 | -1 |
| 24 | 2.149s | 24 | 2026.05.11 22:35 | -1 |
| 1 | 2.084s | 1 | 2026.05.11 22:35 | -1 |

Полный rebuild `60178` строк остановлен после 5 минут без результата.
Для frozen training/offline контракта `vol_regime_24` считался как rolling ATR
по 24 строкам, но validation/test проверка показала `signal_mismatch_rows=0`
при runtime substitution `vol_regime_24 := ATR`.
Watcher больше не сканирует весь `Nero.csv` на каждом poll: при неизменном
`mtime` он сразу уходит в `IDLE`, а при rebuild читает последние строки
seek-чтением с конца файла. Default runtime window уменьшен до `1` строки.

## Следующий шаг

Продолжить с online-запуска live-safe diagnostic watcher:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher \
  --poll-interval-sec 1 \
  --heartbeat-sec 60 \
  --entry-path-score-threshold-override -0.50 \
  --verbose
```

После этого:

1. Провести online-тест несколько часов уже без unsafe watcher.
2. Запустить `ML.online_tester_reconciliation` по новому online/tester участку
   с явными `--start-time` / `--end-time`.
3. Разобрать задержку входа ticket `1581716381`, если она повторится вне края
   файла.
4. Перед финальным закрытием этапа сжать handoff ещё раз до актуального
   состояния, а подробные итоги перенести в `docs/reports/` и коротко в
   `CHANGELOG.md`.
