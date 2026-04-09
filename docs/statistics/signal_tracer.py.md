# signal_tracer.py — Trade-Level Reconciliation

> **Версия**: v2.4 (2026-04-09)
> **Назначение**: Диагностика расхождения между Python и MT4 для двух ML-треков: legacy `regression_updn` и `triple_barrier`
> **Тип**: Инструмент анализа, 3 режима работы

---

## Обзор

`statistics/signal_tracer.py` сейчас умеет разбирать **два execution track**:

- **legacy track**: `ml_signals.csv` с полями `pred_up / pred_dn / ratio_up / ratio_dn`, где SL/TP восстанавливаются по формуле legacy runtime из `lib_ML_Signal_back.mqh`;
- **TB track**: `ml_signals_tb.csv` с полями `sl_atr / tp_atr / prob / ev`, где исход сделки сравнивается с path-ordered TB labels из `DATA/Nero_*_labeled.csv`.

Важно:

- текущий активный `lib_ML_Signal.mqh` уже работает в другом режиме: прямое исполнение parity-check CSV;
- строки `MLP BUY / SELL / CLOSE / SKIP` этим tracer пока **не разбираются**;
- для старого `regression_updn` нужно ориентироваться именно на backup-файл `lib_ML_Signal_back.mqh`.

Это означает, что скрипт покрывает исторический legacy runtime и TB runtime, но не новый прямой `MLP`-контур.

Важно: сам tracer готов к TB runtime-сверке, но полноценный verdict всё равно требует **свежий MT4 tester log**.

---

## Quick Start

```bash
# Single-trace: один сигнал из legacy CSV
python statistics/signal_tracer.py --time "2023.01.03 04:00"

# Batch: top-N legacy сигналов по ratio
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0 --csv-out batch.csv

# From-Log: все legacy сделки из MT4 лога
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --csv-out all_trades.csv

# From-Log: TB сделки из MT4 лога
python statistics/signal_tracer.py \
  --from-log MT/tester/logs/20260408_tb.log \
  --signals MT/MQL4/Files/ml_signals_tb.csv \
  --csv-out tb_reconciliation.csv
```

---

## Поддерживаемые треки

### 1. Legacy `regression_updn`

Используются:

- `MT/MQL4/Files/ml_signals.csv`
- `DATA/Nero_*_labeled.csv`
- `DATA/Nero_*_updn_params.npy`
- `MT/tester/$o$imple.ini`

Что делает tracer:

- восстанавливает SL/TP по формуле legacy runtime из `lib_ML_Signal_back.mqh`;
- денормализует `up_12 / dn_12`;
- классифицирует outcome как:
  - `TP_CLEAR`
  - `SL_CLEAR`
  - `BOTH_HIT`
  - `TIMEOUT`
- сравнивает формульные уровни с фактическими уровнями MT4 из лога.

Этот режим полезен для поиска причин расхождения legacy Python PF и MT4 PF.

### 2. `triple_barrier`

Используются:

- `MT/MQL4/Files/ml_signals_tb.csv`
- `DATA/Nero_*_labeled.csv`
- MT4 log строки вида:
  - `TB BUY prob=0.731 ev=3.42 SL=2.0ATR TP=6.0ATR Val=... Stp=... Prf=... ATR=... bar=2025.01.03 04:00`
  - `TB SELL ...`

Что делает tracer:

- читает `prob`, `ev`, `sl_atr`, `tp_atr` напрямую из TB CSV или TB log line;
- восстанавливает target name (`buy_sl2_tp3`, `sell_sl3_tp6` и т.д.);
- находит соответствующий TB label в `DATA/Nero_*_labeled.csv`;
- классифицирует outcome как:
  - `TP_FIRST` (`1.0`)
  - `SL_FIRST` (`0.0`)
  - `TIMEOUT` (`0.5`)
  - `UNKNOWN`
- сравнивает TB ATR-levels из CSV с фактическими ATR-levels MT4.

Этот режим нужен для честной runtime-сверки уже после validation-first freeze.

---

## Три режима работы

