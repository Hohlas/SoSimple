# PF Uplift Discovery — Hypotheses Longlist

**Date:** 2026-04-13
**Session:** /brainstorming — Источники PF uplift вне ML-слоя
**Hard bans applied:** MA/EMA, close[t+N]-close[t], retraining, architecture change
**Baseline bar:** N=48, PF=8.18 (quantile production)

---

## Контекст при формировании

- Session в quantile: asia=19, london=0, overlap=15, ny=14 — London полностью отсутствует
- Archetype: winning=32 (66.7%), failure=16 (33.3%)
- 2025: все 24 сделки — выигрышные; 2022 и 2023 — убытки
- Exit layer уже исследован (2026-04-08): timeout_only = победитель, новых exit rules нет
- fav_3_vs_12 composition — закрыт (gate_fail, 2023 negative year)
- hold_bars=24, ML_MaxRatio=4.5, ML_MinRatio=3.5, RR_Mode=log+cap(2.5)

---

## Гипотезы (20 штук)

| # | Cat | Формулировка | Механизм влияния на PF | Какие сделки затронет | Как проверить за 1 день |
|---|-----|-------------|----------------------|----------------------|------------------------|
| 1 | R | **London session exclusion**: исключить сигналы в часах 09–13 broker time | London = 0 в quantile-universe → baseline_selected London сделки убыточны; явная фильтрация срежет потери | ~20–25% baseline_selected сделок (london bucket) | session_tag из trade_enriched, PF in/out London; crosstab с archetype |
| 2 | R | **Low realized vol regime**: торговать только если realized vol (H1×24, lookback до входа) ≤ q50 | Низкая vol → меньше случайных adverse excursions, модель лучше откалибрована | ~50% сделок | вычислить vol_q по OHLC, добавить в trade_enriched, PF × vol_bucket |
| 3 | R | **High realized vol exclusion**: исключить vol_q4 (top 25% volatility) | В режиме spike volatility рынок нестационарен → модель теряет predicting power | ~25% сделок | та же vol_q разметка, сравнить PF Q4 vs rest |
| 4 | R | **Day-of-week filter: избегать понедельник** | Понедельник — gap risk, меньше ликвидности, сигналы фрактала от пятницы устаревшие | ~20% сделок | добавить weekday в trade_enriched, PF по дням |
| 5 | R | **Day-of-week filter: избегать пятницу** | Пятница — ранние закрытия позиций, weekend risk, позиция может не удержаться 24 bars | ~20% сделок | та же weekday разметка |
| 6 | S | **Early timeout hold_bars=12**: закрывать позицию после 12 баров вместо 24 | Если бо́льшая часть PnL реализуется к bar 12, удержание до 24 — риск без reward | все сделки | сравнить true_ret12 vs true_ret24 в trade_enriched; если median(ret12) ≈ median(ret24) — uplift |
| 7 | S | **Adaptive timeout: сократить hold для слабых lb сделок** | lb близко к m-порогу → менее уверенный quantile estimate → выходить раньше (bar 12) | Сделки с lb ∈ [m, m+Δ] | bucket lb vs true_ret24; посмотреть разницу ret12/ret24 в weak-lb bucket |
| 8 | S | **Active backstop 2×ATR**: поставить SL на 2ATR вместо текущего 50ATR | Backstop 50ATR = de facto off. SL в 2ATR режет katastrofik losses, не трогает winning archetype | Failure сделки с MAE > 2ATR | mae_atr distribution в trade_enriched; сколько losses были > 2ATR |
| 9 | S | **Partial exit at MFE ≥ 1ATR**: фиксировать 50% позиции при достижении 1ATR прибыли | Protecting gains: winner archetype идёт сразу, lock-in 50% — reduces variance | Winning сделки с mfe ≥ 1ATR | mfe_atr distribution; simulate: pnl_partial = 0.5×min(mfe,1) + 0.5×ret24 |
| 10 | E | **Signal stacking: торговать только если N≥2 сигналов на одном баре** | Дублирование signal=+1 на одном баре (из разных фракталов) — более сильный уровень | ~10–20% сделок (multi-fractal bars) | проверить дубликаты time+signal в seed_007 test predictions (уже замечено в join) |
| 11 | E | **pred_fav6/pred_fav12 < 0.6 (сигнал ещё не выстрелил)** | Аналог fav_3vs12 но на горизонте 6/12; если 6-bar fav < 60% от 12-bar → цена ещё не пошла | ~30–50% сделок | fav_6vs12 уже в trade_enriched; PF < 0.6 vs ≥ 0.6 |
| 12 | F | **pred_q10 > 0 (absolute lower bound positivity)** | Если нижняя граница quantile interval положительна → сигнал "уверенно" bullish/bearish, no ambiguity | ~30–40% квантильных сделок | col lb (= pred_q10 - correction) > 0 vs lb ∈ [m,0]; PF comparison |
| 13 | F | **Interval width фильтр: ub-lb < q50** | Узкий интервал → quantile head уверен; широкий → высокая неопределённость | ~50% сделок | col width (ub-lb) уже из benchmark; PF narrow vs wide |
| 14 | F | **baseline_score threshold ≥ 0.0 (вместо −0.035)** | Повысить порог → exclude сделки с отрицательным направленным score → cleaner baseline subset | ~30% baseline_selected | смотреть pred_score distribution vs outcome в trade_enriched |
| 15 | F | **pred_adv12 cap: исключить сделки с pred_adv12 > q75** | Модель явно предсказывает большой adverse excursion → prob failure | ~25% сделок | pred_adv12 в trade_enriched; PF top-quartile vs rest |
| 16 | X | **hold_bars = 36 (вместо 24) для strong lb сделок** | Если lb >> m → сигнал уверен, рынок может реализовать бо́льшее движение за 36 bars | Сделки с lb > m + Δ (top half of quantile) | compare true_ret24 vs true_ret_24 in labeled (нужно true_ret48 или OHLC simulation до 36 bars) |
| 17 | X | **BypassTrend=false: включить тренд-фильтр** | Тренд-фильтр в lib_ML_Signal_back.mqh отключён (BypassTrend=1). Включение может убрать counter-trend losers | Сигналы против тренда → excluded | проверить EA source на что именно фильтрует BypassTrend; нет Python replication → X категория |
| 18 | X | **MaxRatio cap снижение: 4.5 → 3.5** | Высокий ratio (> 3.5 но уже в baseline) → pred_up очень большой, TP нереалистичен. Но в quantile mode нет TP → снижает только entry signal diversity, не exit | ~15% сделок | ratio12 distribution в trade_enriched |
| 19 | R | **Intraday session overlap только**: overlap 14–18 = London+NY, максимальная ликвидность | Лучшее исполнение, меньше spread, модель обучена на этих режимах | ~30% сделок | session=overlap уже в trade_enriched; PF overlap vs others |
| 20 | R | **Return autocorrelation sign filter** | Если lag-1 return autocorrelation за 48H < 0 (mean-reversion mode) → хуже для directional signals; filter out | ~50% времени | compute 48H rolling autocorr на OHLC close, tag сделки, PF in/out |

---

## Классификация по категории

| Категория | Гипотезы | N |
|-----------|----------|---|
| R — Regime | 1, 2, 3, 4, 5, 19, 20 | 7 |
| S — SL/TP  | 6, 7, 8, 9 | 4 |
| E — Entry  | 10, 11 | 2 |
| F — Feature filters | 12, 13, 14, 15 | 4 |
| X — Execution/EA | 16, 17, 18 | 3 |

---

## Hard-ban проверка

Ни одна гипотеза не содержит:
- MA/EMA фичи или фильтры ✓
- close[t+N]-close[t] таргет ✓
- переобучение или смену архитектуры ✓
- multi-probe ensemble (это отдельный тип плана) ✓

## Long-shot bucket (проверка > 1 дня)

- **#17 BypassTrend=false**: нет Python-репликации тренд-фильтра EA → требует либо MQL-тестера, либо реверс-инжиниринга логики. Откладывается.
- **#20 Autocorrelation filter**: вычислима, но интерпретация lag-1 autocorr на Forex H1 нестабильна; требует осторожности в probe design.
