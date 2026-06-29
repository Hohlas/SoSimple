# Stage 5.2 — регрессия времени до пробоя

> **Date**: 2026-06-25
> **Status**: Draft
> **Level**: кандидат-гипотеза (не диагностика, но и не готовый кандидат)
> **Verdict scope**: `CANDIDATE_HYPOTHESIS` при прохождении всех gate; `DIAGNOSTIC_ONLY` при провале oracle-preflight или model gate. Настоящий `CANDIDATE` — только после независимого frozen test на новом периоде 2026+ или другом инструменте.
> **Goal**: Заменить бинарный таргет «пробьётся ли stop за 6 баров» на регрессионный «через сколько баров пробьётся stop», чтобы проверить, была ли бинарная цель источником потери сигнала. Если регрессия даёт существенно лучшее ранжирование — бинарный таргет был узким местом. Если нет — проблема в самих фрактальных признаках.

## Мотивация

### Почему регрессия может помочь

Бинарный таргет `sell_stop_broken_H6_off05_flag` теряет информацию: пробой через 1 бар и через 5 баров — оба `1.0`. Но для торговой логики разница принципиальна: быстрый пробой = уровень слабый, входить опасно; медленный пробой = уровень живёт дольше, даёт время на тейк. Регрессия времени до пробоя сохраняет эту информацию и потенциально даёт больше сигнала на семпл.

### Почему это может не сработать

Восемь этапов на `H6_off05` (5.0d, 5.0c, 5.0e, 5.0f, 5.1, 5.1b) уперлись в AUC 0.65-0.69. Если проблема в умеренности фрактальных признаков, а не в бинарности цели, регрессия не даст прироста. Спецификация отвечает на этот вопрос честно: предзарегистрированный gate, ниже которого Stage 5.2 закрывается.

### Что уже известно о признаках

Из Stage 5.1/5.1b:
- `back` — единственное поле с самостоятельным устойчивым сигналом (`overall_likely_useful`).
- `impulse` — второй кандидат, но не получает самостоятельный useful verdict.
- Up/Dn поля не улучшают `structure_full`.
- `clock + shift` как baseline; но `clock_shift` слабее `time_only` — add-one дельты нужно читать осторожно.
- Delta CI в 5.1b не вычислены — verdicts слабее 5.1.

Стартовый профиль для Stage 5.2: `clock + shift + back (+ impulse)`, без Up/Dn по умолчанию.

## Предзарегистрированные gate-критерии

Критерии зафиксированы ДО просмотра результатов. Их нельзя менять после обучения.

### Oracle-preflight gate (до обучения моделей)

Oracle-preflight проверяет потолок механики при идеальном знании времени до пробоя. Если потолок не превосходит бинарную постановку, регрессия не оправдана.

Gate:
- Oracle-time (идеальное знание времени до пробоя) даёт PF ≥ 1.3 на канонических издержках на `val_stop` 2021-2022.
- Oracle-time превосходит oracle-binary (идеальное знание факта пробоя) по PF минимум на 0.2.
- Trades/year ≥ 50 на val.
- Результат не держится на одном годе.

Если oracle-preflight не проходит → Stage 5.2 закрывается со статусом `DIAGNOSTIC_ONLY`, вывод: «проблема не в бинарности цели».

### Model gate (после обучения)

- Spearman ρ предсказанного времени до пробоя vs истинного ≥ 0.30 на `val_stop` 2021-2022.
- Spearman ρ модели выше Spearman ρ константного baseline (`always H+1`) минимум на 0.05.
- Spearman ρ модели выше Spearman ρ `time_only` и `clock_shift` минимум на 0.03.
- MAE ≤ 3 бара (половина горизонта H=6) на `val_stop`.
- MAE модели лучше константного baseline (`always H+1`) минимум на 10%.
- AUC по непрерывному `predicted_bars_to_breach` как score против бинарной цели `true_bars_to_breach >= 4` ≥ 0.70 на `val_stop` — это выше потолка бинарной модели (0.69).
- Результат не держится на одном годе из 2021-2022.

Если model gate не проходит → Stage 5.2 закрывается, вывод: «регрессия не превосходит бинарную постановку на фрактальных признаках».

### Что считается успехом этапа

Все gate пройдены → `CANDIDATE_HYPOTHESIS`. Это значит: регрессия перспективна, но требует независимого подтверждения на новом периоде 2026+ или другом инструменте. Настоящий `CANDIDATE` — только после frozen test. Следующий шаг — либо frozen test (если накопится данных), либо переход к Путь B (regression_updn / triple barrier).

## Цензурирование: ключевой дизайн-вопрос

### Проблема

Таргет «число баров до пробоя» определён только если пробой произошёл. Если за H=6 баров пробоя не было, наблюдение right-censored: мы знаем, что время до пробоя > 6, но не знаем точное значение.

