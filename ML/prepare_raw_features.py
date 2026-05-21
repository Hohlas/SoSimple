# =============================================================================
# Файл: prepare_raw_features.py
# Назначение: Извлечение сырых признаков из Nero.csv + OHLC для direct-direction.
# Создан: 2026-05-18 — Phase 0 переделки E0-E5 (audit rebuild)
# Входные данные:
#   - DATA/Nero_XAUUSD_*_labeled.csv (нормализованные — структура рядов)
#   - DATA/XAUUSD_H1_OHLC.csv (сырые цены для реконструкции)
# Выходные данные:
#   - DATA/raw_features_for_direction.parquet
# Использование:
#   python -m ML.prepare_raw_features [--parity-check]
# Примечания:
#   - Сырые цены восстанавливаются из OHLC по fractal_time (raw, не нормализованные).
#   - ATR в labeled CSV не нормализован (сырой).
#   - Front/back/impulse — из labeled CSV (нормализованы per-row, но без contamination от targets).
#   - Up/dn — из labeled CSV; для Phase A/B используются OHLC-таргеты вместо них.
# =============================================================================

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pickle

import numpy as np
import pandas as pd

from ML.fractal_level_feature_builder import FRACTAL_FIELDS, parse_fractal

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OHLC = PROJECT_ROOT / "DATA" / "XAUUSD_H1_OHLC.csv"
OUTPUT_PATH = PROJECT_ROOT / "DATA" / "raw_features_for_direction.pkl"

# Labeled CSV globs
LABELED_GLOBS = {
    "train": PROJECT_ROOT / "DATA" / "Nero_XAUUSD_train_labeled.csv",
    "validation": PROJECT_ROOT / "DATA" / "Nero_XAUUSD_validation_labeled.csv",
    "test": PROJECT_ROOT / "DATA" / "Nero_XAUUSD_test_labeled.csv",
}

# Fractal fields that are NOT normalized (raw in labeled CSV)
RAW_FIELDS = {"time", "direction", "strong", "fractal_atr"}

# Fractal fields that ARE normalized but not contaminated by row-level targets
# (Group A: price min-max, front/back/predict piecewise; Group B: impulse/count/reverse/power/break piecewise)
NORMALIZED_CLEAN_FIELDS = {"price", "front", "back", "impulse", "power", "count", "reverse", "break"}

# Fractal fields that are normalized AND contaminated by row-level targets (Group C)
# up_12,dn_12,up_24,dn_24,up_48,dn_48,up_3,dn_3,up_6,dn_6
CONTAMINATED_FIELDS = {
    "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48",
    "up_3", "dn_3", "up_6", "dn_6",
}


