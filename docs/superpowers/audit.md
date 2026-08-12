# Аудит плана `docs/superpowers/plans/2026-08-11-mi-upper-bound.md`

**Дата аудита:** 2026-08-12
**Аудитируемый документ:** `docs/superpowers/plans/2026-08-11-mi-upper-bound.md` (1044 строки)
**Связанный spec:** `docs/superpowers/specs/2026-08-11-mi-upper-bound-design.md`

## Метод аудита

Доказательный аудит по фактам и уликам, а не по впечатлениям. Каждое замечание подтверждено командой, файлом или численным экспериментом. Проверены: фактические/алгоритмические ошибки, неподтверждённые утверждения, соответствие методологии `docs/methodology`, прагматичность и полнота.

Проверенные артефакты контекста:
- `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`, `DATA/Nero_test_labeled.csv` (заголовки, число строк, дубли `time`)
- `DATA/XAUUSD_H1_OHLC.csv` (диапазон, уникальность `time`)
- `ML/entry_path_task.py` (`ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS`, 42 признака)
- `ML/entry_path_feature_bank.py` (`build_entry_path_feature_bank`, 40 bank-колонок)
- `statistics/feature_catalog.json` (233 признака, MI в nats)
- `statistics/EDA.ipynb` (n_neighbors=3, target=`signal`, top-100 по корреляции)
- `ML/feature_screen_entry_path.py` (референс реализации)
- `tests/test_live_safe_audit.py` (PASS для entry_path_v1, FAIL для 4 систем)
- `docs/audit/retrospective.md` (источник legacy R²)
- `docs/methodology/00-research-management.md`, `03-feature-contract-leakage.md`, `05-eda-data-quality.md`, `06b-oracle-preflight.md`, `16-reporting-audit.md`
- `statistics/data_contract_smoke_check.py` (дефолтные пути)

Численные эксперименты выполнены через `./.venv/bin/python`.

---

## Сводка замечаний

| # | Важность | Место | Краткая суть |
|---|---|---|---|
| 1 | **Критично** | Task 2 Step 3, `_mi_scores`, `estimate_mi` | sklearn MI возвращает nats, план трактует как bits — формула R² потолка неверна |
| 2 | **Критично** | Task 5, `estimate_mi` при `n_permutations=0` | формула `(0+1)/(0+1)=1.0` даёт всегда `perm_p_value=1.0` → всегда FAIL |
| 3 | **Важно** | Task 3 Step 3, утверждается «5 592» дубли | фактическое число 2 796 — ошибка в 2 раза |
| 4 | **Важно** | Global Constraints, Task 3 | smoke-check `data_contract_smoke_check.py` не запускается; план использует другой файл |
| 5 | **Важно** | Task 2 Step 3, `discrete_features=False` | `session_hour` (23 уровня) и `weekday` (5 уровней) — дискретные, переданы как continuous |
| 6 | **Важно** | Plan vs spec | spec требует k=10/15 robustness-проверку — план её не делает |
| 7 | **Важно** | Task 3 Step 3, `y_direction` | `sign(close[t+1]-open[t+1])` возвращает 0 в 3.84% строк — таргет 3-классовый, не binary, домен не описан |
| 8 | **Улучшение** | Unknowns п.3 | «top-100 признаков» в `feature_catalog.json` — фактически 233 признака с MI |
| 9 | **Улучшение** | Task 4.feature_groups | перекрытие групп по подстроке (`break` входит в `row_break_share` и `strong_break`?) — риск двойного счёта |
| 10 | **Улучшение** | Task 5 | rolling по конкатенации train+val+test с окнами через границы split — корректно отмечено, но disclosure в отчёте не формализован |
| 11 | **Вопрос** | Task 6 | gate-критерий `CI не включает 0` применим к fold-CI, но fold-CI и permutation test измеряют разное |

---

## 1. [Критично] sklearn MI возвращает nats, план трактует как bits

**Место:** `2026-08-11-mi-upper-bound.md:230-236` (ключи `*_mi_bits`, поле `r2_ceiling`), `:193` (`_mi_scores`), `:112` (signature `estimate_mi`), `945` (формула в отчёте).

