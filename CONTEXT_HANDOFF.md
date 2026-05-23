# Context Handoff

Дата: 2026-05-21.

## Текущий этап

Завершён Transformer Encoder Direction experiment — проверка трёх семейств таргетов (TB, Reg, Trail) на frozen encoder признаках.

### Результаты

| Семейство | Лучший val PF | Сделок | Gate A (>=1.5) |
|-----------|-------------|--------|-----------------|
| TB (16 комбо) | 1.35 BUY | 73 | провален |
| Reg (2 комбо) | 1.21 SELL | 41 | провален |
| Trail (6 комбо) | 2.41 BUY | 58 | пройден (0.6% util) |

**Вердикт**: Fractal features Transformer-энкодера не несут direction-сигнала. Trail даёт иллюзию на 58 сделках, но не масштабируется. Fine-tune Transformer хуже frozen RF на всех комбинациях.

### Ключевые находки

1. 32-dim CLS token признаки (front/back/impulse/цена) не коррелируют с будущим направлением
2. Очистка таргетов от contamination (OHLC-derived) снизила PF до ~1.0 — честный результат
3. SeqPF — невалидная метрика: shuffle-тест показал разброс 0.68–4728 при PF=1.10
4. Trail — единственное семейство с PF > 1.5, но на 0.6% utilisation
5. Frozen RF > Transformer fine-tune: энкодер не дообучается на малом датасете

### Git

Ветка: `DeepSeek-direct-direction-results`.

### Созданные/изменённые файлы

- `ML/prepare_raw_features.py` — raw up/dn из OHLC (+1000 колонок)
- `ML/transformer_direction_train.py` — DataLoader, frozen RF grid, fine-tune loop
- `DATA/raw_features_for_direction.pkl` — 1544 MB, 3223 колонки
- `ML/reports/transformer_direction/` — все артефакты (prepared_features, targets_*.npz, validation_grid_frozen.json, feature_statistics.json)
- `docs/reports/2026-05-21-transformer-direction.md` — финальный отчёт

## Открытые вопросы

1. **Direction prediction из fractal features — тупик.** Нужны признаки другого типа (макро, альтернативные данные)
2. **Entry_path_v1_live_safe** остаётся лучшим production-кандидатом (не-direction подход, Test PF ~1.4)
3. **Куда дальше?** Принять ограничения fractal features и либо: (а) искать direction signal в других данных, (б) фокусироваться на execution/risk management, (в) улучшать существующий entry_path подход

## Следующий шаг

Обсудить стратегию: признать тупик direct direction и выбрать новое направление исследований.
