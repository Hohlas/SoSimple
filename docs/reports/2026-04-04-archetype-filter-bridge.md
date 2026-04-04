# Archetype × Filter Bridge — Предсказывают ли Variant 4 фильтры winning архетип?

> **Date**: 2026-04-04
> **Status**: Completed
> **Goal**: Проверить, коррелируют ли два holdout-подтверждённых фильтра Variant 4 (`fav_3_vs_12 <= 0.653`, `ratio_3_vs_12 > 4.751`) с принадлежностью к winning архетипу (`flat_or_noisy_drift`), и определить, нужен ли pullback entry поверх фильтра
> **Related reports**: `2026-04-04-signal-path-atlas-readout.md`, `2026-04-04-signal-quality-filter.md`
> **Data source**: atlas pipeline (`API/signal_path_atlas.py`)

## Context

Atlas readout (2026-04-04) п��казал двумодальную структуру: 64% failure vs 36% flat_or_noisy_drift. Оба архетипа реплицированы на holdout. Winning архетип характеризуется минимальным adverse excursion (adv Q50 = 0.48 ATR) — эти сигналы почти не откатываются.

Variant 4 (2026-04-04) дал два holdout-подтверждённых фильтра, но их связь с архетипами не была проверена. Этот этап закрывает этот пробел.

## Методология

1. Загружены данные через atlas pipeline (те же split dates).
2. Архетипы построены на discovery (k-means → 2 кластера после merge), holdout-сигналы классифицированы через fitted модель.
3. Каждый фильтр применён к discovery и holdout, подсчитаны пропорции winning/failure.
4. Market и pullback entry оценены через TP/SL machinery (`build_variant3_scenario_outcomes`, SL=5, TP=50).
5. Fill rate pullback разбит по архетипам.

Discovery: 1752 сигналов. Holdout: 851 сигнал.

## 1. Фильтр × Архетип: пропорции

| Sample | Filter | N | N winning | % winning | N failure | % failure |
|---|---|---:|---:|---:|---:|---:|
| Discovery | Без фильтра | 1752 | 627 | 35.8 | 1125 | 64.2 |
| Discovery | `fav_3_vs_12 <= 0.653` | 194 | 77 | 39.7 | 117 | 60.3 |
| Discovery | `ratio_3_vs_12 > 4.751` | 442 | 172 | 38.9 | 270 | 61.1 |
| **Holdout** | **Без фильтра** | **851** | **318** | **37.4** | **533** | **62.6** |
| **Holdout** | **`fav_3_vs_12 <= 0.653`** | **84** | **37** | **44.0** | **47** | **56.0** |
| **Holdout** | **`ratio_3_vs_12 > 4.751`** | **176** | **59** | **33.5** | **117** | **66.5** |

**Ключевые находки:**
- `fav_3_vs_12 <= 0.653` повышает долю winning архетипа: +3.9 pp на discovery, **+6.6 pp на holdout** (37.4% → 44.0%).
- `ratio_3_vs_12 > 4.751` **НЕ повышает** долю winning архетипа: +3.1 pp на discovery, **-3.9 pp на holdout** (37.4% → 33.5%).
- Оба фильтра пересекаются на 8 (disc) / 4 (hold) сигналах — практически ортогональны.

## 2. Фильтр × Entry: holdout performance

Для справедливого сравнения: market PF через TP/SL (SL=5, TP=50), pullback PF через ту же TP/SL модель.

| Filter | Entry | N filled | % winning | PF (TP/SL) |
|---|---|---:|---:|---:|
| Без фильтра | market | 850 | 37.4 | 1.04 |
| Без фильтра | pullback 1ATR | 514 | 12.6 | 1.43 |
| Без фильтра | pullback 3ATR | 148 | 2.7 | 2.51 |
| `fav_3_vs_12 <= 0.653` | market | 84 | 44.0 | 1.78 |
| `fav_3_vs_12 <= 0.653` | pullback 1ATR | 43 | 23.3 | 2.64 |
| `fav_3_vs_12 <= 0.653` | pullback 3ATR | 11 | 0.0 | 1.66 |
| `ratio_3_vs_12 > 4.751` | market | 176 | 33.5 | 0.81 |
| `ratio_3_vs_12 > 4.751` | pullback 1ATR | 103 | 7.8 | 1.73 |
| `ratio_3_vs_12 > 4.751` | pullback 3ATR | 25 | 0.0 | 3.79 |

