from __future__ import annotations

import re

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDERS = ROOT / "MT" / "MQL5" / "Include" / "ORDERS.mqh"
OUTPUT = ROOT / "MT" / "MQL5" / "Include" / "OUTPUT.mqh"
INPUT = ROOT / "MT" / "MQL5" / "Include" / "INPUT.mqh"
ML_SIGNAL = ROOT / "MT" / "MQL5" / "Include" / "lib_ML_Signal.mqh"
FUNCTIONS = ROOT / "MT" / "MQL5" / "Include" / "FUNCTIONS.mqh"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# Regex for an MQL5 outer function definition: "void EXPERT::Foo(" or
# "void EXPERT_PARENT_CLASS::Foo(" etc. Used to find the next function boundary
# instead of relying on comment markers like "//Ж" (which are brittle and
# cause ValueError instead of a readable assertion failure if moved/changed).
_FUNC_SIGNATURE = re.compile(
    r"^\s*(?:void|bool|int|float|double|string|datetime|ulong|char|short|uchar|ushort)\s+"
    r"(?:[A-Za-z_][A-Za-z0-9_]*::)?[A-Za-z_][A-Za-z0-9_]*\s*\(",
    re.MULTILINE,
)


def _body(text: str, signature: str, next_signature: str) -> str:
    """Return text between two function signatures, asserting both exist.

    Raises AssertionError with a readable message if either anchor is missing
    (instead of ValueError from str.index), and finds the next anchor by
    function-signature regex to avoid depending on comment layout.
    """
    assert signature in text, f"anchor not found: {signature!r}"
    start = text.index(signature)
    # Search forward for the next function signature after `start`.
    for m in _FUNC_SIGNATURE.finditer(text, start + len(signature)):
        candidate = m.group(0).strip()
        if next_signature in text[m.start():]:
            end = m.start()
            return text[start:end]
    raise AssertionError(
        f"next function anchor matching {next_signature!r} not found after {signature!r}"
    )


def test_set_buy_sell_do_not_use_legacy_singleton_as_multi_pos_loop_gate() -> None:
    orders = _text(ORDERS)
    # Anchors use next function definition, not comment markers.
    buy_body = _body(orders, "void EXPERT_PARENT_CLASS::SET_BUY()", "void EXPERT_PARENT_CLASS::SET_SEL()")
    sell_body = _body(orders, "void EXPERT_PARENT_CLASS::SET_SEL()", "void EXPERT_PARENT_CLASS::MODIFY()")

    assert "CanPlaceBuyOrder()" in buy_body
    assert "CanPlaceSellOrder()" in sell_body
    # Audit U2: the legacy loop is `while (repeat>0 && BUY.Val==0)` (one space)
    # and `while (repeat>0 &&  SEL.Val==0)` (two spaces) at ORDERS.mqh:22/46.
    # An exact-string `not in` assertion silently passes if the source gets
    # re-tokenised (e.g. `while(repeat>0 && BUY.Val==0)` or
    # `while (repeat > 0 && BUY.Val == 0)`), leaving the gate regressed but the
    # test green. Use a normalised regex so ANY re-tokenisation of the legacy
    # gate that still references `repeat`, `>`, `0`, `&&` and `BUY.Val==0` fails
    # the test until the line is replaced by the CanPlace* helper.
    _legacy_buy = re.compile(r"while\s*\(\s*repeat\s*>\s*0\s*&&\s*BUY\.Val\s*==\s*0\s*\)")
    _legacy_sel = re.compile(r"while\s*\(\s*repeat\s*>\s*0\s*&&\s*SEL\.Val\s*==\s*0\s*\)")
    assert not _legacy_buy.search(buy_body), "legacy BUY.Val==0 loop gate must be replaced by CanPlaceBuyOrder()"
    assert not _legacy_sel.search(sell_body), "legacy SEL.Val==0 loop gate must be replaced by CanPlaceSellOrder()"
    # Positive checks remain tolerant to whitespace (optional) — keep the exact
    # match here because the replacement is one canonical line authored by this task.
    assert "CanPlaceBuyOrder()" in buy_body
    assert "CanPlaceSellOrder()" in sell_body


def test_close_side_checks_ticket_side_before_zero_price_mutation() -> None:
    output = _text(OUTPUT)
    buy_body = _body(output, "void EXPERT::CloseBuySide", "void EXPERT::CloseSellSide")
    sell_body = _body(output, "void EXPERT::CloseSellSide", "void EXPERT::CLOSE_BUY")

    for body, side in ((buy_body, "POSITION_TYPE_BUY"), (sell_body, "POSITION_TYPE_SELL")):
        side_check = body.index(f"pt != {side}")
        zero_mutation = body.index("if (price == 0)")
        assert side_check < zero_mutation


def test_input_has_no_unused_buyposcnt_estimate() -> None:
    assert "BuyPosCnt" not in _text(INPUT)


def test_count_active_by_type_removed() -> None:
    # Audit U4: after Task 3 removes the BuyPosCnt call site in INPUT.mqh,
    # CountActiveByType in FUNCTIONS.mqh becomes dead code (only call site was
    # INPUT.mqh:18). Keeping it risks a `0 warnings` compile-gate regression.
    assert "CountActiveByType" not in _text(FUNCTIONS)


def test_diagnostic_lifecycle_uses_multi_ticket_tracker() -> None:
    ml_signal = _text(ML_SIGNAL)
    assert "MT5_TRACKED_POSITION" in ml_signal
    assert "MT5_TrackedPositions[]" in ml_signal
    assert "MT5_TrackedTicket" not in ml_signal
    assert "MT5_FindTrackedIndexByTicket" in ml_signal
    assert "MT5_LogLifecycleForTicket" in ml_signal
    # NEW (A5 cleanup): closed tracked positions must be compacted out of the active array.
    assert "MT5_TrackedPositionCount--" in ml_signal or "close_logged" in ml_signal


def test_position_tracker_ticket_uses_ulong() -> None:
    functions = _text(FUNCTIONS)
    assert "struct POSITION_TRACKER { ulong ticket;" in functions
    assert "int FindPosIndexByTicket(ulong ticket)" in functions
    assert "void RemovePositionByTicket(ulong ticket)" in functions
