---
last_updated: 2026-08-12
sources: 1
status: active
---

# MI Upper Bound: информационный потолок XAUUSD H1

> KSG-оценка маргинального MI live-safe признаков: amplitude предсказуема (p=0.005), direction на validation — нет (p=0.229); диагностический потолок R² ≈ 0.006–0.030 кратно ниже legacy R² 0.084–0.18 — наиболее вероятное объяснение разрыва — leakage future-derived входов.

## Хронология

- 2026-08-11/12: первый и пока единственный этап линии (`research_scan`, `RESEARCH_ONLY`): основная конфигурация k=5, robustness k=10/15, rolling MI 2004–2026. Открыта после live-safe аудита (все 5 legacy-систем FAIL) и вопроса «потолок или недостаток моделей».

## Ключевые результаты

- MI (bits, k=5): train direction 0.0041 (p=0.005) / amplitude 0.0222 (p=0.005); validation direction 0.0027 (p=0.229) / amplitude 0.0102 (p=0.005).
- Диагностический потолок R² = 1−2^(−2·I): train 0.0057 / 0.0303; validation 0.0038 / 0.0140 — против legacy R² 0.084 (baseline_clean), 0.10 (BiLSTM), 0.18 (Transformer).
- Rolling MI стабилен на 2004–2026 (direction ≈ 0.007–0.010; amplitude ≈ 0.014–0.035), включая период после 2022 — regime drift в информации признаков не обнаружен (независимый результат относительно drift в доходности).
- Топ-признаки: `row_strong_share_*` (оба таргета), `session_hour` важен для amplitude; группа time не доминирует (микроструктура strong/direction_balance информативнее).
- Robustness по k: ранги и порядок величин устойчивы; p по direction на validation пограничный (0.025–0.23) — вердикт direction «скорее не подтверждена» усиливается.

## Выводы

- Фокус следующих веток — amplitude; sign-стратегии опираются на слабый сигнал.
- Разрыв legacy R² с информационным потолком согласуется с live-safe аудитом (ретроспектива 2.6): часть legacy R² объясняется future-derived входами; сравнение ориентировочное (другие горизонты/входы).
- Маргинальный потолок — не строгая joint-граница; строгая граница требует отдельного эксперимента (npeet, пониженная размерность).
- Fold-CI — только метрика стабильности: на validation фолды смещены вверх (конечновыборочное смещение KSG) и не являются доверительным интервалом оценки.
- Вердикт принимается только по permutation p-value; fold-CI и rolling в вердикте не участвуют.

## Открытые вопросы

- Joint MI (npeet) на пониженной размерности — строгий потолок.
- Amplitude-ветка моделей на live-safe признаках (таргет amplitude).
- Починка `statistics/data_contract_smoke_check.py` (устаревшие колонки `target_*_H6_val`).

## Источники

- `docs/reports/2026-08-11-mi-upper-bound.md` — отчёт этапа: вердикты, таблицы MI/rolling/robustness, disclosure.
- Связанные линии: [execution-tracks-live-safe-audit.md](execution-tracks-live-safe-audit.md) (происхождение вопроса), [fractal-stop-research.md](fractal-stop-research.md) (legacy R² и regime drift).