**Примечания к PF.**
- Market PF считается через TP/SL-модель (SL=5, TP=50) для сопоставимости с pullback. Это совпадает с Variant 4 report: baseline 1.04 ≈ 1.05, fav filter 1.78 = 1.78.
- Pullback PF также чер��з TP/SL.

## 3. Fill rate pullback по архетипам (holdout)

| Filter | Archetype | Pullback | N total | N filled | Fill rate % | PF |
|---|---|---|---:|---:|---:|---:|
| Без фильтра | winning | 1ATR | 318 | 65 | 20.4 | 8.46 |
| Без фильтра | failure | 1ATR | 533 | 449 | 84.2 | 0.87 |
| Без фильтра | winning | 3ATR | 318 | 4 | 1.3 | 25.30 |
| Без фильтра | failure | 3ATR | 533 | 144 | 27.0 | 2.27 |
| `fav_3_vs_12 <= 0.653` | winning | 1ATR | 37 | 10 | 27.0 | 15.40 |
| `fav_3_vs_12 <= 0.653` | failure | 1ATR | 47 | 33 | 70.2 | 1.09 |
| `fav_3_vs_12 <= 0.653` | winning | 3ATR | 37 | 0 | 0.0 | — |
| `fav_3_vs_12 <= 0.653` | failure | 3ATR | 47 | 11 | 23.4 | 1.66 |
| `ratio_3_vs_12 > 4.751` | winning | 1ATR | 59 | 8 | 13.6 | 14.98 |
| `ratio_3_vs_12 > 4.751` | failure | 1ATR | 117 | 95 | 81.2 | 1.17 |
| `ratio_3_vs_12 > 4.751` | winning | 3ATR | 59 | 0 | 0.0 | — |
| `ratio_3_vs_12 > 4.751` | failure | 3ATR | 117 | 25 | 21.4 | 3.79 |

**Это ключевая таблица.** Она объясняет механику pullback entry на архетипном уровне:

- **Winning сигналы почти не заполняются на pullback.** Fill rate winning + 1ATR = 20.4% (без фильтра), 27.0% (fav filter), 13.6% (ratio filter). Fill rate winning + 3ATR = 1.3% (без фильтра), **0%** с обоими фильтрами.
- **Failure сигналы заполняются массово.** Fill rate failure + 1ATR = 84.2%, failure + 3ATR = 27.0%.
- **PF pullback на winning = экстремально высокий** (8.46–25.30), но на мизерных N.
- **PF pullback на failure = умеренный** (0.87–3.79) — это mechanical price improvement.
- **Pullback 3ATR + любой фильтр = 0 winning fills.** Все 25 fills от `ratio_3_vs_12 > 4.751 + 3ATR` — это failure сигналы.

## 4. Holdout archetype profiles (подтверждение стабильности)

| Archetype | N | signed_ret_12 Q50 | fav_12 Q50 | adv_12 Q50 | adverse_first 1ATR |
|---|---:|---:|---:|---:|---:|
| flat_or_noisy_drift | 318 | +1.881 | 3.102 | 0.553 | 11.6% |
| failure_or_adverse_continuation | 533 | -0.875 | 0.804 | 2.034 | 67.7% |

Профили стабильны relative to discovery (readout report). Winning adv Q50 = 0.553 ATR, что объясняет нулевой fill rate на 3ATR.

## Главные выводы

### 1. `fav_3_vs_12 <= 0.653` — единственный фильтр, коррелирующий с winning архетипом

На holdout: 44.0% winning vs 37.4% baseline (+6.6 pp). Эффект воспроизводим на обоих samples (disc: +3.9 pp, hold: +6.6 pp). Фильтр не идеален (56% отфильтрованных всё равно failure), но это лучшее из доступного.

`ratio_3_vs_12 > 4.751` на holdout **ухудшает** архетипный состав (33.5% winning — ниже baseline). Его PF-эффект (1.73 с pullback 1ATR) не связан с обогащением winning архетипа; это чисто mechanical + другие mechanisms.

### 2. Pullback entry на отфильтрованных winning сигналах практически бесполезен

