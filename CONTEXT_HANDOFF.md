# Context Handoff

Короткий baton для следующего агента. Историю этапов читать в `docs/reports/`, краткую хронологию - в `CHANGELOG.md`, синтез - в `wiki/research/`.

## Current Stage

Этап `telemetry_frequency_demo_launch` дополнен 2026-04-28 архитектурным снимком MQL runtime, 2026-04-29 online inference contract hardening и 2026-05-05 live-safe ML audit с `entry_path_v1` live-safe retrain и повторной quantile-проверкой поверх live-safe baseline.

Канонические отчёты:
- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
- [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md)

Что было зафиксировано 2026-04-27:
- high-frequency diagnostic export `telemetry_frequency_v1_highfreq500`;
- `ml_signals.csv` atomic export/copy и runtime reload в MT4;
- multi-position diagnostic режим в существующей `EXPERT::ML_TRADE()`;
- structured MQL logs `MLP BUY/SELL/CLOSE/SKIP`;
- broker-side SL/TP закрытия логируются как `MLP CLOSE ... source=broker_history`;
- daily reconciliation CLI `ML/telemetry_daily_reconciliation.py`;
- документация online pipeline и `#.csv` contract;
- watcher переведён в наблюдаемый `tmux`-режим с heartbeat в stdout;
- `header-only` `Nero.csv` считается штатным ожиданием первого бара.

Что добавлено 2026-04-28:
- MQL expert при старте прогревает `PIC()` по истории через `RECOUNT_HISTORY()`;
- `POC_SIMPLE()` теперь вызывается внутри `PIC()`, чтобы historical warmup и online bar-by-bar проход совпадали;
- `Nero.csv` локально пересобирается по истории и дописывается при новых уровнях;
- watcher использует `runtime_input_snapshot.csv` из хвоста `Nero.csv` (`--max-runtime-rows`, default `12000`), а не весь файл в RAM;
- full-vs-12000 проверка на хвосте дала `signal_mismatch_rows=0`, `pred_*` отличаются только на уровне float-шума (`<=3.37e-7`);
- найдено текущее расхождение online pipeline: live `Nero.csv` содержит `signal=0` и `predict=0` во всех строках;
- причина: offline `predict` формируется через future-derived разметку (`predict = -back * direction`) и не может честно вычисляться в live-момент;
- diagnostic online-export переведён на текущий доступный источник направления: `fractal0.direction` с обратным знаком (`-1 -> BUY`, `1 -> SELL`);
- локальная проверка после изменения дала `nonzero_rows=500`, `buy_rows=444`, `sell_rows=56`, `duplicate_time_rows=0`, `same_time_opposite_signal_groups=0`.

Что добавлено 2026-04-29:
- watcher строит raw `runtime_input_snapshot.csv`, затем
  `runtime_input_preprocessed.csv` через sorting + validation +
  `normalize_rowwise(verbose=False)`;
- `API.api_server` использует тот же `preprocess_online_frame()`, а не прямой
  `normalize_rowwise()`;
- найден критичный ML-contract разрыв: legacy `original_baseline` обучался и
  проверялся с future-derived row features (`predict`, `ret_*`, `fav_*`,
  `adv_*`) как входом модели;
- `API.telemetry_signal_watcher` теперь блокирует
  `original_contour/original_baseline` online по умолчанию через
  `OnlineInferenceContractError`;
- `--allow-unsafe-future-features` оставлен только для старой механической
  диагностики связи MT4 -> Python -> CSV -> MT4.

Главный вывод:
- механическая цепочка diagnostic-контурa была доведена до наблюдаемого вида,
  но legacy ML-контракт `original_baseline` больше не считается online-ready;
- свежий MT4 tester proof за 2025 дал `critical_mismatch_count=0`;
- `missing_close_count=1` объясняется открытой позицией на конце периода;
- прибыльный tester result не считать production-доказательством качества стратегии.
- online diagnostic больше не зависит от future-derived `predict` для
  направления, но сам checkpoint `original_baseline` требует future-derived
  row features и поэтому заблокирован для ML-корректной online-проверки;