**Суть:** План везде называет MI-метрики `*_mi_bits` и использует формулу `r2_ceiling = 1 - 2^(-2 * mean_marginal_mi_bits)`. Формула `1 - 2^(-2·I)` корректна **только если `I` выражено в bits** (двоичный логарифм). Однако `sklearn.feature_selection.mutual_info_regression`/`mutual_info_classif` возвращают MI в **nats** (натуральный логарифм), что прямо следует из документации sklearn (KSG-оценщик, e-based).

**Доказательство (численный эксперимент):**

```
$ ./.venv/bin/python -c "
import numpy as np
from sklearn.feature_selection import mutual_info_regression
rng = np.random.RandomState(42)
X = rng.randn(20000, 1); y = X[:,0] + rng.randn(20000)*0.3
mi = float(mutual_info_regression(X, y, n_neighbors=5, random_state=42)[0])
r = np.corrcoef(X[:,0], y)[0,1]
print(f'true R^2={r**2:.4f}, MI_sklearn={mi:.4f} (nats), MI_bits={mi/np.log(2):.4f}')
print(f'plan formula 1-2^(-2*MI):  {1-2**(-2*mi):.4f}')
print(f'correct 1-2^(-2*MI_bits):  {1-2**(-2*mi/np.log(2)):.4f}')
"
true R^2=0.9190, MI_sklearn=1.2687 (nats), MI_bits=1.8304
plan formula 1-2^(-2*MI):  0.8278
correct 1-2^(-2*MI_bits): 0.9209
```

Эталонный пример: истинная R²=0.919. План-формула даёт потолок 0.828 — **потолок оказался ниже истинной R²**, что абсурдно и нарушает саму идею information-theoretic upper bound. Корректная формула (с переводом nats→bits) даёт 0.921 ≥ 0.919 — соответствует теории.

Дополнительно: `feature_catalog.json` уже содержит MI в nats (max=0.0676). Если интерпретировать как bits, R²-потолок 0.090; как nats — 0.127. Это **2x** отличие в выводе «близко к потолку».

**Почему важно:** Главная цель плана — ответить «модели на пределе или есть запас». Заниженный в ~1.1–2 раза потолок даст ложный вывод «модели близки к пределу, новые признаки не помогут», что прямо противоречит цели исследования и может направить проект по неверному пути (остановка признаковой работы).

**Рекомендуемое исправление:** переменовать ключи в `*_mi_nats` либо конвертировать MI в bits внутри `estimate_mi`: `mean_mi_bits = mean_mi_nats / np.log(2)`. Формула R²: `r2_ceiling = 1 - 2^(-2 * mean_mi_bits)`. Тест `test_estimate_mi_r2_ceiling_formula` (`:151-157`) проверяет тождество формулы против самих значений MI — он пройдёт даже при баге, но не проверит семантику. Добавить тест с известным гауссовым коэффициентом корреляции: `r2_ceiling >= r²_истинной_модели`.

---

## 2. [Критично] `n_permutations=0` всегда даёт `perm_p_value=1.0`

**Место:** `2026-08-11-mi-upper-bound.md:228` (формула p-value), `:784` (rolling MI с `n_permutations=0`), gate-критерии `:334-337`.

**Суть:** Формула permutation p-value:
```python
perm_p_value = float((np.sum(np.asarray(perm_scores) >= mean_mi) + 1) / (n_permutations + 1))
```
При `n_permutations=0` цикл не выполняется, `perm_scores=[]`, `np.sum([])=0`, знаменатель `(0+1)=1`, итог `p_value = (0+1)/1 = 1.0`. Это всегда даёт максимальное p-value, т.е. всегда трактуется как «предсказуемость отсутствует» (FAIL по gate `:336`).

**Доказательство (численный эксперимент):**
```
$ ./.venv/bin/python -c "
import numpy as np
n_permutations=0; perm_scores=[]; mean_mi=0.5
p = float((np.sum(np.asarray(perm_scores) >= mean_mi) + 1) / (n_permutations + 1))
print(f'n_perm=0 -> perm_p_value={p}')"
n_perm=0 -> perm_p_value=1.0
```

Plan Task 5 передаёт именно `n_permutations=0` в `estimate_rolling_mi` (`:784`), мотивируя «только точечные оценки, CI окон не интерпретируются» (`:729`). Но `estimate_mi` всё равно возвращает `perm_p_value` в dict. Если rolling-результат попадёт в общий JSON, gate-критерий из Task 3 (`perm_p_value < 0.05 → PASS`) автоматически даст FAIL для всех rolling-окон. Это противоречит заявлению plana «rolling — диагностический, не вердикт».

