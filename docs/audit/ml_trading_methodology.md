# Методика разработки и аудита ML-моделей торговых систем

> Статус: рабочая методика для проекта SoSimple.
> Область: ML-модели торговых систем на событийных и временных данных Forex, включая offline research, backtest, MT4 tester и online/forward diagnostic.
> Главный принцип: результат нельзя считать качеством модели, пока не доказано, что данные, признаки, разметка, split, правило отбора, экспорт и исполнение соответствуют моменту торгового решения.

## 0. Правила Принятия Решений

### Цель

Убрать произвол из исследования: каждое решение должно иметь входы, проверку, критерий перехода и зафиксированный артефакт.

### Обязательные правила

- Любой запуск с неизвестным источником признаков имеет статус `DIAGNOSTIC_ONLY`.
- Любой `FAIL` или `UNKNOWN` по leakage/preprocessing contract блокирует вывод о прибыльности.
- `validation` используется для выбора модели, признаков, порогов и правил.
- `test` используется один раз для уже замороженного кандидата.
- `forward` или online diagnostic проверяет только правило, принятое до появления новых данных.
- MT4 parity и execution reconciliation не заменяют ML-валидацию, а проверяют отдельный слой исполнения.

### Минимальный пакет артефактов для любого кандидата

- Описание торгового решения: инструмент, таймфрейм, `decision_time`, момент входа, горизонт удержания или правила выхода.
- Контракт данных: список признаков, источник, время доступности, нормализация, порядок колонок.
- Разбиение: даты и размеры train / validation / test / forward.
- Baseline-отчёт.
- Модельный отчёт и frozen rule/checkpoint.
- Backtest с торговыми издержками.
- Проверка устойчивости: временные срезы, стороны BUY/SELL, multi-seed или аналог.
- Export/parity/reconciliation, если кандидат идёт в MT4.
- Итоговый verdict: `reject`, `research_only`, `candidate`, `production_candidate`, `diagnostic_only`.

---

## 1. Постановка Гипотезы

### Цель

Сформулировать проверяемую торговую гипотезу до работы с моделями и не менять её задним числом после просмотра test.

### Входы

- Product goal и ограничения проекта.
- Предыдущие отчёты и wiki-синтез.
- Список доступных данных и торговый контур.

### Действия

1. Описать, что модель должна предсказывать: направление, вероятность события, ожидаемую доходность, MFE/MAE, take/skip, выбор выхода.
2. Зафиксировать единицу решения: строка датасета, бар, фрактал, уровень, сигнал.
3. Зафиксировать `decision_time`: какие данные доступны модели в момент решения.
4. Задать торговый протокол: вход на текущем или следующем баре, single-position или multi-position, hold, SL/TP, закрытие по обратному сигналу.
5. Задать критерии успеха до эксперимента: PF, sequential PF, количество сделок, просадка, отрицательные годы, BUY/SELL устойчивость.
6. Описать baseline, с которым кандидат должен сравниваться.

### Обязательные проверки

- Гипотеза не использует поле или событие, которое известно только после решения.
- Целевая переменная и торговый результат имеют одинаковый момент входа и выхода.
- Критерии успеха включают торговые издержки или явно помечены как gross diagnostic.

### Критерии завершения

- Есть короткая spec-запись: "что предсказываем", "когда решаем", "как торгуем", "как принимаем/reject".
- Известно, какой результат будет считаться провалом.

### Типовые ошибки

- Начинать с выбора модели, не описав торговое решение.
- Подбирать цель под уже увиденный test.
- Считать метрику классификации достаточной для торгового решения.

### Ветвления

- Если `decision_time` не определён: остановить ML-часть, описать торговый контур.
- Если цель зависит от будущего: допустимо использовать её как label, но запрещено как input.
- Если торговая логика ещё неизвестна: проводить только diagnostic research без production verdict.

---

## 2. Инвентаризация Источников Данных

### Цель

Доказать, что сырые данные и их смысл понятны до построения признаков.

### Входы

- Raw export из торговой платформы.
- Документация формата датасета.
- Код или описание producer-а данных.
- История изменений формата.

### Действия

1. Зафиксировать источник raw-файла, инструмент, таймфрейм, период, провайдера котировок.
2. Описать формат строк, разделители, кодировку, количество колонок.
3. Описать вложенные структуры: например, массив фракталов и поля внутри каждого элемента.
4. Разделить поля на группы:
   - доступные в момент строки;
   - labels/targets;
   - future-derived diagnostic fields;
   - поля с неизвестным происхождением.
