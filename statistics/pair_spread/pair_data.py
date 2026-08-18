# =============================================================================
# Файл: statistics/pair_spread/pair_data.py
# Назначение: загрузка OHLC CSV (экспорт MT), сборка лог-спредов кандидатов,
#             константы сплита. Без __init__.py (конфликт statistics/ со stdlib)
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные: MT/MQL4/Files/{M5,H1}/*_OHLC.csv (откуда: MT5-экспорт, Task 2)
#   Выходные данные: pd.Series/pd.DataFrame в памяти (куда: screening.py, backtest.py, run_pair_spread.py)
# Использование: импорт из каталога скрипта (sys.path[0]) или importlib в тестах
# =============================================================================
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TIME_FORMAT = '%Y.%m.%d %H:%M'

TRAIN_END = pd.Timestamp('2022-12-31 23:59')
TEST_START = pd.Timestamp('2023-01-01 00:00')

# Кандидаты спеки (раздел 3.2): legs = (нога A, нога B), спред s = lnA - beta*lnB
CANDIDATES: dict[str, dict] = {
    'AUDNZD': {'legs': ('AUDUSD', 'NZDUSD')},
    'AUDCAD': {'legs': ('AUDUSD', 'USDCAD')},
    'NZDCAD': {'legs': ('NZDUSD', 'USDCAD')},
    'EURGBP': {'legs': ('EURUSD', 'GBPUSD')},
    'EURCHF': {'legs': ('EURUSD', 'USDCHF')},
    'GBPCHF': {'legs': ('GBPUSD', 'USDCHF')},
    'XAUXAG': {'legs': ('XAUUSD', 'XAGUSD')},
}

__all__ = [
    'CANDIDATES', 'TEST_START', 'TRAIN_END', 'TIME_FORMAT',
    'build_log_spreads', 'load_ohlc_csv', 'resample_to_h1',
]


def load_ohlc_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=';')
    df['time'] = pd.to_datetime(df['time'], format=TIME_FORMAT)
    df = df.set_index('time').sort_index()
    df = df[~df.index.duplicated(keep='last')]
    for col in ('open', 'high', 'low', 'close'):
        df[col] = df[col].astype(float)
    df = df[df['close'] > 0]
    return df[['open', 'high', 'low', 'close']]


def resample_to_h1(m5: pd.DataFrame) -> pd.DataFrame:
    h1 = m5.resample('1h', label='left', closed='left').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
    return h1.dropna()


def build_log_spreads(closes_a: pd.Series, closes_b: pd.Series, beta: float) -> pd.Series:
    a, b = closes_a.align(closes_b, join='inner')
    return np.log(a) - beta * np.log(b)
