# PF Uplift Sources Beyond the ML Layer — discovery plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:brainstorming FIRST, then superpowers:writing-plans for each shortlisted hypothesis. Only after that switch to superpowers:subagent-driven-development or superpowers:executing-plans. This plan is a **discovery** plan — it does not implement fixes, it produces a ranked shortlist of **separate** implementation plans.

**Goal:** Найти (а не реализовать) источники PF uplift, которые лежат **вне ML-слоя** — в entry logic, в параметрах SL/TP, в регимных фильтрах, в логике исполнения EA. Выход плана — короткий ранжированный shortlist из 2–3 гипотез с цифровым обоснованием, каждая из которых становится **отдельным** implementation-плана в `docs/superpowers/plans/`.

Этот плана запускается как fallback на случай, если `2026-04-13-quantile-fav-composition.md` даёт verdict `CLOSED — no uplift` / `CLOSED — gate fail`. До этого момента текущий план лежит в backlog. Если composition даёт `PROMOTE-candidate`, этот план может быть временно заморожен (не закрыт) — исчезает немедленный триггер, но backlog остаётся валидным.

**Architecture:** **Read-only discovery**. Никакого реального кода, кроме одноразовых аналитических скриптов в `/tmp/`. Никакого переобучения, никакой правки `MT/`, никаких новых production rules, никаких изменений в EA до отдельного implementation-плана. Выход — `docs/reports/2026-04-13-pf-uplift-discovery.md` + 2–3 спецификации/плана для следующих этапов.

**Tech Stack:** Python 3.11, pandas/numpy, matplotlib для eyeballing, ripgrep, существующие модули `statistics/signal_tracer.py`, `API/signal_research.py`, `API/signal_path_atlas.py`, `API/exit_policy_research.py`. Никаких новых зависимостей.

**Non-goals:**
- **Не переобучать модели** (ни regression_updn, ни quantile, ни новые архитектуры). Ограничение из `feedback_ml_approach`: сначала выжать текущий сигнал.
- Не предлагать EMA/MA как признаки, таргеты или фильтры. Hard ban из `feedback_ml_approach`.
- Не предлагать `close[t+N]-close[t]` в качестве таргета — нужна path-dependent структура.
- Не пересматривать production quantile rule (`lb_gt_m_q35`).
- Не реанимировать TB как production — он frozen до post-2026-06.
- Не строить ML-фичи из этих исследований. Результат — это **параметры**/**правила**/**условия фильтрации**, а не новые columns в predictions CSV.
- Не закрывать направление без явного verdict-отчёта (direction не должен «заглохнуть» молча).
- Не превращать discovery в implementation — плана сознательно останавливается на shortlist.

---

## File Structure

### Read First
- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `.claude/memory/project_ml_status.md` (verify freshness — memory может быть stale)
- `.claude/memory/feedback_ml_approach.md` (hard bans: MA/EMA, `close[t+N]-close[t]`, ML-архитектура как первичное решение)
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md` (прежний design doc, Phase A/B)
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-a.md`
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- `docs/reports/2026-04-12-quantile-status-decision.md` (текущая production-опора для baseline цифр)
- `wiki/concepts/signal-archetypes.md` (двумодальная структура — критичный контекст для regime analysis)
- `wiki/research/execution-tracks.md` (exit policy, triple barrier, entry_path_v1 tracks)
- `wiki/research/signal-quality-research.md`

### Existing Inputs
- `statistics/signal_tracer.py` — path-dependent OHLC трейсер, `--from-log` режим
- `API/signal_research.py` — уже существующий research entrypoint
- `API/signal_path_atlas.py` — архетип-кластеризация
- `API/exit_policy_research.py` — исследование exit логики (часть параллельных треков)
- `ML/reports/entry_path_v1_quantile_selected_rule.json` — production rule quantile (как baseline для сравнений)
- `MT/tester/logs/20260412.log` (и более свежие, если появятся) — MT4 tester logs для signal_tracer
- `MT/MQL4/Include/lib_ML_Signal.mqh` — **только чтение**, source of truth про entry logic, MaxRR, BypassTrend, HoldOverTime

