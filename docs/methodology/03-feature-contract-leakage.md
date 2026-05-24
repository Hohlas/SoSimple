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

### Candidate-source live-safe check

До запуска экспериментов проверить не только признаки, но и механизм, который определяет, какие строки датасета являются кандидатами на торговое решение. Это не часть feature contract — это фильтр строк, применяемый до или после модели.

#### В чём разница с проверкой признаков

Leakage Preflight (пункты 1–15 выше) проверяет, что модель не видит будущие данные через input-признаки. Candidate-source проверяет, что правило отбора строк-кандидатов работает в live без будущих данных.

Пример: `signal != 0` из оффлайн `label_all()`. Это не признак модели, а пост-инференс фильтр: из всех предсказаний выбираются только строки, где оффлайн-разметка говорит «здесь был разворот». В live `Nero.csv` `signal` всегда 0 — фильтр невоспроизводим.

#### Обязательные проверки
- Механизм, решающий «эта строка — кандидат на сигнал», должен работать в live без оффлайн-разметки.
- Ablation: отключить candidate фильтр и проверить, не держится ли весь edge на нём. Если без фильтра PF < 1.0 — результат является артефактом фильтра, а не качеством модели.
- Правильный подход: не фильтровать строки по оффлайн-разметке. Подавать все строки. Решение «входить или нет» принимает сама модель через score/confidence threshold, доступный в live.
- Если candidate-source не live-safe: переобучить модель без этого фильтра или с фильтром, воспроизводимым в live.

#### Типовые ошибки
- Использовать оффлайн `signal != 0` как production gate.
- Использовать `predict != 0` в live (всегда 0 в raw данных).
- Считать, что ranking всех строк без candidate gate эквивалентен исходному контуру — нет, это другой контур.
- Надеяться, что «модель сама выучит не торговать плохие строки» без проверки ablation-ом.

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

