# Context Handoff

Короткий baton для следующего агента. Историю этапов читать в `docs/reports/`, краткую хронологию - в `CHANGELOG.md`, синтез - в `wiki/research/`.

## Current Stage

Этап `telemetry_frequency_demo_launch` дополнен 2026-04-28 архитектурным снимком MQL runtime, 2026-04-29 online inference contract hardening, 2026-05-05 live-safe ML audit и 2026-05-07 закрытием воспроизводимости `entry_path_v1_live_safe + A @ 7.5%`.

Канонические отчёты:
- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
- [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md)
- [`docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`](docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md)
- [`docs/reports/2026-05-07-cpu-gpu-reproducibility.md`](docs/reports/2026-05-07-cpu-gpu-reproducibility.md)
- [`docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md`](docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md)
- [`docs/reports/2026-05-07-entry-path-mt4-parity.md`](docs/reports/2026-05-07-entry-path-mt4-parity.md)

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
- серверный `live_safe_geometry_path_seq50` выполнен (`seed=42`,
  `torch_threads=16`): validation winner не найден, verdict=`reject`; лучший
  validation PF `3.7229` только на `5` сделках и `1.25` сделок/год; при
  минимуме `6` сделок/год лучший PF `0.4899`.
- вывод: добавление MT-накопленных `Up/Dn` path-признаков, geometry-признаков
  и их комбинации не восстановило take/skip прибыльность; прямой live-safe
  rebuild старого take/skip семейства сейчас отклонён.
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
- добавлен `ML/run_entry_path_live_safe_retrain.py`: канонический runner для
  закрытия воспроизводимости `entry_path_v1_live_safe`. Он по каждому seed
  делает train → export validation/test → benchmark и пишет
  `multi_seed_summary.csv/json`, используя только seed-specific checkpoint.
- серверный CPU multi-seed (`7`, `17`, `42`, `77`, `123`) закрыт:
  auto-winner среди `A/B/B_no_path6` слабее (median sequential PF `1.6183`,
  PF > 2.0 у `1/5`), но заранее выбранный production baseline `A @ 7.5%`
  устойчивее: median sequential PF `2.3249`, min `1.8188`, PF > 2.0 у
  `4/5`, PF <= 1.0 у `0/5`. Канонический отчёт:
  `docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`.
- для перепроверки `entry_path_v1_quantile` поверх этого нового CPU baseline
  добавлен `ML/run_entry_path_quantile_live_safe_retrain.py`. Он по каждому
  seed обучает quantile, экспортирует predictions, строит per-seed baseline
  `A @ 7.5%` rule из CPU baseline predictions и запускает quantile benchmark.
- серверный CPU retrain `entry_path_v1_quantile` поверх нового baseline
  завершён. Quantile sequential PF > 2.0 у `5/5` seed, но rule selection
  нестабилен (`lb_gt_m_width_le_w` у `2/5`, `lb_gt_m` у `2/5`, `baseline` у
  `1/5`) и сделок мало (`3..28`, median `8`). Канонический отчёт:
  `docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md`. Verdict:
  research-only, не production.
- отчёт `docs/reports/2026-05-07-cpu-gpu-reproducibility.md` закрыл причину
  CPU/GPU расхождений: CPU/GPU training создаёт разные checkpoint из-за
  dropout RNG и порядка матричных операций, но inference одного CPU-trained
  checkpoint на CPU/GPU даёт одинаковый рейтинг сделок. Решение: production
  retrain только на CPU. `ML.train` получил `--device cpu|cuda|auto` с default
  `cpu`; GPU training теперь только явный research-режим.
- первый MT4 parity-прогон для `entry_path_v1_live_safe + A @ 7.5%` закрыт
  на периоде `2022.10.28` - `2025.12.31`: MT4 открыл `26` сделок, отчет
  тестера показал PF `9.03`, net `5217.70`; reconciliation:
  `expected_signals=26`, `opened_trades=26`, `closed_trades=26`,
  `critical_mismatch_count=0`, `missing_close_count=0`.