### Files To Create
- `docs/reports/2026-04-13-pf-uplift-discovery.md` — главный deliverable, verdict + shortlist
- `docs/superpowers/specs/2026-04-13-pf-uplift-hypotheses.md` — расширенный список гипотез (long list перед ранжированием), если удобно держать отдельно от report
- 2–3 файла `docs/superpowers/plans/2026-04-13-<slug>.md` — по одному на ранжированную гипотезу shortlist, **только шапки и skeleton**, без tasks (полноценное написание — отдельный заход в `/writing-plans`)

### Artefacts To Create During Execution (research only, под `/tmp/` или `ML/reports/pf_uplift_discovery/`)
- `ML/reports/pf_uplift_discovery/baseline_numbers.json` — точка отсчёта: текущие PF / N / win_rate / yearly breakdown для baseline (`regression_updn` без фильтров) и quantile production
- `ML/reports/pf_uplift_discovery/trade_enriched.csv` — обогащённый лог сделок (time, signal, ratio, SL, TP, MFE, MAE, outcome, regime_tag, archetype_tag) — основа для всех probes
- `ML/reports/pf_uplift_discovery/probe_<slug>.json` — по одному на probe, см. Task 4
- `ML/reports/pf_uplift_discovery/hypotheses_longlist.md` — сырая запись из /brainstorming

### Files To Update At Stage Close
- `CONTEXT_HANDOFF.md` — short block: direction moved from «backlog» в «discovery done, shortlist X Y Z»
- `CHANGELOG.md` — одна запись `## [YYYY-MM-DD] - PF uplift discovery`, раздел `### Результаты` + `### Вывод`
- `wiki/research/execution-tracks.md` — через wiki skill ingest для `2026-04-13-pf-uplift-discovery.md`
- `docs/superpowers/roadmap.md` — пункт «PF uplift beyond ML» заменяется на перечень shortlisted implementation-планов (или помечается как closed, см. Task 7 rubric)

---

## Prerequisites / trigger

Этот плана **не должен стартовать**, пока не выполнено хотя бы одно:
1. `docs/reports/2026-04-13-quantile-fav-composition.md` существует и `Verdict ∈ {CLOSED — no uplift, CLOSED — gate fail, INCONCLUSIVE}`
2. Пользователь явно попросил стартовать этот план досрочно (в обход composition verdict)

Если оба условия false — плана остаётся в backlog, перечислен в roadmap, но не исполняется.

---

## Tasks

### Task 1 — Orientation & evidence base

- [ ] Step 1.1 — Прочитать все файлы из `Read First`. Особое внимание к `docs/superpowers/specs/2026-03-27-pf-improvement-design.md` — там уже есть Phase A / Phase B идеи; надо понять, что из них: (a) реализовано, (b) отложено, (c) пересмотрено, (d) до сих пор актуально. Записать 4-колоночную табличку в блокнот.
- [ ] Step 1.2 — Проверить актуальность memory:
  - Прочитать `.claude/memory/project_ml_status.md` → grep текущий код на предмет `transformer_updn_best.pt`, `entry_path_v1_quantile_selected_rule.json`, `processing/label_signals.py:919`. Если что-то переехало/переименовано — обновить memory в конце плана, но **не смешивать** эту правку с контентом discovery.
  - Прочитать `feedback_ml_approach` — hard bans ниже используются как фильтр при brainstorming.
- [ ] Step 1.3 — Собрать baseline цифры в `ML/reports/pf_uplift_discovery/baseline_numbers.json`:
  - Для `regression_updn` baseline (без quantile фильтра): N, PF, win_rate, mean_pnl_atr, per-year breakdown на test split 2023–2026
  - Для `entry_path_v1_quantile` production: те же поля из `frozen_test` и `sequential_summary`
  - Для MT4 tester (если есть свежий `MT/tester/logs/<date>.log`): реальный PF в деньгах через `signal_tracer.py --from-log`
  - Важно: **именно числа отсюда** будут служить bar-ом, который гипотезы должны побить. Никакого «улучшили на глаз» не допускается.
