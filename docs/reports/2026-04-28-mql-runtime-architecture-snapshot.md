# MQL Runtime Architecture Snapshot

> **Date**: 2026-04-28 11:45
> **Status**: Completed
> **Goal**: Зафиксировать текущую архитектуру MQL runtime-контура `Nero.csv -> watcher -> ml_signals.csv` перед дальнейшей диагностикой online-сигналов.
> **Related plan/spec**: `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`, `docs/superpowers/plans/2026-04-27-telemetry-frequency-demo-launch.md`
> **Related commit**: `211cea9`

## Context

После подготовки `telemetry_frequency_v1` был начат локальный M1-прогон, чтобы не ждать H1-бары при проверке online-связки.

Проверка подтвердила, что MT4 expert стартует, читает `#.csv`, обрабатывает новые бары и вызывает `ML_TRADE()`. Отдельно была проверена цепочка `MT4 -> Nero.csv -> Python watcher -> ml_signals.csv`.

Задача этого отчёта - сохранить архитектурное состояние и факты проверки, а не оформлять список исправленных ошибок.

## Current MQL Runtime Architecture

### Startup

При `OnInit()` эксперт:

1. читает строки параметров из `MT/MQL4/Files/#.csv`;
2. создаёт активные строки `EXP[]`, прошедшие фильтр `Name/Symbol/Period/Risk/Magic`;
3. вызывает `EXP[e].INIT()`, где создаётся новый `Nero.csv` с заголовком;
4. выполняет `RECOUNT_HISTORY()`;
5. возвращает штатные online-маркеры `bar=1`, `BarTime=Time[0]`.

`RECOUNT_HISTORY()` проходит доступную историю от старых баров к новым:

```cpp
int UnCounted=Bars-PicPer-1;
for (bar=UnCounted; bar>1; bar--){
   for (uchar e=0; e<ExpTotal; e++){
      if (!EXP[e].PIC()) continue;
   }
}
```

Цель этого прохода - восстановить массив уровней `F[]` с учётом старых сильных фракталов. Простого накопления первых `100` свежих фракталов недостаточно, потому что критерий удаления уровней сохраняет старые сильные уровни.

### PIC / POC

`POC_SIMPLE()` перенесён внутрь `PIC()` и выполняется в конце `PIC()` после:

- поиска нового high/low пика;
- вызовов `NEW_LEVEL()`;
- `LEVELS_FIND_AROUND()`;
- `LOCAL_TREND()`.

Так обычный online-проход и исторический прогрев используют один атомарный расчётный шаг.

### Nero.csv

`Nero.csv` теперь формируется в два этапа:

1. при старте пересобирается по доступной истории через `RECOUNT_HISTORY()`;
2. далее дописывается при появлении новых уровней `PIC()/NEW_LEVEL()`.

В локальном M1-прогоне файл `MT/MQL4/Files/Nero.csv` успешно пересобрался и достиг примерно `500 MB`; новые уровни после старта дописывались.

### ATR и Ready State

Медленный ATR теперь инициализируется сразу после старта, если ещё не рассчитан:

```cpp
if (Atr.Slow<=0 || TimeDay(Time[bar])!=TimeDay(Time[bar+1]))
```

Окно готовности эксперта в `END()` больше не становится отрицательным на M1:

```cpp
int ReadyAgeSec=EXP[e].Per*60-300;
if (ReadyAgeSec<=0) ReadyAgeSec=EXP[e].Per*60;
```

Это сохраняет старую идею проверки свежести, но делает её корректной для малых таймфреймов.

## Watcher Runtime Architecture

`API.telemetry_signal_watcher` теперь использует следующий online-контракт:

1. следит за последним `time` в `MT/MQL4/Files/Nero.csv`;
2. при изменении собирает `runtime_input_snapshot.csv` из хвоста `Nero.csv`;
3. строит predictions через checkpoint:
   - `mode=original_contour`;
   - `feature_mode=original_baseline`;
   - `seq_len=50`;
