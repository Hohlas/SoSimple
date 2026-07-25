# Аудит плана `2026-07-25-fractal0-fixed11-candidate-audit.md`

Дата аудита: 2026-07-25.

Проверяемый файл: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`.

Проверены только связанные источники: связанный locked-test отчёт, предыдущий locked-test protocol plan, методика `06/09/10/11/12/13/16`, `docs/DATA_FLOW.md`, `docs/superpowers/roadmap.md`, runner `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, bootstrap helper, JSON/CSV `ML/reports/fractal0_fixed11_rich_entry_locked_test*`, `leaderboard_closure_audit_rules.csv`.

## Краткий вывод

План в целом правильно ставит задачу read-only аудита и не предлагает новый подбор по `locked_test`. Базовые факты по текущим артефактам подтверждаются: JSON/CSV существуют, 11 правил совпадают с `leaderboard_closure_audit_rules.csv`, хэши основных входов совпадают с локальными файлами, основной PF/BS/N и BUY/SELL PF проходят заявленные пороги.

Блокеры плана: он не требует машинно проверяемого pre-open freeze/policy artifact, пропускает малый N в годовых срезах, использует `BS_p05` как жёсткое условие без проверки, что это настоящий block bootstrap, и не заставляет structured artifact раскрыть все роли split.

## Замечания

### 1. Критично - нет проверки pre-open freeze/policy artifacts

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 28-36, 81-90, 157-172.

Суть проблемы: план говорит, что аудит проверяет frozen 11-rule contract, но не включает в `depends_on` и проверки pre-open freeze/policy artifacts из предыдущего протокола: `ML/reports/fractal0_fixed11_locked_test_freeze.json` и `ML/reports/fractal0_fixed11_locked_test_selection_policy.json`.

Доказательство:

- Предыдущий протокол требует создать эти файлы: `docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md`, строки 55-61.
- Там же указано, что freeze artifact должен записать `rule_hash_sha256`, execution contract и selection policy до открытия `locked_test`: строки 71-75, 284-319.
- В текущем дереве команда `rg --files | rg 'fractal0_fixed11_locked_test|fractal0_fixed11_rich_entry_locked_test|leaderboard_closure_audit_rules'` нашла только:
  - `tests/test_fractal0_fixed11_rich_entry_locked_test.py`
  - `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
  - `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- Методика требует сохранить rule/threshold/checkpoint/feature/export/execution contract и запретить изменения после просмотра `locked_test`: `docs/methodology/09-validation-freeze.md`, строки 44-47, 60-65.

Почему это важно: после открытия `locked_test` нельзя честно восстановить факт, что конкретный rule hash и selection policy были зафиксированы заранее. Без этого аудит может проверить текущую согласованность файлов, но не докажет pre-open freeze.

Рекомендуемое исправление: добавить freeze/policy artifacts в `depends_on` и в `audit_hashes`/`audit_split_policy`. Если их действительно нет, итог аудита должен быть не `candidate_audit_passed`, а минимум `candidate_audit_blocked` с явной причиной `pre_open_freeze_artifact_missing`. Ретроактивно созданный freeze можно использовать только как disclosure, не как доказательство pre-open freeze.

### 2. Улучшение - нужно явно развести аудит 11 правил и последующий отбор по корреляции

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 83-96.

Суть проблемы: план использует `kept_candidates=11` как условие прохода аудита. По уточнённому решению пользователя от 2026-07-25 это допустимо: нужно проверить все 11 кандидатов, а взаимную корреляцию и финальное число оставляемых правил оценить отдельным следующим этапом. Но в плане это стоит назвать точнее, чтобы `kept_candidates=11` не читалось как финальный portfolio selection.

Доказательство:

- Новый план: `rule_count=11`, `kept_candidates=11` как условие pass, строки 83-84; `candidate_audit_passed` ведёт к MT4/tester parity, строки 94-96, 296-298.
- Пользовательское уточнение от 2026-07-25: ограничение до 3 не учитывать в этом аудите; проверить все 11, затем отдельно проверить взаимную корреляцию и решить, сколько оставить.
- Фактический JSON: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, строки 16-17: `rule_count=11`, `kept_candidates=11`.
- Runner помечает `KEEP_CANDIDATE` только по PF/BS/N и не применяет max-3/correlation pruning: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 256-268.