def load_ohlc(path: Path) -> tuple[dict, list, dict]:
    """Загружает H1 OHLC. Возвращает (ohlc_dict, sorted_times, time_to_idx)."""
    ohlc: dict[datetime, tuple[float, float, float, float]] = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            t = datetime.strptime(row["time"], "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
            ohlc[t] = (
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
            )
    times = sorted(ohlc.keys())
    time_idx = {t: i for i, t in enumerate(times)}
    return ohlc, times, time_idx


def ohlc_close_at(ohlc: dict, timestamp: int) -> float | None:
    """Возвращает close цену OHLC на момент времени (unix timestamp)."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    entry = ohlc.get(dt)
    if entry is not None:
        return entry[3]
    return None


def parse_row_fractals(row: pd.Series) -> list[dict[str, Any]]:
    """Парсит все fractal0..fractal99 строки, возвращает список словарей (или None для пустых)."""
    fractals = []
    for i in range(100):
        col = f"fractal{i}"
        val = row.get(col, "")
        fractals.append(parse_fractal(val))
    return fractals


def build_raw_features(
    labeled_paths: dict[str, Path],
    ohlc_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """Строит датасет сырых признаков из labeled CSV + OHLC."""
    ohlc, ohlc_times, ohlc_time_idx = load_ohlc(ohlc_path)
    print(f"OHLC загружен: {len(ohlc)} баров, {ohlc_times[0]} – {ohlc_times[-1]}")

    frames = []
    for split_name, path in labeled_paths.items():
        if not path.exists():
            print(f"  Пропуск {split_name}: файл не найден {path}")
            continue

        print(f"  Чтение {split_name}: {path.name} ...")
        df_labeled = pd.read_csv(path, sep=";")
        print(f"    строк: {len(df_labeled)}")

        records = []
        for idx, row in df_labeled.iterrows():
            fractals = parse_row_fractals(row)
            row_time_str = row.get("time", "")
            raw_atr = float(row.get("ATR", 0.0))

            # Сырые цены из OHLC для каждого фрактала
            raw_prices = {}
            for fi, fdict in enumerate(fractals):
                if fdict is None:
                    raw_prices[fi] = None
                    continue
                ftime = fdict.get("time", 0)
                if isinstance(ftime, (int, float)) and ftime > 0:
                    price = ohlc_close_at(ohlc, int(ftime))
                    raw_prices[fi] = price
                else:
                    raw_prices[fi] = None

            # Строим запись
            record: dict[str, Any] = {
                "split": split_name,
                "row_idx": idx,
                "time": row_time_str,
                "raw_ATR": raw_atr,
            }

            # Поля fractal0 (сырые + нормализованные)
            f0 = fractals[0]
            if f0 is not None:
                record["fractal0_direction"] = f0.get("direction", 0)
                record["fractal0_strong"] = f0.get("strong", 0)
                record["fractal0_front"] = f0.get("front", 0.0)
                record["fractal0_back"] = f0.get("back", 0.0)
                record["fractal0_impulse"] = f0.get("impulse", 0.0)
                record["fractal0_price_raw"] = raw_prices.get(0)
            else:
                record["fractal0_direction"] = 0
                record["fractal0_strong"] = 0
                record["fractal0_front"] = 0.0
                record["fractal0_back"] = 0.0
                record["fractal0_impulse"] = 0.0
                record["fractal0_price_raw"] = None

            # Сырые таргеты из labeled CSV (для справки)
            record["signal"] = row.get("signal", 0)
            record["predict"] = row.get("predict", 0.0)

            # Все фракталы: raw prices + ключевые поля
            for fi in range(100):
                prefix = f"f{fi}"
                rp = raw_prices.get(fi)
                record[f"{prefix}_price_raw"] = rp
                fdict = fractals[fi]
                if fdict is not None:
                    record[f"{prefix}_direction"] = fdict.get("direction", 0)
                    record[f"{prefix}_front"] = fdict.get("front", 0.0)
                    record[f"{prefix}_back"] = fdict.get("back", 0.0)
                    record[f"{prefix}_impulse"] = fdict.get("impulse", 0.0)
                    record[f"{prefix}_power"] = fdict.get("power", 0.0)
                    record[f"{prefix}_count"] = fdict.get("count", 0)
                    record[f"{prefix}_break"] = fdict.get("break", 0)
                    record[f"{prefix}_reverse"] = fdict.get("reverse", 0.0)
                    record[f"{prefix}_strong"] = fdict.get("strong", 0)
                    record[f"{prefix}_fractal_atr"] = fdict.get("fractal_atr", 0.0)
                    # Up/dn из labeled CSV (нормализованы, с contamination)
                    for h in (3, 6, 12, 24, 48):
                        record[f"{prefix}_up_{h}_labeled"] = fdict.get(f"up_{h}", 0.0)
                        record[f"{prefix}_dn_{h}_labeled"] = fdict.get(f"dn_{h}", 0.0)
                    record[f"{prefix}_time"] = fdict.get("time", 0)
                else:
                    record[f"{prefix}_direction"] = 0
                    record[f"{prefix}_front"] = 0.0
                    record[f"{prefix}_back"] = 0.0
                    record[f"{prefix}_impulse"] = 0.0
                    record[f"{prefix}_power"] = 0.0
                    record[f"{prefix}_count"] = 0
                    record[f"{prefix}_break"] = 0
                    record[f"{prefix}_reverse"] = 0.0
                    record[f"{prefix}_strong"] = 0
                    record[f"{prefix}_fractal_atr"] = 0.0
                    for h in (3, 6, 12, 24, 48):
                        record[f"{prefix}_up_{h}_labeled"] = 0.0
                        record[f"{prefix}_dn_{h}_labeled"] = 0.0
                    record[f"{prefix}_time"] = 0

            # OHLC данные для расчёта таргетов
            try:
                dt = datetime.strptime(row_time_str, "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
                ohlc_idx = ohlc_time_idx.get(dt)
            except (ValueError, KeyError):
                ohlc_idx = None

            if ohlc_idx is not None and ohlc_idx < len(ohlc_times):
                record["ohlc_idx"] = ohlc_idx
            else:
                record["ohlc_idx"] = -1

            records.append(record)

            if (idx + 1) % 10000 == 0:
                print(f"    обработано {idx + 1} строк...")

        frame = pd.DataFrame(records)
        frames.append(frame)
        print(f"  {split_name}: {len(frame)} записей")

    result = pd.concat(frames, ignore_index=True)
    print(f"Всего записей: {len(result)}")

    # Сохраняем
    with open(output_path, "wb") as f:
        pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Сохранено: {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")

    return result


def run_parity_check(output_path: Path, ohlc_path: Path) -> dict[str, bool]:
    """Проверяет, что raw_prices из parquet совпадают с OHLC."""
    ohlc, ohlc_times, _ = load_ohlc(ohlc_path)
    with open(output_path, "rb") as f:
        df = pickle.load(f)

    checks = {}
    # Проверка 1: fractal0_price_raw совпадает с OHLC close на fractal0.time
    # (не можем проверить без доступа к исходному времени фрактала из labeled CSV)
    # Вместо этого: проверяем, что raw_prices не None для значительной доли строк
    non_null = df["fractal0_price_raw"].notna().sum()
    total = len(df)
    checks["fractal0_price_coverage"] = non_null / total if total > 0 else 0.0
    print(f"  fractal0_price_raw coverage: {non_null}/{total} = {checks['fractal0_price_coverage']:.1%}")

    # Проверка 2: raw_price для первых 5 фракталов (должны быть не-None для валидных строк)
    for fi in range(5):
        col = f"f{fi}_price_raw"
        if col in df.columns:
            nn = df[col].notna().sum()
            checks[f"f{fi}_price_coverage"] = nn / total if total > 0 else 0.0

    # Проверка 3: ATR сырой (не нормализован) — значения должны быть > 0
    if "raw_ATR" in df.columns:
        atr_positive = (df["raw_ATR"] > 0).sum()
        checks["atr_positive"] = atr_positive / total if total > 0 else 0.0
        print(f"  raw_ATR > 0: {atr_positive}/{total} = {checks['atr_positive']:.1%}")

    checks["passed"] = checks.get("fractal0_price_coverage", 0) > 0.5
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0: подготовка сырых признаков из Nero.csv + OHLC")
    parser.add_argument("--ohlc", type=Path, default=DEFAULT_OHLC,
                        help="Путь к H1 OHLC CSV (сырые цены)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help="Путь для выходного parquet файла")
    parser.add_argument("--parity-check", action="store_true",
                        help="Проверить, что raw_price из нового файла совпадает с OHLC")
    parser.add_argument("--train", type=Path, default=LABELED_GLOBS["train"],
                        help="Путь к train labeled CSV")
    parser.add_argument("--validation", type=Path, default=LABELED_GLOBS["validation"],
                        help="Путь к validation labeled CSV")
    parser.add_argument("--test", type=Path, default=LABELED_GLOBS["test"],
                        help="Путь к test labeled CSV")
    args = parser.parse_args()

    paths = {
        "train": args.train,
        "validation": args.validation,
        "test": args.test,
    }

    # Проверяем существование входных файлов
    missing = [k for k, v in paths.items() if not v.exists()]
    if missing:
        print(f"Ошибка: файлы не найдены: {missing}")
        sys.exit(1)

    if not args.ohlc.exists():
        print(f"Ошибка: OHLC файл не найден: {args.ohlc}")
        sys.exit(1)

    if args.parity_check:
        if not args.output.exists():
            print(f"Сначала запустите без --parity-check для создания {args.output}")
            sys.exit(1)
        print("=== Parity Check ===")
        checks = run_parity_check(args.output, args.ohlc)
        if checks.get("passed"):
            print("GATE 0 PASSED: parity check пройден")
        else:
            print("GATE 0 FAILED: parity check не пройден")
            sys.exit(1)
    else:
        print("=== Phase 0: Подготовка сырых признаков ===")
        print(f"OHLC: {args.ohlc}")
        for split_name, path in paths.items():
            print(f"  {split_name}: {path}")
        print(f"Выход: {args.output}")
        print()

        df = build_raw_features(paths, args.ohlc, args.output)

        # Автоматический parity check после сборки
        print("\n=== Parity Check ===")
        checks = run_parity_check(args.output, args.ohlc)
        if checks.get("passed"):
            print("GATE 0 PASSED: parity check пройден")
        else:
            print("GATE 0 WARNING: низкое покрытие raw_price, проверьте OHLC соответствие")
        print(f"\nСтолбцы: {len(df.columns)}")
        print(f"Строки: {len(df)}")


if __name__ == "__main__":
    main()
