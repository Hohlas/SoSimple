# Stage 4 Brainstorm Result — синтез 5 независимых аудитов

> **Дата**: 2026-06-14
> **Статус**: итоговый синтез
> **Назначение**: ранжирование 5 brainstorm-файлов, объединение принятых предложений, перечень отвергнутых

## Ранжирование аудит-файлов

Ранжирование по глубине анализа, точности данных и полезности выводов:

| # | Файл | Оценка | Обоснование |
|---|------|--------|-------------|
| 1 | `brainstorm_deep.md` | ★★★★★ | **Лучший.** Все эксперименты выполнены с реальными данными на Stage 4.2 инфраструктуре. Partial oracle (PF 14.72 fav vs 6.61 breach), breach-калибровка, асимметрия fav-ошибок, 8 improvement-экспериментов, 14 trailing stop стратегий. Выводы конкретны и проверены. |
| 2 | `brainstorm_codex.md` | ★★★★☆ | Отличная структура диагностических экспериментов, чёткая терминология, хорошо определённые bucket-тесты и 2D-карта. Практичная рекомендация TP-policy сравнения. Но — часть экспериментов уже выполнена в deep, нет концепции трейлинг-стопа. |
| 3 | `brainstorm_Qwen.md` | ★★★☆☆ | Ценное наблюдение про фактический RR (2.5× ниже заявленного). Хорошая 6-блочная структура, precision/recall для breach. Но — использует устаревшие цифры (Stage 4 PF=1.106 вместо 1.015), oracle-цифры от Stage 2 RF, нет трейлинг-стопа. |
| 4 | `brainstorm_GLM.md` | ★★☆☆☆ | Чистая oracle-ablation таблица (A/B/C/D), декомпозиция убытков по категориям, условный PF. Но — очень краткий, поверхностный, старые цифры. |
| 5 | `brainstorm_mimo.md` | ★☆☆☆☆ | Структурированный 4-вариантный план, но: предлагает эксперименты, уже выполненные в deep; использует устаревшие oracle-цифры Stage 2; ошибочный gap-анализ через PF-отношения (PF=1.106/PF=8.02 = 14% — бессмысленная метрика); имена файлов не согласованы с конвенциями проекта. |

---

## Принятые предложения (объединённые и дедуплицированные)

### Уже выполнено (deep)

1. **Partial Oracle декомпозиция** — изоляция breach и fav через подстановку истинных меток. Fav — большее узкое место (PF 14.72 vs 6.61), но синергия колоссальна (perfect_both PF=104.88).
2. **Breach-калибровка по децилям** — модель калибрована (D1: 12.6% pred = 12.6% fact), но даже лучшие корзины дают слабый PF (~1.3). Проблема не в калибровке.
3. **Fav-асимметрия по типу выхода** — SL-сделки: bias +0.87 ATR (массивное завышение). TP-сделки: bias −0.09 (почти точен). Модель входит с ложной уверенностью там, где цена идёт против.
4. **Сканирование параметров** — tp_fraction (0.4 оптимален), stop_offset×tp (off=0.5, tf=0.4 — уникальный оптимум), min_rr (1.0 оптимален). Все параметры уже в локальном оптимуме.
5. **Фильтры не работают** — strong fractal (~0 сделок), ATR regime (PF=0.927, вредит), combined H6+H12 breach (PF=0.916, вредит).
6. **Dynamic TP потолок: PF=3.462** — идеальный выход по лучшей цене до SL. Показывает, что проблема в механике фиксированного выхода, а не в точках входа.
7. **14 trailing stop стратегий** — atr_02 (0.2 ATR трейлинг): PF=1.655 (+64%). avg_loss вдвое меньше, TIMEOUT исчезают. Реалистично (0.2 ATR ≈ 1 пункт XAUUSD). Step-стратегии — нулевой эффект на H1.

### Рекомендовано к выполнению

#### Диагностика (Stage 4.3 — diagnostic-only, не менять модели)

1. **PnL-декомпозиция по типу выхода** (Qwen, GLM, codex — частично покрыто gap diagnostics, но нужен точный подсчёт):
   - Суммарный PnL от TP-сделок, SL-сделок, TIMEOUT-сделок
   - Доля SL-убытков среди всех убытков (разделить на breach-FN — стоп пробит вопреки прогнозу, и ambiguous — стоп/TP в одном баре)
   - Доля TIMEOUT-убытков
   - Вывод: какая категория доминирует в потерях

2. **Breach bucket test** (codex, GLM):
   - Разбить сделки по predict_break: <0.10, 0.10–0.20, 0.20–0.30, 0.30–0.40, 0.40–0.50
   - Для каждого bucket: реальная частота пробоя, PF, сделок/год, TP/SL/TIMEOUT %
   - Цель: понять, умеет ли breach-модель ранжировать сделки. Если PF растёт при снижении порога — сигнал есть, нужно ужесточить порог

3. **Fav bucket test** (codex):
   - Разбить сделки по pred_fav / stop_val: >0.7, >1.0, >1.3, >1.5, >2.0
   - Для каждого bucket: реальный fav, доля TP, PF
   - Цель: понять, полезен ли fav как фильтр входа (а не как расчёт TP)

4. **2D-карта breach × fav** (codex):
   - Строки: predict_break bucket. Колонки: pred_fav / stop_val bucket
   - В ячейках: PF, сделок/год, BS_p05 (bootstrap нижняя граница PF)
   - Цель: найти область устойчивой прибыльности. Если даже в лучших ячейках нет PF > 1.15 — дополнительные фильтры не спасут Stage 4