Почему это важно: без явного разделения этапов следующий исполнитель может принять `kept_candidates=11` за финальный портфельный отбор, хотя это только список правил, прошедших индивидуальный аудит перед корреляционной проверкой.

Рекомендуемое исправление: заменить или дополнить `kept_candidates=11` полями `evaluated_rule_count=11`, `gate_pass_count=11`, `correlation_pruning_status=FOLLOW_UP_REQUIRED`. В `Next Step` явно указать: сначала проверить взаимную корреляцию всех 11 прошедших правил, затем принять отдельное решение о количестве оставляемых кандидатов.

### 3. Важно - годовой gate игнорирует минимальный размер годового среза

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 86-87, 197-199.

Суть проблемы: план требует годовые строки и PF >= 1.20, но не требует `n_trades >= 30` для годового вывода. В фактическом yearly CSV есть 6 годовых срезов с числом сделок меньше 30.

Доказательство:

- Методика: для годовых выводов минимум 30 сделок в год, иначе годовой срез только diagnostic: `docs/methodology/06-temporal-split.md`, строки 59-65.
- Методика robustness требует проверять годовые срезы и принимать решение пакетом проверок, включая число сделок: `docs/methodology/11-robustness.md`, строки 72-106.
- Команда:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
yearly=pd.read_csv('ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv', sep=';')
print(yearly.loc[pd.to_numeric(yearly['n_trades'], errors='coerce')<30,
                 ['original_rank','rule_id','year','n_trades','pf']].to_string(index=False))
