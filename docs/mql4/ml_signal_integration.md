# ML Signal Integration: Python → CSV → MQL4

## Назначение
Файловый обмен ML-сигналами между Python и MT4 Strategy Tester.  
WebRequest не работает в тестере и ненадёжен под Wine — вместо него используется предрассчитанный CSV.

## Архитектура

```
Python (предрасчёт)              MQL4 (тестер/торговля)
───────────────────              ──────────────────────
DATA/Nero_*_labeled.csv ──┐      ┌── MQL4/Files/ml_signals.csv
 + transformer_updn_best  ├→ → →│
 + θ = 2.665              ┘      └── MAIN.mqh → ML_TRADE() → OPEN_BUY/SELL
```

## Компоненты

### 1. Python: генерация сигналов

**Скрипт**: [generate_signals.py](../../API/generate_signals.py)

```bash
source .venv/bin/activate
python -m API.generate_signals                    # дефолт: transformer, H12, θ=2.665
python -m API.generate_signals --horizon 24 --theta 3.0  # кастомные параметры
```

**Алгоритм**:
1. Загружает чекпоинт модели (`transformer_updn_best.pt`) и параметры Optuna
2. Прогоняет все три датасета (train, validation, test) через модель
3. Для каждой строки вычисляет `ratio_up = pred_up / pred_dn`:
   - `ratio_up > θ` → signal = **1** (BUY)
   - `ratio_dn > θ` → signal = **-1** (SELL)
   - иначе → signal = **0** (FLAT)
4. Записывает CSV в `MT/MQL4/Files/ml_signals.csv`

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

### 2. MQL4: библиотека чтения сигналов

**Файл**: [lib_ML_Signal.mqh](../../MT/MQL4/Include/lib_ML_Signal.mqh)

| Функция | Описание |
|---------|----------|
| `ML_INIT()` | Загружает `ml_signals.csv` в глобальные массивы. Вызывается лениво при первом `ML_TRADE()` |
| `ML_FindSignal(datetime)` | Бинарный поиск сигнала по времени бара. Возвращает индекс или -1 |
| `EXPERT::ML_TRADE()` | Метод класса EXPERT. Ищет сигнал для `Time[bar]`, вызывает `OPEN_BUY`/`OPEN_SELL` |

**Интеграция в MAIN.mqh** (3 изменения):
- Строка 51: `void ML_TRADE()` — объявление метода в классе `EXPERT`
- Строка 110: `#include <lib_ML_Signal.mqh>`
- Строка 121: `ML_TRADE()` — вызов после `COUNT()` в `EXPERT::MAIN()`

```
EXPERT::MAIN() {
    EXPERT_SET() → ORDER_CHECK() → TIMER() → COUNT()
                                                 ↓
                                            ML_TRADE()  ← ищет сигнал по Time[bar]
                                                 ↓
    INPUT() → OUTPUT() → TRAILING_STOP() → MODIFY() → ORDERS_SET()
}
```

> [!NOTE]
> `ML_TRADE()` работает **параллельно** с `INPUT()`. Обе функции могут открывать сделки.
> Для тестирования **только ML** — закомментируйте вызов `INPUT()` в MAIN.mqh.

---

### 3. Подготовка к тесту в Strategy Tester

```bash
# 1. Сгенерировать сигналы
python -m API.generate_signals

# 2. Скопировать CSV в каталог тестера (Wine/Linux)
cp MT/MQL4/Files/ml_signals.csv ~/.mt4/drive_c/Program\ Files\ \(x86\)/MetaTrader\ 4/tester/files/

# 3. Скомпилировать $o$imple.mq4 в MetaEditor (F7)
# 4. Запустить тест: XAUUSD, H1
```

> [!WARNING]
> Strategy Tester читает файлы из `tester/files/`, а НЕ из `MQL4/Files/`.
> При обновлении CSV нужно копировать в обе директории (для тестера и для live).

---

## Зависимости

| Компонент | Зависит от |
|-----------|-----------|
| `generate_signals.py` | `ML/data_loader.py`, `ML/models/`, `ML/checkpoints/transformer_updn_best.pt` |
| `lib_ML_Signal.mqh` | `MAIN.mqh` (класс EXPERT), `ml_signals.csv` |
| `ml_signals.csv` | `DATA/Nero_{train,validation,test}_labeled.csv` |