5. Проверить, есть ли duplicate time и что они означают.
6. Зафиксировать known quirks: неполные края, разные таймфреймы, разные провайдеры, режимы tester/online.

### Обязательные проверки

- Raw-поля должны отражать состояние, известное на момент записи строки.
- Дубли времени нельзя удалять без доказательства, что это не разные события одного бара.
- Таймфрейм raw-файла должен совпадать с таймфреймом модели.
- Провайдер котировок фиксируется отдельно от инструмента.

### Критерии завершения

- Создан data inventory: путь, период, провайдер, частота, формат, количество строк, known risks.
- Для каждого raw-поля есть статус: `live_safe`, `target_only`, `future_derived`, `unknown`.

### Типовые ошибки

- Считать поле безопасным только потому, что оно есть в raw CSV.
- Смешивать H1 и M5 данные в одном контуре.
- Схлопывать строки с одинаковым `time`, теряя разные события одного бара.

### Ветвления

- Если поле `unknown`: не использовать как input до source audit.
- Если raw-файл другого таймфрейма: не запускать retrain, пока не подготовлен правильный источник.
- Если duplicate time влияет на MT4 export: добавить export parity, а не менять DATA без анализа.

---

## 3. Feature Contract И Leakage Gate

### Цель

Исключить заглядывание вперёд и несовпадение training/online feature contract.

### Входы

- Список всех input features.
- Список target/label columns.
- Код feature builder-а.
- Online/runtime preprocessing path.
- Чеклист `docs/ML/ml_leakage_preflight_checklist.md`.

### Действия

1. Для каждого признака заполнить feature contract:
   - имя;
   - источник;
   - producer;
   - transformation;
   - consumer;
   - момент доступности;
   - способ нормализации;
   - live-safe verdict.
2. Отдельно проверить candidate-source: откуда берётся сама строка/сигнал-кандидат.
3. Проверить, не попадает ли label в input напрямую или через lag/rolling/normalization pool.
4. Проверить, совпадают ли training и online:
   - список признаков;
   - порядок;
   - количество;
   - типы;
   - масштаб;
   - ATR contract;
   - сортировка фракталов.
5. Запретить silent fallback: отсутствующий online-признак не заменяется нулём.
6. Выполнить leakage preflight перед любым запуском, который может трактоваться как качество ML.

### Обязательные проверки

- Future-derived поля не входят во вход модели.
- Нормализационные пулы не зависят от future-derived полей.
- Labeling не запускается в online/inference path.
- Global scaler fit-ится только на train.
- Online runner падает при несовместимом contract, а не публикует сигнал.

### Критерии завершения

- Все признаки имеют `PASS`.
- `UNKNOWN` отсутствует.
- Есть frozen feature list и ссылка на builder/metadata.

### Типовые ошибки

- Использовать `predict`, `ret_*`, `fav_*`, `adv_*` или lag от future outcome как input.
- Считать лаг безопасным без аудита исходного поля.
- Обучить модель с признаками, которые online честно создать не может.
- Подменить недоступный input нулём.
- Дать future-derived полю влиять на row-wise normalization live-признаков.

### Ветвления

- Если найден `FAIL`: остановить candidate, исправить data contract или переобучить модель.
- Если найден `UNKNOWN`: считать как `FAIL`.
- Если запуск нужен для проверки файловой механики: разрешён только `DIAGNOSTIC_ONLY`.
- Если прибыль старого контура исчезает после live-safe retrain: старый контур не production, но идея может остаться research-only.

---

## 4. Разметка Целей

### Цель

Создать target, который соответствует торговой задаче и не смешивает разные исходы.

### Входы

- Raw/preprocessed data.
- OHLC или иной источник результата сделки.
- Описание торгового протокола.

### Действия

1. Описать label convention: значения, смысл каждого класса, timeout, neutral/skip.
2. Проверить, что label строится из будущего только как target, не как input.
3. Зафиксировать момент входа для расчёта результата: open следующего бара, close текущего, tick-level событие.
4. Для fixed horizon зафиксировать горизонт и единицы: price, ATR, пункты, деньги.
5. Для SL/TP или triple barrier явно определить:
   - что делать, если TP и SL задеты в одном окне;
   - как трактуется timeout;
   - как считаются reversal/hold-over events.