- При 1ATR: fill rate 27% (fav filter) / 13.6% (ratio filter) — теряем ≥70% winning сигналов.
- При 3ATR: fill rate **0%** с обоими фильтрами.
- Winning сигналы не откатываются (adv Q50 = 0.55 ATR). Pullback на них — структурно неработоспособный механизм.

### 3. Pullback PF boost идёт от failure сигналов, не от winning

Pullback (даже без фильтра) заполняет 84% failure vs 20% winning. Его PF boost — это **mechanical price improvement на failure сигналах + extreme PF на единичных winning fills**. Это хрупкая конструкция.

### 4. Оптимальная комбинация: `fav_3_vs_12 <= 0.653` + market entry

| Вариант | N (hold) | % winning | PF (TP/SL) |
|---|---:|---:|---:|
| Baseline + market | 850 | 37.4 | 1.04 |
| `fav_3_vs_12 <= 0.653` + market | 84 | 44.0 | 1.78 |
| `fav_3_vs_12 <= 0.653` + pullback 1ATR | 43 | 23.3 | 2.64 |
| `ratio_3_vs_12 > 4.751` + market | 176 | 33.5 | 0.81 |
| `ratio_3_vs_12 > 4.751` + pullback 1ATR | 103 | 7.8 | 1.73 |

`fav_3_vs_12 <= 0.653 + market` даёт:
- **PF = 1.78** — существенно выше baseline (1.04) и ratio market (0.81)
- **N = 84** — sufficient для среднесрочной оценки, но не large-sample
- **44% winning** — лучший архетипный состав среди всех вариантов
- **Pullback поверх этого фильтра ухудшает winning%** (с 44% до 23.3%) при повышении PF (2.64) за счёт mechanical improvement — это trade-off: больше PF, меньше winning content, меньше N

### 5. Нужен ли pullback вообще?

**Ответ: нет, если фильтр `fav_3_vs_12 <= 0.653` используется.**

- Market entry с этим фильтром даёт PF=1.78 на 84 trades — это уже profitable без pullback.
- Pullback дал бы PF=2.64 на 43 trades, но ценой потери ~50% volume и **снижения winning archetype share** с 44% до 23%.
- Pullback 3ATR вообще не заполняет winning сигналы (0 fills).
- Pullback имеет смысл только как standalone mechanical improver (без фильтра), но тогда его edge не archetype-driven.

**Если `ratio_3_vs_12 > 4.751` используется отдельно:**
- Market entry не работает (PF=0.81)
- Pullback 1ATR спасает PF до 1.73, но это механический эффект, а не archetype-driven
- Этот фильтр **не рекомендуется** как primary filter для archetype selection

## Limitations / Open Questions

1. **N=84 для `fav_3_vs_12 + market`** — medium-sample. Достаточен для directional вывода, но для точной PF оценки нужно больше данных.
2. **Фильтр `fav_3_vs_12 <= 0.653` не идеален** — 56% отфильтрованных сигналов остаются failure. Это enrichment, не separation.
3. **Почему `ratio_3_vs_12 > 4.751` улучшает PF на pullback, не обогащая winning архетип?** Возможный механизм: фильтр убирает самые быстро-разворачивающиеся failures (которые уходят «против» сразу и глубоко), оставляя «медленные» failures, на которых pullback limit fill + mechanical price improvement дают net positive PnL. Это не archetype selection, а severity filtering внутри failure class.
4. **Year-stability `fav_3_vs_12`** в Variant 4 показал деградацию 2022→2024 с recovery в holdout. Устойчивость на более длинных выборках не доказана.
5. **Оба фильтра ортогональны** (пересечение 8/4 сигнала). Комбинация не добавляет ценности.

## Verification

```bash
source .venv/bin/activate
# Atlas pipeline test
python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas
# Analysis scripts
python /tmp/archetype_filter_analysis.py
python /tmp/archetype_filter_supplement.py
```

## Related Materials

- [2026-04-04-signal-path-atlas-readout.md](2026-04-04-signal-path-atlas-readout.md) — atlas readout с архетипами
- [2026-04-04-signal-quality-filter.md](2026-04-04-signal-quality-filter.md) — Variant 4 фильтры
- `API/signal_path_atlas.py` — atlas pipeline
- `/tmp/archetype_filter_analysis.py` — основной аналитический скрипт