- перед production-переходом нужен live-safe retrain: один и тот же набор
  признаков в training/test и online, без future-derived входов.
- live-safe ML audit зафиксировал verdict:
  `quality`, `frequency`, `original_plus_path`, `entry_path_v1`,
  `entry_path_v1_quantile` = `FAIL`.
- legacy export replay выполнен по старым prediction/rule входам:
  старый путь генерации сигналов воспроизводится для всех пяти систем, но
  помечен `diagnostic_only=true` и не доказывает online-valid качество.
- source audit закрыл `ret_dir_atr_lag1` как future-derived:
  это `ret_6_dir_atr.shift(1)`, а `ret_6_dir_atr` строится по будущим барам
  в `label_entry_path_targets()`.
- повторная source-сверка подтвердила: Python `predict`, `ret_*`, `fav_*`,
  `adv_*` считаются после `Nero.csv` по будущим барам; MT-origin `Up/Dn` в
  `Nero.csv` отделены от этих Python labels и сами по себе не считаются
  leakage, если известны на текущем баре.
- audit evidence лежит в `ML/reports/live_safe_ml_audit/`.
- live-safe retrain `entry_path_v1_live_safe` удалил `ret_dir_atr_lag1` и дал:
  validation `ret_pearson_r=0.2681`, frozen test PF `3.6567`,
  sequential test `25` trades, PF `2.3419`, win rate `68.00%`.
- multi-seed follow-up (`7`, `17`, `42`, `77`, `123`): median sequential PF
  `2.3419`, min `1.5171`, max `4.5985`; PF > 2.0 у `3/5`, PF <= 1.0 у `0/5`.
- `API.export_entry_path_v1_signals` теперь поддерживает `A`, `B`,
  `B_no_path6`; для `B` / `B_no_path6` применяется frozen
  validation-нормировка из `validation_csv` внутри rule JSON. Все пять
  `entry_path_v1_live_safe` seed теперь экспортируемы.
- вывод: прибыльность не сохранилась один в один, но система не развалилась.
  Результат живой, но переменный; перед MT4 parity нужно заморозить
  rule-family; exporter больше не является блокером.
- decision: для `entry_path_v1_live_safe` заморожен baseline `A`, потому что
  это самый простой вариант и он повторился в `3/5` seed. `B` / `B_no_path6`
  остаются исследовательскими вариантами, но не основным следующим путем.
- follow-up audit по `A`: как rule-family с per-seed validation threshold
  результат устойчивый (sequential PF `1.5171..4.1370`, median `2.8425`,
  PF > 2.0 у `4/5`, 21 sequential signal повторился во всех 5 seed).
- риск: точный seed-42 threshold `-0.131882885` не переносится на другие seed
  как универсальная шкала (sequential median PF `0.9032`). Production-кандидат
  сейчас - конкретный frozen seed `42` rule, а не любой retrained checkpoint с
  тем же численным порогом.
- review 2026-05-06 нашёл измеримое нарушение контракта нормализации:
  training `predict` входил в пул `front/back`, а online `predict=0`.
  Измерение на `Nero_predict_probe_labeled_temp.csv`: `front/back` менялись в
  `95.93%` строк, среднее изменение `0.0010`, максимум `0.166`.
- исправление: `normalize_rowwise(..., include_predict_in_front_back_pool=False)`
  и `processing/label_main.py --exclude-predict-from-front-back-pool`. Старый
  режим сохранён по умолчанию для legacy reproduction. До retrain на новых CSV
  `entry_path_v1_live_safe + A` остаётся кандидатом, но не готов к MT4 parity.
- `fractal*` в live-safe audit переведены из `UNKNOWN` в `PASS` для MT-origin
  полей из `Nero.csv`; это не распространяется на Python-added future labels.
- `entry_path_v1_quantile` повторно проверен поверх нового live-safe baseline:
  sequential PF > 2.0 у `4/5` seed, но сделок мало (`0..25`), один seed дал
  `0` sequential trades.
- n-boost candidate `lb_gt_m_q40` дал frozen test `35` trades, PF `32.4125`,
  sequential `14` trades, PF `48.7214`, но gate=`fail`, потому что
  `same_winner_ratio=0.60 < 0.80`.