6. Проверить class distribution и side distribution.
7. Добавить invariant tests для label convention.

### Обязательные проверки

- Timeout не смешивается с SL, если это разные исходы.
- BUY и SELL считаются симметрично или асимметрия явно описана.
- Target не зависит от test-selected порога.
- Все target columns исключены из input.

### Критерии завершения

- Есть target contract.
- Есть sanity check распределения классов/сторон.
- Есть тесты или воспроизводимый аудит label convention.

### Типовые ошибки

- Приведение float-label к int, из-за чего timeout становится SL или наоборот.
- Выбор цели только по лучшему test PF.
- Использование одного агрегатного PF без проверки годовых срезов и сторон.

### Ветвления

- Если label convention ambiguous: остановить обучение, написать минимальный reproducer.
- Если класс/сторона слишком редкие: перейти к binary, one-vs-rest, side-specific или abstain formulation.
- Если validation сильная, а test проваливается по годам: считать regime shift, не production.

---

## 5. Препроцессинг И Нормализация

### Цель

Подготовить данные так, чтобы preprocessing не создавал утечку и одинаково работал в training/test/online.

### Входы

- Raw data.
- Feature contract.
- Label contract.
- Preprocessing code.

### Действия

1. Выполнить сортировку событий внутри строки только по данным этой строки.
2. Проверить порядок элементов после сортировки.
3. Выполнить labeling до split, если label строится независимо от будущих строк train/test как supervised target.
4. Применить row-wise normalization только по полям, доступным на момент строки.
5. Если используется global scaler:
   - fit только на train;
   - сохранить scaler;
   - применить transform к validation/test/online.
6. Сохранить параметры нормализации и hash входных файлов.
7. Проверить отсутствие NaN, inf, константных признаков и невалидных диапазонов.

### Обязательные проверки

- Сортировка независима по строкам.
- Row-wise normalization не использует future-derived labels.
- `predict` и похожие future fields не участвуют в live-safe normalization pool.
- ATR contract явно указан.
- Схема колонок после preprocessing совпадает с ожидаемой.

### Критерии завершения

- Preprocessing воспроизводим командой.
- Все output-файлы имеют schema check.
- Путь online preprocessing описан отдельно и совпадает с training contract.

### Типовые ошибки

- Fit scaler на всём датасете.
- Нормализовать live-признаки вместе с future label.
- Проверить только train и не проверить validation/test/online.
- Менять preprocessing после просмотра test.

### Ветвления

- Если ошибка в preprocessing меняет прошлый результат: старый результат помечается invalid или needs-rerun.
- Если online preprocessing не может повторить training: переобучить на live-safe preprocessing.
- Если часть признаков константна: удалить или явно пометить intentionally disabled до retrain.

---

## 6. Временное Разделение Данных

### Цель

Получить честную временную проверку без перемешивания будущего в прошлое.

### Входы

- Preprocessed dataset.
- Временные границы инструмента.
- Гипотеза и ожидаемая частота сделок.

### Действия

1. Разделить данные строго по времени: train, validation, frozen test.
2. При наличии новых данных выделить forward после даты принятия решения.
3. Зафиксировать даты, количество строк, количество target-событий и сделок на каждом split.
4. Проверить, нет ли пересечения по времени, id события или производным артефактам.
5. Для walk-forward задать окна заранее:
   - expanding window;
   - rolling window;
   - anchored train + rolling validation;
   - forward-only production window.
6. Запретить random k-fold для временных строк как основной критерий.

### Обязательные проверки

- Нет shuffle до split.
- Порог/модель/фильтр выбираются только на train/validation.
- Test не участвует в feature selection, target tuning, threshold selection.
- Forward не совпадает со старым test.

### Критерии завершения

- Есть таблица split boundaries.
- Есть frozen test policy: кто и когда имеет право открыть test.
- Есть план forward/walk-forward, если кандидат претендует на production.

### Типовые ошибки

- Повторно использовать test как forward.
- Подбирать годы или периоды вручную после просмотра результата.
- Сравнивать модели на разных test windows.

### Ветвления

- Если данных мало: уменьшить сложность модели, усилить baseline и time-slice analysis, но не переходить к random CV как доказательству.
- Если результат держится только на одном году: требовать дополнительный forward или reject.
- Если validation и test отличаются режимно: исследовать regime shift, не ретюнить на test.

