---
name: project_ml_status
description: Долговечный статус ML: production regression_updn, текущая PF-оптимизация через сигнал и исполнение, без временных задач
type: project
---

## Production опора и устойчивое направление

- Production-модель: `regression_updn` с 10 таргетами, Transformer checkpoint `ML/checkpoints/transformer_updn_best.pt`.
- Production-опора в MT4 использует существующий ML-сигнал, а не смену архитектуры.
- Устойчивое направление исследований: улучшать PF через монетизацию сигнала, entry logic, filtering, SL/TP и regime analysis.

## Долговечные выводы

- Бакет `ratio_12=3-4` слабый и опасный.
- Простые short-horizon directional filters в ratio-threshold форме не дают полезного сигнала.
- Перед изменениями EA нужна path-dependent OHLC диагностика, а не только aggregate metrics.

## Опорные документы

- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- `API/signal_research.py`