- вывод по quantile: прибыльность не исчезла, но production-кандидатом слой
  пока считать нельзя; правило выбора нестабильно между seed.
- после фиксации baseline `A` quantile повторно сверен через n-boost:
  `lb_gt_m_q40` даёт frozen PF `32.4125` на `35` сделках и sequential PF
  `48.7214` на `14` сделках, но gate остаётся `fail` из-за
  `same_winner_ratio=0.60 < 0.80`. Decision: quantile оставить research-only.
- первый take/skip live-safe probe выполнен для `live_safe_baseline_seq50`
  (`seed=42`): старый single-tensor runner без `predict`, `ret_dir_atr_lag1`,
  `ret_*`, `fav_*`, `adv_*`; validation winner не найден, verdict=`reject`,
  лучший validation PF `1.5178` только на `3` сделках.
- вывод по take/skip baseline: старые `quality/frequency` результаты пока не
  сохранились после удаления future-derived row-признаков.
- уточнение по `Up/Dn`: если они пришли из MT в `Nero.csv` как накопленное
  состояние `lib_PIC`, считаем их live-safe; запрещены именно Python future
  labels (`predict`, `ret_*`, `fav_*`, `adv_*`, `ret_dir_atr_lag1`).
- добавлены режимы `live_safe_path`, `live_safe_geometry`,
  `live_safe_geometry_path`; полный `live_safe_path_seq50` нужно запускать на
  мощном сервере, потому что локально построение path/geometry признаков
  слишком долгое.
- серверный `live_safe_path_seq50` выполнен (`seed=42`, `torch_threads=16`):
  validation winner не найден, verdict=`reject`; лучший validation PF `0.9893`
  на `15` сделках, а при минимуме `6` сделок/год PF `0.6155`.
- серверный `live_safe_geometry_seq50` выполнен (`seed=42`,
  `torch_threads=16`): validation winner не найден, verdict=`reject`; лучший
  validation PF `0.5726` на `5` сделках, а при минимуме `6` сделок/год PF
  `0.4125`.
- вывод: добавление MT-накопленных `Up/Dn` path-признаков не восстановило
  take/skip прибыльность; geometry-вариант тоже не восстановил старую
  прибыльность; прямой live-safe rebuild старого take/skip семейства сейчас
  отклонён.
- после повторного retrain без `predict` в пуле нормализации выяснено:
  `entry_path_v1_live_safe` на правильном H1 источнике
  `MT/MQL4/Files/Nero_XAUUSD.csv` сохраняет качество модели
  (`ret_pearson_r` около `0.27`). Провал до `~0.004` был вызван тем, что
  текущий `MT/MQL4/Files/Nero.csv` содержит M5-строки, а `entry_path_v1`
  требует H1-время.
- локальный GPU seed 42 воспроизводится стабильно: sequential PF `2.4897`.
  Локальный CPU seed 42 и серверный CPU seed 42 тоже воспроизводимы внутри
  своего вычислительного пути, но выбирают другую верхушку сделок и дают
  слабый sequential PF (`~1.05..1.21`). Это не отменяет качества модели, но
  показывает чувствительность торгового фильтра к переобучению.
- для защиты от путаницы артефактов `ML.train` получил `--output-dir`: теперь
  checkpoint/result можно сохранять в отдельную папку seed/device запуска.
  JSON и checkpoint включают runtime metadata: seed, device, версии библиотек,
  deterministic flags и sha256 train/validation CSV.

## Next Step

1. Не делать MT4 parity пока пользователь держит этот этап на паузе.
2. Текущий следующий фокус - `entry_path_v1_live_safe` с замороженным baseline
   `A`. Перед MT4 parity нужно прогонять новые seed/device эксперименты только
   через `ML.train --output-dir ...`, затем экспортировать прогнозы из
   seed-specific checkpoint, а не из общего `ML/checkpoints/*_best.pt`.
3. Не продолжать прямой take/skip rebuild без новой узкой гипотезы: baseline,
   path и geometry варианты получили `reject`.