---

## 7. Baseline-Модели

### Цель

Понять, есть ли предиктивный сигнал, и установить нижнюю планку до сложных моделей.

### Входы

- Train/validation split.
- Feature set с `PASS` по leakage.
- Target contract.

### Действия

1. Запустить dummy/random baseline.
2. Запустить простые модели: linear/logistic, tree-based, RF/HGB/boosting.
3. Проверить простые правила без ML, если они отражают торговую гипотезу.
4. Для классификации смотреть не только accuracy/F1, но и minority/side metrics.
5. Для торговли пересчитать сигналы в PnL по тому же execution protocol.
6. Зафиксировать baseline как frozen reference.

### Обязательные проверки

- Baseline использует те же split и cost assumptions.
- Baseline не получает future-derived features.
- Baseline сравнивается по тем же торговым метрикам, что и сложная модель.

### Критерии завершения

- Есть baseline table: model, features, validation metrics, trading metrics.
- Сложная модель не запускается массово, пока baseline не понятен.

### Типовые ошибки

- Игнорировать dummy baseline при дисбалансе классов.
- Считать macro F1 достаточным, когда сигнальные классы редкие.
- Сравнивать NN gross PF с baseline net PF.

### Ветвления

- Если baseline не лучше random: пересмотреть target/features до model zoo.
- Если простая модель лучше NN: принять простую модель как baseline candidate.
- Если BUY и SELL ведут себя по-разному: выделить side-specific baseline.

---

## 8. Выбор Метрик И Gate-Критериев

### Цель

Оценивать модель по метрикам, связанным с торговым решением, а не по красивым ML-числам.

### Входы

- Target type.
- Trading protocol.
- Baseline results.

### Действия

1. Разделить метрики на diagnostic и decision metrics.
2. Для модели считать:
   - classification: precision/recall по активным классам, confusion matrix, calibration;
   - regression: MAE, correlation, rank correlation, residual slices;
   - score/ranking: coverage, lift, monotonicity by buckets.
3. Для торговли считать:
   - PF;
   - net PnL;
   - EV/trade;
   - win rate;
   - max drawdown;
   - trades/year;
   - sequential PF;
   - yearly/monthly slices;
   - BUY PF и SELL PF;
   - concentration of profit.
4. Добавить cost model: spread, commission, swap, slippage, requote/open failure.
5. Зафиксировать gates до validation sweep.

### Обязательные проверки

- Метрика выбора совпадает с целью этапа.
- PF не считается достаточным при малом N.
- Результат проверен по сторонам BUY/SELL.
- Результат проверен sequential, если торговля ограничивает одновременные позиции.

### Критерии завершения

- Есть таблица gate-критериев: metric, threshold, split, reason.
- Есть правило reject для low-N/high-PF.

### Типовые ошибки

- Выбирать по max PF без минимального числа сделок.
- Не учитывать отрицательные годы.
- Игнорировать сторону, которая теряет деньги.
- Не включать spread/commission/slippage.

### Ветвления

- Если gross PF > 1, а net PF <= 1: стратегия не проходит, нужен другой edge или cost-aware target.
- Если BUY проходит, SELL проваливается: рассмотреть BUY-only как отдельного кандидата, а SELL не чинить порогом "заодно".
- Если high PF на N<30: research-only до накопления данных.

---

## 9. Обучение Модели

### Цель

Обучить кандидата воспроизводимо и без бесконтрольного перебора.

### Входы

- Approved feature contract.
- Train/validation split.
- Baseline report.
- Gate criteria.

### Действия

1. Выбрать минимально достаточную постановку:
   - regression;
   - binary;
   - one-vs-rest;
   - direct BUY/SELL/SKIP;
   - ranking/take-skip.
2. Сначала обучить простую модель.
3. Для NN или сложных моделей зафиксировать:
   - seed;
   - device;
   - versions;
   - data hashes;
   - hyperparameters;
   - checkpoint path.
4. Использовать early stopping только по validation metric.
5. Для production retrain использовать CPU-only, если не доказана эквивалентность training на другом устройстве.
6. Изолировать output-dir по seed/device/run.
7. Логировать команды запуска и итоговые артефакты.

### Обязательные проверки

