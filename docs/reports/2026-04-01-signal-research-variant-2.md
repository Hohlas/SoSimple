# Signal Research Variant 2

> **Date**: 2026-04-01
> **Status**: Completed
> **Goal**: Завершить OHLC-ориентированное исследование сигнала перед Variant 3
> **Related plan/spec**: [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](../superpowers/specs/2026-04-01-signal-research-variant-2-design.md)
> **Related commit**: pending

## Контекст

Цель этапа была в том, чтобы превратить `API/signal_research.py` в OHLC-инструмент для практического исследования и ответить на вопросы перед Variant 3: когда лучше входить, как ведёт себя pullback, как влияет геометрия `SL/TP` и как сигнал ведёт себя в разных режимах.

Работа опиралась на действующий pipeline `regression_updn` и проект исследования OHLC. На этом этапе специально не меняли EA, а собирали факты о том, как текущий сигнал ведёт себя по ходу сделки.

OOS run охватил период `2022-07-18 11:00:00` — `2026-03-20 06:00:00` на `DATA/XAUUSD_H1_OHLC.csv`, а источником сигналов был `MT/MQL4/Files/ml_signals.csv`.

## Что сделано

- Расширен `API/signal_research.py` блоками исследования Variant 2.
- Добавлены и расширены тесты в `tests/test_signal_research.py` для нового исследовательского поведения.
- Обновлён `CHANGELOG.md` итогами этапа.
- Запущена проверка Variant 2 на OHLC-датасете и реальных BUY/SELL сигналах.

## Изменённые файлы

- `API/signal_research.py`
- `tests/test_signal_research.py`
- `CHANGELOG.md`

## Проверка

Команды проверки, использованные на этапе:

```bash
python -m pytest tests/test_signal_research.py -q
python -m API.signal_research --test-only
```

## Результаты

Ключевые OOS-факты по завершённому исследованию:

| Метрика | Значение |
|---|---:|
| Реальные BUY/SELL сигналы | 2603 |
| `adv_1` | 5.6 |
| `adv_3` | 8.8 |
| `adv_6` | 12.2 |
| Лучший базовый сетап | `12H / SL=5 / TP=50 / PF=1.05` |
| Лучший `ratio_12` бакет | `4-5` |
| Слабый `ratio_12` бакет | `3-4` |
| `BUY PF_12` | 1.35 |
| `SELL PF_12` | 0.95 |
| `ATR Q4 PF_12` | 1.23 |

Этап также подтвердил, что профиль сигнала — это не сильный импульс, а слабый положительный drift с заметным ранним adverse-движением.

## Выводы

Variant 2 показал, что у текущего ML-сигнала есть слабый положительный edge, но направленного импульса недостаточно, чтобы опираться только на направление.

Главные практические выводы:

- поведение сигнала ближе к слабому drift, чем к сильному breakout-импульсу;
- момент входа важен, потому что раннее adverse-движение встречается часто;
- `ratio_12 = 3-4` — рискованный сегмент, его не стоит считать приоритетной подгруппой;
- `ratio_12 = 4-5` — приоритетная подгруппа для следующего этапа;
- Variant 2 не доказывает, что limit-вход лучше market-входа, поэтому эта гипотеза остаётся открытой для Variant 3.

## Ограничения / открытые вопросы

Этот этап не ответил на алгоритмический вопрос выбора входа. Он только показал, что сигнал часто сначала идёт против входа, и что профиль сделки сильно зависит от времени входа.

Открытые вопросы, которые переносятся в Variant 3:

- Лучше ли market-вход, чем pullback-вход?
- Улучшает ли delayed-вход профиль движения?
- Нужно ли отменять часть сигналов, если ожидаемая конфигурация не появляется достаточно быстро?
- Отличаются ли эти эффекты для `BUY`, `SELL`, бакетов `ratio_12` и ATR-режимов?

## Следующий шаг

Сравнить в Variant 3 сценарии входа `market`, `pullback`, `delayed` и `cancel-window`. Использовать текущий baseline `12H` и делать явное сравнение по `BUY` / `SELL`, по бакетам `ratio_12` и по ATR-подгруппам.

## Связанные материалы

- [docs/superpowers/specs/2026-04-01-signal-research-variant-2-design.md](../superpowers/specs/2026-04-01-signal-research-variant-2-design.md)
- [docs/superpowers/plans/2026-04-01-signal-research-variant-2.md](../superpowers/plans/2026-04-01-signal-research-variant-2.md)
- [docs/superpowers/specs/2026-04-01-signal-research-variant-2-findings.md](../superpowers/specs/2026-04-01-signal-research-variant-2-findings.md)
