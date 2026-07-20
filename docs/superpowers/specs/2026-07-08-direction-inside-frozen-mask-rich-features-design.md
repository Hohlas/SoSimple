# Direction Inside Frozen Mask Rich Features Design

## Цель

Переиграть этап direction-inside-frozen-mask корректно: модель направления обучается на полном честном `train`, а не только на строках, прошедших frozen movement-mask. Маска используется только после обучения: она ограничивает строки, на которых проверяется, есть ли полезное направление внутри уже найденного режима сильного движения.

## Почему старый заход слабый

Старый runner подал в модель почти пустой набор признаков: `ATR`, календарное время и несколько агрегатов плотности фракталов. Это годится только как контроль, но не как серьёзная попытка найти направление. Он также учил модель только на малом подмножестве `selected=True`, поэтому резко уменьшал число обучающих примеров.

Новый этап берёт признаки и target-семейства из предыдущих исследований:

- `entry_based_next_open_closeout`;
- `entry_based_powerful_tabular`;
- `entry_based_fractal_sequence_transformer`;
- `entry_based_amplitude_movement`.

## Основной дизайн

1. Восстановить обычные entry-based split-ы:
   - `train <= 2020`;
   - `validation = 2021-2025`, разделённый на `val_select` и `val_eval`;
   - `2026 = low_n_disclosure`;
   - `locked_test` не открывать.
2. Построить богатые feature-профили для всех строк split-а, не применяя frozen-mask до обучения.
3. Обучать модели на полном `train`.
4. Выбирать winner только по `val_select_inside_mask`: это `val_select` строки с `frozen_selected=True`. Полный `val_select` не выбирает winner, а остаётся диагностикой.
5. Для выбранного winner считать метрики отдельно:
   - на `val_select_inside_mask` — главная метрика выбора;
   - на `val_eval_inside_mask` — обязательное подтверждение после выбора;
   - на полном `val_select` — диагностика вне режима;
   - на полном `val_eval` — диагностика вне режима;
   - на `low_n_disclosure` только для раскрытия, без выбора.
6. Frozen movement rule не менять:
   - `simple_combined`;
   - `extra_trees_small`;
   - `H3`;
   - `top_fraction=0.05`;
   - `seeds=[42,43,44]`.

## Признаки

Feature-профили:

- `simple_combined` — старый бедный контроль;
- `nearest_k60` — сильный профиль из closeout/powerful-tabular;
- `nearest_k80` — exploratory-control из предыдущих powerful-tabular/sequence веток. Он участвует в таблицах, но сам по себе не может создать `DIRECTION_REPLICATION_REQUIRED` в первом прогоне;
- `corridor_5atr` — профиль фракталов около текущей цены;
- `all100` — контроль “вся доступная фрактальная история”.

Разрешённые семейства признаков:

- структурные поля фракталов: направление уровня, сила, пробой, разворот, power, count, impulse;
- возраст уровня: `shift`, `log_shift`, разница возрастов соседних уровней;
- геометрия относительно `fractal0.price`: расстояние в ATR, абсолютное расстояние, направление-aware расстояние;
- исторические `Up/Dn` поля внутри сериализованных `fractal1..fractal99`;
- календарные признаки строки: час и день недели;
- агрегаты плотности/близости фракталов из старого контроля.

Запрещены как вход:

- top-level будущие target-колонки: `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`;
- top-level `up_*`, `dn_*`, `ret_*`, `fav_*`, `adv_*`;
- `target_*`, `label_*`, `outcome_*`;
- frozen movement `score`;
- `selected` из frozen-mask.

## Target-семейства

Использовать несколько горизонтов:

- `H3`;
- `H6`;
- `H12`;
- `H24`.

Основной direction-target:

- регрессия `entry_log_ratio_H`;
- знак прогноза даёт сторону: `> 0` значит up сильнее down, `< 0` значит down сильнее up.
- если `abs(entry_log_ratio_H) < dead_zone_H`, строка считается нейтральной для direction-метрик. Первый прогон использует `dead_zone_H = 0.0` только если распределение target показывает отсутствие микрошумовой массы около нуля; иначе dead-zone задаётся как `max(1e-6, 5-й перцентиль abs(entry_log_ratio_H) на train)`.

Дополнительная проверка:

- отдельно предсказывать `entry_up_H` и `entry_dn_H`;
- сторону брать через сравнение прогнозов: `pred_entry_up_H > pred_entry_dn_H`.

Классификационный target `entry_up_H > entry_dn_H` можно оставить как контроль, но не делать его единственной постановкой.

## Модели

Первый прогон ограниченный, без большого перебора:

- `hist_gradient_boosting`;
- `extra_trees`;
- `xgboost_depth3`, если зависимость доступна в окружении;
- `xgboost_depth5`, если зависимость доступна в окружении.

Если XGBoost недоступен, этап не должен падать целиком: runner пишет это в `failed_runs` и продолжает scikit-learn моделями.

Early stopping и подбор числа итераций по validation запрещены в первом прогоне. Модельные настройки фиксируются заранее. Поэтому отдельный `val-stop` не создаётся. Если реализация добавит early stopping, подбор числа деревьев/эпох или настройку модели по validation, она обязана сначала ввести `val-stop` и не использовать `val-select`/`val-eval` для этих действий.

## Отбор и verdict

Выбор winner:

- только по `val_select_inside_mask`;
- `val_eval_inside_mask` проверяет выбранный вариант;
- full-split метрики не выбирают winner;
- `low_n_disclosure` только раскрывается;
- `locked_test` не открывается.

Главный вопрос этапа:

> Есть ли direction-сигнал внутри frozen movement-mask, если модель направления обучалась на полном train и видела полноценные признаки?

Положительный вывод разрешён только как `DIRECTION_REPLICATION_REQUIRED`, потому что профили и target-семейства выбраны после чтения прошлых отчётов. Это не торговый кандидат и не причина открывать `locked_test`.

Полный перебор раскрывается как `cumulative_search_budget`. При большом grid-е положительный результат не повышается выше `DIRECTION_REPLICATION_REQUIRED` даже при хорошем `val_eval_inside_mask`. Если `val_eval_inside_mask` не подтверждает выбранный на `val_select_inside_mask` вариант, verdict не может быть положительным.

Sample-size gate для masked-срезов:

- `val_select_inside_mask >= 100`;
- `val_eval_inside_mask >= 100`;
- минимум `30` строк на каждый активный знак направления в каждом из этих срезов;
- минимум `30` строк в год для годового masked-среза, иначе годовой вывод помечается только как diagnostic;
- если gate не пройден, максимальный статус результата: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME` или `DIAGNOSTIC_ONLY` внутри отчёта, но не `DIRECTION_REPLICATION_REQUIRED`.

Baseline-сравнения внутри той же frozen-mask обязательны:

- majority/sign-prior baseline;
- старый `simple_combined`;
- no-direction baseline: входить в mask без модели стороны и раскрыть, что это означает для direction-метрик.

Разрешённые verdict:

- `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`;
- `PIVOT_AMPLITUDE_OR_ENTRY_MECHANICS`;
- `DIRECTION_REPLICATION_REQUIRED`;
- `ABORT_CONTRACT_FAIL`.

Запрещённые verdict:

- `CANDIDATE`;
- `FROZEN`;
- `READY_FOR_LOCKED_TEST`;
- любые live/trading claims.

## Проверки качества

Runner обязан записать в JSON:

- полный search width;
- `cumulative_search_budget`;
- feature profiles;
- target horizons;
- target families;
- train row count и frozen-mask row count отдельно;
- proof, что frozen-mask не применялась до fit;
- forbidden-column audit;
- proof доступности `Up/Dn` внутри `fractal1..fractal99`: эти поля должны быть прочитаны из producer-состояния строки, а не из top-level target/postprocessing columns;
- audit доступности `shift`, `fractal0.price`, `ATR` на момент строки;
- train-only scaler contract для любого global scaler;
- split role policy;
- yearly metrics по 2021-2025;
- class/sign balance после mask;
- failed runs;
- low-N disclosure отдельно от выбора.

## Артефакты

Новые артефакты пишутся под отдельным префиксом, чтобы не стирать старый контрольный результат:

- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`;
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`;
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`;
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime-rich-features.md`.

Старый runner можно оставить как контроль, но новый отчёт должен прямо объяснить, что прежний результат был бедным baseline, а не полноценной проверкой направления.