4. `entry_path_v1_quantile` сейчас не продвигать в production: после фиксации
   baseline `A` прибыльные участки есть, но rule selection нестабилен.
5. Чтобы не забыть системы: `quality`, `frequency`, `original_plus_path`,
   `entry_path_v1`, `entry_path_v1_quantile` теперь сведены в Audit Tracker
   внутри `docs/reports/2026-05-05-live-safe-ml-audit.md`.

## Read First

1. [`AGENTS.md`](AGENTS.md) - правила агента и карта источников.
2. [`docs/ML/ml_leakage_preflight_checklist.md`](docs/ML/ml_leakage_preflight_checklist.md) - обязательный leakage/preflight gate для всех ML test/MT4/online выводов.
3. [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md) - текущий verdict по прибыльным ML-системам и первый retrain без `ret_dir_atr_lag1`.
4. [`ML/reports/live_safe_ml_audit/`](ML/reports/live_safe_ml_audit/) - generated audit evidence.
5. [`ML/reports/entry_path_v1_live_safe/`](ML/reports/entry_path_v1_live_safe/) - retrain и multi-seed artifacts.
6. [`ML/reports/entry_path_v1_quantile_live_safe_baseline/`](ML/reports/entry_path_v1_quantile_live_safe_baseline/) - quantile retrain поверх live-safe baseline.
7. [`ML/reports/take_skip_live_safe_baseline/`](ML/reports/take_skip_live_safe_baseline/) - first take/skip live-safe baseline probe.
8. [`ML/reports/take_skip_live_safe_path/`](ML/reports/take_skip_live_safe_path/) - server-side take/skip live-safe path probe.
9. [`ML/reports/take_skip_live_safe_geometry/`](ML/reports/take_skip_live_safe_geometry/) - server-side take/skip live-safe geometry probe.
10. [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md) - итог online telemetry этапа.
11. [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md) - текущая MQL/runtime архитектура и открытый вопрос `signal/predict`.
12. [`docs/MT/trading_strategy.md`](docs/MT/trading_strategy.md) - online pipeline, `#.csv`, MQL logging.
13. [`docs/MT/ml_signal_integration.md`](docs/MT/ml_signal_integration.md) - MT4 `ml_signals.csv` contract.
14. [`docs/ML/telemetry_daily_reconciliation.py.md`](docs/ML/telemetry_daily_reconciliation.py.md) - daily reconciliation.

## Open Risks

- Legacy `original_baseline` нельзя считать online-ready: historical test был
  загрязнён future-derived входными признаками, а live `Nero.csv` этих признаков
  не имеет.
- `entry_path_v1` и `entry_path_v1_quantile` теперь `FAIL`, не `UNKNOWN`.
  Причина: `ret_dir_atr_lag1` доказан как future-derived, а quantile зависит
  от baseline score.
- `entry_path_v1_live_safe` проверен на пяти seed, но после review 2026-05-06
  требует retrain без `predict` в пуле нормализации `front/back`; до этого MT4
  parity откладывается.
- `entry_path_v1_quantile_live_safe_baseline` показал прибыльные участки, но
  n-boost gate не прошёл из-за нестабильности выбранного правила.
- `take_skip_live_safe_baseline` в первом seed не нашёл validation winner;
  прямой rebuild старого baseline без будущих row-признаков пока провален.
- `take_skip_live_safe_path` тоже не нашёл validation winner; прямой rebuild
  старого take/skip семейства сейчас отклонён.
- `take_skip_live_safe_geometry` тоже не нашёл validation winner; добавление
  geometry-признаков не спасло прямой rebuild.
- Diagnostic online demo больше не требует ненулевого `predict/signal` в live `Nero.csv`, но unsafe override проверяет только механику цепочки.
- Python watcher/exporter должен быть запущен постоянно или заменён сервисом с тем же atomic write contract; текущий штатный режим - отдельное окно `tmux`.
- Runtime CSV-файлы частично игнорируются git, поэтому их нужно синхронизировать отдельно.
- `knowledge-rag` reindex в конце этапа ранее падал с `Transport closed`; RAG может отставать от части последних правок.

## Latest Reports

- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
- [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md)
- [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)
- [`docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)