- [ ] Step 1.4 — Собрать `trade_enriched.csv` (один раз, на обе backlog-задачи и на будущие implementation-планы). Колонки:
  - `time, signal, ratio, sl, tp, entry_price, exit_price, mfe, mae, outcome, bars_held, exit_reason`
  - `archetype_tag` (winning/failure) из `signal_path_atlas` — через существующий pipeline
  - `regime_tag` — заполняется позже на Task 3 (пока null)
  - Источник сделок: **фиксированный** — один конкретный tester log + тот же test split predictions, что используется в `entry_path_v1_quantile_selected_rule.json`. Зафиксировать пути в `run_metadata.json`.

### Task 2 — /brainstorming session

**Обязательный skill: `/brainstorming`.** Не заменять текстовым списком.

- [ ] Step 2.1 — Сессия `/brainstorming` с повесткой: «Источники PF uplift вне ML-слоя. Ограничения: не переобучать, не трогать архитектуру, не вводить MA/EMA, путь цены важнее агрегатов, есть production quantile как parallel mode и baseline regression_updn». Лимит — **20 гипотез максимум**, после этого принудительный stop.
- [ ] Step 2.2 — Каждая гипотеза должна быть сформулирована в шаблоне `<фильтр|параметр|правило> → механизм влияния на PF → какие сделки оно затронет → как проверить за 1 день`. Если «как проверить» не умещается в 1 день read-only работы — гипотеза откладывается в «long shot» bucket.
- [ ] Step 2.3 — Категоризация (заранее зафиксированная, чтобы не плодить свободные темы):
  - **E — Entry logic**: улучшение условия входа (timing, confirmation, signal stacking, pullback entry). Сюда же попадают regime-conditional entries.
  - **S — SL/TP parameters**: пересмотр фиксированных SL/TP, динамический R:R, trailing, partial exits, early timeout.
  - **R — Regime analysis**: фильтрация по рыночному режиму (волатильность, тренд/флэт, сессия, новости, day-of-week, корреляции). НЕ через MA — через volatility regimes, return autocorrelation, intraday session buckets, realized volatility quantiles.
  - **X — Execution / EA-side**: всё, что лежит в `lib_ML_Signal.mqh` — MaxRR cap, HoldOverTime, BypassTrend, spread/slippage handling, order type.
  - **F — Feature-level signal filters** (non-retraining): фильтры над уже существующими predictions, не требующие нового train.
- [ ] Step 2.4 — Зафиксировать hard bans прямо в brainstorming: любые MA/EMA-фичи, simple close-diff таргеты, «обучить новую модель», «сменить архитектуру». Отклонять без обсуждения. Reminder из `feedback_ml_approach`.
- [ ] Step 2.5 — Сохранить полный longlist в `ML/reports/pf_uplift_discovery/hypotheses_longlist.md` с категорией, формулировкой, «как проверить», начальной интуицией (1 строка на гипотезу).

### Task 3 — Pre-probe diagnostics (regime tagging)

Эти две диагностики нужны для правильной фильтрации гипотез, их делают ДО probes, чтобы не тратить probes на заведомо слабые идеи.

- [ ] Step 3.1 — Realized volatility regime tagging: для каждой сделки из `trade_enriched.csv` посчитать квантиль realized volatility на окне H1 × 24 (1 день) **на момент входа**, до открытия сделки (no leak). Тегировать `vol_q1/q2/q3/q4`. Использовать realized vol, **не** MA.
- [ ] Step 3.2 — Session bucket tagging: для каждой сделки добавить `session ∈ {asia, london, ny, overlap}` по времени MT4 (UTC с учётом брокерского смещения — проверить в `AGENTS.md`). Не привязываться к day-of-week без сессии.
- [ ] Step 3.3 — Archetype crosstab: посчитать PF и N для каждой пары (`archetype_tag × vol_q`) и (`archetype_tag × session`). Это **диагностическая таблица** — она показывает, где искать regime uplift, а где это бессмысленно.
- [ ] Step 3.4 — Сохранить crosstab в `ML/reports/pf_uplift_discovery/regime_crosstab.csv`. **Эта таблица — не результат, а фильтр для probes**: гипотезы из категории R, которые противоречат crosstab, удаляются из longlist без probe.