### Варианты

| Вариант | Что присвоить no-breach | Плюс | Минус |
|---|---|---|---|
| A. Отбросить | удалить строки | чистая регрессия | теряем ~30-40% данных (no-breach — большинство) |
| B. Присвоить H | `bars_to_breach = 6` | сохраняет данные | пик на H, модель учит «6 = безопасно» |
| C. Присвоить H+1 | `bars_to_breach = 7` | разделяет «почти пробили» и «не пробили» | артефактный разрыв |
| D. Survival analysis | Cox / ускоренное время отказа | теоретически правильно | новая инфраструктура, сложно интерпретировать |

### Рекомендация: Вариант C с раскрытием

`bars_to_breach = H + 1` для no-breach. Логика: «уровень прожил как минимум H+1 баров». Это даёт монотонный сигнал «чем больше — тем безопаснее» без пика на самом H.

**Честное название:** это censored proxy, а не полноценная регрессия времени. Значение 7 не значит «пробой через 7 баров» — оно значит «не пробит за 6 баров, реальное время неизвестно». Модель учится различать «пробит рано» (1-3) от «пробит поздно или не пробит» (4-7), что ближе к ordinal-задаче, чем к непрерывной регрессии.

Альтернатива для будущего цикла: дискретная survival-модель через 6 бинарных задач `P(T > 1), P(T > 2), ..., P(T > 6)`. Это ближе к смыслу задачи и не требует Cox, но требует отдельной инфраструктуры. Если H+1 proxy покажет перспективный сигнал, survival-модель — следующий шаг.

Дополнительно: записать долю censored наблюдений по train/val/holdout. Если censoring rate > 70% — регрессия вырождается в бинарную классификацию с асимметричным кодированием, и смысл этапа теряется. В этом случае Stage 5.2 закрывается.

## Таргет-контракт

### Колонки

| Колонка | Тип | Описание |
|---|---|---|
| `sell_bars_to_breach_H6_off05` | int / NaN | число баров от `row` до первого касания stop_price; `H+1=7` если не пробит за H=6; NaN если направление не совпадает или недостаточно данных |
| `buy_bars_to_breach_H6_off05` | int / NaN | аналогично для BUY |

Суффикс `_target` не используется, чтобы не ломать совместимость с существующими breach-колонками (`*_flag`). Новые колонки вносятся в target denylist для feature builder-а.

### Вычисление

Расширение `label_fractal_stop_breach` (`processing/label_signals.py:1455`):

```python
# Текущая логика (бинарная):
breach = any(ohlc[times[k]][2] <= stop_price for k in range(idx0+1, idx0+1+H))
df.at[i, col] = 1.0 if breach else 0.0

# Новая логика (регрессионная, censored proxy):
bars_to_breach = H + 1  # default: не пробит за H баров
for k in range(idx0 + 1, idx0 + 1 + H):
    if fractal_dir == -1:  # BUY: стоп ниже впадины, пробой = Low касается stop
        if ohlc[times[k]][2] <= stop_price:
            bars_to_breach = k - idx0
            break
    elif fractal_dir == 1:  # SELL: стоп выше пика, пробой = High касается stop
        if ohlc[times[k]][1] >= stop_price:
            bars_to_breach = k - idx0
            break
df.at[i, time_col] = int(bars_to_breach)
```

Тот же OHLC-индекс, тот же stop_price, тот же direction-filter. Разница: вместо `any()` — первый индекс касания. Для BUY проверяется `Low <= stop_price` (цена упала до стопа), для SELL — `High >= stop_price` (цена поднялась до стопа).

### Live-safe статус

Таргет строится из будущих баров OHLC — это label, не признак. Colонки вносятся в denylist. Левередж тот же, что у существующих `*_flag` колонок: future-derived, используется только как target.

## Торговая логика

### Как использовать предсказание времени до пробоя

1. **Time-stop.** Модель предсказывает `bars_to_breach = 4`. Тейк стоит на 2 ATR. Если цена проходит 2 ATR в среднем за 2-3 бара — успеваем взять прибыль до пробоя. Если `bars_to_breach = 1` — уровень слабый, не входим.
2. **Выбор фрактала.** Среди нескольких уровней выбираем тот, у которого `bars_to_breach` наибольший — самый живучий.
3. **Пороговый фильтр.** Вход только если `predicted_bars_to_breach >= threshold` (например, ≥ 4). Это сводится к бинарному решению «входить/нет», но порог оптимизирован под регрессионное предсказание, а не под `breach_flag`.

### Метрики сравнимости с бинарной моделью

AUC считается по **непрерывному** `predicted_bars_to_breach` как score против бинарной цели `true_bars_to_breach >= 4` (уровень проживёт достаточно долго). Это позволяет сравнить ранжирующую способность регрессионной модели с бинарной моделью Stage 5.1 на том же split.

