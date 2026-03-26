# API/

Генерация ML-сигналов для MT4 и REST API сервер.

Подробная документация: [docs/MT/ml_signal_integration.md](../docs/MT/ml_signal_integration.md)

## Скрипты

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [generate_signals.py](generate_signals.py) | Генерация CSV с ML-сигналами для MT4 тестера | checkpoints + labeled CSV → `MT/MQL4/Files/ml_signals.csv` | ✅ |
| [api_server.py](api_server.py) | REST API (FastAPI) для приёма фракталов от MT4 в реальном времени | HTTP request → ML prediction | 🔬 |
| [test_api_client.py](test_api_client.py) | Тестовый клиент для api_server.py | test CSV → HTTP requests | 🔬 |

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
```