PY
```

Результат: 6 строк с `n_trades < 30`, включая 2022 год для ranks 1, 5, 7, 8, 10, 11; минимальный `n_trades=6`.

Почему это важно: высокий PF на 6-25 сделках не может подтверждать годовую устойчивость. План может ошибочно выдать yearly PASS, хотя методика разрешает только diagnostic для таких срезов.

Рекомендуемое исправление: добавить проверку `yearly_n_trades >= 30` для каждого годового среза, по крайней мере как `WARNING`, а для candidate pass - как блокер годовой устойчивости. Для неполных крайних лет заранее задать правило: исключить из yearly gate с disclosure или считать diagnostic-only, но не PASS.

### 4. Важно - `BS_p05` используется как жёсткий gate, но текущий helper не делает block bootstrap

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 84, 193-199.

Суть проблемы: план требует `BS_p05 >= 1.00`, но не проверяет метод расчёта `BS_p05`. В текущем helper с названием `block_bootstrap_pf` параметр `block_size` есть в сигнатуре, но выборка делается одиночными сделками через `rng.choice(pnl, size=len(pnl), replace=True)`.

Доказательство:

- Реализация: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, строки 645-655. В строках 651-654 выборка идёт по отдельным `pnl`, блоки последовательных сделок не строятся.
- Методика требует при временной зависимости сделок использовать block/bootstrap подходы, учитывающие соседние сделки: `docs/methodology/11-robustness.md`, строки 39-42; типовая ошибка - iid bootstrap на временно связанных сделках, строки 120-121.
- Предыдущий protocol plan уже фиксировал эту известную limitation: `docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md`, строки 211-217.

Почему это важно: `BS_p05` может быть завышен, если сделки зависимы во времени. Тогда hard pass по `BS_p05` создаёт ложную уверенность в устойчивости.

Рекомендуемое исправление: в audit plan явно проверять и записывать `bs_p05_method`. До настоящего block/stationary bootstrap считать текущий `BS_p05` diagnostic или `WARNING`, а `candidate_audit_passed` не должен опираться на него как на полноценный uncertainty gate.

### 5. Важно - split disclosure в JSON неполный, а интерфейс аудита проверяет только payload

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 87-88, 163-172.

Суть проблемы: план требует проверить период `locked_test`, row count и отсутствие повторного использования train/validation для выбора, но интерфейс `audit_split_policy(payload)` принимает только JSON payload. В JSON нет дат split, row count, `val_select` и `val_eval` ролей.

Доказательство:

- Фактический JSON содержит только `train_core` и `locked_test`: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, строки 27-30.
- Locked-test report содержит больше disclosure: `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`, строки 355-361.
- Методика требует явные даты и размеры `train`/`validation`/`locked_test`: `docs/methodology/06-temporal-split.md`, строки 84-90.
- Методика отчётности требует Split Disclosure с ролями `val-stop`/`val-select`/`val-eval` и sample size gate: `docs/methodology/16-reporting-audit.md`, строки 18-30, 88-99.
- Команда по CSV подтвердила фактические границы без перекрытия по времени: train `2004.07.06 20:00` - `2019.06.20 14:00`, validation `2019.06.20 16:00` - `2022.12.02 07:00`, locked_test `2022.12.02 11:00` - `2026.06.04 12:00`.

Почему это важно: текущий план может пройти по JSON, не доказав в structured artifact, откуда взялись cutoffs (`val_select`) и что `val_eval` не был использован для нового выбора.

Рекомендуемое исправление: расширить входы аудита: JSON + locked-test report + исходные split CSV или split manifest. В audit JSON требовать поля `split_boundaries`, `split_roles` с `train_core`, `val_select`, `val_eval`, `locked_test`, `locked_test_source_rows=9463`, `locked_test_min_time`, `locked_test_max_time`.

### 6. Важно - hash policy не покрывает все источники результата

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 81-83, 166-172.

Суть проблемы: план требует сверить хэши rules CSV, H1 OHLC, M5 OHLC и locked-test CSV. Но результат также зависит от `ML/reports/fractal0_stop_grid_m5.json` и от runner code. JSON содержит `source_artifact_sha256`, но план не включает его в обязательную hash policy. Для `source_runner` в JSON есть только путь, без SHA256.

Доказательство:

- Locked-test report говорит, что execution contract загружается из `selected_winner` в `ML/reports/fractal0_stop_grid_m5.json`: `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`, строки 74-80.
- Фактический JSON содержит `source_artifact` и `source_artifact_sha256`: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, строки 8-9.
- Фактический JSON содержит `source_runner`, но без hash: строка 5.
- Методика отчётности требует paths и hashes: `docs/methodology/16-reporting-audit.md`, строки 31-32, 96-97.

Почему это важно: если source artifact или код runner поменялись, audit может не обнаружить изменение execution behavior, хотя PF/PNL напрямую зависит от execution contract и симулятора.

Рекомендуемое исправление: добавить в `audit_hashes` обязательную сверку `source_artifact_sha256`. Для runner добавить `source_runner_sha256` в новый audit artifact; если исходный locked-test JSON не содержит hash runner-а, пометить как limitation/blocker для полного reproducibility, а не молча PASS.

### 7. Важно - восстановление `movement_score` раскрыто слишком общо для воспроизводимого аудита

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 89, 193-199.

Суть проблемы: план требует disclosure и extra parity scrutiny для `movement_plus_time`, но не задаёт проверяемые поля: какие правила затронуты, какие параметры movement scorer-а использованы, какие source hashes/thresholds/scaler fit применены, и что locked labels не участвовали в обучении.

Доказательство:

- Фактический JSON содержит только строковое описание: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, строка 38.
- Locked-test report раскрывает общий протокол: scorer обучается на `train_core`, target `entry_movement_3`, profile `simple_combined`, model `extra_trees_small`, seeds из `seeds_for_model`, строки 128-140.
- Runner действительно пересчитывает scores для locked-test: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 66-116, 147-152.
- В selection/summary сейчас 4 правила с `profile_id=movement_plus_time`; команда `value_counts()` по summary дала `time_only=7`, `movement_plus_time=4`.
- Методика для моделей с scaler/normalization требует раскрыть config, fit split и что locked_test не участвовал в выборе scaler/transform: `docs/methodology/16-reporting-audit.md`, строки 33-42, 98-100.

Почему это важно: movement-score restoration является новым вычислением после открытия `locked_test`. Даже если оно задумано как применение frozen protocol, без структурированных параметров и хэшей его трудно независимо повторить и отличить от постфактум изменения.

Рекомендуемое исправление: добавить отдельный audit check `movement_score_restoration_contract` с полями `affected_rule_count=4`, `target`, `profile`, `model_family`, `seeds`, `fit_split=train_core`, `locked_test_label_usage=false`, hashes исходного movement protocol/config или явный `UNKNOWN`. При `UNKNOWN` не блокировать time_only правила, но блокировать или понижать `movement_plus_time` правила до `research_only` до полного disclosure.

### 8. Улучшение - roadmap metadata содержит устаревшее supersedes-утверждение

Место: `docs/superpowers/plans/2026-07-25-fractal0-fixed11-candidate-audit.md`, строки 42-43.

Суть проблемы: план говорит, что supersedes `docs/superpowers/roadmap.md ACTIVE: Regime filter reformulation as next immediate action`. В текущем `roadmap.md` активен уже `Fixed-11 candidate audit`, а `regime filter reformulation` находится в parked-направлениях.

Доказательство:

- Текущий roadmap: `docs/superpowers/roadmap.md`, строки 16-23: `ACTIVE: Fixed-11 candidate audit`.
- `regime filter reformulation` в parked list: `docs/superpowers/roadmap.md`, строки 45-57 и 124-142.

Почему это важно: это не ломает сам аудит, но вводит следующего исполнителя в заблуждение о том, какое состояние roadmap реально superseded.

Рекомендуемое исправление: заменить metadata на `supersedes_prior_roadmap_snapshot: regime filter reformulation was previously next immediate action; current roadmap already points to this audit` или убрать блок `supersedes`.

## Подтверждённые факты без замечаний

- Все ожидаемые locked-test CSV существуют и не пустые. `wc -l` дал: summary 12 строк, selection 12, yearly 56, side 23, trades 14508, rules 12, locked-test source 9464 включая заголовок.
- Текущие локальные SHA256 совпадают с JSON для rules CSV, source artifact, locked-test CSV, H1 OHLC и M5 OHLC:
  - `leaderboard_closure_audit_rules.csv`: `d98c1194d954e20aaa7d7a132547a9ac52caf1c7073f5ce98997cda1ee3b808c`
  - `fractal0_stop_grid_m5.json`: `20e6931a1b47d7d2fe3c5455e698d8bb3160bd570a418a35a0a0ea083358e0b6`
  - `DATA/Nero_XAUUSD_test_labeled.csv`: `5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535`
  - `DATA/XAUUSD_H1_OHLC.csv`: `4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff`
  - `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`: `504666ce286b27f3ae61679d5e722a629a0d8662d93a428c4f8dd5e6b2ce4f60`
- Identity rules в summary совпадают с `leaderboard_closure_audit_rules.csv` по `original_rank`, `rule_id`, `profile_id`, `model_id`, `target_id`, `filter_id`, `score_cutoff_on_val_select`.
- Основные locked-test gate-метрики по summary проходят: min PF `2.6746637849511434`, min `BS_p05=1.927254428301627`, min `n_trades=241`.
- BUY/SELL rows покрывают все 11 правил; min side PF: BUY `3.6196321730145824`, SELL `1.94845364722068`; min side trades: BUY `78`, SELL `163`.
- Locked-test CSV по `time` имеет 9463 строк, период `2022.12.02 11:00` - `2026.06.04 12:00`; train заканчивается `2019.06.20 14:00`, validation заканчивается `2022.12.02 07:00`, то есть проверенная команда не выявила временного перекрытия по `time`.

## Ошибки инструментов

- `knowledge-rag` вернул `no_results` для поиска похожих документов по самому плану и связанному locked-test отчёту. Это использовано только как навигационная неудача; выводы выше проверены по первичным файлам и локальным командам.
