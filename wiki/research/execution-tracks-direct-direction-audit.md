---
last_updated: 2026-05-18
sources: 2
status: active
---

# Execution Tracks: Direct Direction + Chain Audit (05-15 - 05-18)

> Direct-direction ветка дала weak-positive frozen result, но аудит показал, что её нельзя продолжать тюнингом порогов: сначала нужен rebuild feature/target contract.

## Хронология

### Direct Direction Improvement (05-15)

Проверялась замена фиксированного `fractal0.direction` на модель, которая сама
выдаёт `SELL / SKIP / BUY` или две независимые binary-модели.

| Experiment | Result |
|---|---:|
| 3-class RF/HGB/LR | validation PF `1.01-1.11`, gate fail |
| nearest-k / geometry / zones | no stable uplift |
| Binary RF validation | PF `1.25`, SeqPF `1.30` |
| Binary RF frozen test | PF `1.226`, SeqPF `1.537` |
| Frozen BUY | PF `1.904` |
| Frozen SELL | PF `0.618` |

Вывод 05-15 был ограниченно положительным: binary RF лучше direct-bar baseline,
но SELL направление провалено, а годы `2022` и `2023` отрицательные.

### Chain Audit (05-18)

Независимый аудит проверил всю цепочку, а не только пороги.

Доказанные проблемы:

- `processing.normalize.normalize_rowwise()` нормализует фрактальные `Up/Dn` в
  одном пуле с top-level target columns `up_3..dn_48`; минимальная perturbation
  проверка показала, что изменение только top-level targets меняет
  нормализованные `fractal1.Up/Dn`;
- `ML.fractal_level_feature_builder` считает distance/ATR из уже
  min-max-normalized `price` и raw `ATR`, поэтому геометрия уровня имеет
  неверные единицы;
- Target A/C названы `_atr`, но строятся из normalized split `up/dn`, а не из
  raw `up/dn / ATR`;
- `summary.json` E1 выбирает HGB one-sided winner, а frozen test был запущен
  для RF balanced config; selection layer не воспроизводит формальный gate;
- E5 score-direction имеет асимметричный BUY-first selection, поэтому вывод о
  disappearing SELL при высоких thresholds не считается доказанным.

## Выводы

Текущий direct-direction результат нельзя улучшать косметическим threshold
tuning. Приоритет:

1. Разделить `feature_source`, `target_source`, `diagnostic_source`.
2. Строить model inputs из raw/current-row строк без target-dependent
   normalization.
3. Пересчитать distance features в raw price / raw ATR.
4. Пересчитать A/C targets в корректных ATR units или заменить OHLC-derived
   targets.
5. Исправить winner selection и side-specific gates.
6. Запустить validation-only rebuild; test только один раз для frozen winner.

## Открытые вопросы

- Сохранится ли BUY edge после raw/current-row feature rebuild?
- Можно ли восстановить SELL без test tuning?
- Нужен ли balanced BUY/SELL кандидат или честный BUY-only product decision
  лучше слабого симметричного решения?
- Если corrected validation не даст PF/SeqPF > 2.0, следующий безопасный шаг -
  forward data collection, а не дальнейшая historical подгонка.

## Источники

- [docs/reports/2026-05-15-direct-direction-improvement.md](../../docs/reports/2026-05-15-direct-direction-improvement.md)
- [docs/audit/2026-05-18-codex-direct-direction-chain-audit.md](../../docs/audit/2026-05-18-codex-direct-direction-chain-audit.md)
