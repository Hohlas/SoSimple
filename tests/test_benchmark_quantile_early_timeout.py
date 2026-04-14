import math

import pandas as pd

from ML.benchmark_quantile_early_timeout import (
    compute_metrics,
    decide_hold12_gate,
)


def test_compute_metrics_counts_pf_from_named_pnl_column():
    frame = pd.DataFrame({"pnl_atr": [2.0, -1.0, 3.0, 0.0]})

    result = compute_metrics(frame, pnl_column="pnl_atr")

    assert result["n_trades"] == 4
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0
    assert result["win_rate"] == 0.5
    assert result["mean_pnl_atr"] == 1.0


def test_compute_metrics_returns_inf_pf_without_losses():
    frame = pd.DataFrame({"pnl_atr": [1.0, 2.0]})

    result = compute_metrics(frame, pnl_column="pnl_atr")

    assert result["pf"] == math.inf
    assert result["losses"] == 0


def test_decide_hold12_gate_passes_when_hold12_is_stable():
    result = decide_hold12_gate(
        hold24_pf=8.0,
        hold12_pf=10.0,
        hold12_n_trades=48,
        hold12_negative_year_slices=0,
        seed_pf_values=[9.0, 8.0, 7.5, 11.0, 6.0],
    )

    assert result == {"verdict": "gate_pass", "reasons": []}


def test_decide_hold12_gate_rejects_pf_collapse():
    result = decide_hold12_gate(
        hold24_pf=8.0,
        hold12_pf=0.9,
        hold12_n_trades=48,
        hold12_negative_year_slices=0,
        seed_pf_values=[9.0, 8.0, 7.5, 11.0, 6.0],
    )

    assert result["verdict"] == "gate_fail"
    assert "hold12_pf=0.9000 <= 2.0" in result["reasons"]
