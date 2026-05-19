# ML Leakage Preflight Checklist

> Canonical gate перед training, validation/test benchmark, signal export, MT4 tester и online runner. Цель: модель получает только данные, доступные на момент торгового решения.

Если любой пункт `FAIL` или `UNKNOWN`, запуск допустим только как `DIAGNOSTIC_ONLY`: можно проверять механику файлов/логов, но нельзя делать вывод о качестве ML или прибыльности.

## Role Contract

Перед запуском каждое поле должно иметь роль:

| Роль | Можно во вход модели | Правило |
|---|---:|---|
| `live_safe_input` | да | Доступно на decision time и воспроизводимо online тем же способом |
| `row_level_target` | нет | Будущий результат для обучения/оценки текущей строки; только для target construction |
| `future_derived_label` | нет | Любая offline-разметка из будущих баров или будущего path |
| `diagnostic_only` | нет | Поле/score/rule для replay, сверки или анализа; не production input |
| `unknown` | нет | Запрещено, пока не доказаны источник и момент доступности |

Known legacy examples only: `predict`, `ret_*`, `fav_*`, `adv_*`, row-level `up_3..dn_48` are not inputs. `fractal*.Up/Dn` is classified by source and decision-time availability, not by name.

## Required Gates

| # | Gate | PASS | FAIL |
|---:|---|---|---|
| 1 | Decision time | Зафиксированы bar, open/close, timeframe, instrument | Непонятно, что известно модели на момент решения |
| 2 | Temporal split | Train / validation / test идут по времени; no shuffle | Будущее попало в train/validation |
| 3 | Feature role audit | Есть feature/source contract: name, role, source, available_at, normalization, model_input | Есть input с ролью target/future/diagnostic/unknown |
| 4 | Training-online parity | Feature names/count/order/source/normalization совпадают | Online не может создать training features или заполняет пропуски нулями |
| 5 | Online preprocessing | Только sort/validate/live-safe normalize; no future labels | Online вызывает labeling или строит future-derived поля |
| 6 | Fractal order | Проверено убывание времени внутри `fractal*`; равные timestamps допустимы | `fractal0`/слоты имеют разный смысл между режимами |
| 7 | Normalization pools | Input transforms считаются только из live-safe inputs; global scaler fit only train | Input масштаб зависит от target/future/diagnostic fields или full dataset |
| 8 | ATR units | Зафиксировано raw/scaled/ratio и одинаково во всех режимах | Training и online используют разные единицы ATR |
| 9 | Constant inputs | Проверены unique/variance/NaN/zero-rate на train | Константный input оставлен как информативный без решения |
| 10 | Model/rule freeze | Checkpoint, target, threshold, filter, exit frozen до test | Test использован для выбора гипотезы, модели или порога |
| 11 | Target quality | BUY/SELL/SKIP balance, ambiguous rate, yearly BUY/SELL positives проверены на validation | Target слишком редкий, односторонний или неоднозначный без решения |
| 12 | Trading benchmark separation | Target construction отделён от PF/sequential PF/execution-mode checks | Метрика target смешана с trading PF или exit-policy diagnostic |
| 13 | Direction source | Direction heuristic используется как input only, если не доказано обратное | Heuristic direction принят как готовое направление сделки без проверки |
| 14 | Export/MT4 parity | Сверены rows, nonzero, unique time, direction counts, opened trades | Python и MT4 исполняют разные сигналы |
| 15 | Runtime fail-closed | Несовместимый checkpoint/rule блокирует export | Watcher пишет `ml_signals.csv` при неподдержанном contract |

## Normalization Rules

- Row-level targets и input features нормализуются раздельно.
- Per-row normalization pool может содержать только поля, доступные в этой строке на decision time.
- Global-fit transforms fit-ятся только на train и затем применяются к validation/test/online.
- Online `predict=0` или отсутствующее поле не считается эквивалентом training-значения.
- Повторная runtime-нормализация должна пропускаться, если snapshot уже нормализован.

## Diagnostic Rules

- Высокий historical PF не доказывает online-valid систему без `PASS` по этому gate.
- Legacy replay/export доказывает только воспроизводимость старого пути, не live-safe качество.
- Система, зависящая от failed baseline/checkpoint/score, наследует его `FAIL` до rebuild.
- Old score, old threshold и offline signal можно использовать только в явно помеченном diagnostic mode.

## Minimal Evidence

Каждый test/online отчёт должен содержать:

- checkpoint/rule paths и frozen timestamp или commit;
- feature/source contract или ссылку на builder, который его генерирует;
- split boundaries и подтверждение, что test не использовался для выбора;
- результаты gates 1-15: `PASS`/`FAIL`/`UNKNOWN`;
- export counts и MT4 opened trades, если был tester;
- final verdict: `PASS`, `FAIL`, `UNKNOWN` или `DIAGNOSTIC_ONLY`.