- Нет test в цикле обучения.
- Hyperparameter search не выбирает по test.
- Same seed + same data + same code воспроизводит checkpoint или различие объяснено.
- GPU-training не считается production-эталоном без отдельного reproducibility audit.

### Критерии завершения

- Модель обучена, checkpoint сохранён, metadata полная.
- Есть validation report и сравнение с baseline.

### Типовые ошибки

- Запускать большой model zoo до прохождения data contract.
- Смешивать exploration checkpoint и production checkpoint.
- Сохранять checkpoint без seed/data hash/feature list.

### Ветвления

- Если сложная модель не лучше baseline: остановить усложнение.
- Если разные seeds дают разные winners: проверить rule-family robustness.
- Если auto-winner нестабилен, но простая rule-family стабильна: выбрать простую frozen family и подтвердить отдельно.

---

## 10. Validation Selection И Заморозка Кандидата

### Цель

Выбрать ровно одного кандидата для test без подглядывания в test.

### Входы

- Validation predictions.
- Baseline predictions.
- Gate criteria.
- Cost model.

### Действия

1. На validation выбрать:
   - модель;
   - feature set;
   - target formulation;
   - threshold/top-k/coverage;
   - execution rule.
2. Проверить временные срезы validation.
3. Проверить BUY/SELL, long/short balance, side-specific PF.
4. Проверить sequential simulation.
5. Проверить чувствительность к небольшому изменению threshold.
6. Сохранить frozen rule в машинно-читаемом формате.
7. Запретить ручное изменение после просмотра test.

### Обязательные проверки

- Кандидат проходит validation gates.
- Rule/checkpoint/threshold заморожены до test.
- У rule есть понятное имя и version.

### Критерии завершения

- Есть один frozen candidate.
- Есть reject-список альтернатив и причина отказа.

### Типовые ошибки

- Взять несколько кандидатов на test и выбрать лучший.
- Увеличивать grid после каждого слабого validation результата без новой гипотезы.
- Подбирать threshold по test.

### Ветвления

- Если ни один кандидат не проходит validation: остановить этап, написать reject report.
- Если candidate проходит только aggregate PF, но проваливает yearly/side/sequential: research-only или reject.
- Если несколько кандидатов близки: выбрать более простой и устойчивый, остальные оставить как follow-up.

---

## 11. Frozen Test

### Цель

Оценить заранее выбранного кандидата на отложенном периоде.

### Входы

- Frozen checkpoint.
- Frozen rule.
- Test data.
- Cost model.

### Действия

1. Запустить test один раз по frozen артефактам.
2. Посчитать те же метрики, что на validation.
3. Добавить time-slice анализ: годы, кварталы, рыночные режимы при наличии.
4. Добавить side analysis: BUY, SELL, balance.
5. Добавить sequential simulation.
6. Сравнить с baseline на том же test.
7. Зафиксировать verdict.

### Обязательные проверки

- Test не влияет на параметры кандидата.
- Если test провален, не ретюнить в этом же test-cycle.
- Отчёт показывает не только PF, но и N, negative slices, drawdown, sides.

### Критерии завершения

- Verdict принят без изменения rule.
- Если PASS, кандидат переходит к robustness/backtest/parity.
- Если FAIL, кандидат закрыт или возвращён на новую гипотезу с новым cycle.

### Типовые ошибки

- "Чуть поправить" threshold после test.
- Скрыть слабую сторону SELL за общим PF.
- Считать один удачный test достаточным без robustness.

### Ветвления

- Если test PASS и validation/test близки: идти к robustness и MT4 parity.
- Если test weak but positive: research-only, нужен forward.
- Если test FAIL: reject; новая итерация должна иметь новую гипотезу и не использовать test как validation.

---

## 12. Устойчивость И Walk-Forward

### Цель

Понять, не является ли результат случайной удачей одного seed, периода, стороны или провайдера.

### Входы

- Frozen или validation-approved candidate.
- Historical splits.
- Возможные alternate provider/instrument datasets.

### Действия

1. Выполнить multi-seed retrain, если модель стохастическая.
2. Разделить:
   - устойчивость идеи/rule-family;
   - переносимость точного numeric threshold.
3. Проверить rolling или expanding walk-forward:
   - train на прошлом;
   - validation на следующем окне;
   - freeze;
   - test на ещё более позднем окне.
