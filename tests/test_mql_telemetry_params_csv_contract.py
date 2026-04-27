from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "MT/MQL4/Include/FUNCTIONS.mqh"
MAIN = ROOT / "MT/MQL4/Include/MAIN.mqh"
PARAMS_CSV = ROOT / "MT/MQL4/Files/#.csv"
TESTER_INI = ROOT / "MT/tester/$o$imple.ini"


def test_mql_parameter_storage_supports_ml_types():
    text = FUNCTIONS.read_text(encoding="utf-8", errors="replace")

    assert "double   PRM[PARAMS];" in text
    assert "virtual void DATA(string name, int& value)" in text
    assert "virtual void DATA(string name, double& value)" in text
    assert "virtual void DATA(string name, bool& value)" in text
    assert "void MAGIC_ADD" in text


def test_extern_vars_tracks_active_ml_parameters():
    text = MAIN.read_text(encoding="utf-8", errors="replace")

    assert 'DATA(" -  M L  - ");' in text
    for name in (
        "ML_ExitMode",
        "ML_TrailATR",
        "ML_TakeProfitATR",
        "ML_MaxPositions",
        "ML_HoldBars",
        "ML_AllowReversal",
        "ML_UseScoreFilter",
        "ML_ScoreThreshold",
        "ML_BackStopATR",
    ):
        assert f'DATA("{name}", {name});' in text


def _read_semicolon_csv(path: Path) -> list[list[str]]:
    return [line.rstrip("\n\r").split(";") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_hash_csv_contains_single_telemetry_row_with_ml_values():
    rows = _read_semicolon_csv(PARAMS_CSV)
    header = rows[0]
    data_rows = [row for row in rows[1:] if row and row[0].startswith("SoSimple")]

    assert len(data_rows) == 1
    row = data_rows[0]
    values = dict(zip(header, row))

    assert len(header) == 16 + 80
    assert len(row) == len(header)
    assert values["SymPer"] == "XAUUSD60"
    assert values["Risk"] == "1"
    assert values["iSignal"] == "3"
    assert values["ML_ExitMode"] == "0"
    assert values["ML_TrailATR"] == "8"
    assert values["ML_TakeProfitATR"] == "5"
    assert values["ML_MaxPositions"] == "10"
    assert values["ML_HoldBars"] == "24"
    assert values["ML_AllowReversal"] == "0"
    assert values["ML_UseScoreFilter"] == "0"
    assert values["ML_ScoreThreshold"] == "0"
    assert values["ML_BackStopATR"] == "3"
    assert int(values["Magic"]) == _mql_magic_from_row(header, row)


def _mql_magic_from_row(header: list[str], row: list[str]) -> int:
    """Mirror FUNCTIONS.mqh::MAGIC_ADD for fields listed in EXTERN_VARS()."""
    tracked = [
        "PicPer",
        "FltLen",
        "PicCnt",
        "PicPwr",
        "PicImp",
        "Rev",
        "Days",
        "MidTyp",
        "iGlb",
        "iFlt",
        "iLoc",
        "A",
        "a",
        "Ak",
        "PicVal",
        "Target",
        "iSignal",
        "iParam",
        "D",
        "Stp",
        "Prf",
        "oImp",
        "oFlt",
        "oGlb",
        "oLoc",
        "Trl",
        "Wknd",
        "tk",
        "T0",
        "T1",
        "tp",
        "ML_ExitMode",
        "ML_TrailATR",
        "ML_TakeProfitATR",
        "ML_MaxPositions",
        "ML_HoldBars",
        "ML_AllowReversal",
        "ML_UseScoreFilter",
        "ML_ScoreThreshold",
        "ML_BackStopATR",
    ]
    values = dict(zip(header, row))
    magic = 0
    for name in tracked:
        scaled = round(float(values[name]) * 100000.0)
        add = (scaled + 2147483647) & ((1 << 64) - 1)
        magic = (magic * 1315423911 + add + 1) & ((1 << 64) - 1)
    low = magic & 0xFFFFFFFF
    signed = low if low < 2**31 else low - 2**32
    return abs(signed)


def test_tester_ini_selects_telemetry_backtest_row():
    text = TESTER_INI.read_text(encoding="utf-8", errors="replace")

    assert "BackTest=2" in text
    assert "ML_ExitMode=0" in text
    assert "ML_TakeProfitATR=5.00000000" in text
    assert "ML_MaxPositions=10" in text
    assert "ML_HoldBars=24" in text
    assert "ML_BackStopATR=3.00000000" in text
