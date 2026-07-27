from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "MT/MQL4/Include/FUNCTIONS.mqh"
MAIN = ROOT / "MT/MQL4/Include/MAIN.mqh"
ML_SIGNAL = ROOT / "MT/MQL4/Include/lib_ML_Signal.mqh"
PARAMS_CSV = ROOT / "MT/MQL4/Files/#.csv"
TESTER_PARAMS_CSV = ROOT / "MT/tester/files/#.csv"
TESTER_INI = ROOT / "MT/tester/$o$imple.ini"
EXPERT = ROOT / "MT/MQL4/Experts/$o$imple.mq4"
MT4_FILES = ROOT / "MT/MQL4/Files"
MT4_TESTER_FILES = ROOT / "MT/tester/files"

FIXED11_RETAINED_RULES = [
    "rank05_time_only_linear_target_entry_avoid_sl_top30",
    "rank02_time_only_linear_target_entry_ev_regression_top40",
    "rank11_movement_plus_time_linear_target_entry_good_0_5r_top50",
    "rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50",
    "rank10_movement_plus_time_linear_target_entry_ev_regression_top50",
]


def test_mql_parameter_storage_supports_ml_types():
    text = FUNCTIONS.read_text(encoding="utf-8", errors="replace")
    service = (ROOT / "MT/MQL4/Include/SERVICE.mqh").read_text(encoding="utf-8", errors="replace")

    assert "double   PRM[PARAMS];" in text
    assert "virtual void DATA(string name, int& value)" in text
    assert "virtual void DATA(string name, double& value)" in text
    assert "virtual void DATA(string name, bool& value)" in text
    assert "void MAGIC_ADD" in text
    assert "PRINT_TO_LOG_CLASS" in text
    assert "PARAMS_LOADED" in text
    assert "EXP[e].PRM[chr]=StrToDouble(FileReadString(File));" in service
    assert "EXP[e].PRM[chr]=char(StrToDouble(FileReadString(File)))" not in service


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
        "ML_RuleSlot",
    ):
        assert f'DATA("{name}", {name});' in text


def test_expert_exposes_fixed11_rule_slot_setting():
    text = EXPERT.read_text(encoding="utf-8", errors="replace")

    assert "extern int    ML_RuleSlot" in text
    assert "ML_RuleSlot: fixed11 retained rule slot" in text
    assert "extern bool   ML_LogNoSignal" in text
    assert "ML_LogNoSignal: " in text


