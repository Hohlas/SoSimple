# Аудит: docs/methodology/07b-predictability-gate.md

> Дата аудита: 2026-08-12
> Объект: `docs/methodology/07b-predictability-gate.md` (100 строк, untracked — не в git)
> Метод: доказательный аудит по первоисточникам; использованы graphify и knowledge-rag для навигации, выводы сверены с файлами проекта
> Окружение: проверены README.md методики, 03/03b/07/06b/11/16/A3/A4/A5 разделы, `statistics/mi_upper_bound.py`, `statistics/run_mi_upper_bound.py`, `tests/test_mi_upper_bound.py`, `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md`, отчёт `docs/reports/2026-08-11-mi-upper-bound.md`, `ML/reports/mi_upper_bound.json`, `ML/baseline/feature_ablation.py`, `ML/live_safe_audit.py`, `tests/test_live_safe_audit.py`

## Контекст погружения

`07b-predictability-gate.md` — методический этап «предобученческая проверка предсказуемости набора признаков». Заявлены две проверки:
1. **Совместный RF-гейт** (обязательный) — единственная, что вправе отклонить набор (FAIL при p ≥ 0.05 против перестановочного фона).
2. **MI-скрининг** (опциональный, диагностика) — через `statistics/mi_upper_bound.py`; не вправе отклонять набор.

Положение в цепочке: между `06b-oracle-preflight` и `07-baseline-first` (но см. замечание C1 о порядке). Документ ссылается на `07-baseline-first.md`, `16-reporting-audit.md`, `A5-post-mortem-diagnostics.md` и `statistics/mi_upper_bound.py`.

Проверены фактические реализации: в проекте **реализован только MI-скрининг** (`statistics/mi_upper_bound.py`, `run_mi_upper_bound.py`, `tests/test_mi_upper_bound.py`). **Реализация совместного RF-гейта отсутствует**: ни в `ML/`, ни в `statistics/`, ни в `ML/baseline/` нет модуля, соответствующего описанию 07b шаг 1 (RF `n_estimators=100, max_depth=10, random_state=42` + walk-forward CV по времени + перестановочный тест). Поиск `grep -rn "RF-gate|RF-gейт|совместный RF|predictability gate" ML/ statistics/ docs/superpowers/` — пуст.

---

## Сводка замечаний

| ID | Важность | Кратко |
|----|---------|--------|
| C1 | Критично | Порядок 07b противоречит README и `07-baseline-first.md` (07b должен идти до 07, но в README стоит после 07) |
| C2 | Критично | Совместный RF-гейт не реализован — обязательный компонент методики не существует в коде |
| C3 | Важное | RF-гейт заявляет walk-forward CV по времени, но в проекте нет реализации TimeSeriesSplit (только комментарий в EDA) |
| C4 | Важное | Документ не упоминает 03b (feature selection) в заказе pipeline, хотя 03b идёт между 03 и 07 |
| C5 | Важное | Параметры RF не полны: нет `n_jobs`, `class_weight`, `min_samples_leaf` — воспроизводимость под вопросом |
| C6 | Важное | MI-отчёт выдаёт `PASS`/`FAIL` verdicts, но 07b говорит MI — «не основание для reject» — расхождение методики и отчёта |
| C7 | Важное | «joint-MI в >5–10 измерениях статистически недостоверно» — источник не подтверждается; spec говорит о 42-мерной ненадёжности |
| C8 | Улучшение | «минимум 199 перестановок; p_min=0.005» рассинхрон с spec/кодом: в обоих 200, 1/(200+1)≈0.00498 |
| C9 | Улучшение | Нет требований к воспроизводимости/сохранению RF-гейта как structured artifact (JSON) |
| C10 | Улучшение | Нет ответа на вопрос о делении N наборов через тренинг: сказано «раскрыть число», но не указано как сравнивать/корректировать |
| C11 | Улучшение | «typo xor» в «XOR-эффект» — избегать англицизмов вне списка разрешённых |
| C12 | Вопрос | Нет association между RF-гейтом 07b и RF-фильтром 03b шаг 2 — оба обучают RF с одними параметрами |
| C13 | Вопрос | Есть ли single seed (`random_state=42`) у RF-гейта; как работает «проверить по seeds» из строки 69? |
| C14 | Улучшение | Документ не указывает `decision_time` / target contract как обязательные входы явно (только «target contract» общо) |

---

## Полные замечания

### C1 — Критично: порядок 07b противоречит README и 07-baseline-first.md

