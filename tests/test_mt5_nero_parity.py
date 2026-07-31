"""Tests for compare_nero_parity.py using synthetic fixtures."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ML" / "baseline"))
from compare_nero_parity import (
    determine_verdict,
    load_csv,
    numeric_checks,
    parse_fractal_field,
    structural_checks,
)

HEADER = "time;signal;predict;ATR;" + ";".join(f"fractal{i}" for i in range(100))


def make_fractal_22(t="1562076000", price="1394.6", direction="1", shift=None):
    fields = [t, price, direction] + ["0.0"] * 19
    if shift is not None:
        fields.append(str(shift))
    return ":".join(fields)


def make_row(time_str, atr="4.6", fractal0=None, n_fractals=100, fields_per=22):
    if fractal0 is None:
        fractal0 = make_fractal_22()
    fractals = [fractal0] + [make_fractal_22(t=str(1562076000 + i * 3600)) for i in range(1, n_fractals)]
    if fields_per == 23:
        fractals = [f + ":1" for f in fractals]
    return ";".join([time_str, "0", "0", atr] + fractals)


def write_csv(path, rows, encoding="utf-8"):
    content = HEADER + "\n" + "\n".join(rows) + "\n"
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


@pytest.fixture
def mt4_file(tmp_path):
    p = tmp_path / "mt4.csv"
    rows = [
        make_row("2019.07.02 15:00", atr="4.5", fractal0=make_fractal_22(direction="1", price="1394.0")),
        make_row("2019.07.02 16:00", atr="4.6", fractal0=make_fractal_22(direction="-1", price="1395.0")),
        make_row("2019.07.02 17:00", atr="4.7", fractal0=make_fractal_22(direction="1", price="1396.0")),
    ]
    write_csv(p, rows)
    return str(p)


@pytest.fixture
def mt5_file(tmp_path):
    p = tmp_path / "mt5.csv"
    rows = [
        make_row("2019.07.02 15:00", atr="4.5", fractal0=make_fractal_22(direction="1", price="1394.5"), fields_per=23),
        make_row("2019.07.02 16:00", atr="4.6", fractal0=make_fractal_22(direction="-1", price="1395.2"), fields_per=23),
        make_row("2019.07.02 17:00", atr="4.7", fractal0=make_fractal_22(direction="1", price="1396.1"), fields_per=23),
    ]
    write_csv(p, rows)
    return str(p)


class TestParseFractalField:
    def test_valid(self):
        fields = parse_fractal_field("123:456.7:1:2.0")
        assert fields == ["123", "456.7", "1", "2.0"]

    def test_empty(self):
        assert parse_fractal_field("") is None
        assert parse_fractal_field(None) is None


class TestStructuralChecks:
    def test_column_match(self, mt4_file, mt5_file):
        df4 = load_csv(mt4_file, "utf-8")
        df5 = load_csv(mt5_file, "utf-8")
        structural, _, _, _ = structural_checks(df4, df5)
        assert structural["column_match"] is True
        assert structural["intersection_rows"] == 3

    def test_column_mismatch(self, mt4_file, tmp_path):
        p = tmp_path / "bad.csv"
        content = "time;signal;predict;ATR_EXTRA;" + ";".join(f"fractal{i}" for i in range(100)) + "\n"
        content += make_row("2019.07.02 15:00") + "\n"
        with open(p, "w") as f:
            f.write(content)
        df4 = load_csv(mt4_file, "utf-8")
        df5 = load_csv(str(p), "utf-8")
        structural, _, _, _ = structural_checks(df4, df5)
        assert structural["column_match"] is False

    def test_duplicates_counted(self, tmp_path):
        p4 = tmp_path / "mt4_dup.csv"
        rows = [
            make_row("2019.07.02 15:00"),
            make_row("2019.07.02 15:00"),
            make_row("2019.07.02 16:00"),
        ]
        write_csv(p4, rows)
        p5 = tmp_path / "mt5_dup.csv"
        write_csv(p5, [make_row("2019.07.02 15:00", fields_per=23), make_row("2019.07.02 16:00", fields_per=23)])
        df4 = load_csv(str(p4), "utf-8")
        df5 = load_csv(str(p5), "utf-8")
        structural, _, _, _ = structural_checks(df4, df5)
        assert structural["duplicate_time_count_mt4"] == 1
        assert structural["duplicate_time_count_mt5"] == 0

    def test_22_vs_23_not_fail(self, mt4_file, mt5_file):
        df4 = load_csv(mt4_file, "utf-8")
        df5 = load_csv(mt5_file, "utf-8")
        structural, _, _, _ = structural_checks(df4, df5)
        assert 22 in structural["field_count_distribution_mt4"]
        assert 23 in structural["field_count_distribution_mt5"]


class TestNumericChecks:
    def test_direction_agreement(self, mt4_file, mt5_file):
        df4 = load_csv(mt4_file, "utf-8")
        df5 = load_csv(mt5_file, "utf-8")
        _, df4_int, df5_int, times = structural_checks(df4, df5)
        numeric = numeric_checks(df4_int, df5_int, times)
        assert numeric["fractal0_direction_agreement_rate"] == 1.0

    def test_price_diff_summary(self, mt4_file, mt5_file):
        df4 = load_csv(mt4_file, "utf-8")
        df5 = load_csv(mt5_file, "utf-8")
        _, df4_int, df5_int, times = structural_checks(df4, df5)
        numeric = numeric_checks(df4_int, df5_int, times)
        assert numeric["fractal0_price_diff"]["count"] == 3
        assert numeric["fractal0_price_diff"]["max"] == pytest.approx(0.5, abs=0.01)

    def test_timestamp_agreement(self, mt4_file, mt5_file):
        df4 = load_csv(mt4_file, "utf-8")
        df5 = load_csv(mt5_file, "utf-8")
        _, df4_int, df5_int, times = structural_checks(df4, df5)
        numeric = numeric_checks(df4_int, df5_int, times)
        assert numeric["fractal0_T_agreement_rate"] == 1.0


class TestVerdict:
    def test_pass(self):
        structural = {"column_match": True, "field_count_distribution_mt4": {22: 100}, "field_count_distribution_mt5": {23: 100}}
        numeric = {
            "fractal0_direction_agreement_rate": 0.98,
            "fractal0_price_diff": {"p95": 2.0},
            "atr_diff": {"p95": 0.5},
        }
        assert determine_verdict(structural, numeric) == "PARITY_PASS"

    def test_partial(self):
        structural = {"column_match": True, "field_count_distribution_mt4": {22: 100}, "field_count_distribution_mt5": {23: 100}}
        numeric = {
            "fractal0_direction_agreement_rate": 0.90,
            "fractal0_price_diff": {"p95": 2.0},
            "atr_diff": {"p95": 0.5},
        }
        assert determine_verdict(structural, numeric) == "PARITY_PARTIAL"

    def test_fail_column_mismatch(self):
        structural = {"column_match": False, "field_count_distribution_mt4": {22: 100}, "field_count_distribution_mt5": {23: 100}}
        numeric = {
            "fractal0_direction_agreement_rate": 0.99,
            "fractal0_price_diff": {"p95": 1.0},
            "atr_diff": {"p95": 0.1},
        }
        assert determine_verdict(structural, numeric) == "PARITY_FAIL"

    def test_fail_no_data(self):
        structural = {"column_match": True, "field_count_distribution_mt4": {}, "field_count_distribution_mt5": {}}
        numeric = {
            "fractal0_direction_agreement_rate": None,
            "fractal0_price_diff": {"p95": None},
            "atr_diff": {"p95": None},
        }
        assert determine_verdict(structural, numeric) == "PARITY_FAIL"
