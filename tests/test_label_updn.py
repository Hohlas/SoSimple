# =============================================================================
# Файл: tests/test_label_updn.py
# Назначение: Unit-тесты для parse_fractal и label_updn из processing/label_signals.py
# Язык: Python 3.10+
# Обновлён: 2026-06-11
# Зависимости:
#   Входные данные:
#     - синтетические строки фракталов (23 поля), pandas DataFrame
#   Выходные данные:
#     - pytest assertions
# Внешние зависимости:
#   - pytest>=8.0, pandas>=2.0
# Использование:
#   ./.venv/bin/python -m pytest tests/test_label_updn.py -q
# Примечания:
#   - строгий 23-полевой формат (fractal_v24_raw_price)
#   - label_updn: трекинг fractal0 по времени, last-seen логика
# =============================================================================

import sys
import pytest
import pandas as pd
sys.path.insert(0, 'processing')
from label_signals import parse_fractal

# 23-полевой фрактал: T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:Atr:Shift
FRACTAL_23 = ("1705312800:1.28450:1:0.0034:0.0021:1:0:0.0:0.0025:3:0.0018"
              ":0.0015:0.0010:0.0028:0.0019:0.0040:0.0031"
              ":0:0:0:0:0.00092:0")


def test_parse_fractal_23_fields():
    result = parse_fractal(FRACTAL_23)
    assert result is not None
    assert result['direction'] == 1
    assert result['price'] == pytest.approx(1.28450, abs=1e-5)
    assert result['up_12'] == pytest.approx(0.0015, abs=1e-6)
    assert result['dn_12'] == pytest.approx(0.0010, abs=1e-6)
    assert result['up_24'] == pytest.approx(0.0028, abs=1e-6)
    assert result['dn_24'] == pytest.approx(0.0019, abs=1e-6)
    assert result['up_48'] == pytest.approx(0.0040, abs=1e-6)
    assert result['dn_48'] == pytest.approx(0.0031, abs=1e-6)
    assert result['fractal_atr'] == pytest.approx(0.00092, abs=1e-6)
    assert result['shift'] == 0


def test_parse_fractal_accepts_integer_like_float_fields():
    raw = FRACTAL_23.replace(":1:0.0034:", ":1.0:0.0034:")
    raw = raw.replace(":1:0:0.0:", ":1.0:0.0:0.0:")
    raw = raw.replace(":3:0.0018:", ":3.0:0.0018:")

    result = parse_fractal(raw)

    assert result is not None
    assert result['direction'] == 1
    assert result['strong'] == 1
    assert result['break'] == 0
    assert result['count'] == 3


def test_parse_fractal_rejects_normalized_float_integer_fields():
    raw = FRACTAL_23.replace(":1:0:0.0:", ":1:0.1700000018:0.0:")

    assert parse_fractal(raw) is None


def test_parse_fractal_none_input():
    assert parse_fractal(None) is None
    assert parse_fractal('') is None


def test_parse_fractal_wrong_fields():
    """22 поля — reject."""
    assert parse_fractal("1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1:1") is None


# ── label_updn tests ─────────────────────────────────────────────────────────
from label_signals import label_updn


def _make_fractal(t, price, up12, dn12, up24, dn24, up48, dn48, strong=0, brk=0, atr=0.001):
    """Helper: build a 23-field fractal string."""
    return (f"{t}:{price:.5f}:1:0.001:0.001:{strong}:{brk}:0.0:0.001:1:0.001"
            f":{up12:.5f}:{dn12:.5f}:{up24:.5f}:{dn24:.5f}:{up48:.5f}:{dn48:.5f}"
            f":0:0:0:0:{atr:.5f}:0")


def test_label_updn_basic():
    """Fractal0 appears in 3 subsequent rows; last row has final Up/Dn."""
    T0 = 1705312800  # fractal being tracked
    T1 = 1705316400  # another fractal

    rows = [
        {"time": "2026.01.15 10:00",
         "fractal0": _make_fractal(T0, 1.28, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
         "fractal1": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008)},
        {"time": "2026.01.15 11:00",
         "fractal0": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008),
         "fractal1": _make_fractal(T0, 1.28, 0.002, 0.001, 0.004, 0.002, 0.0, 0.0)},
        {"time": "2026.01.15 12:00",
         "fractal0": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008),
         "fractal1": _make_fractal(T0, 1.28, 0.003, 0.002, 0.006, 0.004, 0.010, 0.007)},
        {"time": "2026.01.15 13:00",
         "fractal0": _make_fractal(T1, 1.27, 0.005, 0.003, 0.008, 0.005, 0.012, 0.008),
         "fractal1": ""},  # T0 evicted
    ]
    df = pd.DataFrame(rows)
    result = label_updn(df)

    # Row 0: target = last found values for T0 = row 2's values
    assert result.at[0, 'up_12'] == pytest.approx(0.003, abs=1e-5)
    assert result.at[0, 'dn_12'] == pytest.approx(0.002, abs=1e-5)
    assert result.at[0, 'up_48'] == pytest.approx(0.010, abs=1e-5)


def test_label_updn_fractal0_missing():
    """Row with no fractal0 gets zeros."""
    df = pd.DataFrame([{"time": "2026.01.15 10:00", "fractal0": ""}])
    result = label_updn(df)
    assert result.at[0, 'up_12'] == 0.0
    assert result.at[0, 'up_48'] == 0.0


def test_label_updn_distinguishes_two_fractals_on_same_bar():
    t0 = 1705312800
    hi_now = (
        f"{t0}:101.00000:1:0.001:0.001:0:0:0.0:0.001:1:0.001"
        f":0.00000:0.00000:0.00000:0.00000:0.00000:0.00000"
        f":0.00000:0.00000:0.00000:0.00000:0.00100:0"
    )
    lo_now = (
        f"{t0}:99.00000:-1:0.001:0.001:0:0:0.0:0.001:1:0.001"
        f":0.00000:0.00000:0.00000:0.00000:0.00000:0.00000"
        f":0.00000:0.00000:0.00000:0.00000:0.00100:0"
    )
    hi_future = (
        f"{t0}:101.00000:1:0.001:0.001:0:0:0.0:0.001:1:0.001"
        f":2.00000:1.00000:3.00000:1.50000:4.00000:2.00000"
        f":0.50000:0.25000:1.00000:0.50000:0.00100:1"
    )
    lo_future = (
        f"{t0}:99.00000:-1:0.001:0.001:0:0:0.0:0.001:1:0.001"
        f":1.50000:2.50000:2.00000:3.50000:2.50000:4.50000"
        f":0.25000:0.75000:0.50000:1.25000:0.00100:1"
    )

    df = pd.DataFrame([
        {"time": "2026.01.15 10:00", "fractal0": hi_now, "fractal1": lo_now},
        {"time": "2026.01.15 11:00", "fractal0": "", "fractal1": hi_future, "fractal2": lo_future},
        {"time": "2026.01.15 12:00", "fractal0": ""},
    ])

    result = label_updn(df)

    assert result.at[0, "up_3"] == pytest.approx(0.5, abs=1e-6)
    assert result.at[0, "dn_3"] == pytest.approx(0.25, abs=1e-6)
    assert result.at[0, "up_12"] == pytest.approx(2.0, abs=1e-6)
    assert result.at[0, "dn_12"] == pytest.approx(1.0, abs=1e-6)