5. **Precision/Recall breach-модели на пороге p=0.4** (Qwen):
   - y_true = реально пробит стоп, y_pred = breach_proba < 0.4 (модель разрешает вход)
   - Precision = доля действительно не пробитых среди вошедших
   - Recall = доля хороших сделок, которые модель не пропустила
   - Если precision < 65% — breach пропускает слишком много пробоев

#### Валидация трейлинг-стопа (Stage 4.4)

6. **Trailing stop на Stage 5.1** (deep):
   - atr_02 (PF=1.655) — готовое улучшение механики выхода. Не заменяет улучшение моделей, но даёт +64% PF без переобучения
   - Для Stage 5.1: тестировать Transformer breach + RF fav + трейлинг-стоп atr_02
   - Ожидаемый PF: 2.0–3.0 при +50–100 bp AUC от Transformer

#### План для Stage 5.0 (Transformer breach-only)

7. **Feature importance ablation для breach** (MiMo):
   - Какие группы признаков несут breach-сигнал: геометрия фракталов, временные признаки, ATR-каналы
   - Ablation: удаление групп → изменение AUC
   - Цель: понять, какие признаки брать в Transformer

8. **Sensitivity PF к breach AUC** (MiMo):
   - Как PF в торговом симуляторе меняется при варьировании breach AUC
   - Целевой AUC для PF > 1.5
   - Цель: установить реалистичный gate для Stage 5.0

---

## Отвергнутые предложения

1. **PF-ratio как мера «использования потенциала» (MiMo: «1.106/8.02 = 14%»)** — PF не аддитивен, отношение PF бессмысленно. Правильная метрика: partial oracle PF vs baseline PF (уже сделано в deep).
   - `brainstorm_mimo.md`

2. **Новый скрипт `benchmark_fractal_stop_stage4_diag.py` (Qwen)** — отдельный скрипт для oracle-ablation избыточен: partial oracle уже реализован в `diagnose_stage4_gap.py` и `oracle_fractal_stop_fav.py`.
   - `brainstorm_Qwen.md`

3. **Гипотеза «tp_fraction=0.7–0.8 улучшит PF» (Qwen)** — опровергнуто экспериментом: все tf > 0.4 ухудшают PF (scan 0.4–2.0 в improve_stage4.py §5.1).
   - `brainstorm_Qwen.md`

4. **4 отдельных скрипта для 4 диагностик (MiMo: `diagnose_breach_vs_fav.py`, `feature_ablation_breach.py`, `breach_threshold_sensitivity.py`, `fav_error_analysis.py`)** — избыточно. Диагностики должны быть в одном скрипте (как `diagnose_stage4_gap.py`) или добавлены в существующий.
   - `brainstorm_mimo.md`

5. **Filter: Consecutive confirmation (Qwen: `fractal0.direction == fractal1.direction`)** — нет доказательств, что последовательные фракталы одного направления улучшают breach-сигнал. Дополнительный фильтр без диагностической базы — data mining.
   - `brainstorm_Qwen.md`

6. **Filter: Time-of-day (Qwen: только London+NY overlap)** — высокий риск календарной подгонки. Без проверки out-of-sample устойчивости по годам неприменим.
   - `brainstorm_Qwen.md`

7. **Filter: Volatility regime — исключение высокой волатильности (Qwen, GLM)** — опровергнуто экспериментом: ATR-фильтр вредит PF (0.927 vs 1.015). Модель лучше работает в волатильные периоды.
   - `brainstorm_Qwen.md`, `brainstorm_GLM.md`

8. **Filter: Fractal strength (Qwen, codex)** — опровергнуто: strong-флаг почти всегда 0, фильтр оставляет 1 сделку из 503. Неприменим.
   - `brainstorm_Qwen.md`, `brainstorm_codex.md`

9. **Quantile fav q=0.3 как cost-sensitive (deep)** — опровергнуто: PF=0.152, 4 сделки. Слишком консервативен при текущих порогах. Возможен при смягчении порогов, но отдельный большой эксперимент.
   - `brainstorm_deep.md`

10. **Fav confidence через ensemble variance (GLM)** — RF не предоставляет variance предсказаний. Для XGBoost-fav — возможно, но XGBoost-fav хуже RF-fav (Stage 4.1).
    - `brainstorm_GLM.md`

11. **Dynamic TP как реальная стратегия (deep)** — НЕ отвергнут как концепция, но текущая реализация («идеальный выход по лучшей цене») — look-ahead. Реалистичная версия — trailing stop atr_02, уже протестирована (PF=1.655).
    - `brainstorm_deep.md`

12. **Гипотеза «breach — главный bottleneck» (MiMo, Qwen)** — опровергнута partial oracle: fav даёт PF=14.72 против breach PF=6.61. Fav в 2.6× важнее breach. Оба критичны из-за синергии (perfect_both=104.88).
    - `brainstorm_mimo.md`, `brainstorm_Qwen.md`

---

**Связанные файлы:**
- `docs/audit/2026-06-14-stage4-brainstorm_codex.md` — источник
- `docs/audit/2026-06-14-stage4-brainstorm_deep.md` — источник (основной)
- `docs/audit/2026-06-14-stage4-brainstorm_GLM.md` — источник
- `docs/audit/2026-06-14-stage4-brainstorm_mimo.md` — источник
- `docs/audit/2026-06-14-stage4-brainstorm_Qwen.md` — источник
- `docs/reports/2026-06-14-stage4-deep-diagnostics.md` — отчёт deep
- `ML/baseline/diagnose_stage4_gap.py` — partial oracle + калибровка
- `ML/baseline/improve_stage4.py` — 8 improvement-экспериментов
- `ML/baseline/trail_stop_stage4.py` — 14 trailing stop стратегий