**Почему важно:** Противоречие между gate-критериями Task 3 (требует `perm_p_value < 0.05`) и Task 5 (явно `n_permutations=0`). Отчёт Task 6 выходит строить вердикт по rolling или включает его в JSON — риск либо ложного FAIL, либо противоречивых чисел.

**Рекомендуемое исправление:** при `n_permutations=0` возвращать `perm_p_value=None` (не None как число) и явно помечать в JSON `"perm_p_value": null, "note": "n_permutations=0 — p-value не вычислялось"`. В gate-критериях Task 6 явно исключить rolling-секцию из вердикта PASS/FAIL. Добавить edge-case тест: `assert estimate_mi(..., n_permutations=0)['perm_p_value'] is None`.

---

## 3. [Важно] Число дублей `time` в train ошибочно указано как 5 592 (фактически 2 796)

**Место:** `2026-08-11-mi-upper-bound.md:377` (Task 3 Step 3, примечание про дубли).

**Суть:** План утверждает: «train: 5 592 строк-дублей (44 159 → 41 363, −6.3%)». Число 5 592 неверно (это ~12.7% от 44 159, а не 6.3%). Фактическое число дубликатов = 2 796 (что и даёт указанный процент 6.3%).

**Доказательство:**
```
$ ./.venv/bin/python -c "
import pandas as pd
df = pd.read_csv('DATA/Nero_train_labeled.csv', delimiter=';')
print(f'raw={len(df)} unique={df.time.nunique()} dups_keep_last={len(df)-df.time.nunique()}')
print(f'44159-41363={44159-41363} (план: 5592)')
print(f'drop%={100*(len(df)-df.time.nunique())/len(df):.2f}% (план: 6.3%)')"
raw=44159 unique=41363 dups_keep_last=2796
44159-41363=2796 (план: 5592)
drop%=6.33% (план: 6.3%)
```

Процент (6.3%) корректен, но абсолютное число (5 592) — это `2796 × 2`. Validation доли: plan «−5.1%» — факт 5.05% (478/9463) — совпадает. Test: plan «−5.4%» — факт 5.43% (514/9463) — совпадает. То есть ошибка **только в train**, удвоение числа.

**Почему важно:** Число дубликатов фиксируется в disclosure и JSON (`n_dedup_dropped`). Удвоенное значение войдёт в отчёт как факт о данных и подорвёт доверие к остальным числам. Independent cross-check: `44159 - 41363 = 2796` — арифметически очевидно противоречит «5 592». Возможно план где-то считает оба `keep='first'` и `keep='last'` и сложил, но операция идемпотентна.

**Рекомендуемое исправление:** исправить в `:377` число «5 592» на «2 796» и добавить `(44 159 → 41 363, −6.3%)` как есть. После реализации проверить, что `load_mi_data` возвращает `n_dedup_dropped=2796`, а не иное значение.

---

## 4. [Важно] Smoke-check методологии 05 не запускается; план использует другой файл

**Место:** `2026-08-11-mi-upper-bound.md:21` (ссылка на методологию 05-eda), `:61` (Task 1 «Методология 05»), отсутствует явный шаг smoke-check.

**Суть:** Методология `docs/methodology/05-eda-data-quality.md:29-40` **обязательна** перед любым запуском, где результат интерпретируется как ML-quality: запуск `statistics/data_contract_smoke_check.py`. План в Task 1 (Аудит существующих MI) и Task 3 (запуск оценки) этот smoke-check не выполняет — только собственную проверку колонок (`assert 'time' in df.columns`, `assert not missing`).

Дополнительно: smoke-check настроен на **другие пути** — `Nero_XAUUSD_train_labeled.csv` (с префиксом инструмента), тогда как план работает с `Nero_train_labeled.csv` (без префикса):
```
statistics/data_contract_smoke_check.py:31-33:
    'train': DATA_DIR / 'Nero_XAUUSD_train_labeled.csv',
    'validation': DATA_DIR / 'Nero_XAUUSD_validation_labeled.csv',
    'test': DATA_DIR / 'Nero_XAUUSD_test_labeled.csv',
```