### 1. `--time`

Показывает полное dossier по одному времени сигнала.

Подходит для:

- разбора конкретного MT4 кейса;
- проверки того, какой именно target выбрал TB;
- просмотра raw diagnostics (`prob`, `ev`, `sl_atr`, `tp_atr`).

### 2. `--batch`

Пакетный режим для top-N сигналов по `ratio`.

Важно:

- этот режим по-прежнему **legacy-centric**, потому что фильтрация основана на `ratio`;
- для TB основным режимом остаётся `--from-log`.

### 3. `--from-log`

Главный reconciliation mode.

Что происходит:

1. Парсится MT4 лог.
2. Для каждого `bar_time` ищется строка сигнала в CSV.
3. Для каждой сделки строится dossier:
   - prediction layer;
   - labeled ground truth;
   - фактические уровни и результат MT4;
   - deltas между Python и MT4.
4. По желанию пишется `--csv-out`.

`--from-log` понимает и legacy строки `ML BUY/SELL ...`, и TB строки `TB BUY/SELL ...`.

---

## TB-специфика

### Формат `ml_signals_tb.csv`

```text
time;signal;sl_atr;tp_atr;prob;ev
2023.01.03 04:00;1;2.0;6.0;0.731;3.42
2023.01.03 10:00;-1;3.0;3.0;0.642;1.57
2023.01.03 11:00;0;0;0;0;0
```

### Как определяется TB исход

Tracer ищет target по комбинации:

- направление `signal`
- `sl_atr`
- `tp_atr`

Например:

- `signal=1`, `sl_atr=2`, `tp_atr=6` → `buy_sl2_tp6`
- `signal=-1`, `sl_atr=3`, `tp_atr=3` → `sell_sl3_tp3`

Дальше соответствующее значение читается из labeled CSV:

- `1.0` → `TP_FIRST`
- `0.5` → `TIMEOUT`
- `0.0` → `SL_FIRST`

### Что показывает TB dossier

- выбранный `target_name`
- `prob`
- `ev`
- SL/TP в ATR
- label outcome из Python dataset
- при наличии лога:
  - `MT4 result`
  - фактические `SL / TP ATR`
  - `Δ ATR units` между CSV и MT4

---

## Входные данные

### Общие

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`
- `DATA/Nero_test_labeled.csv`

### Только legacy

- `DATA/Nero_*_updn_params.npy`
- `MT/tester/$o$imple.ini`
- `MT/MQL4/Files/ml_signals.csv`

### Только TB

- `MT/MQL4/Files/ml_signals_tb.csv`
- MT4 логи с `TB BUY` / `TB SELL`

---

## CLI аргументы

Основные:

- `--time`
- `--batch`
- `--from-log`
- `--signals`
- `--nero`
- `--csv-out`

Legacy-specific:

- `--min-ratio`
- `--ml-min-ratio`
- `--ml-max-rr`
- `--ml-scale-k`
- `--ml-min-sl-atr`

---

## CSV экспорт

`--csv-out` пишет совместимый с Excel `;`-separated файл.

Ключевые поля:

- `time`
- `direction`
- `ratio`
- `sl_dist`, `tp_dist`
- `sl_atr`, `tp_atr`
- `category`
- `mt4_result`
- `sl_delta`, `tp_delta`, `atr_delta`

Для TB:

- `ratio` фактически хранит `prob`, чтобы не ломать общий export schema;
- подробные поля `prob`, `ev`, `target_name` видны в stdout dossier и доступны внутри runtime reconciliation.

---

## Практический смысл

Если цель — понять, почему legacy PF в Python разваливается в MT4, используйте legacy `ml_signals.csv` и смотрите на `BOTH_HIT`, `TIMEOUT`, `SL` deltas и lag bias.

Если цель — проверить готовность TB как отдельного EA-mode, используйте `ml_signals_tb.csv` и свежий TB tester log. В этом случае tracer уже умеет показать не только фактический MT4 результат, но и то, совпадает ли он с path-ordered TB label, по которому модель вообще обучалась.