- **Место**: `docs/methodology/README.md:60-61` против `docs/methodology/07-baseline-first.md:17` и `docs/methodology/07b-predictability-gate.md:98`.
- **Суть**: В README таблица «задача → файл» ставит 07b **после** 07-baseline-first (строка 61 после 60). Но `07-baseline-first.md:17` шаг 0 требует: «Убедиться, что `07b-predictability-gate.md` пройден; `FAIL` гейта запрещает обучение и baseline». В 07b строка 98 ветвления: «RF-гейт PASS → далее `07-baseline-first.md`». Эти указания согласованы между собой (07b → 07), но противоречат таблице в README, где порядок обратный. Новый пользователь методики, идущий по таблице, попадёт в 07 (baseline) раньше 07b и нарушит обязательный pre-step.
- **Доказательство**:
  - `docs/methodology/README.md:60`: `| Baseline-модели: dummy, простые ML, сравнение | 07-baseline-first.md |`
  - `docs/methodology/README.md:61`: `| Предобученческая проверка предсказуемости ... | 07b-predictability-gate.md |`
  - `docs/methodology/07-baseline-first.md:17`: «0. Убедиться, что `07b-predictability-gate.md` пройден; `FAIL` гейта запрещает обучение и baseline.»
  - `docs/methodology/07b-predictability-gate.md:98`: «RF-гейт PASS → далее `07-baseline-first.md`».
- **Почему важно**: нарушение порядкаereoда шагов — типовой источник leakage и ложных выводов (A3-typical-false-conclusions.md упоминает «сразу обучать Transformer без baseline» как типовую ошибку). Аудитория projectа идёт по README первым.
- **Рекомендация**: переставить строку 61 в README **до** строки 60, чтобы 07b стоял между 06b и 07. Либо переименовать 07 → 07c (baseline), чтобы порядок нумерации совпадал с порядком выполнения. Альтернатива — явный текстовый маркер в README «важно: 07b выполнять до 07».

### C2 — Критично: совместный RF-гейт не реализован в коде

- **Место**: `docs/methodology/07b-predictability-gate.md:21-40` (шаг 1); сравнить с `statistics/mi_upper_bound.py`, `statistics/run_mi_upper_bound.py`.
- **Суть**: Документ заявляет **обязательный** совместный RF-гейт как единственную проверку, способную отклонить набор (строка 9: «Решение об отклонении принимает **только совместный RF-гейт**»; строка 65: «Отклонить набор без обучения — только если совместный RF-гейт: p ≥ 0.05»). Однако реализован только MI-скрининг (шаг 2, **опциональная диагностика**). RF-гейт — отсутствующий артефакт. Поиск:
  - `grep -rn "RF-gate|RF-gейт|predictability gate|совместный RF" ML/ statistics/` — пусто.
  - В `ML/baseline/feature_ablation.py:163` есть `RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)`, но это часть feature-selection сцены (03b шаг 2), **не** совместный гейт с walk-forward CV и перестановочным тестом.
  - В `ML/baseline/benchmark_fractal_stop_stage3_1.py`, `oracle_fractal_stop_fav.py` и др. есть RF-обучение для других сцен, но ни одно экспонирует API вида «given (X_train, y_train) → verdict + p-value + walk-forward scores».
- **Доказательство**: `docs/methodology/07b-predictability-gate.md:9,21-40,65-67` против `ls statistics/` (только `mi_upper_bound.py`, `run_mi_upper_bound.py`, `signal_tracer.py`, `statistics.py`, `EDA.ipynb`), и `ls ML/baseline/ | grep -i gate` — пусто.
- **Почему важно**: методика требует **обязательной** проверки, отсутствие которой блокирует переход к обучению (`07-baseline-first.md:17`). В проекте сейчас **невозможно** пройти gate 07b → формально весь дальнейший pipeline нарушил методику, либо gate молчаливо обходили. Любые отчёты экспериментов, заявляющие baseline-training, формально в долге перед обязательным pre‑gate.
- **Рекомендация**: либо реализовать `statistics/predictability_gate.py` (RF + `TimeSeriesSplit` + permutation test,JSON-артефакт согласно 16-reporting-audit.md) и привязать к нему тесты (по шаблону `tests/test_mi_upper_bound.py`), либо явно пометить 07b как `DRAFT`/`planned` (как сделано с другими «b»-разделами в каталогах планов), чтобы не выдавать идею за обязательную практику. Подробнее форма — `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md` (шаблон спецификации): identify `Что оценщик делает`, `Артефакты` (JSON + plot), `Stop Rules`.

### C3 — Важное: отсутствие TimeSeriesSplit / walk-forward CV в коде

- **Место**: `docs/methodology/07b-predictability-gate.md:23`: «на train с **walk-forward CV по времени** (перемешивание строк запрещено)».
- **Суть**: Документ требует walk-forward CV по времени, но в проекте **нет точки реализации** `TimeSeriesSplit` или эквивалента. Поиск `grep -rn "TimeSeriesSplit" ML/ statistics/` возвращает только комментарий в EDA ноутбуке `statistics/reports/EDA_executed.ipynb:5290` (discarded code). Реализованный MI-оценщик не использует CV для verdicts — он использует fold-CI как метрику стабильности (`mi_upper_bound.py:144-155`), а verdict берётся из permutation p-value на полном объёме train. Для RF-гейта тот же паттерн невозможен в sklearn без явного `TimeSeriesSplit`.
- **Доказательство**:
  - `grep -rn "TimeSeriesSplit" ML/ statistics/` → только `statistics/reports/EDA_report.md`, `statistics/reports/EDA_executed.ipynb`, `statistics/EDA.ipynb` (все три — строки комментария «Временной порядок (для TimeSeriesSplit)», без реализации).
  - `statistics/mi_upper_bound.py:122-178` — нет CV для verdict.
  - `docs/methodology/11-robustness.md:55-69` даёт определения `expanding`/`anchored`/`rolling`/`warm-start`, но нигде не фиксирует выбор по умолчанию для 07b.