- этот MT4-прогон не покрывает весь файл `ml_signals.csv`: после
  `2025.12.31` остаются 3 ненулевых сигнала (`2026.01.21 22:00`,
  `2026.03.24 05:00`, `2026.03.27 00:00`). Для полного parity нужен прогон
  до конца файла сигналов, лучше до `2026.04.22` плюс запас на закрытие.

## Next Step

1. Следующий рабочий фокус - закрыть полный MT4 parity для
   `entry_path_v1_live_safe + A @ 7.5%`: запустить Strategy Tester до конца
   файла сигналов (`2026.04.22` плюс запас на закрытие последней позиции) и
   выполнить reconciliation по свежему `MT/tester/logs/*.log`.
2. Python-side MT4 export уже подготовлен командой
   `./.venv/bin/python -m ML.prepare_entry_path_mt4_parity --output-dir ML/reports/mt4_entry_path_v1_live_safe_parity --copy-to-mt4`.
   Ожидаемый файл: `MT/tester/files/ml_signals.csv`, sha256
   `f213a8689bcac8fee0f7294bc56c5fc647e63cf58ab83321eda505d82d2af852`,
   `29` ненулевых сигналов (`21` BUY, `8` SELL). Python sequential check:
   `27` trades, PF `5.9352`.
3. MT4 preset уже переключён на H1 fixed-hold contract:
   `SymPer=XAUUSD60`, `ML_MaxPositions=1`, `ML_HoldBars=24`,
   `ML_TakeProfitATR=0`, `ML_BackStopATR=999`, `ML_UseScoreFilter=0`.
4. Важно: после bugfix `SERVICE.mqh` эксперт должен быть перекомпилирован.
   Ожидаемая версия в логе: `OnInit() SoSimple.V260.332`. Старый `.ex4`
   может давать `EXP[0].Mgc != Magic`, потому что раньше `PARAMS` читались как
   `char` и `ML_BackStopATR=999` превращался в `-25`.
5. Первый короткий MT4 parity до `2025.12.31` уже прошёл без критических
   расхождений. Рекомендуемый период полного MT4 parity: с `2022.10.28` по
   `2026.04.22` плюс запас на закрытие последней позиции, то есть диапазон
   `ml_signals.csv`.
6. После MT4 test run выполнить:
   `./.venv/bin/python -m ML.telemetry_daily_reconciliation --signals MT/tester/files/ml_signals.csv --mt4-log <fresh-log> --output-dir ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation --label entry_path_v1_live_safe_a075_mt4_parity --export-metadata ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json`.
7. Перед MT4 parity не запускать новые seed/device эксперименты вручную через
   общий `ML/checkpoints/*_best.pt`. Если retrain всё же нужен, использовать
   только `ML.run_entry_path_live_safe_retrain --output-dir ...`, чтобы прогнозы
   экспортировались из seed-specific checkpoint.
8. Воспроизводимость `entry_path_v1_live_safe + A` считать закрытой для
   research-этапа: подтверждён baseline `A @ 7.5%`, не auto-winner.
   Повторный `entry_path_v1_quantile` поверх CPU baseline тоже закрыт:
   прибыльность есть, но production-gate не пройден.
9. Не продолжать прямой take/skip rebuild без новой узкой гипотезы: baseline,
   path, geometry и geometry_path варианты получили `reject`.
10. `entry_path_v1_quantile` сейчас не продвигать в production: после фиксации
   baseline `A` прибыльные участки есть, но rule selection нестабилен.
11. Чтобы не забыть системы: `quality`, `frequency`, `original_plus_path`,
   `entry_path_v1`, `entry_path_v1_quantile` теперь сведены в Audit Tracker
   внутри `docs/reports/2026-05-05-live-safe-ml-audit.md`.

## Read First