def _read_semicolon_csv(path: Path) -> list[list[str]]:
    return [line.rstrip("\n\r").split(";") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_hash_csv_contains_five_fixed11_rule_rows_with_ml_values():
    rows = _read_semicolon_csv(PARAMS_CSV)
    header = rows[0]
    data_rows = [row for row in rows[1:] if row and row[0].startswith("SoSimple")]

    assert len(data_rows) == 5
    assert "ML_RuleSlot" in header

    seen_slots = []
    seen_rules = []
    for expected_slot, (expected_rule, row) in enumerate(zip(FIXED11_RETAINED_RULES, data_rows, strict=True), start=1):
        values = dict(zip(header, row))

        assert len(row) == len(header)
        assert " " in values["INFO"]
        assert "-" in values["INFO"]
        assert expected_rule in values["INFO"]
        assert values["SymPer"] == "XAUUSD60"
        assert values["Risk"] == "1"
        assert values["iSignal"] == "3"
        assert values["ML_ExitMode"] == "0"
        assert values["ML_TrailATR"] == "0"
        assert values["ML_TakeProfitATR"] == "0"
        assert values["ML_MaxPositions"] == "1"
        assert values["ML_HoldBars"] == "24"
        assert values["ML_AllowReversal"] == "0"
        assert values["ML_UseScoreFilter"] == "0"
        assert values["ML_ScoreThreshold"] == "0"
        assert values["ML_BackStopATR"] == "50"
        assert values["ML_RuleSlot"] == str(expected_slot)
        assert int(values["Magic"]) == _mql_magic_from_row(header, row)
        seen_slots.append(values["ML_RuleSlot"])
        seen_rules.append(expected_rule)

    assert seen_slots == ["1", "2", "3", "4", "5"]
    assert seen_rules == FIXED11_RETAINED_RULES


def test_fixed11_backtest_numbers_match_mql_csv_reader_line_numbers():
    rows = _read_semicolon_csv(PARAMS_CSV)
    header = rows[0]

    for backtest, row in enumerate(rows[1:], start=2):
        values = dict(zip(header, row))

        assert values["ML_RuleSlot"] == str(backtest - 1)


def test_runtime_and_tester_params_csv_are_identical():
    assert TESTER_PARAMS_CSV.read_text(encoding="utf-8") == PARAMS_CSV.read_text(encoding="utf-8")


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
        "ML_RuleSlot",
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
    assert "BackTest,1=2" in text
    assert "BackTest,2=1" in text
    assert "BackTest,3=6" in text
    assert "ML_ExitMode=0" in text
    assert "ML_TakeProfitATR=0.00000000" in text
    assert "ML_MaxPositions=1" in text
    assert "ML_HoldBars=24" in text
    assert "ML_BackStopATR=50.00000000" in text
    assert "ML_RuleSlot=1" in text
    assert "ML_LogNoSignal=0" in text


def test_service_logs_loaded_csv_parameters():
    service = (ROOT / "MT/MQL4/Include/SERVICE.mqh").read_text(encoding="utf-8", errors="replace")
    functions = FUNCTIONS.read_text(encoding="utf-8", errors="replace")

    assert "PRINT_TO_LOG.EXTERN_VARS(e)" in service
    assert "CSV parameters loaded" in functions


def test_ml_signal_runtime_reload_uses_file_modify_time():
    text = ML_SIGNAL.read_text(encoding="utf-8", errors="replace")

    assert "MLP_LoadedFileModifyTime" in text
    assert "MLP_FileModifyTime()" in text
    assert "MLP_SignalsFileName()" in text
    assert "FILE_MODIFY_DATE" in text
    assert "MLP_RELOAD_IF_CHANGED()" in text
    assert "MLP_RELOAD: file changed" in text
    assert "MLP_INIT()" in text


def test_ml_signal_runtime_selects_file_by_fixed11_rule_slot():
    text = ML_SIGNAL.read_text(encoding="utf-8", errors="replace")

    assert '#define MLP_DEFAULT_SIGNALS_FILE "ml_signals.csv"' in text
    for slot in range(1, 6):
        assert f'if (ML_RuleSlot == {slot}) return "ml_signals_fixed11_rule0{slot}.csv";' in text
    assert "MLP_SignalsFileName()" in text
    assert "MLP_INIT: rule_slot=" in text


def test_ml_no_signal_logging_is_optional_to_keep_tester_log_readable():
    text = ML_SIGNAL.read_text(encoding="utf-8", errors="replace")

    assert "if (!ML_LogNoSignal) return;" in text
    assert ":: MLP NO_SIGNAL" in text


def test_fixed11_rule_signal_files_exist_in_runtime_and_tester_dirs():
    for slot in range(1, 6):
        filename = f"ml_signals_fixed11_rule0{slot}.csv"
        runtime_path = MT4_FILES / filename
        tester_path = MT4_TESTER_FILES / filename

        assert runtime_path.exists()
        assert tester_path.exists()
        assert runtime_path.read_text(encoding="utf-8") == tester_path.read_text(encoding="utf-8")


def test_fixed11_rule_signal_files_use_plain_time_signal_contract():
    for slot in range(1, 6):
        path = MT4_FILES / f"ml_signals_fixed11_rule0{slot}.csv"
        rows = _read_semicolon_csv(path)

        assert rows[0] == ["time", "signal"]
        assert len(rows) > 1
        assert len({row[0] for row in rows[1:]}) == len(rows) - 1
        assert {row[1] for row in rows[1:]} <= {"-1", "1"}


def test_ml_signal_writes_structured_trade_event_csv():
    text = ML_SIGNAL.read_text(encoding="utf-8", errors="replace")

    assert '#define MLP_EVENTS_FILE_PREFIX "ML_Trade_Events_"' in text
    assert 'string MLP_EventsFileName(int magic)' in text
    assert 'MLP_EventsFileName(magic)' in text
    assert "MLP_WriteEventHeaderIfNeeded" in text
    assert "MLP_LogTradeEvent(" in text
    assert '"OPEN_FAILED"' in text
    for field in (
        "event",
        "ticket",
        "direction",
        "signal_time",
        "entry_time",
        "exit_time",
        "bid",
        "ask",
        "spread",
        "bar_open",
        "bar_high",
        "bar_low",
        "bar_close",
        "entry",
        "stop",
        "take_profit",
        "close",
        "profit",
        "swap",
        "commission",
        "reason",
    ):
        assert field in text


def test_ml_signal_resets_tester_trade_event_csv_once():
    text = ML_SIGNAL.read_text(encoding="utf-8", errors="replace")

    assert "MLP_EventsFilePrepared" in text
    assert "void MLP_PrepareEventFileIfNeeded(int magic)" in text
    assert "if (IsTesting()) FileDelete(MLP_EventsFileName(magic));" in text
    assert "MLP_PrepareEventFileIfNeeded(magic);" in text


def test_ml_trading_uses_explicit_hold_boundary_adaptive_slippage_and_retries():
    text = ML_SIGNAL.read_text(encoding="utf-8", errors="replace")

    assert "bool MLP_IsTimeoutDue(int hold_bars)" in text
    assert "#define MLP_TRADE_RETRIES 5" in text
    assert "#define MLP_MAX_SLIPPAGE_ATR 0.25" in text
    assert "int MLP_TradeSlippagePoints(string sym, double atr_value)" in text
    assert "int slippage = spread_points + 5;" in text
    assert "if (slippage < 3) slippage = 3;" in text
    assert "int atr_cap = (int)MathFloor(atr_value * MLP_MAX_SLIPPAGE_ATR / point);" in text
    assert "if (slippage > atr_cap) slippage = atr_cap;" in text
    assert "slippage > 500" not in text
    assert "int hold_bars = SHIFT(OrderOpenTime());" in text
    assert "MLP_IsTimeoutDue(hold_bars)" in text
    assert "for (int repeat = MLP_TRADE_RETRIES; repeat > 0 && !ok; repeat--)" in text
    assert "OrderClose(ticket, lots, close_price, MLP_TradeSlippagePoints(OrderSymbol(), atr_value), clrRed)" in text
    assert "OrderSend(sym, order_type, lot_to_send, N5(entry_price, sym), MLP_TradeSlippagePoints(sym, atr_value)," in text
    assert "OrderClose(ticket, lots, close_price, 3, clrRed)" not in text
    assert "N5(entry_price, sym), 3," not in text


def test_history_recount_and_pic_contract_are_present_in_mql_flow():
    service = (ROOT / "MT/MQL4/Include/SERVICE.mqh").read_text(encoding="utf-8", errors="replace")
    pic = (ROOT / "MT/MQL4/Include/lib_PIC.mqh").read_text(encoding="utf-8", errors="replace")
    count = (ROOT / "MT/MQL4/Include/COUNT.mqh").read_text(encoding="utf-8", errors="replace")
    expert = (ROOT / "MT/MQL4/Experts/$o$imple.mq4").read_text(encoding="utf-8", errors="replace")

    assert "POC_SIMPLE();" in pic
    assert "POC_SIMPLE();" not in count
    assert "void RECOUNT_HISTORY()" in expert
    assert "for (bar=UnCounted; bar>1; bar--)" in expert
    assert "for (uchar e=0; e<ExpTotal; e++)" in expert
    assert "if (!EXP[e].PIC()) continue;" in expert
    assert "RECOUNT_HISTORY();" in service


def test_atr_slow_initializes_without_waiting_for_next_day():
    atr = (ROOT / "MT/MQL4/Include/lib_ATR.mqh").read_text(encoding="utf-8", errors="replace")

    assert "if (Atr.Slow<=0 || TimeDay(Time[bar])!=TimeDay(Time[bar+1]))" in atr


def test_end_ready_window_handles_m1_without_negative_freshness():
    service = (ROOT / "MT/MQL4/Include/SERVICE.mqh").read_text(encoding="utf-8", errors="replace")

    assert "int ReadyAgeSec=EXP[e].Per*60-300;" in service
    assert "if (ReadyAgeSec<=0) ReadyAgeSec=EXP[e].Per*60;" in service
    assert "TimeCurrent() - GlobalVariableGet(NameSymPer) < ReadyAgeSec" in service
