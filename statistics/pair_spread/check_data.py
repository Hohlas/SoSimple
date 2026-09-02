# =============================================================================
# Файл: statistics/pair_spread/check_data.py
# Назначение: проверка полноты экспорта M5/H1 перед запуском этапа
# Использование: ./.venv/bin/python statistics/pair_spread/check_data.py
# =============================================================================
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SYMBOLS = ['AUDUSD', 'NZDUSD', 'USDCAD', 'EURUSD', 'GBPUSD', 'USDCHF', 'XAUUSD', 'XAGUSD']
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / 'MT' / 'MQL4' / 'Files'
COSTS_CSV = DATA_DIR / 'pair_spread_costs_snapshot.csv'
MIN_START = pd.Timestamp('2010-01-01')  # XAGUSD брокер отдаёт только с 2008-11;
                                         # 2010 выбран круглым порогом с запасом;
                                         # реальную глубину контролирует MIN_TRAIN_YEARS=10
MIN_END = pd.Timestamp('2026-01-01')
MIN_TRAIN_YEARS = 10


def check(data_dir: Path, tf: str) -> list[str]:
    problems = []
    for sym in SYMBOLS:
        path = data_dir / f'{sym}_{tf}_OHLC.csv'
        if not path.exists():
            problems.append(f'{tf} {sym}: файл отсутствует')
            continue
        df = pd.read_csv(path, sep=';')
        t = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M')
        start, end = t.min(), t.max()
        if start > MIN_START:
            problems.append(f'{tf} {sym}: старт {start} позже {MIN_START}')
        if end < MIN_END:
            problems.append(f'{tf} {sym}: конец {end} раньше {MIN_END}')
        if (df['close'] <= 0).any():
            problems.append(f'{tf} {sym}: есть close <= 0')
        years_train = (pd.Timestamp('2022-12-31') - max(start, pd.Timestamp('2005-01-01'))).days / 365.25
        if years_train < MIN_TRAIN_YEARS:
            problems.append(
                f'{tf} {sym}: train-окно {years_train:.1f} лет < {MIN_TRAIN_YEARS}'
            )
    return problems


def main() -> int:
    problems = check(DATA_DIR, 'M5') + check(DATA_DIR, 'H1')
    if not COSTS_CSV.exists():
        problems.append('pair_spread_costs_snapshot.csv отсутствует')
    if problems:
        print('FAIL:')
        for p in problems:
            print(' -', p)
        return 1
    print('PASS: все 8 символов × M5/H1 на месте, снимок издержек найден')
    return 0


if __name__ == '__main__':
    sys.exit(main())