4. Проверить provider drift отдельно от cross-instrument transfer.
5. Проверить временную концентрацию прибыли.
6. Проверить sensitivity к cost assumptions.
7. Проверить confidence intervals или bootstrap по сделкам, если N позволяет.

### Обязательные проверки

- Multi-seed не заменяет forward, но выявляет lucky checkpoint.
- Cross-instrument transfer не смешивается с provider drift.
- Один слабый год не маскируется общей прибылью.

### Критерии завершения

- Кандидат имеет стабильность по seed/time/side или явно ограничен как research-only.
- Известно, что переносится: идея, конкретный threshold или только frozen checkpoint.

### Типовые ошибки

- Считать auto-winner устойчивым без проверки rule-family.
- Делать вывод о переносимости по одному новому инструменту.
- Игнорировать отрицательные годы при хорошем aggregate PF.

### Ветвления

- Если idea stable, threshold unstable: freeze exact checkpoint/rule и не переиспользовать threshold после retrain.
- Если only BUY stable: оформить BUY-only как отдельный кандидат.
- Если provider stable, но instruments fail: не заявлять универсальность, ограничить рынок.

---

## 13. Backtest С Торговыми Издержками

### Цель

Проверить, сохраняется ли edge после реалистичного исполнения.

### Входы

- Frozen signals.
- OHLC/tick/tester data.
- Trading protocol.
- Cost assumptions.

### Действия

1. Описать cost model:
   - spread;
   - commission;
   - swap;
   - slippage;
   - requote/open failure;
   - latency/next-bar entry.
2. Запустить offline backtest с тем же входом/выходом, что в production plan.
3. Запустить sequential simulation при single-position ограничении.
4. Проверить edge при повышенных cost assumptions.
5. Проверить SL/TP, timeout, close reason и edge cases.
6. Для MT4-кандидата выполнить tester run.

### Обязательные проверки

- Gross и net results разделены.
- Entry timing совпадает с планом.
- Spread/commission/slippage не оставлены "на потом" для production verdict.
- Timeout PnL и SL/TP PnL анализируются отдельно.

### Критерии завершения

- Net PF и drawdown проходят gates.
- Известно, какие издержки убивают стратегию.
- Есть список расхождений offline vs tester.

### Типовые ошибки

- Игнорировать комиссии и spread при PF около 1.
- Считать close по OHLC эквивалентом tick execution.
- Не учитывать пропущенные входы.

### Ветвления

- Если edge исчезает после costs: reject или redesign target/rule.
- Если расхождения только в timeout, а SL/TP совпадают: отделить market-close risk от signal risk.
- Если requote/open failures частые: сначала чинить execution reliability, не модель.

---

## 14. Export, MT4 Parity И Reconciliation

### Цель

Доказать, что MT4 исполняет тот же сигнал, который был проверен в Python.

### Входы

- Frozen export CSV.
- Rule metadata.
- MT4 tester log.
- Trade event-log.

### Действия

1. Зафиксировать export format.
2. Проверить counts:
   - rows total;
   - nonzero rows;
   - unique time;
   - unique time+signal;
   - duplicate time;
   - opposite signals on same time.
3. Запустить MT4 tester на заданном периоде.
4. Сверить:
   - expected signals;
   - opened trades;
   - closed trades;
   - missing opens;
   - critical mismatches;
   - close reasons.
5. В online/tester сверке сопоставлять по `signal_time + direction`, а не по ticket.
6. Логировать `OPEN_FAILED`, spread, slippage, Bid/Ask, commission, swap, balance/equity.
7. Исключить неполные края периода из строгого verdict.

### Обязательные проверки

- Python export не меняет rule после test.
- MT4 читает именно проверенный файл.
- Есть reconciliation report.
- Все missing trades объяснены или помечены как blocker.

### Критерии завершения

- `critical_mismatch_count = 0` или расхождения классифицированы и приняты как non-blocking.
- Разница строк export и opened trades объяснена.
- Online/tester diagnostic не объявляется proof of profitability.

### Типовые ошибки

- Сравнивать количество строк `ml_signals.csv` с количеством сделок без учёта duplicate time.
- Игнорировать границы tester interval.
- Не писать `OPEN_FAILED`, из-за чего пропущенные сделки выглядят "потерянными".
- Смешивать mechanical parity и ML quality.

### Ветвления