- **Почему важно**: без указания **типа** walk-forward (expanding vs anchored vs rolling vs TimeSeriesSplit) «walk-forward CV по времени» неоднозначен. Метрика RF-гейта (val score) сильно зависит от выбора окна; разные реализации дадут разные вердикты. Кроме того, 11-robustness.md:68 явно предупреждает: «Окно с малым N можно показывать только как diagnostic» — это влияет на конфигурацию CV в 07b.
- **Рекомендация**:
  1. Указать в 07b тип walk-forward (минимум — `TimeSeriesSplit(n_splits=K)` sklearn; обосновать K относительно `sample_size_gate` из `06-temporal-split.md:50-67`).
  2. Явно указать, что **verdict** берётся по агрегированному CV-score против перестановочного фона, а не по одному окну (это уже в духе `11-robustness.md:67-69` — «выбирать не максимальный PF одного окна, а устойчивый паттерн»).
  3. Сохранять seed-стабильность (см. `11-robustness.md:55-69`).

### C4 — Важное: документ игнорирует 03b (feature selection) в заказе pipeline

- **Место**: `docs/methodology/07b-predictability-gate.md:15-17` (входы «проверяемый набор признаков (live-safe, после Leakage Gate п.3)»), в противовес `docs/methodology/03b-feature-selection.md:10` и `docs/methodology/README.md:55`.
- **Суть**: 07b принимает «набор признаков (live-safe, после Leakage Gate п.3)» и не упоминает 03b (feature-selection gate), который в README (`README.md:55`) стоит **после** 03 и **до** 07. При этом `03b-feature-selection.md:10` явно связывает себя с 07b: «Проверка „предсказуем ли target от набора вообще“ — отдельный гейт: `07b-predictability-gate.md`». Это односторонняя ссылка; 07b не возвращает её. Следствие: трактовка «на каком наборе проверять предсказуемость» (полный список / отфильтрованный 03b / предварительно отобранный через RF-важность) — неоднозначна.
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:17` — единственный „pipeline-референс“ в `Входах` — это Leakage Gate п.3, **03b отсутствует**.
  - `docs/methodology/03b-feature-selection.md:10` явно отправляет читателя в 07b.
  - `docs/methodology/README.md:54-55,60-61` подтверждает порядок: 03 → 03b → ... → 07 → 07b.
- **Почему важно**: отложенный/отфильтрованный 03b набор может дать FAIL на 07b даже при PASS полного, либо наоборот — поэтому нужно явно фиксировать, какой набор проходит 07b: «полный live-safe» или «минимальный, после 03b». Детекция „signalльь в шуме“ зависит от состава набора (07b:37-40 — «при больших W дешевле агрегировать окно до статистик»).
- **Рекомендация**: в разделе «Входы» указать: «проверяемый набор — полный live-safe (после `03b-feature-selection` если selection уже выполнен); в отчёте раскрывать, на каком наборе считается gate». Либо явно зафиксировать: 07b работает **до** 03b (как prefilter для feature selection), чтобы не смешивать цели.

### C5 — Важное: неполные параметры RF

- **Место**: `docs/methodology/07b-predictability-gate.md:22`: «Random Forest (`n_estimators=100, max_depth=10, random_state=42`)».
- **Суть**: Указаны три параметра, но в `ML/baseline/` все RF-использования фиксируют дополнительно `n_jobs=-1` (для скорости), а в `ML/baseline/oracle_fractal_stop_fav.py:111` — и `min_samples_leaf=50`. В progetto также встречаются дисбалансированные классы (см. `docs/reports/2026-08-11-mi-upper-bound.md` «direction/attribute class 0 ~3.84%», и `03b:28` — про precision/recall/F1/MCC). Несохранённые параметры (`class_weight`, `min_samples_leaf`, `n_jobs`) сделают разные прогоны не воспроизводимыми.
- **Доказательство**:
  - `ML/baseline/feature_ablation.py:163`: `RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)` — добавлено `n_jobs=-1`.
  - `ML/baseline/oracle_fractal_stop_fav.py:111`: добавлено `min_samples_leaf=50`.
  - `docs/methodology/03b-feature-selection.md:25` — тот же mismatch (тоже 3 параметра), но это связанная проблема.
  - `docs/methodology/05-eda-data-quality.md` и 03b `'discriminant' class balancing` — упоминается в контексте дисбаланса, но в 07b баланса классов не упоминается.
- **Почему важно**: дисбаланс классов direction (см. JSON отчёта MI: `direction_class_balance` зафиксирован как `{"-1": ..., "0": ..., "1": ...}`) значителен. Если RF без `class_weight` обучается базовым majority — он занижает чувствительность к minorитарным классам → ложно FAIL на данных, где для разбросанных rare-классов существует истинный сигнал. Сильная гипотеза про FAIL из 07b строки 35-37 («FAIL при сильной гипотезе signal в порядке шагов — не automatic reject») требует сравнения метрик; параметр `class_weight` критичен.
- **Рекомендация**: добавить в 07b: `class_weight='balanced'` для несбалансированного target, зафиксировать `n_jobs`, `min_samples_leaf`. Либо явно указать: «параметры по умолчанию: `sklearn.ensemble.RandomForestClassifier` defaults with `random_state=42`»; и **требовать** в отчёте полный набор используемых параметров RF (это уже частично в 07b строке 59 — «параметры RF и CV», но список не формализован).

### C6 — Важное: расхождение между MI-отчётом и 07b (вердикт PASS/FAIL MI)

- **Место**: `docs/methodology/07b-predictability-gate.md:56`: «Результат MI-скрининга **не является основанием для reject**»; `docs/reports/2026-08-11-mi-upper-bound.md:5,207` (′PASS для amplitude / FAIL на validation direction′).
- **Суть**: 07b устанавливает, что MI — **опциональная диагностика** и **не вправе отклонять набор**. В то же время фактический отчёт MI использует термины `PASS`/`FAIL` для verdicts (`docs/reports/2026-08-11-mi-upper-bound.md:5` «Смешанный — amplitude PASS / direction FAIL на validation», строка 207 «PASS для amplitude»). В отчёте ставится verdict (через `perm_p_value < 0.05`), но **нет явного предупреждения**, что этот PASS/FAIL ≠ gate-вердикт 07b. Читатель может спутать «PASS MI» с «PASS predictability gate», хотя RF-гейт (обязательный) не запускался.
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:42,56`: «MI-скрининг (опционально, диагностика)»; «Результат MI-скрининга не является основанием для reject».
  - `docs/methodology/07b-predictability-gate.md:70-72`: «Диагностический R²-потолок из MI ниже лучшего исторического R² target — не reject, а предупреждение».
  - `docs/reports/2026-08-11-mi-upper-bound.md:5`: «Вердикт: смешанный — amplitude PASS (p=0.005 на train и validation), direction FAIL на validation (p=0.229)».
  - `docs/reports/2026-08-11-mi-upper-bound.md:207`: «**PASS** для amplitude (perm_p_value = 0.005 на train и validation)».
  - `ML/reports/mi_upper_bound.json`: ключи verdicts через `perm_p_value` на каждом split.
