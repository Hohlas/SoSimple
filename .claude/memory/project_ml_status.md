---
name: project_ml_status
description: Статус ML: Phase A завершена (PF=1.23), Phase B в работе — triple_barrier модель исправлена, ждёт переобучения
type: project
---

## Текущий статус (2026-03-27)

### Production модель (работает в MT4)
- **Файл**: `ML/checkpoints/transformer_updn_best.pt`
- **Задача**: `regression_updn` — предсказывает [up_12, dn_12, up_24, dn_24, up_48, dn_48]
- **Метрика**: pearson_r ≈ 0.56, PF=1.23 в MT4 бэктесте (XAUUSD H1, 2024)
- **ML сигналы**: `DATA/ml_signals.csv`, формат: `time;signal;ratio;value`

### Phase A результаты (завершена)
- ML_MaxRatio=4.5 убрал 72% SL-bound сделок → PF 0.53→1.23
- ML_CalcRR: `min(log(ratio/MinRatio)+1, cap)`, RR_Mode=1
- ML_ExitEnabled=0 (лучший результат без exit)
- Конфиг: T1=7, ML_ExitEnabled=0, ML_MaxRatio=4.5, ML_RR_Mode=1, ML_RR_Cap=2.5, ML_MinRatio=3.5
- Файл настроек оптимизатора: `MT/tester/opt.set`

### Phase B — triple_barrier (в работе)
**Проблема**: Path-ordering — 92% BOTH_HIT сделок идут SL_FIRST несмотря на max excursion → TP

**Решение**: label_first_barrier_hit() — bar-by-bar scan по H1 OHLC, заменяет сломанный label_triple_barrier()

**Пайплайн данных** (регенерирован 2026-03-27):
- `DATA/Nero_*_labeled.csv` — новые метки {0=SL_FIRST, 0.5=TIMEOUT, 1=TP_FIRST}
- TB метки: buy_sl2_tp3=40% WIN, sell_sl3_tp3=50% WIN (train set)

**Найденные баги (исправлены)**:
1. `label_triple_barrier()` сравнивал нормализованные up_24 с raw ATR — всегда WIN=0. Fix: заменён на `label_first_barrier_hit()` в `processing/label_signals.py`
2. `compute_binary_classification_metrics()` вызывал roc_auc_score с targets {0, 0.5, 1} → зависал. Fix: маска `(yt==0)|(yt==1)` в `ML/utils.py`
3. **TIMEOUT (0.5) soft labels в BCE loss** — модель конвергировала к logit=0 для 16-60% строк → AUC=0.51. Fix (2026-03-27): TIMEOUT→0 в `ML/data_loader.py`
4. **pos_weight bug** — TIMEOUT(0.5) считался как 0.5 в n_pos, сильно искажал веса. Fix (2026-03-27): `n_pos = (y==1).sum()` в `ML/train.py`

**СЛЕДУЮЩИЙ ШАГ**: Очистить кэш (старые файлы с TIMEOUT=0.5 регенерировались упавшим процессом) и запустить переобучение:
```bash
rm DATA/y_train_triple_barrier.npy DATA/y_val_triple_barrier.npy DATA/y_test_triple_barrier.npy
python -m ML.train --task triple_barrier --model transformer --epochs 80 --patience 15 2>&1 | tee /tmp/tb_retrain.log
```
**ВАЖНО**: win rate в логе должен быть ~32% для buy_sl2_tp3 (НЕ 40.2% — это признак старого кэша с TIMEOUT=0.5).

Если AUC > 0.55 → интегрировать в EA через `lib_ML_Signal_TB.mqh` (iSignal=5, уже реализован).
Если AUC ≈ 0.5 → тогда переходить к **asymmetric loss на regression_updn** (Phase B Task 7).

### Phase B план (полный)
Файл: `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`

- Task 1 ✅ Path-ordering analysis → 92% SL_FIRST в BOTH_HIT
- Task 2: Limit order slippage (анализ)
- Task 3: 2025H2 weakness (PF=0.63, причина?)
- Task 4: EA limit entry (Buy Limit at fractal price)
- Task 5 ✅ label_first_barrier_hit() — реализовано
- Task 6: 3H/6H targets (up_3, dn_3, up_6, dn_6)
- Task 7: Asymmetric loss для regression_updn (alpha=2.5 для adverse direction)
- Task 8: Retrain triple_barrier → **текущий шаг**
- Task 9: MT4 тест с iSignal=5

### Ключевые файлы
- `ML/train.py` — обучение, поддерживает `--task triple_barrier`
- `ML/data_loader.py` — загрузка данных, TIMEOUT→LOSS fix добавлен
- `ML/utils.py` — метрики, TIMEOUT exclusion в AUC добавлен
- `ML/losses.py` — FocalLoss, HuberLoss, AsymmetricLoss
- `processing/label_signals.py` — label_first_barrier_hit()
- `processing/label_main.py` — main pipeline, --ohlc аргумент
- `MT/MQL4/Include/lib_ML_Signal_TB.mqh` — EA handler для TB формата
- `MT/MQL4/Include/lib_ML_Signal.mqh` — ML_CalcRR, ML_Exit, ML_MaxRatio
- `statistics/analyze_path_ordering.py` — path ordering analysis tool

**Why:** Нужен полный контекст для продолжения в следующем чате.
**How to apply:** Прочитай этот файл в начале сессии перед продолжением работы.
