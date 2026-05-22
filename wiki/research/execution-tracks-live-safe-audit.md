---
last_updated: 2026-05-14
sources: 4
status: active
---

# Execution Tracks: Live-Safe ML Audit + Retrain (05-05)

## 10. Live-Safe ML Audit (05-05)

Повторный аудит прибыльных ML-систем отделил старую прибыльность от права идти
в online. Нормативный gate: `docs/audit/ml_trading_methodology.md#3-feature-contract-и-leakage-gate`.

Проверены пять систем:

| System | Legacy result | Live-safe verdict |
|---|---:|---|
| `quality` | PF `39.74` | `FAIL` |
| `frequency` | PF `13.12` | `FAIL` |
| `original_plus_path` | PF `38.78` | `FAIL` |
| `entry_path_v1` | PF `2.87` sequential | `FAIL` |
| `entry_path_v1_quantile` | PF `8.18` frozen test, `3.64` sequential | `FAIL` |

Current follow-up order:

| System | Follow-up state | Next action |
|---|---|---|
| `entry_path_v1` | `entry_path_v1_live_safe` profitable across five seeds; baseline rule-family frozen on `A`. | Main live-safe candidate if MT4 parity resumes. |
| `entry_path_v1_quantile` | Rebuilt over frozen live-safe baseline `A`; profitable pockets remain, rule selection unstable. | Keep research-only; do not promote as next production layer. |
| `quality` / `frequency` / `original_plus_path` | Direct take/skip baseline/path/geometry rebuilds rejected. | Pause unless a new live-safe hypothesis is defined. |

Главный вывод:

- take/skip контуры (`quality`, `frequency`, `original_plus_path`) используют
  future-derived входы: `predict`, `ret_*`, `fav_*`, `adv_*`;
- `entry_path_v1` нельзя считать PASS: `ret_dir_atr_lag1` доказан как
  future-derived (`ret_6_dir_atr.shift(1)`, где `ret_6_dir_atr` строится по
  будущим барам);
- `entry_path_v1_quantile` наследует этот fail через baseline dependency;
- ни одна из пяти систем не готова к online trading как ML-quality proof.

Дополнительно воспроизведён старый export по старым prediction/rule входам:
`quality` дал 30 ненулевых сигналов, `frequency` - 78,
`original_plus_path` - 37, `entry_path_v1` - 23,
`entry_path_v1_quantile` - 18. Это проверяет старую механику выгрузки, но
помечено как `diagnostic_only=true`, потому что источник входных признаков уже
провалил live-safe gate.

Следующий шаг был выполнен в том же этапе: retrain `entry_path_v1_live_safe`.

Источник: [2026-05-05-live-safe-ml-audit.md](../../docs/reports/2026-05-05-live-safe-ml-audit.md)

## 11. Entry Path v1 Live-Safe Retrain (05-05)

Первый rebuild `entry_path_v1` без `ret_dir_atr_lag1`. Старый профиль сохранён
для воспроизводимости, новый профиль называется `entry_path_v1_live_safe`.

| Check | Trades | PF | Win rate |
|---|---:|---:|---:|
| validation winner `A @ 7.5%` | 36 | 2.8881 | 66.67% |
| frozen test | 37 | 3.6567 | 72.97% |
| sequential test | 25 | 2.3419 | 68.00% |

Сравнение со старым `entry_path_v1`: sequential было 30 trades, PF 2.87,
win rate 66.67%. Значит, прибыльность не сохранилась один в один: сделок и PF
стало меньше. Но система не развалилась после удаления опасного признака и
остаётся прибыльным кандидатом.

Multi-seed follow-up (`7`, `17`, `42`, `77`, `123`):

| Metric | Value |
|---|---:|
| median sequential PF | 2.3419 |
| min sequential PF | 1.5171 |
| max sequential PF | 4.5985 |
| PF > 2.0 seeds | 3 / 5 |
| PF <= 1.0 seeds | 0 / 5 |
| same winner | `A` in 3 / 5 |

Вывод уточнён: результат живой, но переменный. MT4 signal export теперь
поддерживает `A`, `B` и `B_no_path6`; для `B` / `B_no_path6` используется
frozen validation-нормировка из rule JSON. Значит, exporter больше не блокер.
Decision: baseline rule-family заморожен на `A`, потому что это самый простой
вариант и он повторился в `3 / 5` seed. `B` / `B_no_path6` остаются
исследовательскими вариантами, но не основным следующим путем. MT4 parity
отложен по решению пользователя.

Follow-up audit по `A` разделил family-устойчивость и точный frozen threshold:

| Check | Result |
|---|---:|
| `A` per-seed validation threshold sequential PF | `1.5171 .. 4.1370` |
| `A` per-seed median sequential PF | `2.8425` |
| `A` per-seed PF > 2.0 | `4 / 5` seeds |
| sequential signals repeated in all 5 seeds | `21` |
| exact seed-42 threshold median sequential PF across seeds | `0.9032` |

Вывод: `A` как простая rule-family выглядит устойчиво, но численная шкала
score между seed не калибрована. Основной production-кандидат сейчас - именно
frozen seed `42` rule, а не любой заново обученный checkpoint с тем же численным
порогом.

Источник: [2026-05-05-live-safe-ml-audit.md](../../docs/reports/2026-05-05-live-safe-ml-audit.md)

## 12. Entry Path v1 Quantile Over Live-Safe Baseline (05-05)