- **Почему важно**: согласованность методики и отчётов — обязательная проверка по `16-reporting-audit.md:91` (отчёт обязан раскрывать forbidden_interpretations). MI-отчёт имеет блок `forbidden_interpretations` (`2026-08-11-mi-upper-bound.md:16`), но в нём нет явного «PASS/FAIL MI ≠ gate verdict 07b». 07b строка 56 указывает на «не основание для reject», но не объясняет, как MI-вердикт должен помечаться в отчётах, чтобы его не путали с gate.


### C7 — Важное: «joint-MI в >5–10 измерениях» — источник не подтверждается

- **Место**: `docs/methodology/07b-predictability-gate.md:53-55`: «прямое joint-MI в >5–10 измерениях статистически недостоверно. Если всё же нужен joint-MI: топ-k фич (k ≤ 5), PCA-компоненты, групповое MI по семействам.»
- **Суть**: В 07b заявлено, что joint-MI теряет достоверность в «>5–10 измерениях». Сравним со spec'ом: «Оценка I(X1..X42; Y) в **42-мерном** пространстве ненадёжна при доступных объёмах данных» (`2026-08-11-mi-upper-bound-design.md:68`). Spec объясняет ненадёжность **объёмом данных** (train ~41K строк × 42 признака), не привязываясь к волшебной границе «5-10». Конкретная граница 5-10 в 07b не подкреплена ссылкой на источник, расчётом или опыт проекта. У `2026-08-11-mi-upper-bound-design.md:181,244-245` joint-MI по топ-k (k≤5) и npeet обозначены как **follow-up исследование** (открытые вопросы), не как готовое правило.
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:53`: «прямое joint-MI в >5–10 измерениях статистически недостоверно».
  - `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md:68`: «Оценка I(X1..X42; Y) в **42-мерном** пространстве ненадёжна при доступных объёмах данных» — **не** «>5–10».
  - `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md:181`: «Joint-оценка (например, npeet на пониженной размерности) — отдельное follow-up исследование».
  - `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md:234-245`: «Stop rules», «Открытые вопросы для implementation plan» — нет утверждения «>5–10».
  - В отчёте 2026-08-11-mi-upper-bound.md тоже не упоминается «>5–10 измерений».
- **Почему важно**: методика — управляющий документ; некрепкое число может быть использовано как догмат. Если в следующем эксперименте кто-то посчитает joint-MI в 7 измерениях и доверится ему (ведь «5-10 — граница, 7 внутри»), это будет противоречить spec, где упор на **объём данных** и конкретный объект (XAUUSD H1, 42 признака). Правильный критерий — «данные/параметр KSG достаточны для данной размерности», который требует отдельных обоснований (как в spec) и проведения empirical проверки.
- **Рекомендация**: убрать «>5–10 измерений»; вставить конкретнее: «joint-MI в 42-мерном пространстве недостоверен при объёмах train (~41K строк); если всё же нужен joint-MI — редуцировать до топ-k (k≤5 по маргинальному MI), PCA-компонент или группового MI по семействам, и оценить устойчивость через с перестановочный тест». Сослаться на spec 2026-08-11-mi-upper-bound-design, Шаг 5: «joint MI follow-up».

### C8 — Улучшение: p_min = 0.005 рассинхронизирован с spec/кодом

- **Место**: `docs/methodology/07b-predictability-gate.md:47`: «перестановочный p-value (минимум 199 перестановок; p_min = 1/(n_perm+1) = 0.005)».
- **Суть**: 07b фиксирует минимум 199 перестановок → `p_min=1/(199+1)=0.005`. В spec: «≥200 перестановок y» (`2026-08-11-mi-upper-bound-design.md:66`). В коде `statistics/run_mi_upper_bound.py:148` default `--n-permutations=200`. В фактическом прогоне `ML/reports/mi_upper_bound.json:5` — `n_permutations: 200`, `p_min = 1/(200+1) ≈ 0.00498`. То есть «199» в 07b выбрано **искусственно** так, чтобы заменить 200 на «199+1=200» по формуле — логика понятна, но создаёт путаницу: reader видит «199», конфиг/spec — «200». Кроме того, `07b:78` «Число перестановок зафиксировано и отражено в минимально достижимом p» — это правильно, но требует **одного** числа в коде/spec/методике.
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:47`: «п_min = 1/(n_perm+1) = 0.005».
  - `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md:66`: «≥200 перестановок».
  - `statistics/run_mi_upper_bound.py:148`: `--n-permutations default=200`.
  - `ML/reports/mi_upper_bound.json:5`: `"n_permutations": 200`, `"perm_p_value": 0.004975...`.