Файлы физически различаются (md5 не совпадает, хотя колонки и `time` overlap 100%):
```
98d623dff58bb832276ba01b212aa268  DATA/Nero_train_labeled.csv
ddcc60283994175caf08122d8b531445  DATA/Nero_XAUUSD_train_labeled.csv
```

Smoke-check успешно прогоняется на `Nero_XAUUSD_*` файлам, но не запускается на файлах плана. Корректность `Nero_train_labeled.csv` остаётся непроверенной по инвариантам `direction ∈ {-1,1}`, `up/dn ∈ [0,1]` и т.д.

**Почему важно:** Прямое нарушение п. 05 «Если smoke-check не прошёл — результаты модели имеют статус `DIAGNOSTIC_ONLY` или `FAIL`». План должен либо запустить smoke-check на своих путях, либо обосновать, почему `Nero_train_labeled.csv` эквивалентен `Nero_XAUUSD_train_labeled.csv` и smoke-check на последнем покрывает оба.

**Рекомендуемое исправление:** добавить в Task 3 Step 4 перед запуском `run_mi_upper_bound.py` шаг:
```bash
.venv/bin/python statistics/data_contract_smoke_check.py \
    --train DATA/Nero_train_labeled.csv \
    --val DATA/Nero_validation_labeled.csv \
    --test DATA/Nero_test_labeled.csv
```
Если smoke-check не принимает эти пути — запустить на эквивалентных `Nero_XAUUSD_*` и явно зафиксировать в disclosure эквивалентность (сравнить md5/строки/время или сослаться на pipeline-документацию, что `Nero_*` и `Nero_XAUUSD_*` — одно и то же).

---

## 5. [Важно] `session_hour`/`weekday` дискретны, передаются как continuous

**Место:** `2026-08-11-mi-upper-bound.md:193` (`discrete_features=False`), `:423` (X из `ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS`).

**Суть:** `ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS` включает 2 календарных признака `session_hour`, `weekday` — оба дискретные (`session_hour` 23 уровня: 1–23, нет 0; `weekday` 5 уровней: 0–4). Остальные 40 признаков feature bank (`row_*_w{5,10,20,50,100}`) — непрерывные агрегаты. План единообразно вызывает `mutual_info_*` с `discrete_features=False` для всей матрицы X, т.е. трактует дискретные календарные признаки как непрерывные.

**Доказательство:**
```
$ ./.venv/bin/python -c "
import pandas as pd
df = pd.read_csv('DATA/Nero_train_labeled.csv', delimiter=';')
print(f'session_hour nunique={df.session_hour.nunique()} values={sorted(df.session_hour.unique())}')
print(f'weekday nunique={df.weekday.nunique()} values={sorted(df.weekday.unique())}')"
session_hour nunique=23, values=[1..23]
weekday nunique=5, values=[0,1,2,3,4]
```

KSG-оценщик при `discrete_features=False` добавляет шум к continuous-признаку (sklearn docs: «adding small noise to continuous variables in order to remove repeated values»). Для дискретного `weekday` с 5 уровнями это размоет оценку и потенциально систематически исказит MI для time-фичей. Это особенно важно, так как гипотеза `7.6` («time-only dominance») проверяется именно через MI time-фичей — а они обрабатываются неправильно.

**Почему важно:** Одно из главных интерпретационных утверждений плана — `MI(time_features) >> MI(other_features)` подтвердит/опровергнет time-only dominance. Оценка MI time-фичей через `discrete_features=False` корректна, но не оптимальна: для дискретных признаков точнее указать `discrete_features=[mask]` (sklearn применит иной оценщик для них). Может получиться заниженная или зашумлённая MI time-фичей, что приведёт к неверному выводу о dominance.

**Рекомендуемое исправление:** в `estimate_mi`/`estimate_mi_per_feature` принимать параметр `discrete_features` (`array-like` масок) и для `session_hour`/`weekday` явно указывать discrete. Либо запустить отдельный per-feature режим: для каждого признака выбрать оценщик по типу. Минимум — добавить в disclosureаffect: «time-признаки трактуются как continuous; оценка может быть смещена».

---

## 6. [Важно] spec требует k=10/15 robustness-проверку — план её не делает

**Место:** `2026-08-11-mi-upper-bound-design.md:61` vs `2026-08-11-mi-upper-bound.md:944` (фиксировано k=5).

