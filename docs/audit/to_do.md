# Audit To Do

## После Stage 4.3 Diagnostic-Only

Stage 4.3 специально ограничен диагностикой текущего winner и не должен включать новые исследовательские ветки. Следующие темы вынесены из Stage 4.3 не потому, что они не нужны, а потому что для них нужны отдельные планы и отдельные критерии интерпретации.

Единый master-план выполнения: `docs/superpowers/plans/2026-06-15-stage4_remaining-hypotheses-master.md`.

- [x] **Stage 5.0-prep: breach feature ablation.**
  Выполнено 2026-06-15. Результат: time_only (4 признака, AUC=0.6286) превосходит no_time (1001 признак, AUC=0.6113) — календарный риск подтверждён. no_price улучшает AUC на 32 bp. Отчёт: `docs/reports/2026-06-15-stage5-prep-diagnostics.md`.

- [x] **Stage 5.0-prep: AUC→PF sensitivity.**
  Выполнено 2026-06-15. Первый проход PF-gate > 1.15 при alpha=0.1, AUC=0.8442. Требуемый прирост AUC: +1768 bp от baseline 0.6674. Отчёт: `docs/reports/2026-06-15-stage5-prep-diagnostics.md`.

- [x] **Отдельный план: trailing / partial exit mechanics.**
  Выполнено 2026-06-15. trail_atr_0_2: PF=1.831, BS_p05=1.462 — первый diagnostic-результат, заслуживающий чистого цикла. Breakeven убивает PF (0.717). Отчёт: `docs/reports/2026-06-15-stage4_5-exit-mechanics.md`.

- [x] **Отдельный план: чистый candidate-cycle для найденной Stage 4.5 зоны.**
  Выполнено 2026-06-15 (расширено до 2026). trail_atr_0_2 на val_select (2019-2022): PF=2.041, BS_p05=1.618, concentration=0.434 — прошёл gate. На val_eval (2023-2026, из Nero.csv): PF=0.897 — провал. Breach-модель ≤2016 не обобщается на +7 лет. Отчёт: `docs/reports/2026-06-15-stage4_6-clean-candidate-cycle.md`.

## Вывод после выполнения master-плана

Все гипотезы из to_do.md проверены. Результаты:
1. **Календарный риск** подтверждён — Stage 5.0 Transformer должен включать календарный baseline.
2. **Tребуемый AUC-прирост** для PF-gate = 1768 bp — масштаб значительный.
3. **Trailing-механика** (trail_atr_0_2) показала сильный сигнал на 2019-2022 (PF=2.041), но провалила val_eval 2023-2026 (PF=0.897).
4. **Следующий шаг:** Stage 5.0 Transformer. Fixed TP R=0.7 — основной baseline торгового слоя. Trail_atr_0_2 — отдельная диагностическая ветка для будущего чистого цикла с более длинным split.
