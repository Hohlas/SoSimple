# API/

Генерация ML-сигналов для MT4 и REST API сервер.

Подробная документация: [docs/MT/ml_signal_integration.md](../docs/MT/ml_signal_integration.md)

## Скрипты

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [generate_signals.py](generate_signals.py) | Генерация CSV с ML-сигналами для MT4 тестера | checkpoints + labeled CSV → `MT/MQL4/Files/ml_signals.csv` | ✅ |
| [exit_policy_research.py](exit_policy_research.py) | Validation-first offline research для ML exit / position management | `ml_signals.csv` + OHLC + split catalogs → stdout ranking / frozen policy JSON | 🔬 |
| [api_server.py](api_server.py) | REST API (FastAPI) для приёма фракталов от MT4 в реальном времени | HTTP request → ML prediction | 🔬 |
| [test_api_client.py](test_api_client.py) | Тестовый клиент для api_server.py | test CSV → HTTP requests | 🔬 |
| [signal_path_atlas.py](signal_path_atlas.py) | ATR-normalized discovery/holdout path atlas for ML signals | `ml_signals.csv` + OHLC -> stdout tables / optional CSV export | 🔬 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания | 🔬 Экспериментальный

## Команды

```bash
source ~/git/SoSimple/.venv/bin/activate

# Генерация сигналов (дефолт: θ=2.665, horizon=12)
python -m API.generate_signals

# Кастомные параметры
python -m API.generate_signals --theta 3.0 --horizon 24

# С Conformal Prediction
python -m API.generate_signals --conformal

# Triple Barrier сигналы
python -m API.generate_signals --task triple_barrier --theta 0.6

# Path atlas research
python -m API.signal_path_atlas --test-only
python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas

# Exit policy research
python -m API.exit_policy_research --split-profile validation_research
python -m API.exit_policy_research --split-profile test_final --policy ML/reports/frozen_exit_policy.json
```