**Суть:** Spec прямо фиксирует: «`n_neighbors` (k): 5 — основной; k = 10, 15 — robustness-проверка (не для выбора по результату)». План во всех шагах и runnerе использует только k=5 (`:481`, `:140`, `:155`, `:164`, `:264`). Robustness-проверка с k=10/15 отсутствует.

**Доказательство:**
```
$ grep -n "k=5\|k=10\|k=15\|--k " docs/superpowers/plans/2026-08-11-mi-upper-bound.md
:140:    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, ...)
:481:    parser.add_argument('--k', type=int, default=5)
:944: k=5, CI по 10 временным фолдам
```
Ни одного вызова с k=10 или k=15 нет.

**Почему важно:** KSG-оценщик чувствителен к выбору k — это известная слабость непараметрических MI-оценок (spec `:177` упоминает «Разные оценщики дают разные значения»). Без robustness по k результат R²-потолка не проверен на устойчивость к гиперпараметру оценщика. Методология spec явно это требует — план её не выполняет.

**Рекомендуемое исправление:** добавить Task 6.5 «Robustness по k»: для финальной выбранной конфигурации сделать доп. прогон с `--k 10` и `--k 15`, сохранить в отдельный JSON `mi_upper_bound_k10.json`/`..._k15.json`, в отчёте привести диапазон MI значений для каждой метрики при трёх k. Не использовать для выбора итогового значения, только для disclosure диапазона устойчивости.

---

## 7. [Важно] `y_direction` трёхклассовый (3.84% нулей), домен не задокументирован

**Место:** `2026-08-11-mi-upper-bound.md:331`, `:431-434` (`y_direction = np.sign(...).astype(np.float64)`), `:361` (тест допускает `-1, 0, 1`).

**Суть:** Таргет `T1: sign(close[t+1] - open[t+1])` возвращает 0 когда close=open. План в spec (`:84`) называет его «binary direction», фактически это трёхклассовый таргет с классом 0 (нет движения).

**Доказательство:**
```
$ ./.venv/bin/python -c "
import pandas as pd, numpy as np
ohlc = pd.read_csv('DATA/XAUUSD_H1_OHLC.csv', delimiter=';')
df = pd.read_csv('DATA/Nero_train_labeled.csv', delimiter=';')
df = df.drop_duplicates('time', keep='last').reset_index(drop=True)
m = df.merge(ohlc[['time','open','close']], on='time', how='inner', validate='one_to_one')
no, nc = m['open'].shift(-1), m['close'].shift(-1)
diff = (nc-no).dropna()
zero_pct = 100*(diff==0).sum()/len(diff)
print(f'sign=0 rows: {(diff==0).sum()} ({zero_pct:.2f}%)')"
sign=0 rows: 1590 (3.84%)
```

1590 строк (3.84%) получают `y_direction=0`. `mutual_info_classif` с 3 классами корректно обработает это, но:
- Спека (`:84`) заявляет «binary direction» — фактически трёхклассовый.
- План в тесте (`:361`) использует `assert set(np.unique(y_direction)).issubset({-1.0, 0.0, 1.0})` — корректно, но не фиксирует долю нулей.
- Интепретация MI для 3-классового target vs binary разная; результаты direction могут отличаться от ожидаемых legacy-моделей (которые предсказывали up/dn на горизонтах 12/24/48H, а не sign(t+1)).

**Почему важно:** Сравнение `MI(features; direction)` с legacy-моделями (R² на 12/24/48H up/dn) станет нестрогим, и подобно тому что план сам предупреждает про legacy («ориентировочное сравнение»), здесь добавляется ещё различие: «direction — это binarised sign(t+1), а не up/dn на H». Интерпретация «amplitude устойчивее direction» может оказаться следствием того, что 3.84% строк у direction в классе «нет движения», а у amplitude получается 0 — формально у amplitude тоже 0 но это «точное значение», а у direction — отдельный класс.

**Рекомендуемое исправление:** в spec/plane изменить описание на «three-class direction (sign)»: явно указать домен `{-1, 0, 1}` с долей нулей. Рассмотреть альтернативу: бинарный direction `np.where(close > open, 1, -1)` без нуля, либо явно исключить строки с `y_amplitude < epsilon`. Зафиксировать в disclosure распределение классов `y_direction` для train/val.