4. применяет frozen rule `telemetry_frequency_v1`;
5. атомарно обновляет `ml_signals.csv` в runtime/tester каталогах.

Ограничение окна задаётся параметром:

```bash
--max-runtime-rows 12000
```

Это не требование модели. Модель принимает решение по одной строке `Nero.csv`, внутри которой уже есть `fractal0..fractal99`. Окно нужно runtime-контуру, чтобы MT4 видел достаточный ряд `time;signal` в `ml_signals.csv`.

## Verification

```bash
./.venv/bin/python -m pytest tests/test_telemetry_signal_watcher.py
# 14 passed

./.venv/bin/python -m py_compile API/telemetry_signal_watcher.py
# ok
```

Локальная проверка watcher-а:

```bash
./.venv/bin/python -m API.telemetry_signal_watcher --verbose --max-runtime-rows 12000
```

Результат:

- память больше не уходит в десятки GB;
- rebuild завершился успешно;
- `runtime_input_snapshot.csv`, `runtime_predictions.csv`, `runtime_ml_signals.csv` обновляются.

Проверка `full vs 12000`:

- full prediction export собран чанками по всему `Nero.csv`, чтобы не держать файл в RAM;
- на хвосте `12000` строк максимальное отличие `pred_*` от full-эталона: `3.37e-7`;
- `signal_mismatch_rows=0`;
- `signal_mismatch_rate=0.0`.

Это показывает, что snapshot-окно не искажает модельные prediction на проверенном хвосте сильнее обычного float-шума.

## Results

| Check | Result |
|---|---:|
| `Nero.csv` rows | `63009+` |
| full prediction rows | `63010` |
| snapshot rows | `12000` |
| prediction max abs diff on overlap | `<= 3.37e-7` |
| signal mismatches on overlap | `0` |
| watcher tests | `14 passed` |

Дополнительно проверены окна `1000`, `2000`, `4000`, `8000` против `12000`. На пересечении prediction отличались только на уровне float-шума, а итоговые `signal` не расходились.

## Current Open Finding

Текущий live `Nero.csv` содержит:

```text
signal_nonzero: 0
predict_nonzero: 0
```

То есть MT4 уже пишет строки `Nero.csv`, но поля `signal` и `predict` в online-файле остаются нулевыми.

Для текущего diagnostic exporter-а это критично: направление сделки берётся из знака `predict`.

```text
predict > 0 -> BUY
predict < 0 -> SELL
predict = 0 -> no trade
```

Поэтому при текущем online `Nero.csv` итоговый `ml_signals.csv` будет содержать только `signal=0`, даже если ML predictions успешно считаются.

## Conclusions

- MQL runtime теперь стартует не в холодном состоянии: `RECOUNT_HISTORY()` восстанавливает уровни по истории до online-работы.
- `Nero.csv` формируется и дописывается на новых уровнях.
- Python watcher теперь использует правильный checkpoint contract и ограничивает рабочее окно, что делает его пригоднее для менее дорогого сервера.
- Главный следующий вопрос не в памяти watcher-а и не в запуске MQL, а в соответствии live `Nero.csv` offline/test pipeline: нужно восстановить online-формирование ненулевого направления `predict/signal` или изменить diagnostic rule на другой источник направления.

## Next Step

Разобрать offline postprocessing `Nero.csv` перед обучением и тестированием:

1. найти, где формировались ненулевые `signal` / `predict`;
2. определить, должно ли это вычисляться в MQL, Python watcher-е или отдельном lightweight preprocessing step;
3. после правки снова проверить `MT4 -> Nero.csv -> watcher -> ml_signals.csv` на M1 и затем переносить на H1/server.

## Related Materials

- `docs/MT/trading_strategy.md`
- `docs/API/telemetry_signal_watcher.py.md`
- `docs/MT/ml_signal_integration.md`
- `API/telemetry_signal_watcher.py`
- `MT/MQL4/Experts/$o$imple.mq4`
- `MT/MQL4/Include/lib_PIC.mqh`
- `MT/MQL4/Include/SERVICE.mqh`