- **Почему важно**: согласованность параметров между методикой, spec и кодом — обязательное условие воспроизводимости (16-reporting-audit.md:97 — «ключевые числа сверены со structured artifact»). Разночтение «минимум 199» vs «≥200» вынуждает будущего агента выбирать — и, например, взять `n_perm=199` в violation фактического кода. p_min 0.005 — округлённое значение, но методика должна **точно** отражать код.
- **Рекомендация**: в 07b указать «минимум 200 перестановок» (как в spec), и пояснить, что `p_min = 1/(200+1) ≈ 0.00498` (округление 0.005 — приближённое). Либо завести одну `config.py`/константу в коде (например, `MIN_PERMUTATIONS = 200`) и в методике сослаться на неё.

### C9 — Улучшение: нет требования к RF-гейту как structured artifact

- **Место**: `docs/methodology/07b-predictability-gate.md:58-61` (раздел «Фиксация результата»).
- **Суть**: Документ требует «Вердикт RF-гейта, p-value, параметры RF и CV, число проверенных наборов — в отчёт эксперимента (формат: `16-reporting-audit.md`)». Но 16-reporting-audit.md:97 требует: «Ключевые числа в отчёте (AUC, PF, trades count, yearly PF) **сверены со structured artifact (JSON/CSV/parquet)**. Если structured artifact отсутствует, отчёт обязан содержать команду воспроизведения и hash входов». 07b не упоминает structured artifact (JSON) для RF-гейта, только текстовый отчёт. Для сравнения, MIский spec (`2026-08-11-mi-upper-bound-design.md:212-230`) перечисляет: «Артефакты: `ML/reports/mi_upper_bound.json` ... JSON обязан содержать: MI для каждого таргета, permutation p-value, ..._Verdict: PASS/FAIL/INCONCLUSIVE».
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:58-61`: упоминает только «отчёт эксперимента».
  - `docs/methodology/16-reporting-audit.md:97`: «Ключевые числа ... сверены со structured artifact (JSON/CSV/parquet). ... Расхождение отчёт↔artifact — блокирующая ошибка.»
  - `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md:214-218`: указаны конкретные пути артефактов.
- **Почему важно**: отсутствие structured artifact означает, что следующий агент не сможет сверить «p-value=0.03» из отчёта с реальным значением → risk расхождения отчёта и фактической оценки (16-reporting-audit.md:120 «Копировать числа в отчёт вручную без сверки со structured artifact — источник расхождений отчёт↔результат»).
- **Рекомендация**: в 07b добавить в «Фиксация результата»: «RF-гейт сохраняется как `ML/reports/predictability_gate_<run>.json`: набор, RF-параметры, CV-конфигурация, score на оригинале, перестановочный фон (массив), p-value, n_permutations, verdict. Plot fold-scores и permutation distribution. JSON сверяется с отчётом (см. `16-reporting-audit.md:97`)».

### C10 — Улучшение: «выбор лучшего из N проверок смещён» без протокола

- **Место**: `docs/methodology/07b-predictability-gate.md:79-80`: «Если проверялось несколько наборов — раскрыть их число: выбор лучшего из N проверок смещён (multiple testing, см. `16-reporting-audit.md`)».
- **Суть**: Документ говорит «раскрыть число» и ссылается на 16-reporting-audit.md, но 16-reporting-audit.md:22 только требует **disclosure** поиска (cumulative_search_budget), без **коррекции** (нет Bonferroni/BH). 09-validation-freeze.md:120 уточняет: «Не корректировать множественное тестирование при переборе >10 конфигураций на одном validation. Чем больше search budget, тем выше риск ложного winner; результат без коррекции не должен становиться `frozen_rule_for_locked_test`». 07b даёт **несмотря на ссылку на 16-reporting-audit** — без указания, что **делать** при several провальных наборах. «multiple testing» не разобрано как практическое последствие для gate: должен ли быть `Bonferroni-corrected p-value < 0.05` для PASS? Или достаточно disclosure?
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:79-80`: правило только «раскрыть число».
  - `docs/methodology/16-reporting-audit.md:22`: «Multiple Testing Context: ... применённая коррекция или статус `DIAGNOSTIC_ONLY`/`RESEARCH_ONLY`».
  - `docs/methodology/09-validation-freeze.md:120`: «Не корректировать ... >10 конфигураций ... результат без коррекции не должен становиться `frozen_rule_for_locked_test`».
  - `docs/methodology/A3-typical-false-conclusions.md:28`: «Множественное тестирование без коррекции: лучший PF из большого числа конфигураций может оказаться статистически неотличим от случайности».
