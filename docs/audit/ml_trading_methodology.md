# Методика разработки и аудита ML-моделей торговых систем

> Статус: основной пайплайн разработки и аудита ML-моделей торговых систем в проекте SoSimple.
> Область: ML-модели торговых систем на событийных и временных данных Forex.
> Роль в проекте: управляющий документ качества ML-разработки. `docs/DATA_FLOW.md` описывает маршрут данных, а эта методика задаёт обязательные проверки, критерии перехода между этапами и правила интерпретации результатов.
> Главный принцип: результат нельзя считать качеством модели, пока не доказано, что данные, признаки, разметка, split, правило отбора, экспорт и исполнение соответствуют моменту торгового решения.

## Оглавление

- [Как использовать методику](#как-использовать-методику)
- [0. Управление исследованием](#0-управление-исследованием)
- [1. Инвентаризация сырых данных](#1-инвентаризация-сырых-данных)
- [2. Формирование исходного pipeline данных](#2-формирование-исходного-pipeline-данных)
- [3. Feature Contract и Leakage Gate](#3-feature-contract-и-leakage-gate)
- [4. Разметка целей](#4-разметка-целей)
- [5. Data Quality, EDA и статистический аудит](#5-data-quality-eda-и-статистический-аудит)
- [6. Временное разделение и протокол валидации](#6-временное-разделение-и-протокол-валидации)
- [7. Baseline-first этап](#7-baseline-first-этап)
- [8. Разработка модели](#8-разработка-модели)
- [9. Validation selection и freeze-протокол](#9-validation-selection-и-freeze-протокол)
- [10. Frozen test, OOS и walk-forward](#10-frozen-test-oos-и-walk-forward)
- [11. Устойчивость и robustness](#11-устойчивость-и-robustness)
- [12. Backtest с торговыми издержками](#12-backtest-с-торговыми-издержками)
- [13. Export, MT4 parity и reconciliation](#13-export-mt4-parity-и-reconciliation)
- [14. Forward-test и online diagnostic](#14-forward-test-и-online-diagnostic)
- [15. Monitoring и retraining policy](#15-monitoring-и-retraining-policy)
- [16. Отчётность и аудит ошибок](#16-отчётность-и-аудит-ошибок)
- [Сводный чеклист разработки](#сводный-чеклист-разработки)
- [Сводный чеклист аудита готового результата](#сводный-чеклист-аудита-готового-результата)
- [Типовые причины ложных выводов в проекте](#типовые-причины-ложных-выводов-в-проекте)
- [Verdict-статусы кандидатов](#verdict-статусы-кандидатов)
- [Stop conditions](#stop-conditions)
- [Примеры первичных источников для проверки](#примеры-первичных-источников-для-проверки)

## Как использовать методику

Методика применяется к любому новому ML-кандидату: классификации направления, регрессии MFE/MAE, take/skip, triple barrier, фильтру сигналов, execution-policy или модели выбора стороны сделки.

Каждый этап имеет одинаковую структуру:

- цель;
- входы;
- пошаговые действия;
- обязательные проверки;
- критерии успешного завершения;
- типовые ошибки;
- ветвления по результатам проверки.

Результат этапа получает один из статусов:

| Статус | Значение |
|---|---|
| `PASS` | Этап прошёл обязательные проверки, можно переходить дальше |
| `FAIL` | Найден блокирующий дефект; следующий этап запрещён |
| `UNKNOWN` | Данных недостаточно; считать как `FAIL`, пока не доказано обратное |
| `DIAGNOSTIC_ONLY` | Можно проверять механику pipeline, но нельзя делать вывод о прибыльности или качестве ML |

Главные источники для сверки:

- pipeline и leakage-инварианты: [`docs/DATA_FLOW.md`](../DATA_FLOW.md);
- формат датасета: [`docs/dataset_description.md`](../dataset_description.md);
- обязательный leakage gate: [`Feature Contract и Leakage Gate`](#3-feature-contract-и-leakage-gate);
- отчёты по прошлым ошибкам: [`docs/reports/`](../reports/);
- wiki использовать как навигацию, но выводы проверять по первичным отчётам.

---

## 0. Управление исследованием

### Цель

Убрать произвол из процесса: до запуска экспериментов должно быть понятно, что проверяется, по каким данным, какими метриками и на каком основании кандидат будет принят или отклонён.

### Входы

- продуктовая цель и ограничения проекта;
- актуальный pipeline данных;
- предыдущие отчёты и открытые риски;
- список доступных источников данных;
- предполагаемый торговый контур.

### Пошаговые действия

1. Назвать исследовательскую гипотезу одной фразой.
2. Зафиксировать тип задачи: direction, regression, take/skip, barrier outcome, execution policy, signal filter.
3. Зафиксировать единицу решения: строка датасета, бар, фрактал, уровень, сигнал или сделка.
4. Зафиксировать `decision_time`: open/close бара, таймфрейм, инструмент, момент входа.
5. Заранее задать gate-критерии: PF, sequential PF, число сделок, просадка, отрицательные годы, BUY/SELL устойчивость, baseline uplift.
6. Заранее определить, что будет считаться провалом.
7. Создать короткую запись о гипотезе, split-протоколе, метриках и expected artifacts.

### Обязательные проверки

- Гипотеза не менялась после просмотра test.
- Test не используется как validation.
- Для каждого будущего результата заранее известен allowed verdict.
- Любой результат с неясным feature contract помечается `DIAGNOSTIC_ONLY`.

### Критерии успешного завершения

- Есть проверяемая гипотеза.
- Есть список метрик и gate-порогов.
- Есть план, какие данные относятся к train, validation, test и forward.
- Известно, какие артефакты должны быть сохранены.

### Типовые ошибки

- Начинать с выбора модели вместо постановки торгового решения.
- Подбирать цель или порог после просмотра test.
- Считать высокий PF доказательством без аудита признаков.
- Смешивать механическую диагностику MT4 с доказательством качества ML.

### Ветвления

- Если `decision_time` неизвестен: остановить ML-часть и описать торговый контур.
- Если критерии успеха не заданы: проводить только exploratory analysis без verdict.
- Если задача меняется после test: открыть новый экспериментальный цикл с новым frozen test.

---

## 1. Инвентаризация сырых данных

### Цель

Доказать, что источник данных, формат строк и смысл полей понятны до построения признаков и меток.

### Входы

- raw export из торговой платформы;
- документация формата датасета;
- описание producer-а данных;
- история изменений формата;
- сведения о провайдере котировок и таймфрейме.

### Пошаговые действия

1. Зафиксировать источник raw-файла: инструмент, таймфрейм, провайдер, период, timezone.
2. Проверить фактический CSV contract: разделитель, кодировку, количество колонок, вложенный формат.
3. Описать, как формируется строка в момент времени `t`.
4. Разделить поля на группы:
   - `live_safe`: доступны на момент решения;
   - `target_only`: используются только как label;
   - `future_derived`: построены из будущих баров;
   - `unknown`: происхождение не доказано.
5. Проверить дубли времени: являются ли они разными событиями одного бара или ошибкой.
6. Зафиксировать known quirks: неполные края, смена таймфрейма, разные провайдеры, tester/online отличия.
7. Сохранить data inventory: путь, период, размеры, provider, frequency, fields, risks.

### Обязательные проверки

- Raw-поля не объявляются безопасными только потому, что они есть в CSV.
- Дубли времени не удаляются без доказательства.
- Таймфрейм соответствует задаче.
- Provider drift отделён от transfer на другой инструмент.
- Поля `unknown` не допускаются во вход модели.

### Критерии успешного завершения

- Для каждого raw-поля есть статус `live_safe`, `target_only`, `future_derived` или `unknown`.
- Известно, какие поля можно использовать online.
- Известно, какие поля можно использовать только для offline-разметки.

### Типовые ошибки

- Схлопывать строки с одинаковым временем и терять разные события одного бара.
- Смешивать H1 и M5 источники в одном ML-контуре.
- Использовать поле, момент доступности которого не доказан.
- Переносить старый вывод на нового провайдера без отдельной проверки.

### Ветвления

- Если поле `unknown`: исключить из input или провести source audit.
- Если raw-файл не того таймфрейма: не обучать production-кандидата.
- Если provider changed: сначала проверить provider drift на том же инструменте, потом cross-instrument transfer.

---

## 2. Формирование исходного pipeline данных

### Цель

Получить воспроизводимый путь от raw данных до подготовленного train/validation/test набора без скрытых ручных операций.

### Входы

- raw data inventory;
- описание producer-а данных;
- preprocessing modules;
- target contract;
- ожидаемые выходные CSV.

### Пошаговые действия

1. Зафиксировать raw producer: например, торговая платформа формирует строковые snapshots.
2. Проверить сортировку внутри строки, если строка содержит массив событий или фракталов.
3. Выполнить labeling только в offline-пути.
4. Присвоить всем новым target/label колонкам говорящий префикс, например `target_`, `label_` или `outcome_`.
5. Выполнить нормализацию строго по разрешённой схеме.
6. Выполнить последовательный split.
7. Сохранить подготовленные файлы и metadata:
   - источник raw;
   - команды запуска;
   - параметры нормализации;
   - размеры split;
   - hash или manifest.
8. Проверить, что runtime/inference path не запускает offline-labeling.

Пример текущего проекта: `Nero.csv` -> сортировка фракталов внутри строки -> offline labeling -> row-wise normalization -> sequential split -> train/validation/test. Это пример структуры pipeline, а не разрешение переносить конкретные решения без нового source audit.

### Обязательные проверки

- Сортировка независима по строкам или доказано, почему межстрочная операция не создаёт leakage.
- Offline labels не попадают в online preprocessing.
- Target/label колонки имеют явный префикс и не маскируются под обычные признаки.
- Row-wise normalization не использует future-derived поля в пулах live-признаков.
- Global scaler fit-ится только на train.
- `ATR` или другой volatility contract явно описан: raw, ratio или scaled.

### Критерии успешного завершения

- Pipeline запускается одной воспроизводимой командой или документированной последовательностью команд.
- Все выходные файлы имеют ожидаемые колонки и размеры.
- Есть проверка формата вложенных структур.
- Есть metadata, по которой можно повторить подготовку.

### Типовые ошибки

- Использовать старый normalization mode, где future-derived поле влияет на масштаб live-признаков.
- Запускать target builder в online-пути.
- Называть будущую метку обычным feature-like именем, из-за чего она позже попадает в input по wildcard/regex.
- Полагаться на cache после смены feature contract.
- Не проверять, что `fractal0` или аналогичный свежий элемент означает одно и то же в train/test/online.

### Ветвления

- Если preprocessing не воспроизводится: остановить модельные эксперименты.
- Если online path не может создать те же признаки: переобучить модель на live-safe contract.
- Если найден риск в normalization pool: пересчитать данные и считать старые результаты `DIAGNOSTIC_ONLY`.

---

## 3. Feature Contract и Leakage Gate

### Цель

Исключить заглядывание вперёд, target-derived inputs и несовпадение training/online feature contract до того, как метрики validation/test/MT4/online будут интерпретированы как качество ML.

### Когда применять

Применять перед каждым запуском, где результат может быть использован как доказательство качества ML:

- обучение или retrain модели;
- validation/test/frozen-test benchmark;
- изменение feature builder, target builder, preprocessing, normalization или split logic;
- экспорт `ml_signals.csv`;
- MT4 tester-прогон;
- online watcher / runner;
- сравнение online и historical test.

Не применять как строгий production-gate только для явно помеченной механической диагностики цепочки `MT4 -> Python -> CSV -> MT4`, если её результаты не интерпретируются как качество модели. Такие запуски получают статус `DIAGNOSTIC_ONLY`.

### Критерий допуска

Запуск разрешено интерпретировать как ML-quality evidence только если все проверки этого раздела имеют статус `PASS`.

Если хотя бы один пункт имеет `FAIL` или `UNKNOWN`, запуск можно делать только как диагностику механики с явной пометкой:

```text
ML result is not valid for production/backtest comparison.
Reason: unresolved leakage/preprocessing contract risk.
```

### Входы

- список input features;
- список target/label/future-derived columns;
- feature builder;
- target builder;
- preprocessing/normalization code;
- split manifest;
- online/runtime preprocessing path;
- exporter / MT4 consumer, если есть execution layer;
- checkpoint metadata, если модель уже существует.

### Пошаговые действия

1. Зафиксировать `decision_time`: open/close бара, таймфрейм, инструмент, момент входа.
2. Для каждого признака заполнить feature contract:
   - имя;
   - роль: input, target, diagnostic, metadata;
   - источник;
   - producer;
   - transformation;
   - consumer;
   - момент доступности;
   - способ нормализации;
   - live-safe verdict.
3. Отдельно проверить candidate-source: откуда берётся сама строка или сигнал-кандидат.
4. Проверить прямое попадание targets в input.
5. Проверить косвенное попадание future outcome через lag, rolling, ratio, normalization pool или feature selection.
6. Проверить, что feature builder использует явный allowlist input-признаков или строгий denylist target/future-derived колонок.
7. Сравнить training и online contract:
   - names;
   - order;
   - count;
   - dtype;
   - scale;
   - missing value policy;
   - ATR contract;
   - sequence length.
8. Запретить silent fallback: отсутствующий online-признак не заменяется нулём без явного контракта.
9. Зафиксировать итоговый verdict: `PASS`, `FAIL`, `UNKNOWN` или `DIAGNOSTIC_ONLY`.

### ML Leakage Preflight Checklist

| # | Проверка | Зачем | Чем подтвердить | `FAIL`, если |
|---:|---|---|---|---|
| 1 | Зафиксирован `decision_time` | Нужно знать, какие данные доступны модели на баре `t` | В отчёте указан open/close бара, таймфрейм, инструмент, момент входа | Непонятно, на каком баре и в какой момент модель видит данные |
| 2 | Split строго временной | Будущее не должно попадать в train/validation | Указаны границы train/validation/test; нет shuffle по строкам | Есть случайное перемешивание временных строк до split |
| 3 | Целевые и future-derived поля не входят во вход модели | Модель должна предсказывать результат, а не читать ответ | Input columns сравнены со списком target/label/future-derived columns | Во входе есть `predict`, `ret_*`, `ret_dir_atr_lag1`, `fav_*`, `adv_*`, `target_*`, `label_*`, `outcome_*` или другие поля из будущих баров |
| 4 | Row features разделены на live-safe и future-derived | Часть строковых признаков может быть доступна online, часть нет | Есть явный allowlist live-safe полей и denylist target/future-derived полей | Недостающие online-поля молча заполняются нулями и подаются в модель |
| 5 | Training и online feature contract совпадают | Модель должна получать одинаковое число признаков с одинаковым смыслом | Для checkpoint зафиксированы input names/count/order; online builder воспроизводит их без заглушек | Training builder создаёт N признаков, online честно создаёт M<N, а остальные заполняются `0` |
| 6 | Фракталы или другие event elements отсортированы одинаково | `fractal0` должен означать одно и то же в train/test/online | Проверка порядка, например `fractal_time[i] >= fractal_time[i+1]` | `fractal0` в одном режиме свежий, а в другом старый или случайный |
| 7 | Нормализация применена тем же способом | Модель не должна получать другой масштаб чисел | Проверка диапазонов и normalization metadata | Training использовал нормализованные поля, а online подаёт raw значения, или наоборот |
| 8 | Нормализационные пулы не зависят от future-derived полей | Даже row-wise normalization может исказить live-признаки | Описано, какие поля входят в per-row pools | `predict` или future targets влияют на normalization pool live-признаков |
| 9 | Labeling не запускается в online path | Online не знает будущий исход сделки | В online runner нет вызова future label builders | Online перед inference создаёт `ret_*`, `fav_*`, `adv_*` или аналоги по будущим барам |
| 10 | Global scaler не использует future validation/test/online | Нельзя fit-ить scaler на данных, которые модель ещё не должна знать | Для StandardScaler/RobustScaler/min-max указано: fit только на train | Scaler fit-ится на полном датасете включая validation/test/forward |
| 11 | ATR/volatility contract совпадает | ATR может быть raw, ratio или scaled | В отчёте указано, ждёт ли checkpoint raw `ATR`, `ATR_ratio` или scaler-normalized ATR | Training использовал один ATR contract, online подаёт другой |
| 12 | Константные признаки выявлены до retrain | Мёртвые признаки маскируют реальный feature contract | Есть variance/unique-count check по train input columns | Признак константный на train, но оставлен как информативный input без решения |
| 13 | Exporter не меняет правило после test | Test должен проверять уже выбранное правило | Rule JSON/checkpoint зафиксирован до test | Порог, top-k, target, exit или фильтр выбираются после просмотра test |
| 14 | MT4 получает тот же сигнал, который проверял Python | Иначе прибыль MT4 нельзя сравнивать с Python | Сверка rows, nonzero rows, unique time, opened trades | Python считает строки, а MT4 исполняет уникальные времена без parity |
| 15 | Online runner блокирует неподдержанный ML-контракт | Лучше не выдать сигнал, чем выдать нечестный сигнал | При несовместимом checkpoint есть явная ошибка | Watcher публикует `ml_signals.csv`, хотя нужные live-safe признаки отсутствуют |

### Быстрая ручная проверка признаков

Перед запуском открыть список входных колонок модели и разделить его на три группы:

| Группа | Примеры | Допуск |
|---|---|---|
| Доступно на текущем баре | `time`, `ATR`, `session_hour`, `weekday`, отсортированные `fractal*.price/time/direction` | Можно использовать при совпадении training/online contract |
| Доступно только после будущих баров | `predict`, `ret_*`, `ret_dir_atr_lag1`, `fav_*`, `adv_*`, future outcome, future path | Нельзя использовать как input |
| Неясно | engineered-поля без описания времени доступности | Запуск запрещён до source audit |

Правило простое: если непонятно, когда поле становится известно, считать его запрещённым до доказательства обратного.

### Особые случаи проекта

#### `predict`

`predict` нельзя считать обычным live-признаком. В training pipeline `predict` строится через будущую цель, поэтому это future-derived поле. В live `Nero.csv` значение `predict=0` не является эквивалентом training `predict`: это не нейтральное значение, а другой смысл поля. Если checkpoint обучался с `predict` во входе, online не должен подменять его нулём.

Отдельный риск: исторически `normalize_rowwise()` нормализует `abs(predict)` в одном пуле с `front/back`. Если в training в этот пул входит реальный future-derived `predict`, а online туда попадает `0`, то меняется не только сам `predict`, но и нормализация `front/back`. Для live-safe retrain нужно исключить `predict` из входа и из live-нормализационных пулов или явно доказать другой эквивалентный контракт.

#### `ret_dir_atr_lag1`

`ret_dir_atr_lag1` не становится безопасным только потому, что он сдвинут на одну строку. Если он вычислен из `ret_6_dir_atr.shift(1)`, то исходный `ret_6_dir_atr` уже содержит будущие бары относительно своей строки. Значит, сдвиг всё ещё может смотреть вперёд относительно текущего решения.

#### `Up/Dn` из MT `Nero.csv`

`Up/Dn` внутри `fractal*` допустимы как live-safe историческое состояние только если доказано, что они накоплены producer-ом к моменту строки и не пересчитаны Python-постобработкой по будущим барам. Если похожие поля построены как supervised targets или future OHLC outcome, они относятся к target/future-derived группе и не допускаются во вход.

### Нормализация

`normalize_rowwise()` сама по себе не является leakage, если её параметры считаются только внутри текущей строки по уже известным фракталам. Проверять нужно две разные вещи:

- для row-wise normalization: в её pool не должны попадать future-derived поля, влияющие на live-признаки;
- для global scaler (`StandardScaler`, `RobustScaler`, min-max по датасету): параметры fit-ятся только на train и затем применяются к validation/test/online.

ATR нужно проверять отдельно. Если checkpoint обучался на raw `ATR`, online должен подавать raw `ATR`. Если checkpoint обучался на scaler-normalized ATR, online обязан применять тот же scaler с сохранёнными train-параметрами. Каждый новый checkpoint явно фиксирует свой ATR/volatility contract.

### Проверка информативности признаков

Перед retrain проверить каждый input feature:

- `unique_count`;
- долю `NaN`;
- долю нулей;
- стандартное отклонение на train.

Если признак константный на всём train, его нельзя оставлять как информативный вход без явного решения. Его нужно удалить из feature builder до retrain или пометить как intentionally disabled.

### Минимальный пакет доказательств

Каждый test/online отчёт должен содержать:

- путь к checkpoint;
- путь к rule JSON, если правило отбора есть;
- список input columns или ссылку на feature builder;
- список запрещённых target/future-derived колонок и подтверждение, что их нет во входе;
- feature count и порядок признаков для checkpoint;
- границы train/validation/test;
- результат проверки сортировки фракталов или других event elements;
- результат проверки нормализации;
- ATR/volatility contract: raw, ratio или scaler-normalized;
- результат проверки константных признаков;
- количество сигналов в Python export;
- количество реально открытых сделок в MT4, если был MT4 tester;
- явный verdict: `PASS`, `FAIL`, `UNKNOWN` или `DIAGNOSTIC_ONLY`.

### Запрещённые практики

- Заполнять отсутствующие online-признаки нулями без явного разрешения в контракте модели.
- Подменять future-derived `predict` нулём в online и считать это совместимым с training.
- Оставлять в training признаки, которые online не может честно воспроизвести.
- Давать future-derived полям влиять на нормализацию live-признаков.
- Выбирать model inputs как "все числовые колонки".
- Использовать `target_*`, `label_*`, `outcome_*` wildcard как input.
- Использовать один и тот же `test` для подбора порогов и для финального доказательства.
- Сравнивать online и backtest, если online preprocessing отличается от training/test preprocessing.
- Считать высокий `PF` доказательством качества, если не пройдены проверки этого раздела.
- Называть diagnostic watcher production-ready, если он проверяет только файловую цепочку.

### Критерии успешного завершения

- Все input features имеют `PASS`.
- `UNKNOWN` отсутствует.
- Есть frozen feature list.
- Есть frozen target/future-derived denylist.
- Есть ссылка на builder или metadata.
- Candidate-source live-safe.
- Rule/checkpoint/exporter совместимы с одним и тем же feature contract.
- Online runner падает при несовместимом contract, а не публикует сигнал.
- Есть явный verdict preflight: `PASS`.

### Типовые ошибки

- Использовать future-derived поля как input.
- Считать lag безопасным без аудита исходного поля.
- Обучить модель с признаками, которые online нельзя честно создать.
- Подменить недоступный input нулём.
- Оставить offline candidate gate, который нельзя воспроизвести live.
- Строить input как "все числовые колонки", из-за чего новые target columns автоматически попадают в модель.

### Ветвления

- Если найден `FAIL`: остановить candidate, исправить data contract или переобучить модель.
- Если найден `UNKNOWN`: считать как `FAIL`.
- Если запуск нужен только для проверки файловой механики: разрешён только `DIAGNOSTIC_ONLY`.
- Если старый profitable contour не проходит contract: его выводы использовать только как research hints.

---

## 4. Разметка целей

### Цель

Создать target, который соответствует торговой задаче, не смешивает разные исходы и не попадает во вход модели.

### Входы

- подготовленные raw/preprocessed данные;
- OHLC или другой источник результата сделки;
- trading protocol;
- feature contract;
- описание target convention.

### Пошаговые действия

1. Описать label convention: значения, классы, timeout, neutral/skip, reversal.
2. Назвать target/label колонки так, чтобы их нельзя было спутать с input-признаками:
   - обязательный префикс для новых колонок: `target_`, `label_` или `outcome_`;
   - legacy-колонки без префикса допустимы только при явном allowlist/denylist contract;
   - feature builders должны выбирать input по allowlist, а не по схеме "всё, кроме нескольких известных targets".
3. Зафиксировать момент входа и выхода для расчёта результата.
4. Для fixed horizon указать горизонт и единицы: price, ATR, пункты, деньги.
5. Для SL/TP или triple barrier определить:
   - что делать, если TP и SL задеты в одном окне;
   - как трактуется timeout;
   - как считать reversal;
   - какие цены используются: open, close, high/low, bid/ask.
6. Проверить distribution targets по train/validation/test.
7. Проверить distribution по сторонам BUY/SELL.
8. Добавить invariant tests или воспроизводимый audit label convention.

### Обязательные проверки

- Target строится из будущего только как label.
- Все target columns исключены из input.
- Новые target/label columns имеют говорящий префикс; legacy-имена без префикса внесены в denylist.
- Timeout не смешивается с SL, если это разные исходы.
- BUY и SELL считаются симметрично или асимметрия явно описана.
- Target не зависит от test-selected threshold.

### Критерии успешного завершения

- Есть target contract.
- Есть список target/label column names и denylist для feature builder-а.
- Есть sanity check распределения классов и сторон.
- Есть тесты или audit для edge cases.
- Известно, какие target-колонки являются production labels, а какие diagnostic.

### Типовые ошибки

- Приведение label к неподходящему типу и перекодировка исходов.
- Подбор target по лучшему test PF.
- Смешивание timeout, SL и neutral без явного смысла.
- Использование future target как feature из-за удобного расположения в CSV.
- Использование `target_*`/`label_*` wildcard как input из-за нестрогого парсинга колонок.

### Ветвления

- Если label convention неоднозначна: не обучать модель, пока не описаны edge cases.
- Если target columns названы как обычные features: переименовать новые колонки или добавить явный denylist для legacy-полей до обучения.
- Если класс слишком редкий: перейти к take/skip, ranking, binary one-vs-rest или изменить задачу.
- Если одна сторона имеет другой режим: рассмотреть отдельные BUY/SELL модели, но как новый кандидат.

---

## 5. Data Quality, EDA и статистический аудит

### Цель

Найти проблемы данных и понять базовую структуру сигнала до сложных моделей.

### Входы

- train split;
- validation split только для проверки устойчивости выводов, не для ручного подбора признаков;
- data inventory;
- target contract;
- feature contract.

### Пошаговые действия

1. Проверить количество строк, период, пропуски, `NaN`, `inf`, пустые вложенные элементы.
2. Проверить диапазоны признаков и монотонные инварианты.
3. Проверить class balance и side balance.
4. Найти константные и почти константные признаки.
5. Построить распределения признаков по классам и сторонам.
6. Проверить временную концентрацию событий.
7. Проверить drift между train и validation.
8. Выполнить простые статистические тесты как диагностику, а не как разрешение использовать признак.
9. Сохранить EDA report с выводами и ограничениями.

### Обязательные проверки

- EDA проводится только на данных, разрешённых для этого этапа.
- Feature importance не отменяет leakage audit.
- Константные признаки не оставляются как якобы информативные.
- Accuracy не используется как основная метрика при сильном дисбалансе.

### Критерии успешного завершения

- Известны дисбаланс классов, распределение сторон, выбросы и мёртвые признаки.
- Есть список data quality defects.
- Есть решение: исправить данные, исключить признаки или продолжать.

### Типовые ошибки

- По p-value или feature importance легализовать future-derived поле.
- Игнорировать minority-class precision/recall.
- Делать вывод по aggregate metric без годовых и сторонних срезов.
- Переносить EDA-вывод с validation на test.

### Ветвления

- Если много NaN/inf: исправить preprocessing и пересобрать данные.
- Если признаки константны из-за отсутствующего источника: удалить или пометить intentionally disabled.
- Если signal крайне редкий: выбрать метрики, устойчивые к дисбалансу, и baseline, который это отражает.

---

## 6. Временное разделение и протокол валидации

### Цель

Защититься от утечки будущего через split и обеспечить честную проверку во времени.

### Входы

- подготовленный датасет;
- timestamps;
- target horizon;
- planned validation/test/forward windows.

### Пошаговые действия

1. Отсортировать строки по времени в направлении, соответствующем pipeline.
2. Задать train/validation/test границы датами и индексами.
3. Проверить, что shuffle временных строк не применяется.
4. Если label horizon пересекает границу split, оценить нужен ли embargo gap.
5. Если проводится hyperparameter search, использовать только train/validation.
6. Если нужен walk-forward, заранее задать rolling или expanding windows.
7. Сохранить split manifest.

### Обязательные проверки

- Validation используется для выбора модели, признаков, порогов и правил.
- Test открывается только для frozen candidate.
- Forward включает только данные после даты принятия решения.
- Нельзя объединять test и forward задним числом.

### Критерии успешного завершения

- Есть явные даты и размеры train/validation/test.
- Есть правило, что можно подбирать на validation.
- Есть правило, что запрещено менять после test.
- Есть план walk-forward или причина, почему он не нужен на данном этапе.

### Типовые ошибки

- Случайный split временного ряда.
- Многократный test после каждого изменения.
- Называть старый frozen test forward validation.
- Подбирать threshold на test, а потом заявлять OOS.

### Ветвления

- Если test уже использован для выбора: нужен новый holdout или strictly-forward период.
- Если validation/test режимы сильно различаются: добавить walk-forward и regime analysis.
- Если forward данных нет: verdict `watch/no_forward_data`, не `confirmed`.

---

## 7. Baseline-first этап

### Цель

Получить нижнюю планку качества и sanity checks до сложных моделей.

### Входы

- train/validation split;
- target contract;
- feature contract;
- выбранные метрики.

### Пошаговые действия

1. Запустить dummy baseline:
   - majority class;
   - random class с class prior;
   - always skip;
   - простое direction rule, если применимо.
2. Запустить простые ML baselines:
   - logistic/linear model;
   - tree model;
   - random forest или gradient boosting;
   - simple ranking/threshold rule.
3. Для sequence task сравнить flattened, engineered и sequence representations.
4. Считать classification metrics и trading metrics отдельно.
5. Проверить BUY/SELL отдельно.
6. Сохранить baseline report и confusion matrix.
7. Зафиксировать baseline, который должен быть побит новым кандидатом.

### Обязательные проверки

- Baseline использует тот же split и тот же live-safe feature contract.
- Baseline не подбирается на test.
- При дисбалансе смотреть precision/recall/F1/MCC, а не только accuracy.
- Trading baseline включает издержки или помечен gross diagnostic.

### Критерии успешного завершения

- Есть минимум один dummy и один простой ML baseline.
- Известно, насколько модель превосходит или не превосходит baseline.
- Есть baseline для сравнения в final verdict.

### Типовые ошибки

- Сразу обучать Transformer/ensemble без baseline.
- Сравнивать сложную модель с неправильной метрикой.
- Считать низкое число сделок высоким PF без статистической базы.
- Не проверять, не держится ли результат только на BUY или SELL.

### Ветвления

- Если baseline сильнее сложной модели: не усложнять, изучить target/features.
- Если baseline уже использует leakage: baseline invalid, начать с feature contract.
- Если простая модель даёт близкий результат: усложнение должно иметь практический смысл, а не только лучшую offline metric.

---

## 8. Разработка модели

### Цель

Обучить кандидата так, чтобы архитектура, признаки и параметры были воспроизводимы и проверяемы.

### Входы

- train/validation data;
- baseline report;
- model family candidates;
- reproducibility policy;
- resource constraints.

### Пошаговые действия

1. Выбрать модельную формулировку:
   - классификация;
   - регрессия;
   - ranking;
   - binary one-vs-rest;
   - multi-output regression;
   - barrier probability.
2. Выбрать минимально достаточную архитектуру.
3. Зафиксировать seed, device, library versions, batch size, epochs, early stopping.
4. Зафиксировать feature count, order, sequence length и target order.
5. Проверить cache invalidation при смене feature contract.
6. Обучать и логировать каждую конфигурацию.
7. Сохранять checkpoint, config, metrics, predictions и run metadata.
8. Для нейросетей проверить несколько seed или объяснить, почему это невозможно.

### Обязательные проверки

- Модель получает ровно те признаки, что указаны в feature contract.
- Target order в training, evaluation и export совпадает.
- Early stopping смотрит только validation.
- Production retrain воспроизводим на зафиксированном устройстве.
- Checkpoint нельзя использовать без metadata.

### Критерии успешного завершения

- Есть воспроизводимый training run.
- Есть сохранённые predictions на validation.
- Есть run metadata.
- Есть сравнение с baseline.

### Типовые ошибки

- Менять feature contract без очистки cache.
- Перепутать порядок targets при export/evaluation.
- Делать вывод по одному seed при нестабильном торговом фильтре.
- Считать CPU/GPU checkpoints одинаковыми только из-за одинакового seed.

### Ветвления

- Если модельная метрика растёт, а trading metric нет: пересмотреть target и execution mapping.
- Если seeds дают разные winners: заморозить простое правило или снизить статус до research-only.
- Если GPU/CPU дают разные checkpoints: production retrain выполнять только в выбранном воспроизводимом режиме.

---

## 9. Validation selection и freeze-протокол

### Цель

Выбрать одного кандидата на validation и заморозить всё до test.

### Входы

- validation predictions;
- baseline report;
- metric/gate plan;
- candidate rules;
- cost assumptions.

### Пошаговые действия

1. Провести grid/sweep только на validation.
2. Считать не только PF, но и:
   - sequential PF;
   - trades count;
   - trades per year;
   - win/loss;
   - yearly/monthly slices;
   - BUY/SELL slices;
   - drawdown;
   - concentration of profit.
3. Применить production gates до выбора winner.
4. Зафиксировать один winner.
5. Сохранить rule JSON, threshold, checkpoint path, feature contract, export command.
6. Запретить изменение rule после просмотра test.

### Обязательные проверки

- Winner selection уважает minimum trades и другие gates.
- Нельзя выбирать максимальный PF среди кандидатов, которые не проходят gate.
- Test не участвует в выборе threshold/top-k/exit/filter.
- Если используется ensemble/stacking, нужен out-of-fold protocol или отдельный holdout.

### Критерии успешного завершения

- Есть ровно один frozen candidate.
- Есть frozen artifacts.
- Есть validation report с rejected alternatives.
- Известно, какой baseline кандидат должен побить на test.

### Типовые ошибки

- `pick_winner` выбирает высокий PF на малом N.
- Менять threshold после test.
- Выбирать rule-family по test, а параметры по validation.
- Считать структурную стабильность между seeds доказанной без формального tolerance.

### Ветвления

- Если нет validation candidate, проходящего gates: reject или изменить гипотезу.
- Если несколько кандидатов близки: выбрать заранее заданным tie-breaker, а не по test.
- Если winner нестабилен между seeds: понизить статус или использовать более простое frozen rule.

---

## 10. Frozen test, OOS и walk-forward

### Цель

Проверить уже выбранного кандидата на данных, не использованных для выбора.

### Входы

- frozen checkpoint/rule;
- test split;
- split manifest;
- cost model;
- baseline test metrics, если они заранее допустимы.

### Пошаговые действия

1. Перед test проверить, что rule/checkpoint/exporter не менялись после validation.
2. Запустить test один раз для frozen candidate.
3. Считать модельные и торговые метрики.
4. Считать time slices: год, квартал или regime buckets.
5. Считать BUY/SELL отдельно.
6. Сравнить с baseline.
7. Если есть заранее заданный walk-forward: выполнить rolling/expanding evaluation без ретюнинга на test.
8. Сохранить predictions, trades, summary и limitations.

### Обязательные проверки

- Test не используется для подбора нового правила.
- Aggregate PF не скрывает отрицательные годы.
- Aggregate PF не скрывает слабую сторону BUY/SELL.
- Walk-forward не подменяется повторным test.
- Кандидат проходит заранее заданные gates.

### Критерии успешного завершения

- Есть frozen test report.
- Есть verdict: `reject`, `research_only`, `candidate`.
- Все слабые срезы перечислены.
- Известно, какие проверки нужны перед MT4/forward.

### Типовые ошибки

- Считать PF > 1 достаточным без учёта издержек и стабильности.
- Игнорировать два отрицательных года, если aggregate PF положительный.
- После слабого SELL результата объявлять BUY-only без нового validation cycle.
- Перезапускать test после каждой правки.

### Ветвления

- Если test fail: reject или новый cycle, но не подстройка на test.
- Если aggregate pass, но side fail: оформить side-specific стратегию как новый кандидат.
- Если test pass, но нет forward: статус не выше `candidate`.

---

## 11. Устойчивость и robustness

### Цель

Понять, является ли результат устойчивым или держится на одном периоде, стороне, провайдере, seed или редких сделках.

### Входы

- frozen test trades;
- validation/test predictions;
- multi-seed runs;
- provider/instrument data, если применимо;
- portfolio/correlation context.

### Пошаговые действия

1. Проверить устойчивость по годам и кварталам.
2. Проверить BUY и SELL отдельно.
3. Проверить sequential simulation при ограничении числа позиций.
4. Проверить sensitivity к threshold, top-k, hold, SL/TP, costs.
5. Проверить multi-seed для training и rule selection.
6. Проверить provider drift на том же инструменте.
7. Только после provider drift проверять transfer на другие инструменты.
8. Проверить correlation с существующими системами, если кандидат идёт в portfolio.

### Обязательные проверки

- Устойчивость не доказывается одним aggregate PF.
- Transfer не заявляется без отдельного теста.
- Provider drift и instrument transfer не смешиваются.
- Side-specific failure не скрывается balance metric.

### Критерии успешного завершения

- Известно, какие режимы рынка кандидат переносит плохо.
- Есть решение: reject, narrow-scope, research-only или candidate.
- Есть список stress conditions, которые убивают edge.

### Типовые ошибки

- Считать одну удачную конфигурацию доказательством family stability.
- Игнорировать слабую SELL сторону.
- Считать provider-stable систему универсальной для других инструментов.
- Использовать старые до-audit transfer выводы для live-safe версии.

### Ветвления

- Если один side fail: новый BUY-only/SELL-filter cycle, не post-test tweak.
- Если один год fail: проверить regime, но не исключать год без заранее заданного правила.
- Если provider stable, но instruments fail: ограничить scope инструментом.

---

## 12. Backtest с торговыми издержками

### Цель

Проверить, сохраняется ли edge после реалистичного исполнения.

### Входы

- frozen signals или trades;
- OHLC/tick/tester data;
- trading protocol;
- cost assumptions;
- position constraints.

### Пошаговые действия

1. Описать cost model:
   - spread;
   - commission;
   - swap;
   - slippage;
   - requote/open failure;
   - latency;
   - next-bar entry;
   - position limits.
2. Считать gross и net results отдельно.
3. Запустить offline backtest по тому же trading protocol.
4. Запустить sequential simulation для single-position или max-positions ограничения.
5. Проверить повышенные costs.
6. Разделить close reasons: SL, TP, timeout, reversal, manual/forced close.
7. Для MT4-кандидата выполнить tester run.

### Обязательные проверки

- Cost assumptions указаны до final verdict.
- Entry timing совпадает с target и export.
- Spread/commission/slippage не оставлены "на потом".
- Timeout PnL и SL/TP PnL анализируются отдельно.
- Пропущенные входы не считаются нулевым риском без обоснования.

### Критерии успешного завершения

- Net PF и drawdown проходят gates.
- Известно, какие издержки убивают стратегию.
- Есть список расхождений offline vs tester.
- Gross-only результат не выдан за production.

### Типовые ошибки

- Игнорировать комиссии и spread при PF около 1.
- Считать OHLC close эквивалентом tick execution.
- Не учитывать requote и missed opens.
- Делать вывод о модели по M5 diagnostic, если production H1.

### Ветвления

- Если edge исчезает после costs: reject или redesign target/rule.
- Если расхождения только в timeout: отделить market-close risk от signal risk.
- Если requote/open failures частые: сначала чинить execution reliability, не модель.

---

## 13. Export, MT4 parity и reconciliation

### Цель

Доказать, что торговая платформа исполняет тот же сигнал, который был проверен в Python.

### Входы

- frozen export CSV;
- rule metadata;
- MT4 tester log;
- trade event-log;
- reconciliation tool.

### Пошаговые действия

1. Зафиксировать export format.
2. Зафиксировать hash экспортированного файла.
3. Проверить counts:
   - rows total;
   - nonzero rows;
   - unique time;
   - unique time+signal;
   - duplicate time;
   - opposite signals on same time.
4. Запустить MT4 tester на заданном периоде.
5. Сверить:
   - expected signals;
   - opened trades;
   - closed trades;
   - missing opens;
   - wrong direction;
   - critical mismatches;
   - close reasons.
6. В online/tester сверке сопоставлять по `signal_time + direction`, а не по ticket.
7. Логировать `OPEN_FAILED`, spread, slippage, Bid/Ask, commission, swap, balance/equity.
8. Исключить неполные края периода из строгого verdict.

### Обязательные проверки

- MT4 читает именно проверенный файл.
- Exporter не меняет rule после test.
- Есть reconciliation report.
- Все missing trades объяснены или помечены blocker.
- Механический parity не объявляется forward profitability proof.

### Критерии успешного завершения

- `critical_mismatch_count = 0` или расхождения классифицированы и приняты как non-blocking.
- Разница строк export и opened trades объяснена.
- Известен effect duplicate timestamps.
- Online/tester diagnostic не объявляется proof of profitability.

### Типовые ошибки

- Сравнивать число строк CSV с числом сделок без учёта duplicate time.
- Игнорировать границы tester interval.
- Не писать `OPEN_FAILED`.
- Смешивать mechanical parity и ML quality.
- Не очищать tester event-log перед новым прогоном.

### Ветвления

- Если сигналы не совпадают: чинить export/runtime, не менять модель.
- Если сигналы совпадают, но PnL отличается: разбирать execution layer.
- Если open failures существенны: улучшать retry/slippage или снижать trading frequency.

---

## 14. Forward-test и online diagnostic

### Цель

Проверить frozen candidate на новых данных после принятия решения.

### Входы

- frozen checkpoint/rule;
- новые raw или prediction данные после decision date;
- online event-log;
- monitoring metrics;
- risk limits.

### Пошаговые действия

1. Зафиксировать дату production decision.
2. Собирать forward data только после этой даты.
3. Не менять rule на forward window.
4. Считать metrics и time slices.
5. Разделять:
   - signal quality;
   - execution quality;
   - infrastructure health.
6. Контролировать delays, missed opens, requotes, spread spikes.
7. Если данных нет, выставить `watch/no_forward_data`.

### Обязательные проверки

- Forward window строго новее validation/test.
- Нет ретюнинга на forward до verdict.
- Online preprocessing проходит leakage preflight.
- Diagnostic timeframe не подменяет production timeframe.
- Forward результат не смешивается с historical test.

### Критерии успешного завершения

- Есть verdict: `confirmed`, `watch`, `revisit`, `reject`.
- Есть next action на основе forward.
- Есть список execution issues отдельно от signal issues.

### Типовые ошибки

- Называть старый frozen test forward validation.
- Менять threshold после нескольких online сделок.
- Делать вывод о H1-модели по M5 diagnostic.
- Не отделять пропущенный вход от плохого сигнала.

### Ветвления

- Если forward нет: продолжать сбор, не повышать статус.
- Если N мало: `watch`, если это было задано заранее.
- Если risk limits нарушены: остановить торговлю и открыть audit.
- Если signal ok, execution fail: чинить execution layer.

---

## 15. Monitoring и retraining policy

### Цель

Не допустить, чтобы после допуска к online frozen candidate незаметно устарел, начал работать в другом data regime или был заменён новой моделью без полного validation cycle.

### Входы

- production candidate или confirmed model;
- online predictions;
- trade event-log;
- post-factum outcomes;
- baseline distributions train/validation/test;
- feature contract version;
- risk limits.

### Пошаговые действия

1. Логировать каждый prediction:
   - timestamp;
   - feature contract version;
   - checkpoint/rule version;
   - score/probability;
   - signal;
   - skip/take reason.
2. Логировать каждую сделку:
   - signal_time;
   - entry_time;
   - direction;
   - Bid/Ask;
   - spread;
   - slippage;
   - commission;
   - swap;
   - close reason;
   - PnL.
3. Мониторить signal frequency, BUY/SELL balance, score distribution и skip rate.
4. Мониторить drift live-safe признаков относительно train/validation baseline.
5. Мониторить trading metrics: net PF, EV/trade, drawdown, missed opens, requotes, timeout PnL.
6. Задать retraining triggers:
   - календарный;
   - degradation по заранее заданным метрикам;
   - data drift;
   - feature/data contract change;
   - broker/provider change.
7. Новый retrain проводить только через полный cycle методики: feature contract -> validation -> frozen test -> robustness/parity -> forward.
8. Поддерживать rollback: предыдущий frozen checkpoint/rule остаётся доступен до принятия нового.

### Обязательные проверки

- Monitoring не меняет threshold/rule online без нового validation cycle.
- Drift alert означает audit, а не автоматическое включение новой модели.
- Метрики исполнения отделены от метрик качества сигнала.
- Feature contract version сохранён рядом с prediction и trade event.
- Retrain не использует forward/test как validation.

### Критерии успешного завершения

- Есть monitoring checklist и incident procedure.
- Есть политика: когда кандидат остаётся `watch`, когда отключается, когда допускается retrain.
- Есть rollback procedure.
- Есть минимальный набор полей логов для post-factum reconciliation.

### Типовые ошибки

- Менять threshold по live PnL без нового validation cycle.
- Смешивать broker execution failure с деградацией модели.
- Не хранить feature contract version рядом с prediction.
- Автоматически заменять production candidate свежим retrain checkpoint.
- Считать drift proof of failure без проверки trading impact и execution layer.

### Ветвления

- Если drift есть, а PnL и risk limits нормальные: статус `watch`, усилить monitoring.
- Если execution failures растут: чинить MT4/broker layer, не модель.
- Если signal quality деградировала на достаточном N: остановить candidate и запустить новый research cycle.
- Если contract изменился: старый checkpoint нельзя использовать без compatibility audit.

---

## 16. Отчётность и аудит ошибок

### Цель

Сделать результаты воспроизводимыми и пригодными для следующей итерации.

### Входы

- команды запуска;
- artifacts;
- metrics;
- modified files;
- reports;
- known limitations.

### Пошаговые действия

1. Написать отчёт с секциями:
   - Context;
   - What Was Done;
   - Changed Files;
   - Verification;
   - Results;
   - Conclusions;
   - Limitations / Open Questions;
   - Next Step;
   - Related Materials.
2. Указать команды, версии, paths, hashes, rules, checkpoints.
3. Явно перечислить invalidated assumptions.
4. Для принятого кандидата создать model card:
   - назначение модели;
   - instrument/timeframe;
   - `decision_time`;
   - feature contract version;
   - target/label contract;
   - training/validation/test/forward windows;
   - checkpoint/rule/export paths;
   - cost assumptions;
   - validation/test/forward verdict;
   - known risks;
   - monitoring/retraining policy;
   - stop conditions.
5. Если найден баг прошлого вывода:
   - доказать минимальным reproducer;
   - оценить material impact;
   - пометить старые выводы как invalid, superseded или unchanged.
6. Обновить changelog/handoff/wiki только если этап действительно закрыт или выводы изменили проектное знание.

### Обязательные проверки

- Отчёт отделяет факты от гипотез.
- Есть список limitations.
- Все источники результата доступны.
- Для принятого кандидата есть model card.
- Старые противоречащие выводы помечены.
- Документировано, что запрещено делать дальше.

### Критерии успешного завершения

- Следующий агент может воспроизвести результат по отчёту.
- Ясно, что делать дальше.
- Ясно, какой статус получил кандидат.

### Типовые ошибки

- Писать только итоговый PF без команд.
- Повышать статус кандидата без model card.
- Не фиксировать, почему candidate rejected.
- Удалять неудачные эксперименты из истории.
- Не обновлять вывод после найденной ошибки симулятора.

### Ветвления

- Если result strong, но contract failed: verdict `diagnostic_only`.
- Если bug не меняет verdict: зафиксировать unchanged impact.
- Если bug меняет verdict: закрыть старый candidate и запустить новый cycle.

---

## Сводный чеклист разработки

Использовать перед запуском нового ML-кандидата.

- [ ] Гипотеза описана до экспериментов.
- [ ] `decision_time` зафиксирован.
- [ ] Raw data inventory создан.
- [ ] Feature contract заполнен для всех input fields.
- [ ] Leakage preflight: `PASS`.
- [ ] Candidate-source live-safe.
- [ ] Target contract описан и проверен.
- [ ] Preprocessing воспроизводим.
- [ ] Нормализация не использует будущие поля.
- [ ] Split строго временной.
- [ ] Validation/test/forward границы указаны.
- [ ] Baseline-модели запущены.
- [ ] Метрики и gates заданы до validation sweep.
- [ ] Hyperparameter/model selection не использует test.
- [ ] Один frozen candidate выбран на validation.
- [ ] Rule/checkpoint/exporter заморожены до test.
- [ ] Test открыт один раз для frozen candidate.
- [ ] Backtest учитывает spread, commission, swap, slippage и position limits.
- [ ] Проверены yearly/monthly slices.
- [ ] Проверены BUY/SELL отдельно.
- [ ] Проверены sequential metrics.
- [ ] Проверена multi-seed или иная устойчивость.
- [ ] Export parity выполнен перед MT4 verdict.
- [ ] MT4 tester/reconciliation выполнены для execution candidate.
- [ ] Forward/online diagnostic не смешан с historical test.
- [ ] Monitoring/retraining policy описана для production candidate.
- [ ] Для принятого кандидата создан model card.
- [ ] Итоговый отчёт содержит commands, artifacts, limitations, next step.

## Сводный чеклист аудита готового результата

Использовать перед повышением статуса кандидата.

- [ ] Можно указать, какие данные модель видит в момент сделки.
- [ ] Нет `UNKNOWN` признаков.
- [ ] Нет future-derived input.
- [ ] Candidate-source live-safe.
- [ ] Training и online feature contract совпадают.
- [ ] Нормализация не использует future-derived поля в live-пулах.
- [ ] Global scaler fit только на train.
- [ ] Target order одинаков в train/evaluate/export.
- [ ] Rule/checkpoint/threshold заморожены до test.
- [ ] Test не использовался для выбора.
- [ ] PF не основан на малом N без пометки research-only.
- [ ] Нет скрытого провала одной стороны BUY/SELL.
- [ ] Нет скрытого провала отдельных годов.
- [ ] Издержки включены или результат помечен gross diagnostic.
- [ ] Python export соответствует MT4 opened trades.
- [ ] Online/tester расхождения классифицированы.
- [ ] Все open failures и requote видимы в логах.
- [ ] Feature contract version сохраняется рядом с prediction/trade event.
- [ ] Monitoring не меняет rule без нового validation cycle.
- [ ] Reproducibility metadata сохранена.
- [ ] Для production/confirmed кандидата есть model card.
- [ ] Старые противоречащие выводы обновлены или помечены.

## Типовые причины ложных выводов в проекте

Эти ошибки уже проявлялись в исследованиях и должны проверяться явно:

- Высокий исторический PF был получен на future-derived inputs.
- Training feature contract не совпадал с online contract.
- Offline candidate-source был недоступен в live.
- `signal != 0` использовался как gate, хотя в live raw data он не воспроизводится тем же способом.
- Lag от future outcome ошибочно считался безопасным.
- Future-derived поле влияло на normalization pool live-признаков.
- CPU/GPU training давали разные checkpoints при одном seed.
- Auto-winner selection выбирал высокий PF на малом числе сделок.
- Timeout/SL label convention смешивались в симуляторе.
- Test использовался как фактическая validation через повторные попытки.
- Python export и MT4 execution считались равными без parity.
- Duplicate timestamps интерпретировались как ошибка данных, хотя это разные события одного бара.
- Online/tester PnL-разница смешивала ML signal risk и execution risk.
- Spread, slippage, requote и missed opens не были включены в ранний вывод.
- Aggregate PF скрывал слабую сторону SELL или отрицательный год.
- BUY-only или SELL-filter объявлялись улучшением после test, хотя это новая гипотеза и требует нового validation cycle.
- Рост PF объяснялся "лучшим сигналом", хотя фактически мог идти от лучшей цены входа на провальных сигналах.

## Verdict-статусы кандидатов

| Verdict | Значение | Разрешённые действия |
|---|---|---|
| `reject` | Гипотеза не прошла обязательные gates | Закрыть или сформулировать новую гипотезу |
| `diagnostic_only` | Проверялась механика, но ML quality не доказана | Использовать только для отладки pipeline |
| `research_only` | Есть сигнал, но не хватает устойчивости или contract неполный | Продолжать исследования, не подключать к production |
| `candidate` | Прошёл validation/test, но нет полного execution/forward подтверждения | Готовить parity, robustness, forward |
| `production_candidate` | Прошёл data contract, baseline comparison, frozen test, net-cost backtest, robustness или walk-forward, MT4 parity/reconciliation | Допускается controlled forward/online diagnostic; forward ещё не обязателен |
| `confirmed` | Forward подтвердил frozen rule на заранее заданных критериях | Поддерживать monitoring, rollback и periodic retrain policy |

## Stop conditions

Остановить текущий cycle и не продолжать model sweep, если:

- data contract не прошёл leakage gate;
- online features недоступны;
- candidate-source не live-safe;
- test уже был использован для выбора;
- validation gate не пройден;
- единственный плюс кандидата держится на одной стороне, одном году или очень малом N;
- cost-aware result отрицателен;
- MT4 parity показывает critical mismatch;
- forward data отсутствуют, но требуется forward verdict.

Правильный следующий шаг в этих случаях: написать reject/diagnostic report и сформулировать новую ограниченную гипотезу.

## Примеры первичных источников для проверки

- Live-safe audit: [`2026-05-05-live-safe-ml-audit.md`](../reports/2026-05-05-live-safe-ml-audit.md).
- Online contract hardening: [`2026-04-29-online-inference-contract-hardening.md`](../reports/2026-04-29-online-inference-contract-hardening.md).
- Candidate-source audit: [`2026-05-14-entry-path-all-rows-ranking.md`](../reports/2026-05-14-entry-path-all-rows-ranking.md), [`2026-05-14-entry-path-causal-surrogate.md`](../reports/2026-05-14-entry-path-causal-surrogate.md), [`2026-05-14-entry-path-direct-bar-model.md`](../reports/2026-05-14-entry-path-direct-bar-model.md).
- Симулятор и label convention: [`2026-04-12-tb-verdict.md`](../reports/2026-04-12-tb-verdict.md).
- Winner selection и gate: [`2026-04-12-quantile-status-decision.md`](../reports/2026-04-12-quantile-status-decision.md).
- Forward/no-forward статус: [`2026-04-13-quantile-forward-validation.md`](../reports/2026-04-13-quantile-forward-validation.md).
- CPU/GPU reproducibility: [`2026-05-07-cpu-gpu-reproducibility.md`](../reports/2026-05-07-cpu-gpu-reproducibility.md).
- MT4 parity: [`2026-05-07-entry-path-mt4-parity.md`](../reports/2026-05-07-entry-path-mt4-parity.md), [`2026-04-22-signal-export-parity.md`](../reports/2026-04-22-signal-export-parity.md).
- Online/tester execution: [`2026-05-12-online-tester-execution-reconciliation.md`](../reports/2026-05-12-online-tester-execution-reconciliation.md).
- Пример side failure: [`2026-05-15-direct-direction-improvement.md`](../reports/2026-05-15-direct-direction-improvement.md).