После пересборки baseline повторно проверен `entry_path_v1_quantile`. Старый
quantile-результат был `FAIL` для online не из-за самой quantile-идеи, а потому
что production rule зависел от старого `entry_path_v1` baseline score.

Новая проверка использовала baseline:
`ML/reports/entry_path_v1_live_safe/entry_path_trade_filter_selected_rule.json`.

Multi-seed (`7`, `17`, `42`, `77`, `123`):

| Metric | Value |
|---|---:|
| sequential PF > 2.0 seeds | 4 / 5 |
| sequential PF <= 1.0 seeds | 1 / 5 |
| sequential trades range | 0..25 |
| seed with 0 sequential trades | 1 / 5 |

N-boost candidate `lb_gt_m_q40`:

| Check | Trades | PF | Win rate |
|---|---:|---:|---:|
| frozen test | 35 | 32.4125 | 88.57% |
| sequential | 14 | 48.7214 | 92.86% |

Gate result: `gate_fail`, because `same_winner_ratio=0.60 < 0.80`.

Вывод после фиксации baseline `A`: quantile-слой не развалился, но
production-кандидатом считать нельзя. Прибыльность есть, однако выбранное
правило нестабильно между seed, один seed даёт 0 sequential trades, один seed
fallback-ится на baseline, а sequential-сделок мало. Это research-promising,
но не production approval.

Источник: [2026-05-05-live-safe-ml-audit.md](../../docs/reports/2026-05-05-live-safe-ml-audit.md)

## 13. Take/Skip v2 Live-Safe Baseline Probe (05-05)

Первый live-safe rebuild для старого take/skip семейства (`quality`,
`frequency`, `original_plus_path`) проверил прямой вопрос: сохранится ли старая
прибыльность, если оставить single-tensor runner, но убрать будущие row-признаки.

Новый режим: `live_safe_baseline`.

Оставлены row-признаки:

- `ATR`
- `session_hour`
- `weekday`
- `range_atr_6`
- `body_atr_3`
- `vol_regime_24`

Удалены из входов модели: `predict`, `ret_dir_atr_lag1`, `ret_*`, `fav_*`,
`adv_*`.

Запуск `live_safe_baseline_seq50`, seed `42`:

| Metric | Value |
|---|---:|
| best epoch | 4 |
| validation BCE | 0.036112 |
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | 1.5178 |
| best observed validation trades | 3 |
| best observed trades/year | 0.75 |
| best observed negative year slices | 1 |

Вывод: это не близкий проход. Прямой rebuild старого take/skip baseline без
future-derived row-признаков не воспроизвёл tradable validation region. Старые
`quality/frequency` результаты пока нужно считать зависимыми от запрещённых
входов, пока не найден другой live-safe feature family.

Follow-up уточнение: `Up/Dn` внутри `fractal*` считаются live-safe, если они
пришли из MT `Nero.csv` как накопленное состояние `lib_PIC`, известное на
момент строки. Запрещёнными остаются Python future-label поля:
`predict`, `ret_dir_atr_lag1`, `ret_*`, `fav_*`, `adv_*`.

Повторная сверка источников подтвердила различие: `predict` в
`processing/label_signals.py` ищет будущие строки того же `fractal0.time`;
`ret_*`, `fav_*`, `adv_*` строятся по будущему OHLC-окну после входа;
`ret_dir_atr_lag1` является лагом от уже будущего `ret_6_dir_atr`. Поэтому
эти Python-поля нельзя использовать как online-входы, даже если похожие по
смыслу MT-поля уже известны в строке `Nero.csv`.

Для следующей проверки добавлены режимы `live_safe_path`, `live_safe_geometry`,
`live_safe_geometry_path`. Полный `live_safe_path_seq50` не завершался локально:
построение path/geometry признаков оказалось слишком дорогим для текущей
машины. Это не меняет методику обучения; следующий запуск нужно выполнить на
мощном сервере с тем же кодом и теми же CSV.

Серверный `live_safe_path_seq50` выполнен на том же коде и тех же CSV:

| Metric | Value |
|---|---:|
| input features | 770 |
| engineered features | 750 |
| best epoch | 5 |
| validation BCE | 0.034260 |
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | 0.9893 |
| best observed validation trades | 15 |
| best candidate meeting 6 trades/year | PF 0.6155 |

Вывод усилен: добавление MT-накопленных `Up/Dn` path-reaction признаков не
восстановило старую take/skip прибыльность.

Следующий серверный запуск проверил `live_safe_geometry_seq50`:

| Metric | Value |
|---|---:|
| input features | 642 |
| engineered features | 622 |
| best epoch | 7 |
| validation BCE | 0.033775 |
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | 0.5726 |
| best observed validation trades | 5 |
| best candidate meeting 6 trades/year | PF 0.4125 |

Следующий серверный запуск закрыл optional `live_safe_geometry_path_seq50`:

| Metric | Value |
|---|---:|
| validation winner | none |
| final verdict | `reject` |
| best observed validation PF | 3.7229 |
| best observed validation trades | 5 |
| best observed trades/year | 1.25 |
| best candidate meeting 6 trades/year | PF 0.4899 |

Вывод: path, geometry и geometry+path не восстановили старую прибыльность.
Прямой live-safe rebuild старого take/skip семейства сейчас отклонён;
продолжать его стоит только при новой узкой гипотезе, а не простым перебором
близких режимов.

Источник: [2026-05-05-live-safe-ml-audit.md](../../docs/reports/2026-05-05-live-safe-ml-audit.md)