### Task 4 — Cheap probes (max 6, max 1 day each, read-only)

Probe — это быстрая диагностика гипотезы на 1 день максимум, без изменения кода EA. Выбирается **максимум 6** наиболее перспективных гипотез из longlist после фильтра Task 3. Остальные откладываются в «not probed, low priority» bucket.

- [ ] Step 4.1 — Ранжирование longlist → top-6 по двум критериям: (a) potential impact — насколько большую долю сделок гипотеза затронет, (b) cost to verify — насколько просто сделать probe. Если impact низкий и cost высокий — drop.
- [ ] Step 4.2 — Для каждой из 6 выбранных гипотез создать одноразовый аналитический скрипт в `/tmp/probe_<slug>.py`. Скрипт читает `trade_enriched.csv` + regime crosstab, применяет гипотезу как фильтр или переоценку SL/TP, возвращает:
  - `{"hypothesis": "...", "n_in": ..., "n_out": ..., "pf_in": ..., "pf_out": ..., "pf_delta": ..., "negative_years_in": ..., "negative_years_out": ..., "archetype_shift": {...}, "caveats": [...]}`
- [ ] Step 4.3 — **Path-dependent check:** любая probe, которая меняет SL/TP или entry timing, ОБЯЗАНА считать MFE/MAE trajectory из trade_enriched, **не только** агрегатный outcome. Напомнить себе: «BOTH_HIT ≠ up > dn». Если probe пользуется только aggregate outcome → STOP, вернуть к /brainstorming.
- [ ] Step 4.4 — Каждая probe сохраняется в `ML/reports/pf_uplift_discovery/probe_<slug>.json`. **Никакого git-коммита** скриптов из `/tmp/` — это одноразовые артефакты.
- [ ] Step 4.5 — No p-hacking rule: если probe показывает PF uplift, но (a) negative_year_slices увеличилось, ИЛИ (b) N упало > 50%, ИЛИ (c) результат зависит от конкретного года — probe помечается как `weak` и идёт в «requires forward validation», а не в shortlist.

### Task 5 — Ranking & shortlist

- [ ] Step 5.1 — Свести результаты probes в единую таблицу: `hypothesis, category, n_before, n_after, pf_before, pf_after, pf_delta, negative_years_delta, archetype_shift, strength`.
- [ ] Step 5.2 — Scoring rubric (заранее зафиксирован):
  - **Strong** (top-shortlist): pf_delta > +0.3 (абсолютная), N не упало >30%, negative_years не увеличилось, path-dependent check прошёл, гипотеза не дублирует существующий quantile filter.
  - **Medium**: pf_delta > +0.15, одно из условий Strong может быть нарушено, но не более одного.
  - **Weak**: остальные. Идут в «not shortlisted».
- [ ] Step 5.3 — Выбрать shortlist: **максимум 3** Strong; если Strong меньше 3 — дополнить лучшими Medium до 3, явно пометив их. Если Strong+Medium вместе даёт 0 — это valid outcome, см. Task 7 rubric «direction closed».
- [ ] Step 5.4 — Для каждой гипотезы в shortlist **короткая независимая проверка коллизий** с существующими направлениями:
  - не перекрывает ли она composition track (если тот PROMOTE-candidate)?
  - не дублирует ли она правило, уже вшитое в `lib_ML_Signal.mqh`?
  - есть ли pre-existing spec в `docs/superpowers/specs/2026-03-27-*`?
  - Если коллизия найдена — shortlist не теряет гипотезу, но в её записи ссылка на коллизию обязательна.

### Task 6 — Draft skeleton plans for shortlist

**Обязательный skill: `/writing-plans` для каждой гипотезы.** Не генерировать tasks «от руки» по шаблону.