---

## 8. [Улучшение] «top-100 признаков» в `feature_catalog.json` — фактически 233

**Место:** `2026-08-11-mi-upper-bound.md:1026` (Unknowns п.3), `:98` (Task 1 Step 3).

**Суть:** План утверждает, что существующий MI в `feature_catalog.json` посчитан «только для top-100 признаков». Фактически в JSON 233 признака, и все 233 имеют числовое значение `mutual_information` (без None/нулей-заглушек).

**Доказательство:**
```
$ ./.venv/bin/python -c "
import json
data = json.load(open('statistics/feature_catalog.json'))
print(f'total: {len(data)}, with MI: {sum(1 for d in data if d.get(\"mutual_information\") is not None)}')"
total: 233, with MI: 233
```

EDA.ipynb (lines 3369-3379) действительно считает MI только для top-100 по корреляции (`top_100_features = corr_df.head(100)['feature'].values`), но в `feature_catalog.json` — 233 признака с MI. Возможно MI для остальных посчитан в другом блоке EDA или позже.

**Почему важно:** слабое место аргументации. План опирается на «MI посчитан для top-100» как на причину не переиспользовать `feature_catalog.json`. Реальная причина (target=`signal`, future-derived, n_neighbors=3) достаточна; «top-100» — неточный довод, который легко опровергается и подрывает доверие к аудиторским выводам plana.

**Рекомендуемое исправление:** убрать упоминание «top-100 признаков» или скорректировать: «MI посчитан для 233 engineered-признаков против `signal` (future-derived), n_neighbors=3».

---

## 9. [Улучшение] Группировка признаков по подстроке может давать перекрытия

**Место:** `2026-08-11-mi-upper-bound.md:608-618` (`FEATURE_GROUPS`).

**Суть:** Группы определяются через подстроки: `'strong': [... if 'strong' in c]`, `'break': [... if 'break' in c]`, и т.д. Колонки feature bank: `row_{strong_share, break_share, direction_balance, back_mean, back_std, impulse_mean, power_mean, count_mean}_w{5,10,20,50,100}`. Подстроки: `strong`, `break`, `direction_balance`, `back`, `impulse`, `power`, `count`.

Потенциальное перекрытие: подстрока `'back'` входит в `row_back_mean_w*`. Подстрока `'count'` — в `row_count_mean_w*`. Проверка:
```
import ML.entry_path_feature_bank as fb
cols = fb.FEATURE_BANK_COLUMNS
[c for c in cols if 'back' in c and 'break' in c]  # []
print([c for c in cols if 'strong' in c and 'break' in c])  # []
```
Перекрытий нет, но `'back'` встречается и в `row_back_mean` и в `row_back_std` — обе попадут в одну группу `back`, что ожидаемо и корректно. **Проблем не найдено.** Замечание можно аннулировать.

**Однако** — `group_mi` фильтрует `df['feature'].isin(group_features)`. Если какая-то колонка не попала ни в одну группу (например `'direction_balance'` нет в списке групп, кроме как `direction_balance`), её MI не войдёт в суммарный анализ. Проверка списка групп: `time`, `strong`, `break`, `direction_balance`, `back`, `impulse`, `power`, `count`. Все 8 метрик feature bank покрыты.

**Доказательство:** все 40 feature bank колонок покрыты 8 группами. Колонка `session_hour`, `weekday` — отдельная группа `time`. Покрытие полное.

**Рекомендуемое исправление:** слабое улучшение — добавить assertion `assert sum(mask.sum() for ...) >= 38` (40 bank + 2 time = 42, но колонки могут входить в 1 группу), гарантирующий, что все 42 признака вошли хотя бы в одну группу. Это страховка от опечаток в подстроках.

---

## 10. [Улучшение] Rolling MI через границы сплитов — disclosurea не формализован

**Место:** `2026-08-11-mi-upper-bound.md:723-729`, `:808-836`, `:838-845`.

**Суть:** Plan корректно аргументирует, что конкатенация `train + validation + test` (2004–2026) нужна для обнаружения regime drift после 2022, и явно говорит «окна на стыках split'ов — допустимы (диагностика)». Однако:

