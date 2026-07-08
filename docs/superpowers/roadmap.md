# SoSimple Research Roadmap

## Контекст

Текущая рабочая точка проекта описана в [CONTEXT_HANDOFF.md](../../CONTEXT_HANDOFF.md).
Этот файл хранит только будущие направления, а не историю и не выводы
прошлых этапов. Завершённые исследования см. в [docs/reports/](../reports/).

---

## Ближайшие направления

### 1. Amplitude / movement-regime audit для `entry-based next open`

**Контекст:** ветка `entry-based next open` не дала устойчивого direction после
price-feature matrix, fractal-selection ablation, closeout, powerful tabular и
ordered sequence Transformer. При этом `entry_up` / `entry_dn` amplitude trace
повторяется сильнее direction.

**Задача:** выполнить план
[2026-07-07-entry-based-amplitude-movement-regime-audit.md](plans/2026-07-07-entry-based-amplitude-movement-regime-audit.md):
проверить, является ли amplitude полезным movement-regime signal или он
объясняется простыми признаками вроде ATR, времени суток, расстояния до уровня
и плотности фракталов.

**Что важно для интерпретации:**

- это не торговый сигнал и не выбор направления;
- `entry_log_ratio` не является primary target;
- `time_only_clean`, `no_time_sequence` и `no_price_coord_sequence` обязательны;
- `price_coord_atr` tails около 40% требуют отдельного audit;
- результат должен включать quantile tables: top 5/10/20% predicted movement
  против остальных, по годам;
- `low_n_disclosure=2026` только disclosure;
- `locked_test` не открывать.

Статус: завершено 2026-07-07.

Итог: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`.
Движение после входа хорошо ранжируется, но лучший результат объясняется
простыми признаками (`time_plus_atr`, `simple_combined`). Это не trading signal
и не freeze-кандидат. См.
[`docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`](../reports/2026-07-07-entry-based-amplitude-movement-regime.md).

### 2. Movement filter design

**Контекст:** amplitude / movement-regime audit не показал добавочную ценность
сложных фрактальных профилей поверх простых baseline. Поэтому следующий шаг —
не усложнение модели, а проверка, можно ли заранее зафиксированный простой
movement-filter превратить в полезный decision layer без выбора направления.

**Задача:** сформулировать фильтр “есть движение / нет движения” без выбора
стороны сделки.

**План:** выполнить
[`2026-07-07-entry-based-movement-filter-design.md`](plans/2026-07-07-entry-based-movement-filter-design.md).

**Возможный контракт:**

- модель выдаёт вероятность или score сильного движения;
- фильтр разрешает или запрещает вход;
- отдельный слой позже решает направление или выход;
- если направления нет, сигнал пропускается.

**Ограничения:**

- не брать direction из `entry_up - entry_dn` без отдельной проверки;
- не смешивать movement filter и trading backtest в одном первом плане;
- до gross/backtest слоя нужен frozen movement-filter rule на validation.

Статус: ближайший незавершённый план.

### 3. Fractal-price entry mechanics foundation

**Контекст:** уже есть сильный признак, что исходный Up/Dn target связан с
областью вокруг `fractal0_price`, а не с немедленным входом по следующему open.
Отрицательный результат по `next open` не закрывает гипотезу уровня.

**Задача:** отдельно проверить механику входа, привязанную к `fractal0_price`:
возврат к уровню, ретест, лимитный вход около цены фрактала или вход после
касания/подтверждения.

**Что должно быть в будущем плане:**

- точный `decision_time`;
- точное правило entry eligibility;
- first executable price после доступности признаков;
- oracle-preflight потолка механики;
- новые targets от фактической точки входа;
- отдельный split/audit contract.

**Ограничения:**

- не смешивать с `next open` audit;
- не использовать старые цели от `fractal0_price` как готовую торговую
  разметку без проверки исполнимости;
- не открывать `locked_test` до frozen rule.

Статус: следующий крупный research branch после movement-regime audit или
параллельная отдельная гипотеза по решению пользователя.

### 4. Direction inside confirmed movement regimes

**Контекст:** direction по всей выборке `entry-based next open` не прошёл. Но
если будет найден устойчивый movement filter, можно проверить direction только
внутри режимов, где движение вообще ожидаемо.

**Задача:** проверить направление внутри заранее выбранных movement-regime
сегментов.

**Минимальные условия входа в этот этап:**

- movement filter выбран на `val_select`;
- movement filter survived `val_eval`;
- quantile/yearly checks пройдены;
- direction-план заранее фиксирует сегменты и не выбирает их по direction.

**Ограничения:**

- direction нельзя брать из того же amplitude-result как скрытый proxy;
- direction проверяется только после freeze movement segmentation;
- 2026 и `locked_test` не участвуют в выборе.

Статус: отложено до подтверждения movement-regime.

### 5. Мульти-актив / мульти-таймфрейм валидация

Проверить fractal-концепт на другом инструменте или таймфрейме. Это полезно
только после того, как появится подтверждённая рабочая постановка сигнала или
чёткий повод проверять переносимость результата.

Важно: перенос на другой инструмент не заменяет защиту от переобучения. Сначала
нужны устойчивость внутри исходного инструмента, yearly checks, multi-seed и
чистый split.

Статус: отложено до появления подтверждённой исполнимой механики.

---

## Отложенные инфраструктурные направления

### Central multi-profile inference service

**Контекст:** текущий online-контур исторически опирался на отдельный watcher для
связки `Nero.csv -> ml_signals.csv`. Если снова появится несколько live-safe
runtime-профилей, ручной запуск отдельных процессов станет операционным риском.

**Задача:** заменить ручной single-profile watcher одним управляемым Python-сервисом,
который по конфигу обслуживает несколько runtime-профилей: входной `Nero*.csv`,
checkpoint, frozen rule, output `ml_signals*.csv`, state/log/metadata.

**Выход:** managed service без обязательного `tmux`, при сохранении текущего
Python training/inference pipeline и совместимости с Strategy Tester через CSV
exports.

Design note: [2026-04-28-central-inference-service-design.md](specs/2026-04-28-central-inference-service-design.md)

Статус: есть дизайн, отчёт о реализации центрального multi-profile сервиса не
найден.

### Risk filters only after system discovery

**Контекст:** фильтры поверх уже найденного сигнала часто сокращают сделки и
повышают риск подгонки.

**Задача:** применять риск-фильтры только после того, как найден самостоятельный
источник прибыли или стабильный диагностический сигнал.

**Выход:** отдельный bounded benchmark для фильтра, где заранее ограничены число
правил и критерии успеха.

Статус: отложенный принцип для будущих торговых кандидатов; сейчас не является
ближайшим исследовательским шагом.

---

## Где держать что

- `CONTEXT_HANDOFF.md` — текущая точка остановки, ближайший следующий шаг, риски.
- `docs/superpowers/roadmap.md` — короткая очередь незавершённых направлений между несколькими планами.
- `docs/superpowers/specs/*.md` — проектные решения до реализации.
- `docs/superpowers/plans/*.md` — детальные исполнимые планы по отдельным направлениям.
- `docs/reports/*.md` — канонические отчёты завершённых этапов.
- `docs/DATA_FLOW.md` — стабильная карта пайплайна, не рабочий список исследований.
