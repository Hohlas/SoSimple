# ML Signal Integration: Python → CSV → MQL4

> **Назначение**: Операционный гайд по генерации ML-сигналов и запуску в MT4 Strategy Tester.
> Алгоритм торговых решений (ML_TRADE, INPUT, OUTPUT) описан в [trading_strategy.md](trading_strategy.md).

## Почему файловый обмен

WebRequest не работает в Strategy Tester и ненадёжен под Wine (error 5200) — вместо него используется предрассчитанный CSV.

---

## 1. Генерация сигналов (Python)

**Скрипт**: [generate_signals.py](../../API/generate_signals.py)

```bash
source ~/git/SoSimple/.venv/bin/activate
python -m API.generate_signals                           # дефолт: transformer, H12, θ=2.665
python -m API.generate_signals --horizon 24 --theta 3.0  # кастомные параметры
python -m API.generate_signals --conformal               # с Conformal Prediction фильтром
```

**Что делает**:
1. Загружает чекпоинт `ML/checkpoints/transformer_updn_best.pt` + параметры Optuna
2. Прогоняет все три датасета (train, validation, test) через модель
3. Для каждой строки: `ratio_up = pred_up / pred_dn`
   - `ratio_up > θ` → signal = **1** (BUY)
   - `ratio_dn > θ` → signal = **-1** (SELL)
   - иначе → signal = **0** (FLAT)
4. Записывает `MT/MQL4/Files/ml_signals.csv` (~58K строк, 2004–2026)

**Формат CSV** (`;` разделитель):
```
time;signal;pred_up;pred_dn;ratio_up;ratio_dn
2023.01.03 04:00;1;0.477;0.045;10.71;0.09
2023.01.03 10:00;-1;0.077;0.476;0.16;6.16
2023.01.03 11:00;0;0.134;0.130;1.03;0.97
```

> [!IMPORTANT]
> `time` берётся из исходного Nero CSV (формат `YYYY.MM.DD HH:MM`), совпадает с `Time[bar]` в MT4.

---

## 2. Запуск в Strategy Tester

```bash
# 1. Сгенерировать сигналы
python -m API.generate_signals

# 2. Скопировать CSV в каталог тестера (Wine/Linux)
cp MT/MQL4/Files/ml_signals.csv MT/tester/files # MT/MQL4/Files - файлы для реалтайм торговли; MT/tester/files - файлы для тестера и оптимизации

# 3. Скомпилировать $o$imple.mq4 в MetaEditor (F7)
# 4. Запустить тест: XAUUSD, H1, параметр iSignal=3
```

> [!WARNING]
> Strategy Tester читает файлы из `tester/files/`, а НЕ из `MQL4/Files/`.
> При обновлении CSV нужно копировать в обе директории (для тестера и для live).

### Ключевые параметры эксперта для ML

| Параметр | Значение | Описание |
|----------|----------|----------|
| `iSignal` | 3 | Включает ML_TRADE() |
| `ML_MinRatio` | 5.0 | Минимальный ratio для открытия (в lib_ML_Signal.mqh) |
| `Stp` | 3 | Стоп = 1.6×ATR |
| `Prf` | 3 | Тейк = 1.6×ATR (R:R = 1:1) |

---

## 3. Зависимости

| Компонент | Зависит от |
|-----------|-----------|
| `generate_signals.py` | `ML/data_loader.py`, `ML/models/`, `ML/checkpoints/transformer_updn_best.pt` |
| `lib_ML_Signal.mqh` | `MAIN.mqh` (класс EXPERT), `ml_signals.csv` |
| `ml_signals.csv` | `DATA/Nero_{train,validation,test}_labeled.csv` |
