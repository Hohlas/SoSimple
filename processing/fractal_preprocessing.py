# =============================================================================
# Файл: fractal_preprocessing.py
# Назначение: Общая сортировка фракталов внутри строки для training и online pipeline.
# Обновлён: 2026-04-29
# Входные данные:
#   - DataFrame с колонками fractal0..fractalN (откуда: raw Nero.csv или runtime snapshot)
# Выходные данные:
#   - DataFrame с fractal0..fractalN, отсортированными по времени убыванию
# Использование:
#   from processing.fractal_preprocessing import sort_fractals_in_dataframe
# Примечания:
#   - Сортировка независима по строкам и не использует future labels.
# =============================================================================

from __future__ import annotations

from typing import Iterable

import pandas as pd


def fractal_columns_in_order(columns: Iterable[str]) -> list[str]:
    """Return fractal columns ordered by their numeric suffix."""
    names = [name for name in columns if str(name).startswith("fractal")]

    def _suffix(name: str) -> int:
        raw = str(name).replace("fractal", "", 1)
        try:
            return int(raw)
        except ValueError:
            return 10**9

    return sorted(names, key=_suffix)


def sort_row_fractals(
    row_data: pd.Series,
    fractal_columns: list[str],
    *,
    debug: bool = False,
    row_idx: int | None = None,
) -> list[str]:
    fractals: list[dict[str, object]] = []

    for col_name in fractal_columns:
        fractal_str = row_data[col_name]
        if pd.isna(fractal_str) or fractal_str == "":
            continue

        parts = str(fractal_str).split(":")
        if not parts:
            continue
        try:
            time_val = int(float(parts[0]))
            fractals.append({"time": time_val, "data": str(fractal_str)})
        except (ValueError, IndexError) as exc:
            if debug:
                print(f"  [Строка {row_idx}] Ошибка парсинга фрактала в {col_name}: {exc}")
            continue

    fractals.sort(key=lambda item: int(item["time"]), reverse=True)
    return [str(item["data"]) for item in fractals]


def sort_fractals_in_dataframe(df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
    if debug:
        print(f"\n[СОРТИРОВКА] Начало сортировки фракталов в {len(df)} строках")

    result = df.copy()
    fractal_columns = fractal_columns_in_order(result.columns)

    for idx, row in result.iterrows():
        sorted_fractals = sort_row_fractals(row, fractal_columns, debug=debug, row_idx=idx)

        for i, fractal_data in enumerate(sorted_fractals):
            if i < len(fractal_columns):
                result.at[idx, fractal_columns[i]] = fractal_data

        for i in range(len(sorted_fractals), len(fractal_columns)):
            result.at[idx, fractal_columns[i]] = ""

    if debug:
        print("[СОРТИРОВКА] Завершена")

    return result
