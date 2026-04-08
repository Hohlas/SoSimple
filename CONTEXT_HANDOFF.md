# Context Handoff

## Current Stage
Этап Triple Barrier: пересчёт разметки и повторная проверка в MT4 завершён. Найдена и исправлена главная причина старого расхождения между Python и MT4: TB-разметка считала исход не от времени строки сигнала, а от более раннего времени `fractal0`. После полной пересборки база вне MT4 стала такой: зафиксированное правило `theta=0.475`, `min_ev=0.10`, test `PF=1.11`, `N=253`. Новый MT4-прогон по свежему `ml_signals_tb.csv` дал `PF=1.27`, `N=92`. По жёстким исходам `TP/SL` совпадение уже `61 из 65`, а средняя разница по уровням SL/TP почти нулевая. Старый вывод “TB не переносится в MT4” больше не актуален.

## Last Completed Stage
Triple Barrier: причина старого расхождения найдена, цепочка пересобрана и заново проверена в MT4 (2026-04-08).

## Next Step
Следующий шаг для TB теперь не в новой переоптимизации, а в честном сравнении по одинаковым торговым правилам.

1. Добавить в Python режим оценки, который повторяет MT4 один в один: вход на следующем баре, только одна открытая позиция, `HoldOverTime`, `TB_Reversal`, пропуск новых сигналов при открытой позиции.
2. На этом режиме ещё раз сравнить offline и MT4 по одному и тому же `ml_signals_tb.csv`.
3. Только после этого решать, продвигать ли TB дальше как отдельный торговый режим и стоит ли строить новые таргеты поверх этой схемы.
4. `regression_updn` не смешивать с TB: это отдельный трек с другой логикой и другим набором выводов.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `ML/reports/threshold_analysis_tb.md`
- `ML/reports/evaluate_test_tb.md`
- `ML/reports/tb_selected_rule.json`
- `MT/MQL4/Files/ml_signals_tb.csv`

## Open Risks
- Offline и MT4 всё ещё считают не в полностью одинаковых правилах: в MT4 есть `PosBlock`, `HoldOverTime`, `TB_Reversal` и вход на следующем баре.
- Сравнение `253` offline trades и `92` MT4 trades пока не является сравнением “один к одному”.
- SELL-часть TB выглядит слабее BUY-части.
- Есть риск снова начать улучшать модель до того, как будет готов честный offline-режим под правила MT4.

## Latest Report
`docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