Порог `predicted_bars_to_breach >= 4` зафиксирован до обучения (половина от H+1=7, округлённая вниз). По этому порогу считаются отдельные метрики: precision, recall, trades/year, PF — но не AUC (AUC по одному порогу бессмысленен).

## Дизайн эксперимента

### Этап 0: Oracle-preflight

До обучения моделей. Проверяет потолок механики через first-touch trade simulator.

**Симулятор.** Для каждого входа: entry_price = `Close[row]` (diagnostic only), stop_price = `fractal0.price ± 0.5 * ATR`, take_price = `entry_price ± 2 * ATR` (в сторону входа). Симулятор проходит будущие бары и определяет, какая преграда задета первой: TP, SL или timeout (H=6 баров). Результат сделки: PnL в ATR-единицах.

**Oracle-time.** Подставляет истинное `bars_to_breach`. Вход только если `true_bars_to_breach >= 4` (уровень проживёт достаточно долго). Затем симулятор проверяет: успевает ли TP сработать до SL или timeout.

**Oracle-binary.** Подставляет истинный `breach_flag`. Вход только если `true_breach_flag == 0` (не пробьют за H). Тот же симулятор.

**Сравнение.** Оба oracle проходят через один и тот же first-touch симулятор с одинаковыми TP/SL/timeout. oracle-time выигрывает только если более ранний вход (благодаря знанию времени до пробоя) даёт TP до позднего stop. Если oracle-time просто включает больше сделок, но без превосходства по PF — регрессия не оправдана.

Gate:
- Oracle-time даёт PF ≥ 1.3 на канонических издержках на `val_stop` 2021-2022.
- Oracle-time превосходит oracle-binary по PF минимум на 0.2.
- Trades/year ≥ 50 на val.
- Результат не держится на одном годе.

Если oracle-preflight не проходит → Stage 5.2 закрывается со статусом `DIAGNOSTIC_ONLY`, вывод: «проблема не в бинарности цели».

### Этап 1: Labeling

- Расширить `label_fractal_stop_breach` вычислением `bars_to_breach`.
- Новые колонки: `sell_bars_to_breach_H6_off05`, `buy_bars_to_breach_H6_off05`.
- Проверить censoring rate по split.
- Тесты: паритет с бинарным флагом (`bars_to_breach <= H` ⟺ `flag == 1`), edge cases (недостаточно баров, направление).

### Этап 2: Обучение

- Модель: XGBoost (`objective: reg:squarederror` или `reg:pseudohubererror`).
- Профили (из выводов 5.1/5.1b):
  - `time_only` (обязательный контроль — 5.1b показал, что `clock_shift` слабее `time_only`)
  - `clock_shift` (baseline)
  - `clock_shift + back`
  - `clock_shift + impulse`
  - `clock_shift + back + impulse`
  - `structure_full`
  - `structure_full_without_back`
- Константный baseline (`always H+1`): вычисляется без обучения, как `np.full(n, H+1)`.
- 2 цели: sell, buy.
- 3 seed: [42, 77, 123].
- Split: train ≤2020, val 2021-2022, diagnostic holdout 2023-2025 (disclosure), low-N 2026.
- 7 профилей × 2 цели × 3 seed = 42 прогона + константный baseline без обучения.

### Метрики

| Метрика | Период | Назначение |
|---|---|---|
| Spearman ρ | val, holdout | ранговая корреляция предсказания и истинного времени |
| MAE (бары) | val, holdout | средняя абсолютная ошибка в барах |
| Censored MAE | val | MAE только на uncensored (breach=1) строках |
| AUC (непрерывный score) | val, holdout | `predicted_bars_to_breach` как score vs бинарная цель `true_bars >= 4` |
| Fixed-threshold PF/precision/recall | val | порог `predicted >= 4` → trade simulation |
| Improvement vs constant (`always H+1`) | val | MAE и Spearman модели минус константный baseline |
| Yearly Spearman / MAE | val (2021, 2022), holdout (2023, 2024, 2025) | устойчивость по годам |
| Calibration table | val | предсказали 1-2 / 3-4 / 5-7, что реально произошло (median true) |
| Censoring rate | train, val, holdout | доля no-breach |

### Sanity checks

1. `bars_to_breach <= H` ⟺ `breach_flag == 1` — паритет с существующим бинарным таргетом.
2. Censoring rate согласуется с breach rate из Stage 5.1 (no-breach ≈ 60-70%).
3. `structure_full` на регрессии не должен быть хуже `clock_shift` — если хуже, проблема в сборке.

## Риски

