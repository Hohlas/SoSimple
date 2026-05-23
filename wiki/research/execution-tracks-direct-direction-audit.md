---
last_updated: 2026-05-21
sources: 3
status: completed
---

# Execution Tracks: Direct Direction + Audit + Rebuild (05-15 - 05-21)

> Direct-direction ветка прошла полный цикл: эксперименты → аудит → исправление ошибок → честный отрицательный вердикт.

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

- Сохранился ли BUY edge после raw/current-row feature rebuild? **Нет**: test win rate 50.5% (случайный).
- Можно ли восстановить SELL без test tuning? Не проверялось (BUY-only только).
- Нужен ли balanced BUY/SELL кандидат или честный BUY-only product decision лучше слабого симметричного решения? BUY-only — правильный выбор, но и он не работает.
- Если corrected validation не даст PF/SeqPF > 2.0, следующий безопасный шаг — forward data collection, а не дальнейшая historical подгонка. **Подтверждено**: validation PF=1.77, но test PF=0.99.

### Direct Direction Rebuild (05-21)

Исполнение промпта `docs/audit/2026-05-18-redo-prompt.md`: полный rebuild с исправлением всех 6 ошибок аудита.

| Phase | Что сделано | Gate |
|-------|------------|------|
| Phase 0 | Извлечение сырых признаков из OHLC (raw prices) | Passed |
| Phase A | BUY-only RF, directional close target, 54 features | Passed (val PF=1.77, SeqPF=1.99) |
| Phase B | +Regime (trend_strength, vol_regime) + direction-specific features | Passed (но хуже A) |
| Phase D | Frozen test (Phase A winner, thr=0.0, buy_thr=0.6) | **Failed** (Test PF=0.99) |

**Исправленные ошибки**:
1. Feature-in-target contamination: OHLC raw prices вместо normalized CSV
2. Неверные единицы расстояния: `(raw_price_i − raw_price_0) / raw_ATR`
3. A/C targets: directional close из OHLC вместо normalized up/dn
4. Winner protocol: negative_years=0 gate, сортировка по sequential PF
5. SELL anti-signal: полный отказ от SELL
6. Trailing-profit target: заменён на directional close

**Итог**: Fractal-level признаки (front/back/impulse) не несут direction-сигнала. Test BUY win rate = 50.5% (статистически неотличимо от случайного). Sequential PF=1.96 на 52 сделках — положительный, но недостаточный для production.

**Рекомендация**: не деплоить fractal-level direct direction. Следующий шаг — Transformer encoder как feature extractor, или альтернативный подход (score gate + direction resolver).

## Источники

- [docs/reports/2026-05-15-direct-direction-improvement.md](../../docs/reports/2026-05-15-direct-direction-improvement.md)
- [docs/audit/2026-05-18-codex-direct-direction-chain-audit.md](../../docs/audit/2026-05-18-codex-direct-direction-chain-audit.md)
- [docs/reports/2026-05-18-direct-direction-rebuild.md](../../docs/reports/2026-05-18-direct-direction-rebuild.md)
