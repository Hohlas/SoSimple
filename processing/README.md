# processing/

Препроцессинг данных: сортировка фракталов → маркировка → нормализация → split → сохранение.

Подробная документация: [docs/processing/](../docs/processing/)

## Скрипты

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [label_main.py](label_main.py) | CLI оркестратор pipeline | `Nero.csv` → `DATA/Nero_{train,validation,test}_labeled.csv` | 🏁 |
| [fractal_preprocessing.py](fractal_preprocessing.py) | Общая сортировка фракталов внутри строки | DataFrame с `fractal*` → отсортированный DataFrame | ✅ |
| [online_causal_preprocessing.py](online_causal_preprocessing.py) | Online-safe subset preprocessing: сортировка + validation + тихая rowwise-нормализация без future labels | runtime snapshot → preprocessed snapshot | ✅ |
| [label_signals.py](label_signals.py) | Маркировка signal/predict + Up/Dn таргеты | sorted DataFrame → labeled DataFrame | 🏁 |
| [normalize.py](normalize.py) | Построчная нормализация признаков | labeled DataFrame → normalized DataFrame + `Nero_*_updn_params.npy` | 🏁 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

## Команды

```bash
source ~/git/SoSimple/.venv/bin/activate

# Полный pipeline: сортировка + маркировка + нормализация + split
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug

# Live-safe пересборка: predict не влияет на нормализацию front/back
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --exclude-predict-from-front-back-pool

# Без нормализации (для отладки)
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --no-normalize
```

## Ключевые функции

- `fractal_preprocessing.py` → `sort_fractals_in_dataframe()`
- `online_causal_preprocessing.py` → `preprocess_online_frame()`, `preprocess_online_csv()`, `validate_fractal_sorting()`
- `label_main.py` → `split_train_val_test()`
- `label_signals.py` → `label_all()`, `label_updn()`, `label_triple_barrier()`
- `normalize.py` → `normalize_rowwise()`