1. [`AGENTS.md`](AGENTS.md) - правила агента и карта источников.
2. [`docs/ML/ml_leakage_preflight_checklist.md`](docs/ML/ml_leakage_preflight_checklist.md) - обязательный leakage/preflight gate для всех ML test/MT4/online выводов.
3. [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md) - текущий verdict по прибыльным ML-системам и первый retrain без `ret_dir_atr_lag1`.
4. [`docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`](docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md) - подтверждение CPU baseline `A @ 7.5%`.
5. [`docs/reports/2026-05-07-cpu-gpu-reproducibility.md`](docs/reports/2026-05-07-cpu-gpu-reproducibility.md) - почему production retrain только CPU.
6. [`docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md`](docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md) - quantile поверх CPU baseline, verdict research-only.
7. [`docs/ML/prepare_entry_path_mt4_parity.py.md`](docs/ML/prepare_entry_path_mt4_parity.py.md) - подготовка `ml_signals.csv` для MT4 parity текущего кандидата.
8. [`ML/reports/live_safe_ml_audit/`](ML/reports/live_safe_ml_audit/) - generated audit evidence.
9. [`ML/reports/entry_path_v1_live_safe/`](ML/reports/entry_path_v1_live_safe/) - ранние retrain и multi-seed artifacts.
10. [`ML/reports/entry_path_v1_quantile_live_safe_baseline/`](ML/reports/entry_path_v1_quantile_live_safe_baseline/) - ранний quantile retrain поверх live-safe baseline.
11. [`docs/MT/trading_strategy.md`](docs/MT/trading_strategy.md) - online pipeline, `#.csv`, MQL logging.
12. [`docs/MT/ml_signal_integration.md`](docs/MT/ml_signal_integration.md) - MT4 `ml_signals.csv` contract.
13. [`docs/ML/telemetry_daily_reconciliation.py.md`](docs/ML/telemetry_daily_reconciliation.py.md) - daily reconciliation.

## Open Risks

- Legacy `original_baseline` нельзя считать online-ready: historical test был
  загрязнён future-derived входными признаками, а live `Nero.csv` этих признаков
  не имеет.
- `entry_path_v1` и `entry_path_v1_quantile` теперь `FAIL`, не `UNKNOWN`.
  Причина: `ret_dir_atr_lag1` доказан как future-derived, а quantile зависит
  от baseline score.
- MT4 parity для `entry_path_v1_live_safe + A @ 7.5%` ещё не выполнен: Python
  proof есть, MT4 proof пока нет.
- Для `entry_path_v1_live_safe` критично использовать H1 источник
  `MT/MQL4/Files/Nero_XAUUSD.csv`; текущий `MT/MQL4/Files/Nero.csv` может
  содержать M5-строки и ломает смысл entry_path targets.
- Production retrain должен быть CPU-only. GPU training допустим только как
  research, потому что даёт другой checkpoint даже при том же seed.
- `entry_path_v1_quantile` показал прибыльные участки поверх CPU baseline, но
  production-gate не прошёл из-за нестабильности выбранного правила и малого
  числа сделок.
- Прямой take/skip rebuild старых `quality`, `frequency`, `original_plus_path`
  отклонён: baseline, path, geometry и geometry_path варианты не нашли
  пригодный validation winner.
- Diagnostic online demo больше не требует ненулевого `predict/signal` в live `Nero.csv`, но unsafe override проверяет только механику цепочки.
- Python watcher/exporter должен быть запущен постоянно или заменён сервисом с тем же atomic write contract; текущий штатный режим - отдельное окно `tmux`.
- Runtime CSV-файлы частично игнорируются git, поэтому их нужно синхронизировать отдельно.
- `knowledge-rag` reindex в конце этапа ранее падал с `Transport closed`; RAG может отставать от части последних правок.

## Latest Reports

- [`docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md`](docs/reports/2026-05-07-entry-path-live-safe-reproducibility.md)
- [`docs/reports/2026-05-07-cpu-gpu-reproducibility.md`](docs/reports/2026-05-07-cpu-gpu-reproducibility.md)
- [`docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md`](docs/reports/2026-05-07-entry-path-quantile-cpu-baseline.md)
- [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md)
- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