- [ ] Step 6.1 — Для каждой гипотезы в shortlist создать `docs/superpowers/plans/2026-04-13-<slug>.md` **скелетом**:
  - Goal (одно предложение из probe)
  - Non-goals (явно: не retraining, не MA/EMA, не новая архитектура, не MT4-прод без parity test)
  - Read First (минимум: baseline_numbers.json, probe_<slug>.json, соответствующий source file: `lib_ML_Signal.mqh` / `API/exit_policy_research.py` / и т.д.)
  - Expected gate (N/PF/negative_years criteria, совместимые с quantile-style n-boost gate)
  - Placeholder `## Tasks` секция с пометкой `TBD — to be filled in dedicated /writing-plans pass`
- [ ] Step 6.2 — Сkeletons **не** исполняются в рамках этого плана. Единственная цель — чтобы verdict report ссылался на конкретные файлы, а не на «устные гипотезы».
- [ ] Step 6.3 — Если shortlist пуст (Task 5.3 дал 0 кандидатов) — skeletons не создаются, направление закрывается явно.

### Task 7 — Verdict report & stage close

Verdict rubric (заранее зафиксирован, применяется один раз):

- **SHORTLISTED (N ∈ [1,3])** — есть как минимум одна Strong или Medium гипотеза, skeletons созданы. Направление активно, следующий шаг — отдельный /writing-plans pass и implementation plan для каждой гипотезы.
- **INCONCLUSIVE** — все probes показали `weak` по причине недостатка данных (N < 30 после фильтра), а не по отсутствию эффекта. Направление замораживается до накопления post-2026-06 forward данных.
- **CLOSED — no uplift found** — все probes показали pf_delta ≤ +0.15 ИЛИ breaking negative_years ИЛИ breaking N-cut. Направление закрывается явно.
- **ESCALATE** — в ходе discovery обнаружен баг в baseline цифрах / crosstab противоречит `docs/reports/2026-04-12-quantile-status-decision.md` / числа из Task 1.3 не сходятся с `entry_path_v1_quantile_selected_rule.json.frozen_test`. Остановить план, поднять к пользователю.

- [ ] Step 7.1 — Создать `docs/reports/2026-04-13-pf-uplift-discovery.md`. Структура:
  - Дата, статус, цель, источники, trigger (composition verdict)
  - **Method**: /brainstorming с категориями, longlist size, regime tagging approach, probe budget
  - **Baseline numbers** (из `baseline_numbers.json`) — явно, чтобы читать без перехода в JSON
  - **Longlist summary** — сколько гипотез в каждой категории, сколько дропнуто hard bans, сколько дропнуто по Task 3 crosstab
  - **Probe results table** — все 6 probes с полями из Task 5.1
  - **Rubric** — копия из Step 7 + явная классификация каждой probe
  - **Verdict** — одно из четырёх состояний
  - **Shortlist** (если есть) — пронумерованный список с ссылками на skeleton plans, для каждой: rationale, expected impact, risks
  - **Not shortlisted** — очень краткий список с одним предложением на каждую (чтобы в будущем не повторять ту же гипотезу через полгода)
  - **Next actions** — явный checklist: «open /writing-plans for X», «close direction», «awaiting forward data till DATE»
- [ ] Step 7.2 — Обновить `CONTEXT_HANDOFF.md`: новая строчка «Last Completed Stage: PF uplift discovery (verdict)», Next Step обновить под исход, ссылка на отчёт в Read First.
- [ ] Step 7.3 — `CHANGELOG.md` — одна запись с цифрами baseline и verdict. Без дублирования содержимого отчёта.
- [ ] Step 7.4 — Wiki ingest через `skill wiki, action=ingest, report=docs/reports/2026-04-13-pf-uplift-discovery.md`. Ручная правка `wiki/index.md` запрещена — делает skill.
- [ ] Step 7.5 — `docs/superpowers/roadmap.md`:
  - SHORTLISTED: пункт «PF uplift beyond ML» раскрывается в подсписок из shortlisted плана
  - INCONCLUSIVE: пункт помечен «awaiting forward data, earliest 2026-06»
  - CLOSED: пункт помечен closed + ссылка на отчёт
  - ESCALATE: roadmap не трогать до решения пользователя
- [ ] Step 7.6 — Memory update: если в Task 1.2 нашлась устаревшая строка в `.claude/memory/project_ml_status.md` — обновить её отдельной правкой. Не смешивать с discovery-коммитом.