- В runner (`:817-835`) `compute_rolling_mi` конкатенирует через `np.concatenate` без отметок split boundary в result.
- В JSON `rolling.splits` (`:833`) содержит список путей, но не помечает, какие timestamps относятся к какому split.
- В отчёте (`:968-971`) Markdown в раздел «5. Rolling MI» явно не включает disclosure о границах сплитов.

**Почему важно:** Окно длиной 500 баров, попадающее на границу `train|validation` (например, последние 250 баров train + первые 250 баров validation), имеет смешанную природу: train размечен по одной логике рекурсивной генерации, validation — по другой (расширенная). MI в этом окне объединяет две популяции. Это и есть диагностическая ценность (видно smoother переход), но:

- Когда MI падает после 2022, нужно знать, попадает ли падение в окно, охватывающее границу `val|test` (и тогда это смешанный эффект).
- Без визуальных меток на rolling-plot (`mi_rolling.png`) штрих-старта сплитов читателю придётся искать границы вручную.

**Рекомендуемое исправление:** добавить в `compute_rolling_mi` возврат `split_boundaries` (timestamps, где кончается train и validation); в plot добавить вертикальные линии на границах. В отчёте явно сказать: «окно W=500 может охватывать два сплита; на границах значения MI имеют смешанный характер и интерпретируются как сглаженный переход».

---

## 11. [Вопрос] gate-критерий `CI не включает 0` применим к fold-CI, но fold-CI ≠ статистический CI

**Место:** `2026-08-11-mi-upper-bound.md:334-337` (gate), `:218-221` (CI через percentile fold_scores).

**Суть:** Gate-критерий verdictuse:
- `perm_p_value < 0.05` и `CI не включает 0` → PASS
- `perm_p_value >= 0.05` → FAIL
- `p < 0.05, но CI включает 0` → INCONCLUSIVE

`mi_ci_p05`/`mi_ci_p95` — это 5-я и 95-я перцентили разброса MI по 10 временным фолдам. Это **не статистический доверительный интервал** в классическом смысле (нет repeating, нет t-distribution). Это эмпирический разброс между непересекающимися сегментами данных. План сам корректно отмечает (`:181`): «точечная оценка на полном объёме может лежать выше fold-CI — ожидаемое следствие конечновыборочного смещения KSG».

Permutation test оценивает H0: «MI между X и y = 0», перемешивая y. Это статистическая проверка. CI и permutation test измеряют разное: permutation test — значимость в смысле «есть ли связь вообще», fold-CI — устойчивость связи по времени.

Если MI существенно дрейфит во времени (что и ожидает план обнаружить — regime drift), fold-CI будет широким и может включать 0, **даже если связь в каждом фолде значима**. Тогда gate `CI включает 0 → INCONCLUSIVE` даст ложный «неопределённый» результат для данных, где на самом деле есть значимая, но нестационарная связь.

**Вопрос для уточнения:** это намеренная интерпретация (хотим пометить нестационарность как INCONCLUSIVE) или неучтённое противоречие? Spec (`:130`) говорит: «Если MI падает после 2022 — это количественное подтверждение regime drift». То есть дрейф — ожидаемый результат, а не INCONCLUSIVE. Gate `CI включает 0 → INCONCLUSIVE` может классифицировать именно regime drift (который мы ищем) как «неопределённо», что противоречиво.

**Рекомендуемое уточнение:** развести gate-критерии:
- Для агрегированного verdict: permutation p-value (значимость связи в среднем) + средний MI ≠ 0.
- Для стабильности: отдельная метрика «доля фолдов с MI > threshold» или «коэффициент вариации fold_scores», без жёсткого бинаря «CI включает 0».
- Явно зафиксировать, что regime drift (MI падает на части фолдов) — это самостоятельный осмысленный результат, а не INCONCLUSIVE.

---

## Дополнительные проверки (без замечаний)

### Доказанные корректные утверждения plana