- Если сигналы не совпадают: чинить export/runtime, не менять модель.
- Если сигналы совпадают, но PnL отличается: разбирать execution layer.
- Если open failures существенны: улучшать retry/slippage или снижать trading frequency.

---

## 15. Forward-Test И Online Diagnostic

### Цель

Проверить frozen candidate на новых данных после принятия решения.

### Входы

- Frozen checkpoint/rule.
- Новые raw или prediction данные после decision date.
- Online event-log.

### Действия

1. Зафиксировать дату production decision.
2. Собирать forward data только после этой даты.
3. Не менять rule на forward window.
4. Считать metrics и time slices.
5. Для online diagnostic отделять:
   - signal quality;
   - execution quality;
   - infrastructure health.
6. Если forward данных нет, verdict должен быть `watch/no_forward_data`, а не `confirmed`.

### Обязательные проверки

- Forward window строго новее validation/test.
- Нет ретюнинга на forward до verdict.
- Online preprocessing проходит leakage preflight.

### Критерии завершения

- Есть verdict: `confirmed`, `watch`, `revisit`, `reject`.
- Есть next action, основанный на forward, а не на повторе старого test.

### Типовые ошибки

- Называть старый frozen test forward validation.
- Менять threshold после нескольких online сделок.
- Делать вывод о модели по M5 diagnostic, если production модель H1.

### Ветвления

- Если forward нет: продолжать сбор, не повышать статус.
- Если forward слабее, но N мало: `watch`, не `reject`, если заранее так задано.
- Если forward нарушает risk limits: остановить торговлю и открыть audit.

---

## 16. Отчётность И Аудит Ошибок

### Цель

Сделать результаты воспроизводимыми и понятными для следующей итерации.

### Входы

- Все отчёты этапов.
- Команды запуска.
- Метрики.
- Изменённые файлы.

### Действия

1. Написать отчёт с секциями: Context, What Was Done, Verification, Results, Conclusions, Limitations, Next Step.
2. Указать все команды, версии, paths, hashes, rules, checkpoints.
3. Явно перечислить ошибки и invalidated assumptions.
4. Обновить changelog/handoff/wiki, если этап закрыт.
5. Если найден баг в прошлом выводе:
   - доказать минимальным reproducer;
   - оценить material impact;
   - пометить старые выводы как invalid, superseded или unchanged.

### Обязательные проверки

- Отчёт отделяет факты от гипотез.
- Есть список limitations.
- Все источники результата доступны.

### Критерии завершения

- Следующий агент может воспроизвести результат по отчёту.
- Ясно, что делать дальше и что запрещено делать.

### Типовые ошибки

- Писать только итоговый PF без команд.
- Не фиксировать, почему candidate rejected.
- Удалять "плохие" эксперименты из истории.

### Ветвления

- Если результат сильный, но contract failed: verdict `diagnostic_only`, не production.
- Если bug не меняет verdict: зафиксировать unchanged impact.
- Если bug меняет verdict: закрыть старый candidate и запустить новый cycle.

---

## Сводный Чеклист Разработки

Использовать перед запуском нового ML-кандидата.

- [ ] Гипотеза описана до экспериментов.
- [ ] `decision_time` зафиксирован.
- [ ] Raw data inventory создан.
- [ ] Feature contract заполнен для всех input fields.
- [ ] Leakage preflight: `PASS`.
- [ ] Target contract описан и протестирован.
- [ ] Preprocessing воспроизводим и live-safe.
- [ ] Split строго временной.
- [ ] Baseline-модели запущены.
- [ ] Метрики и gates заданы до validation sweep.
- [ ] Hyperparameter/model selection не использует test.
- [ ] Один frozen candidate выбран на validation.
- [ ] Test открыт один раз для frozen candidate.
- [ ] Backtest учитывает spread, commission, swap, slippage и ограничения позиции.
- [ ] Проверены yearly/monthly slices.
- [ ] Проверены BUY/SELL отдельно.
- [ ] Проверены sequential metrics.
- [ ] Проверена multi-seed или иная устойчивость.
- [ ] Export parity выполнен перед MT4 verdict.
- [ ] MT4 tester/reconciliation выполнены для execution candidate.
- [ ] Forward/online diagnostic не смешан с historical test.
- [ ] Итоговый отчёт содержит commands, artifacts, limitations, next step.

## Сводный Чеклист Аудита Готового Результата

Использовать перед повышением статуса кандидата.