### Task 8 — Self-review checklist

- [ ] Step 8.1 — Никаких изменений в `processing/`, `ML/train.py`, `ML/checkpoints/`, `MT/MQL4/`, `MT/tester/` (только чтение). Никаких новых production rules в `ML/reports/` рядом с существующими frozen rules.
- [ ] Step 8.2 — Все longlist hypotheses соответствуют hard bans из `feedback_ml_approach`. Ни одна не основана на MA/EMA, на `close[t+N]-close[t]`, и ни одна не предлагает смену архитектуры/переобучение как первичное решение.
- [ ] Step 8.3 — Каждая probe прошла path-dependent check (MFE/MAE учтены, не только outcome).
- [ ] Step 8.4 — Verdict rubric применена ровно один раз, по зафиксированным критериям, без подгона.
- [ ] Step 8.5 — Если shortlist непустой — для КАЖДОЙ гипотезы существует skeleton plan файл, и verdict report ссылается на каждый по имени файла.
- [ ] Step 8.6 — Если shortlist пустой — в отчёте явно сказано «direction CLOSED», и одна строка на причину в roadmap.
- [ ] Step 8.7 — `git status` — затронуты только файлы из списка `Files To Create` / `Files To Update At Stage Close` + артефакты `ML/reports/pf_uplift_discovery/`. Скрипты `/tmp/` не попадают в git.
- [ ] Step 8.8 — `git commit` — только по явной просьбе пользователя.

---

## Safeguards & stop conditions

- **STOP и escalate к пользователю**, если:
  - Baseline numbers (Task 1.3) расходятся с `entry_path_v1_quantile_selected_rule.json.frozen_test` более чем на ~1% — разбираться в источнике до любых probes.
  - Regime crosstab (Task 3.3) показывает, что квантиль volatility имеет сильное ML-смещение (все winning archetype в одном quantile) — это противоречит независимости regime tag от сигнала и требует более глубокой диагностики.
  - Какая-то probe меняет PF ниже 1.0 (ухудшение) — это может означать баг в фильтре, а не отсутствие эффекта.
  - Появляется соблазн «просто обучить под новый таргет» — STOP, это нарушает hard ban, направлять к отдельному research-plану.
- **Don't do:**
  - Не подключать ничего к MT4 в рамках этого плана, даже при сильном probe результате.
  - Не делать multi-probe ensemble («а что если объединить probe_1 и probe_3») — это другой тип плана (composition-style), см. `2026-04-13-quantile-fav-composition.md` как шаблон.
  - Не оптимизировать параметры probe под желаемый результат. Все пороги (vol quantile cutoff, ratio bucket, session window) берутся либо из данных (квантили), либо из prior specs.
  - Не переписывать `signal_tracer.py` / `signal_path_atlas.py` / `exit_policy_research.py` — только вызывать.

---

## Definition of Done

План считается выполненным, когда:
1. `docs/reports/2026-04-13-pf-uplift-discovery.md` существует с явным verdict ∈ {SHORTLISTED, INCONCLUSIVE, CLOSED, ESCALATE}.
2. Артефакты `ML/reports/pf_uplift_discovery/{baseline_numbers,trade_enriched,regime_crosstab,hypotheses_longlist,probe_*,run_metadata}.{json,csv,md}` существуют.
3. Если verdict == SHORTLISTED: 1–3 skeleton plan файла в `docs/superpowers/plans/2026-04-13-<slug>.md`.
4. `CONTEXT_HANDOFF.md`, `CHANGELOG.md`, `wiki/research/execution-tracks.md`, `docs/superpowers/roadmap.md` отражают исход.
5. Никаких изменений за пределами списка `Files To Create` / `Files To Update At Stage Close` + `ML/reports/pf_uplift_discovery/`.
6. Никакого нового production кода, rules, MT4-интеграций.

После этого: либо активируется последовательность implementation-плана для shortlisted гипотез (каждый — отдельный /writing-plans → /test-driven-development → verdict pass), либо направление явно закрыто в roadmap, либо заморожено до forward-данных.