1. **Цензурирование доминирует.** Если no-breach > 70%, censored proxy вырождается в бинарную классификацию с асимметричным кодированием. Gate: если censoring rate > 70% на train — остановка.
2. **Регрессия не превосходит бинарную.** Восемь этапов показали потолок AUC 0.69. Если Spearman ρ < 0.30 или AUC непрерывного score < 0.70 — фрактальные признаки умеренны независимо от типа цели. Это не провал, а честный отрицательный результат.
3. **2023-2025 сожжены.** Diagnostic holdout уже использовался в 5.0f/5.1/5.1b. Регрессионный таргет — формально новая постановка, но если параметры выбираются по этим годам — они сожжены. Gate-критерии предзарегистрированы до просмотра holdout; holdout — только disclosure. Даже при прохождении всех gate статус — `CANDIDATE_HYPOTHESIS`, не `CANDIDATE`.
4. **MAE чувствителен к цензурированию.** Censored наблюдения (bars_to_breach = H+1) создают систематическую ошибку, если модель предсказывает меньше. Censored MAE (только на breach=1) и improvement vs constant baseline — дополнительные метрики для честности.
5. **Новая инфраструктура labeling.** Расширение `label_fractal_stop_breach` рискует сломать существующие breach-колонки. Тесты паритета обязательны до обучения.
6. **Oracle-preflight может быть обманчив.** First-touch симулятор использует `Close[row]` как entry — это diagnostic only. Если live-задержка не позволяет войти по `Close[row]`, реальный PF будет ниже oracle.
7. **clock_shift слабее time_only.** Stage 5.1b показал это. Поэтому `time_only` включён как обязательный контроль. Если регрессионная модель побеждает `clock_shift`, но не `time_only` — вывод ослабляется.

## Выходные артефакты

```text
ML/reports/stage5_2_time_to_breach_regression.json
docs/reports/YYYY-MM-DD-stage5_2-time-to-breach-regression.md
```

Минимальная структура JSON:
- `stage`: `"5.2_time_to_breach_regression"`
- `status`: `"ORACLE_FAILED"` / `"MODEL_GATE_FAILED"` / `"CANDIDATE_HYPOTHESIS"` / `"DIAGNOSTIC_ONLY"`
- `oracle_preflight`: oracle-time vs oracle-binary PF/PnL/trades через first-touch симулятор
- `censoring`: rates по split
- `constant_baseline`: Spearman ρ и MAE для `always H+1`
- `raw_runs`: per-profile per-target per-seed
- `summary`: Spearman ρ, MAE, censored MAE, AUC (непрерывный score vs `true >= 4`), fixed-threshold PF/precision/recall, improvement vs constant, yearly, calibration table
- `gate_results`: pass/fail по каждому критерию
- `sanity_checks`: паритет с бинарным, censoring vs breach rate, model > constant baseline

## Решение после этапа

1. **Oracle-preflight провален.** Проблема не в бинарности цели. Закрыть, перейти к Путь B (regression_updn / triple barrier).
2. **Model gate провален.** Регрессия не помогает. Фрактальные признаки умеренны независимо от типа цели. Закрыть, перейти к Путь B.
3. **Все gate пройдены.** `CANDIDATE_HYPOTHESIS`. Регрессия перспективна, но требует независимого подтверждения. Следующий шаг — frozen test на 2026+ (если накопится данных) или переход к Путь B с переносом `back` как гипотезы. `CANDIDATE_HYPOTHESIS` не означает, что Путь B отменён — они не исключают друг друга.

Запрещённые выводы:
- «Регрессия доказала прибыльность Fractal Stop.»
- «`back` — production-признак для регрессии.»
- «2023-2025 — независимое подтверждение.»
- «Статус CANDIDATE — можно запускать торговлю.» (только `CANDIDATE_HYPOTHESIS`, нужен frozen test)
- «Путь B отменён, потому что 5.2 прошёл.» (5.2 и Путь B не исключают друг друга.)

## Связанные материалы

- `docs/superpowers/roadmap.md` — roadmap (Stage 5.2 + альтернативы)
- `docs/superpowers/specs/2026-06-24-stage5_1-structural-fractal-field-ablation-design.md` — спецификация Stage 5.1
- `docs/superpowers/specs/2026-06-24-stage5_1b-updn-fields-and-shift-baseline-design.md` — спецификация Stage 5.1b
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md` — отчёт Stage 5.1b (выводы по признакам)
- `docs/reports/2026-06-24-stage5_1-structural-field-ablation.md` — отчёт Stage 5.1
- `docs/methodology/04-labeling.md` — методика разметки целей
- `docs/methodology/06b-oracle-preflight.md` — методика oracle-preflight
- `docs/methodology/06-temporal-split.md` — методика split
- `processing/label_signals.py` — `label_fractal_stop_breach` (line 1455), `BR_BREACH_HORIZONS` (line 561)
- `ML/baseline/benchmark_stage5_transformer_breach.py` — раннер Stage 5.x
- `ML/reports/stage5_1b_updn_field_ablation.json` — JSON Stage 5.1b
