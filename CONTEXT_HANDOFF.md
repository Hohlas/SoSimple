# Context Handoff

Дата: 2026-05-21.

## Текущий этап

Завершён Direct Direction Rebuild (Phase 0 → A → B → D) — переделка E0–E5 с исправлением 6 критических ошибок аудита.
Phase C (Transformer feature extractor) пропущен.

### Результаты

| Фаза | Best PF (val) | Best Seq PF (val) | Test PF | Test Seq PF | Gate |
|------|---------------|-------------------|---------|-------------|------|
| Phase 0 | — | — | — | — | Passed |
| Phase A (BUY-only RF) | 1.77 | 1.99 | — | — | Passed |
| Phase B (+regime) | 1.64 | 2.22 | — | — | Passed (но хуже A) |
| Phase D (frozen test) | — | — | 0.99 | 1.96 | **Failed** |

**Вердикт**: Fractal-level RF на directional close не даёт статистически значимого сигнала (test win rate 50.5%). Sequential PF=1.96 на 52 сделках — положительный, но число сделок недостаточно.

### Ключевые находки

1. Fractal-level признаки (front/back/impulse) не несут direction-специфичной информации
2. Regime-признаки (trend_strength_50, vol_regime_ratio) — top importance, но не улучшают test
3. Validation PF не переносится на test из-за regime shift (2004–2017 vs 2022–2026)
4. BUY-only win rate ~50% — модель не лучше случайного выбора

### Что исправлено

Все 6 критических ошибок аудита:
- Feature-in-target contamination ✅
- Неверные единицы расстояния ✅
- A/C targets из normalized up/dn ✅
- Winner selection protocol ✅
- SELL anti-signal (отказ от SELL) ✅
- Шумный trailing-profit таргет ✅

## Git

Локальная ветка: `improve-direct-direction-results`.

## Созданные файлы

- `ML/prepare_raw_features.py` — Phase 0 (извлечение сырых признаков)
- `ML/benchmark_buy_only_direction.py` — Phase A/B/D (BUY-only RF benchmark)
- `DATA/raw_features_for_direction.pkl` — артефакт Phase 0 (1060 MB)

Артефакты:
- `ML/reports/buy_only_direction_rebuild/` — Phase A/B/D результаты
- `docs/reports/2026-05-18-direct-direction-rebuild.md` — финальный отчёт

## Открытые вопросы

1. **Нет direction-сигнала в fractal-level features** — основной вывод. Признаки front/back/impulse описывают структуру вокруг уровня, но не «куда пойдёт цена».
2. **Transformer encoder (Phase C) не проверен** — может дать нелинейные взаимодействия.
3. **Entry_path_v1_live_safe + A @ 7.5%** — остаётся лучшим production-кандидатом (Test PF ≈ 1.4, 41 seq сделка).
4. **Альтернативный таргет** (фиксированный SL/TP) — не проверен в этом цикле.

## Следующий шаг

1. Не деплоить fractal-level direct direction model (PF < 1.0).
2. Исследовать Transformer encoder как feature extractor (Phase C) или альтернативный подход (score gate + direction resolver).
3. Либо принять entry_path_v1_live_safe как текущий production baseline и переключиться на другие задачи.