- [ ] Можно указать, какие данные модель видит в момент сделки.
- [ ] Нет `UNKNOWN` признаков.
- [ ] Нет future-derived input.
- [ ] Candidate-source live-safe.
- [ ] Training и online feature contract совпадают.
- [ ] Нормализация не использует будущие поля.
- [ ] Global scaler fit только на train.
- [ ] Rule/checkpoint/threshold заморожены до test.
- [ ] Test не использовался для выбора.
- [ ] PF не основан на малом N без пометки research-only.
- [ ] Нет скрытого провала одной стороны BUY/SELL.
- [ ] Нет скрытого провала отдельных годов.
- [ ] Издержки включены или результат помечен gross diagnostic.
- [ ] Python export соответствует MT4 opened trades.
- [ ] Online/tester расхождения классифицированы.
- [ ] Все open failures и requote видимы в логах.
- [ ] Reproducibility metadata сохранена.
- [ ] Старые противоречащие выводы обновлены или помечены.

## Типовые Причины Ложных Выводов В Этом Проекте

- Высокий исторический PF был получен на future-derived inputs.
- Training feature contract не совпадал с online contract.
- Offline candidate-source был недоступен в live.
- `signal != 0` использовался как gate, хотя в live raw data он не воспроизводится тем же способом.
- CPU/GPU training давали разные checkpoints при одном seed.
- Auto-winner selection скрывал нестабильность rule-family.
- Timeout/SL label convention смешивались в аналитике.
- Test использовался как фактическая validation через повторные попытки.
- Python export и MT4 execution считались равными без parity.
- Duplicate timestamps интерпретировались как ошибка данных, хотя это разные события одного бара.
- Online/tester PnL-разница смешивала ML signal risk и execution risk.
- Spread, slippage, requote и missed opens не были включены в ранний вывод.
- Aggregate PF скрывал слабую сторону SELL или отрицательный год.

## Статусы Verdict

| Verdict | Значение | Разрешённые действия |
|---|---|---|
| `reject` | Гипотеза не прошла обязательные gates | Закрыть или сформулировать новую гипотезу |
| `diagnostic_only` | Проверялась механика, но ML quality не доказана | Использовать только для отладки pipeline |
| `research_only` | Есть сигнал, но не хватает устойчивости или contract неполный | Продолжать исследования, не подключать к production |
| `candidate` | Прошёл validation/test, но нет полного execution/forward подтверждения | Готовить parity, robustness, forward |
| `production_candidate` | Прошёл data contract, frozen test, robustness, MT4 parity | Допускается controlled forward/online diagnostic |
| `confirmed` | Forward подтвердил frozen rule | Поддерживать мониторинг и periodic retrain policy |

## Примеры Источников Для Проверки

- Pipeline и leakage-инварианты: `docs/DATA_FLOW.md`.
- Формат датасета: `docs/dataset_description.md`.
- Leakage gate: `docs/ML/ml_leakage_preflight_checklist.md`.
- Baseline-модели: `docs/ML/baseline_experiments.py.md`.
- NN pipeline: `docs/ML/neural_networks.md`.
- Live-safe audit: `docs/reports/2026-05-05-live-safe-ml-audit.md`.
- Reproducibility: `docs/reports/2026-05-07-cpu-gpu-reproducibility.md`.
- MT4 parity: `docs/reports/2026-05-07-entry-path-mt4-parity.md`.
- Online/tester execution: `docs/reports/2026-05-12-online-tester-execution-reconciliation.md`.
- Candidate-source audit: `docs/reports/2026-05-14-entry-path-all-rows-ranking.md`, `docs/reports/2026-05-14-entry-path-causal-surrogate.md`, `docs/reports/2026-05-14-entry-path-direct-bar-model.md`.
- Direct direction experiments: `docs/reports/2026-05-15-direct-direction-improvement.md`.

## Stop Conditions

Остановить текущий cycle и не продолжать model sweep, если:

- data contract не прошёл leakage gate;
- online features недоступны;
- test уже был использован для выбора;
- validation gate не пройден;
- единственный плюс кандидата держится на одной стороне, одном году или очень малом N;
- cost-aware result отрицателен;
- MT4 parity показывает critical mismatch;
- forward data отсутствуют, но требуется forward verdict.

В этих случаях правильный следующий шаг: написать reject/diagnostic report и сформулировать новую ограниченную гипотезу.