- **Почему важно**: практический сценарий: агент проверил 5 наборов → 4 FAIL, 1 PASS при p≈0.04. Документ 07b требует «раскрыть 5», но не указывает, что PASS-набор уже с поправкой Bonferroni (p<0.01 или 0.05/5=0.01), либо что статус понижается до `research_only` (по правawe `09-validation-freeze.md:120`). Если агент перейдёт к 07-baseline-first с p=0.04 без коррекции — будет ложноположительный gate.
- **Рекомендация**: в 07b раздел «Обязательные проверки» добавить: «Если RF-гейт проверял N наборов и хотя бы один получил PASS, применять **Bonferroni correction**: PASS если `p < 0.05/N`. Если `N*hath` policy для нескольких gate (полный + подгруппы по фичам) — раскрывать cumulative_search_budget Meinung, статус не выше `DIAGNOSTIC_ONLY` до отдельного повторного прогона» (по аналогии с `09-validation-freeze.md:120` и `00-research-management.md:88-89`).

### C11 — Улучшение: «XOR-эффект» — англицизм вне списка разрешённых

- **Место**: `docs/methodology/07b-predictability-gate.md:50`: «маргинальное MI не видит взаимодействий (XOR-эффект)».
- **Суть**: Per `AGENTS.md` «Rules of dialogue»: язык ответов — простой, ясный, русский; «английские слова допустимы только для имён файлов, функций, колонок, команд, библиотек и устойчивых обозначений проекта: CSV, MT4, ATR, PF, PnL. Технический термин при первом использовании объяснять». «XOR» — строгий математический термин, но в контексте ML он означает «взаимодействие признаков через исключающее-или»; sing слово не широко понятно русскоговорящему читателю-неспециалисту. AGENTS.md упоминает, что я превзoxожу пользователя по знаниям и обязан пояснять.
- **Доказательство**: `AGENTS.md` > «Правила ответов» > «НЕ ИСПОЛЬЗУЙ: жаргон, англицизмы и узкие термины. Английские слова допустимы только для имён файлов, функций, колонок, команд, библиотек и устойчивых обозначений проекта». «XOR» не входит в список явных разрешённых терминов.
- **Почему важно**: нарушение стилевой политики проекта; в остальном документе 07b строго соблюдается стиль (RF, MI, CV, PASS, FAIL помеченом как методические термины). Этот термин **embedded** в важное объяснение — "маргинальное MI не видит взаимодействий" — и должен быть понят.
- **Рекомендация**: заменить на «взаимодействие признаков (исключающее-или, классический пример XOR: две бинарные фичи, каждая без сигнала, но их XOR даёт таргет)», либо добавить в скобках аналогию. Либо использовать «синергию» (из spec `2026-08-11-mi-upper-bound-design.md:181` «возможна синергия»).

### C12 — Вопрос: связь RF-гейта 07b и RF-фильтра 03b шаг 2

- **Место**: `docs/methodology/07b-predictability-gate.md:22` (`n_estimators=100, max_depth=10, random_state=42`) против `docs/methodology/03b-feature-selection.md:25` (те же параметры).
- **Суть**: Оба документа описывают RF `n_estimators=100, max_depth=10, random_state=42` на train. В 03b — это фильтр важности (важность признаков → удаление шумовых); в 07b — совместный гейт предсказуемости (RF + walk-forward CV + permutation test). Одинаковые параметры — либо это дублирование, либо 07b переиспользует 03b. Документы не ссылаются друг на друга.
- **Доказательство**:
  - `docs/methodology/03b-feature-selection.md:25`: «Обучить RF (`n_estimators=100, max_depth=10, random_state=42`) на train. Извлечь `feature_importances_`».
  - `docs/methodology/07b-predictability-gate.md:22`: «Random Forest (`n_estimators=100, max_depth=10, random_state=42`) на train с **walk-forward CV по времени**».
