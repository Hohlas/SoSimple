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
   - обязательный префикс для новых колонок: `target_`, `label_` или `outcome_` — либо суффикс `_flag`, `_label`, `_target`, если роль колонки явно зафиксирована в target contract и колонка внесена в denylist/не попадает в input allowlist;
   - без префикса или суффикса колонки допустимы только при явном allowlist/denylist contract;
   - feature builders должны выбирать input по allowlist, а не по схеме "всё, кроме нескольких известных targets".
3. Зафиксировать момент входа и выхода для расчёта результата.
4. Для fixed horizon указать горизонт и единицы: price, ATR, пункты, деньги.
5. Для SL/TP или triple barrier определить:
   - что делать, если TP и SL задеты в одном окне;
   - как трактуется timeout;
   - как считать reversal;
   - какие цены используются: open, close, high/low, bid/ask.
6. Если label зависит от исполнения, включить execution-aware поля в target contract:
   - `entry_price` convention;
   - measured/canonical spread convention для BUY и SELL;
   - fill/no-fill outcome;
   - `fill_lag`;
   - ambiguous same-bar policy;
   - `pnl_r` или другую заранее выбранную PnL-единицу для evaluation.
7. Проверить distribution targets по train/validation/locked_test.
8. Проверить distribution по сторонам BUY/SELL.
9. Добавить invariant tests или воспроизводимый audit label convention.

### Обязательные проверки

- Target строится из будущего только как label.
- Все target columns исключены из input.
- Новые target/label columns имеют говорящий префикс (`target_`/`label_`/`outcome_`) или суффикс (`_flag`/`_label`/`_target`) с явной ролью в target contract и denylist/input allowlist; legacy-имена без префикса/суффикса внесены в denylist.
- Timeout не смешивается с SL, если это разные исходы.
- BUY и SELL считаются симметрично или асимметрия явно описана.
- Если направление определяется по `fractal0.dir` (live-safe), каждая строка получает target/label только для своей стороны; противоположная сторона = NaN. Модель учится только на релевантных ей примерах — это не ошибка, а намеренное сужение обучающей выборки.
- Target не зависит от test-selected threshold.
- Если live не может исполнить вход по `Close[row]`, такая label convention разрешена только как `DIAGNOSTIC_ONLY`.
- Если canonical spread не равен нулю, labels со `spread=0` разрешены только как `DIAGNOSTIC_ONLY`.
- PF для execution-aware labels считается по PnL (`pnl_r`, пункты или деньги), а не по `count(TP) / count(SL)`, если timeout/fill/no-fill могут иметь ненулевой результат.

### Критерии успешного завершения

- Есть target contract.
- Есть список target/label column names и denylist для feature builder-а.
- Есть sanity check распределения классов и сторон.
- Есть тесты или audit для edge cases.
- Известно, какие target-колонки являются production labels, а какие diagnostic.
- Если используется limit/stop entry, известны no-fill rate, fill-lag distribution и ambiguous-rate.

### Типовые ошибки

- Приведение label к неподходящему типу и перекодировка исходов.
- Подбор target по лучшему `locked_test` PF.
- Смешивание timeout, SL и neutral без явного смысла.
- Использование future target как feature из-за удобного расположения в CSV.
- Использование `signal` как источника кандидатов для рабочего контура. `signal` построен по будущему состоянию уровня `fractal0` — это фильтр по будущим данным. Для фрактальных BUY/SELL-постановок направление должно браться из `fractal0.dir`.
- Использование `target_*`/`label_*` wildcard как input из-за нестрогого парсинга колонок.
- Поздно добавлять spread/entry/fill convention только на backtest-этапе, если они меняют labels или candidate selection.
- Считать `Close[row]` реалистичной ценой входа без доказательства, что live-контур может открыть сделку по этой цене.
- Использовать zero-spread labels как production target или validation gate.

### Ветвления

- Если label convention неоднозначна: не обучать модель, пока не описаны edge cases.
- Если target columns названы как обычные features: переименовать новые колонки или добавить явный denylist для legacy-полей до обучения.
- Если класс слишком редкий: перейти к take/skip, ranking, binary one-vs-rest или изменить задачу.
- Если одна сторона имеет другой режим: рассмотреть отдельные BUY/SELL модели, но как новый кандидат.

### Entry/Exit convention examples

#### Общее правило

Execution convention has two layers: general contract and project-specific availability proof. General contract fixes entry type, entry price, spread, fill/no-fill, latency and PnL convention. Project-specific proof explains when the signal-producing object becomes available in live.

#### Проектный пример: `fractal0`-контур

Для текущего MT-контура `fractal0` становится полностью известен только на `Close` своего подтверждающего третьего бара. После этого MQL записывает строку 100 фракталов в `Nero.csv`, watcher считывает файл, выполняет preprocessing/inference и передаёт сигнал дальше. Общие задержки:

| Источник задержки | Что определяет | Типовой порядок |
|---|---|---|
| Row materialization | Время записи строки в CSV | Секунды |
| Watcher polling interval | Как часто watcher проверяет файл | Секунды |
| Preprocessing/inference | Время обработки и предсказания | Сотни мс |
| Order-send delay | Время отправки ордера в MT4 | Сотни мс |

Следствие: `Close[row]`-entry для fractal0-контура является только `DIAGNOSTIC_ONLY`. `Open[row+1]` допустим только если доказано, что суммарная задержка позволяет отправить ордер до этого open. Иначе нужен first executable tick/price или MT tester execution.

### Для multi-target регрессии с монотонной структурой

Когда модель предсказывает несколько целевых переменных с известной иерархией (например up_3, up_6, up_12, up_24, up_48 — более длинный горизонт не может иметь меньшее движение):

1. Проверить корреляцию между таргетами. Сильная корреляция — ожидаема, но если модель не усваивает монотонность — diagnostic signal.
2. Loss-функция должна учитывать ранговую структуру. Нарушение монотонности в предсказаниях (up_3 > up_12) — признак того, что модель не усвоила временную структуру.
3. При оценке качества смотреть метрики по каждому горизонту отдельно, не только среднее. Средний Pearson r может скрывать провал на одном из горизонтов.
4. Проверить, что multi-target обучение не хуже, чем отдельные модели на каждый горизонт (если один горизонт тянет loss вниз, это маскирует качество остальных).
5. Итоговый торговый сигнал использует один конкретный горизонт. Но остальные таргеты — diagnostic: если модель хороша на горизонте 12, но плоха на 48, это ограничение области применения.

---
