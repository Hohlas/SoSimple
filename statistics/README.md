# statistics/

Статистический анализ данных и диагностика расхождений ML vs MT4.

Подробная документация: [docs/statistics/](../docs/statistics/)

## Скрипты

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [statistics.py](statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | `Nero.csv` → `.json`, `.csv` | 🏁 |
| [EDA.ipynb](EDA.ipynb) | Разведочный анализ данных | `Nero_train_labeled.csv` → `plots/`, `reports/` | 🏁 |
| [signal_tracer.py](signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | ml_signals.csv + labeled CSV + updn_params.npy + MT4 log → dossiers, CSV | ✅ |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

## Команды

```bash
source ~/git/SoSimple/.venv/bin/activate

# Статистика по размеченным данным
python statistics/statistics.py DATA/Nero_train_labeled.csv

# EDA ноутбук
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb

# signal_tracer: разбор одного сигнала
python statistics/signal_tracer.py --time "2023.01.03 04:00"

# signal_tracer: batch-анализ top-N сигналов
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0 --csv-out batch.csv

# signal_tracer: разбор сделок из MT4 лога
python statistics/signal_tracer.py --from-log MT/tester/logs/20260324.log --losses-only --csv-out losses.csv
```

## Артефакты (генерируемые файлы)

| Каталог/файл | Содержимое |
|---|---|
| `plots/` | Визуализации: heatmaps, boxplots, PCA, t-SNE и др. |
| `reports/` | EDA_report.md, EDA_executed.ipynb |
| `EDA_files/` | PNG-файлы из EDA ноутбука |
| `*.json` | feature_catalog, class_statistics, statistics_summary, nero_features_metadata |
| `*.csv` | class_balance_report, feature_distributions, nero_sample_stratified |