- **Почему важно**: одинаковый RF с одинаковой конфигурацией в двух местах — опасность drift: если parameters RF в одном обновят, а в другом забудут — конфигурации расходятся. Кроме того, неясно, можно ли **переиспользовать** один прогон RF из 07b (c CV) для importance-фильтрации 03b, чтобы не запускать RF дважды. С точки зрения прагматики проект — personal research; экономия процессорного времени важна.
- **Рекомендация**: в 07b указать связь с 03b: «RF-гейт 07b — расширение шага 2 из `03b-feature-selection.md`: тот же RF-объект, дополненный walk-forward CV и permutation test. Importance-значения можно переиспользовать для шага 2 из 03b». Либо развести их: «07b использует `TimeSeriesSplit` CV → типично другое распределение RF importance по сравнению с 03b (по полному train)» — и зафиксировать выбор отдельно.

### C13 — Вопрос: single seed `random_state=42` против «проверить стабильность по seeds»

- **Место**: `docs/methodology/07b-predictability-gate.md:22,68-69`: «`random_state=42` ... Если RF-гейт FAIL на малой выборке, это может быть ошибка второго рода: проверить стабильность по seeds и размеру train до окончательного reject».
- **Суть**: Документ фиксирует единственный seed 42 для основного прогона, но требует «проверить стабильность по seeds» при FAIL на малой выборке. Не разобрано: **сколько seeds**, **какой verdict при разных seeds** (majority vote? все должно пройти? среднее score?). Замечание в A3 (типовые ошибки): «Один seed — одна выборка из распределения метрик; разница в AUC около 0.001–0.005 на single-seed неразличима с шумом. Без multi-seed CI нельзя заявлять воспроизводимость».
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:22`: один `random_state=42`.
  - `docs/methodology/07b-predictability-gate.md:68-69`: «проверить стабильность по seeds и размеру train».
  - `docs/methodology/A3-typical-false-conclusions.md:31`: «Один удачный результат на проверочной выборке трактовался как устойчивый сигнал. Один seed — одна выборка ... Без multi-seed CI нельзя заявлять воспроизводимость».
  - `docs/methodology/00-research-management.md:67-75`: «min_seeds: ...» явно требуется в plan.
- **Почему важно**: «проверить стабильность по seeds» — без конкретики легко исполнить формально (запустить 2-3 seeds и принять решение на глаз). Должно быть: «минимум 5 seeds, quantitative rule (e.g. все 5 p-values <0.05, либо среднее + min/max, зафиксировать в plan)».
- **Рекомендация**: указать **минимум** seeds (5 — по аналогии с `2026-06-23-stage5_0d-diagnostic-screening.md:46` — `Seeds: [42, 77, 123]` для screening и `min_seeds` из `00-research-management.md:73`), и правило интерпретации: «PASS устойчив, если >X% из N seeds дают p<0.05; при mixed → проверяем мощность / расширяем train / понижаем статус до `research_only`».

### C14 — Улучшение: `decision_time` отсутствует в обязательных входах

- **Место**: `docs/methodology/07b-predictability-gate.md:13-17` (Входы).
- **Суть**: В списке входов: `train split`, `target contract`, `проверяемый набор признаков`. Не упомянут `decision_time`. Но `03-feature-contract-leakage.md:46` и `00-research-management.md:20` требуют `decision_time` как фундамент pre-ML. 07b — единственный этап, использующий(target contract + признаки), и без `decision_time` непонятно, что mean «train split» с точки зренияleakage: если `decision_time` неизвестен, как проверить, что все признаки live-safe (как требует вход 17)?
- **Доказательство**:
  - `docs/methodology/07b-predictability-gate.md:13-17`: нет `decision_time`.
  - `docs/methodology/03-feature-contract-leakage.md:46`: «Зафиксировать `decision_time`».
  - `docs/methodology/00-research-management.md:20`: «Зафиксировать `decision_time`: open/close бара, таймфрейм, инструмент, момент входа».
- **Почему важно**: 07b требует «проверяемый набор признаков (live-safe, после Leakage Gate п.3)» — но leakage gate проверяет live-safe именно **относительно** `decision_time`. Если вход не требует `decision_time` в 07b, агент может запустить gate на наборе без полной уверенности оfreshness каждой фичи — формально пройдя «после Leakage Gate», но технически с пробелом.
- **Рекомендация**: добавить в Входы 07b: «`decision_time` (из `00-research-management.md` и Leakage Gate п.3)». Либо явно: «проверяемый набор признаков (live-safe, после Leakage Gate п.3, с зафиксированным `decision_time`)».

---

## Независимая проверка утверждений документа

### Проверка формулы `p_min = 1/(n_perm+1)` (строка 47)

- **Утверждение**: «p_min = 1/(n_perm+1) = 0.005» при n_perm=199.
- **Пересчёт**: python `1/(199+1) = 0.005`. Верно (для n=199).
- **Фактический код** (`statistics/mi_upper_bound.py:163`): `perm_p_value = (np.sum(...) + 1) / (n_permutations + 1)` — формула идентичная.
- **Однако**: spec и код используют `n_perm=200`, не 199 → `1/201 ≈ 0.00498`. См. C8.

### Проверка «формула R²-потолка из маргинального MI» (строка 70-72)

- **Утверждение 07b:70-72**: «Диагностический R²-потолок из MI ниже лучшего исторического R² target — не reject, а предупреждение».
- **Spec проверка** (`2026-08-11-mi-upper-bound-design.md:25-28`): `R² <= 1 - 2^(-2·I(features; target))` — формула для **joint MI**, не для `mean marginal MI`.
- **07b:51-52** явно отмечает: «среднее маргинальное MI — диагностическая величина, **не строгая граница** совместной информации». Согласуется.
- **Код** (`statistics/mi_upper_bound.py:173`): `r2_ceiling = 1 - 2**(-2 * mean_mi)` — где `mean_mi` — среднее маргинальных MI, **не joint**. Это означает, что `r2_ceiling` в коде — **оценка** снизу для потенциального joint MI (так как joint MI ≥ max маргинальных, но ≤ sumмаргинальных; возможна синергия). Spec:9 explains: «среднее и максимум **маргинальных** MI... интерпретация R²-потолка из неё — диагностическая (см. Ограничения, п. 4)». Согласуется с 07b.
- **Это подтверждено** в 07b:70-72: «не reject, а предупреждение» — корректно, т.к. `r2_ceiling` диагностический.

### Проверка «walk-forward CV по времени» против «shuffle запрещён» (строка 23)

- **Утверждение 07b:23**: «walk-forward CV по времени (перемешивание строк запрещено)».
- **06-temporal-split.md:33**: «Проверить, что shuffle временных строк не применяется» — согласовано.
- **09-validation-freeze.md не указывает CV для baseline**, но 11-robustness.md:55-69 перечисляет 4 вида walk-forward. См. C3.

### Проверка «joint-MI в >5-10 измерениях» (строка 53)

- См. C7. Утверждение **не подтверждается** первоисточниками проекта (spec говорит о 42-мерной ненадёжности из-за объёма данных, не из-за общего правила «>5-10»).

### Проверка «проект не закрывать Fractal Stop» (имплицитное утверждение)

- Документ 07b не упоминает Fractal Stop — но его критика «FAIL при сильной гипотезе» прямо согласуется с `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md` (sell +0.0111 < 0.02 порог). Однако в 5.0d XGBoost читался как **baseline screening** (см. spec 5.0d), а не предсказуемость-гейт. Это на будущее.

---

## Сводка рекомендаций

1. **C1 (критично)**: переставить 07b **до** 07 в `docs/methodology/README.md:60-61`.
2. **C2 (критично)**: реализовать RF-гейт (`statistics/predictability_gate.py` + тесты) либо пометить 07b как `DRAFT`/`planned`.
3. **C3 (важное)**: указать тип walk-forward CV (минимум `TimeSeriesSplit`) и обязательность verdict по агрегату, не по одному окну.
4. **C4 (важное)**: явно связать 07b с 03b (какой набор проходит gate: полный или после 03b).
5. **C5 (важное)**: формализовать полный параметр RF (`class_weight`, `n_jobs`, `min_samples_leaf`) — необходим для class imbalance в direction.
6. **C6 (важное)**: в MI-отчёте не использовать термины `PASS`/`FAIL` без префикса `mi_screening` или явно пометить «MI verdict ≠ gate verdict».
7. **C7 (важное)**: убрать «>5-10 измерений»; заменить на конкретику spec (42-мерная ненадёжность, объём данных, top-k ≤5).
8. **C8 (улучшение)**: согласовать «199» vs «200» перестановок — указать «200 (p_min ≈ 0.005)».
9. **C9 (улучшение)**: требовать JSON артефакт RF-гейта с сверкой отчёт↔artifact (по 16-reporting-audit.md:97).
10. **C10 (улучшение)**: указать процедуру коррекции multiple testing (Bonferroni `p < 0.05/N` или понижение статуса).
11. **C11 (улучшение)**: заменить «XOR-эффект» на русский эквивалент с пояснением.
12. **C12 (вопрос)**: развязать RF-гейт 07b и RF-фильтр 03b шаг 2 (можно ли переиспользовать прогон).
13. **C13 (вопрос)**: зафиксировать `min_seeds` (≥5) и правило интерпретации mixed seeds для FAIL.
14. **C14 (улучшение)**: добавить `decision_time` в обязательные входы 07b.

## Мониторинг ошибок

- **STRUCT**: `docs/methodology/07b-predictability-gate.md` is **untracked** в git (`git status` показал `untracked files`) — новый файл, не закоммичен. Рекомендация: после правок закоммитить.
- **DOC**: в проекте нет реализации RF-гейта — ссылка 07b на будущий артефакт фактически битая (без явной пометки «planned»). См. C2.
- **MCP**: не применимо.