| Утверждение plana | Проверка | Статус |
|---|---|---|
| В labeled CSV нет `open`/`close` | `head -1 DATA/Nero_train_labeled.csv` — колонок нет | ✅ Корректно |
| OHLC: `time;open;high;low;close;volume;atr14` | `head -1 DATA/XAUUSD_H1_OHLC.csv` | ✅ Корректно |
| OHLC `time` уникален | `ohlc['time'].is_unique == True`, 128698 строк | ✅ Корректно |
| OHLC-джойн ≤ 5% потерь | train: 0.00% потерь (`41363 → 41363`) | ✅ Совпадает с намного большим запасом |
| 42 признака live-safe | `ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS` = 2 + 40 bank | ✅ Согласовано с `ML/entry_path_task.py:32` и `ML/entry_path_feature_bank.py:23` |
| `feature_screen_entry_path.py:rank_features_by_mutual_information` — референс | Функция существует, использует `mutual_info_classif/regression` | ✅ Подтверждено |
| `feature_catalog.json` n_neighbors=3, target=`signal` | `EDA.ipynb:3375` `mutual_info_classif(X_top100, y_target, n_neighbors=3)`, target=`signal` (line 3341) | ✅ Подтверждено |
| Конвенция `drop_duplicates('time', keep='last')` в `ML/benchmark_execution_policy_v2.py:78` | `grep` находит строку | ✅ Подтверждено |
| BiLSTM R²=0.10 (r=0.32), Transformer R²=0.18 (r=0.43), `baseline_clean` R²=0.084 | `docs/audit/retrospective.md:17, 33` | ✅ Все три значения точно совпадают |
| Live-safe audit: 5 систем FAIL (4 + entry_path_v1 PASS) | `tests/test_live_safe_audit.py:121-130` | ✅ Подтверждено тестами (4 FAIL, 1 PASS) |
| `statistics/` конфликтует со stdlib | нет `__init__.py`, namespace pkg | ✅ Импорт через `from mi_upper_bound import ...` корректен |
| `path_6_class` не используется как замена direction | spec/план правильно отвергают это | ✅ Корректное решение |

### Код plana, проверенный на корректность алгоритма

- `estimate_mi` fold-разбиение через `np.array_split` корректно для временных рядов (chunks chronological, не random) — ✅
- `np.array_split` на пустом массиве возвращает список пустых чанков — ✅ не крэшит
- `perm_p_value` при `n_permutations>0`: формула `(count + 1)/(N+1)` — корректная permutation p (включает само наблюдение) — ✅
- `y_amplitude = abs(log(next_close/next_open))` корректно (log отношений считается правильно) — ✅
- `valid = np.isfinite(y_amplitude) & np.isfinite(y_direction)` — фильтрация последней строки (NaN при shift) — ✅ корректно
- OHLC-джойн `validate='one_to_one'` — корректно, дубли `time` отлавливаются — ✅
- Сортировка `merge.sort_values('time')` после merge — ✅ сохраняет хронологию
- Возврат `n_dedup_dropped` и `n_join_dropped` — ✅ хорошая disclosure-практика

### Проверка ImportError-паттерна (edge case)

`build_entry_path_feature_bank` на пустом df (теоретически возможный edge case при пустом split) возвращает df с 40 колонками bank — корректно, не крэшит. Реально в данных все сплиты непустые.

---

## Сводка для пользователя

**Критично (2):** формулы R²-потолка (nats≠bits, п.1) и permutation p-value при n_perm=0 (всегда FAIL, п.2) — обе искажают основной численный результат плана и могут увести проект в неверном направлении. Должны быть исправлены до реализации.

**Важно (5):** фактическая ошибка в числе дубликатов (п.3), пропущенный обязательный smoke-check (п.4), дискретные признаки как continuous (п.5), пропущенная robustness-проверка по k (п.6), недокументированный 3-классовый direction target (п.7). Каждое искажает интерпретацию или нарушает методологию.

**Улучшение (3):** неточность про top-100 (п.8), неформализованный disclosure границ сплитов в rolling (п.10), потенциально противоречивый gate «CI включает 0 → INCONCLUSIVE» (п.11). Группа признаков по подстроке (п.9) проверена — корректна, замечание аннулировано.

**Сильные стороны плана:** корректная работа с feature bank, грамотный отказ от reusing `feature_catalog.json` из-за future-derived target, чёткая фиксация гипотезы до запуска (`research_scan`, `research_only`), правильное обоснование неприменимости row-bootstrap для KSG, последовательная структура TDD с failure-first тестами, аккуратная ссылка на ретроспективу с реальными числами (для 5 из 6 утверждений).

**Приоритет исправлений:** 1 → 2 → 4 → 6 → 3 → 5 → 7 → 11 → 10 → 8. Замечания 1 и 2 — блокирующие, без их исправления результат эксперимента будет численно неверным.
